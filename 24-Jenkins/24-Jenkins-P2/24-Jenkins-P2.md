# CI/CD in MLOps with Jenkins

[toc]

```bash
nano ~/.ssh/config
# Now paste the IP of your server

cd server-files/

scp -r Traefik/ provision.sh requirements.txt server:~/ 

ssh server
```

> Inside Traefik there are two files `traefik.yml` and `dynamic.yml`:
>
> 🚩 `traefik.yml` is responsible for **"starting Traefik up"** (static configuration).
>
> 🚩`dynamic.yml` is responsible for **"how to route requests"** (dynamic configuration).



## 1- Provision Server and Start Traefik 

```bash
./provision.sh

sudo traefik --configfile=/etc/traefik/traefik.yml
```

> For Traefik, we also can run it as a service using systemd. For this matter run the following commands:
>
> ```bash
> sudo tee /etc/systemd/system/traefik.service >/dev/null <<'EOF'
> [Unit]
> Description=Traefik Proxy
> After=network-online.target
> Wants=network-online.target
> 
> [Service]
> User=traefik
> Group=traefik
> ExecStart=/usr/local/bin/traefik --configFile=/etc/traefik/traefik.yml
> Restart=always
> # Allow binding to privileged ports (80, 443) without running as root
> AmbientCapabilities=CAP_NET_BIND_SERVICE
> LimitNOFILE=1048576
> 
> [Install]
> WantedBy=multi-user.target
> EOF
> 
> sudo systemctl daemon-reload
> sudo systemctl enable --now traefik
> ```
>
> Ans wanted to see logs in this scenario?
>
> ```bash
> sudo journalctl -u traefik -f
> ```



## 2- Set Up ArvanCloud Object Storage (S3 Compatible)

ArvanCloud's Object Storage is S3-compatible, which makes it straightforward to integrate with MLflow and DVC.

**Create a Bucket:**

- Log in to your ArvanCloud console.
- Navigate to the "Object Storage" service.
- Create a new bucket. Choose a unique name (e.g., `mlflow-bucket-INITIALs`) and select an appropriate region.

## 3- Configure DVC to Use ArvanCloud Object Storage

DVC will use your ArvanCloud bucket as its remote storage for data and model versions.

**Configure S3 Credentials and Endpoint:** DVC needs to know your ArvanCloud credentials and the custom endpoint. You can configure this globally or per-project.

- **Per-Project (Recommended for specific projects):** Edit your `.dvc/config.local` file to add the following lines:

  ```
  [core]
      remote = arvancloud-remote
  
  ['remote "arvancloud-remote"']
      url = s3:/YOUR_BUCKET_NAME/dvc_data
      endpointurl = https://s3.ir-thr-at1.arvanstorage.ir
      access_key_id = YOUR_ACCESS_KEY
      secret_access_key = YOUR_SECRET_KEY
  ```
  
  🚩 **Security Note:** Storing credentials directly in `config` is not ideal for production.



## 4- Configure MLflow to Use ArvanCloud Object Storage

MLflow needs a backend store for metadata (runs, parameters, metrics) and an artifact store for models, plots, etc.

### Remote MLflow Tracking Server with ArvanCloud Backend and Artifact Store `systemd`

```bash
sudo tee /etc/mlflow.env >/dev/null <<'EOF'
MLFLOW_BACKEND_URI=postgresql+psycopg2://mlflow_user:c9e4f401065060100f03ad43bb2d35b4@localhost/mlflow_db
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
MLFLOW_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir
EOF
sudo chmod 600 /etc/mlflow.env

sudo tee /etc/systemd/system/mlflow.service >/dev/null <<'EOF'
[Unit]
Description=MLflow Tracking Server
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
WorkingDirectory=/home/ubuntu
EnvironmentFile=/etc/mlflow.env
ExecStart=/home/ubuntu/.venv/bin/mlflow server --backend-store-uri ${MLFLOW_BACKEND_URI} --default-artifact-root s3:/YOUR_BUCKET_NAME/mlflow_artifacts --host 0.0.0.0 --port 5000 --allowed-hosts "*" --cors-allowed-origins "https://mlflow.elmedade.ir"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

and then

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mlflow

#🚩 restart the service if you have any specific changes like me in the video
sudo systemctl restart mlflow
```

If you wanted to see logs of mlflow service

```bash
sudo journalctl -u mlflow -f
```




## 5- ArvanCloud CDN configs

First add your domain in the CDN panel of ArvanCloud. Then set name servers in your domain registrar. After near 30 minutes your domain will be activated in ArvanCloud. 

For your domain `elmedade.ir` in the CDN of ArvanCloud create three A records for below subdomains and **turn the sign of cloud off** and for its server ip insert the ip address of the VM that you turned on at the beginning of session. 

1. mlflow.elmedade.ir
2. jenkins.elmedade.ir
3. traefik.elmedade.ir

**Note:** the name of subdomains is up to you.

**Note:** If you want to check if your settings are correct run the following command

```bash
dig mlflow.elmedade.ir +short
```



## 6- Github Configs

1. Create one **private repo** for example `jenkins`.
2. Create a token for this repo and define one webhook as follows as you saw in the video
   🚩 `https://jenkins.elmedade.ir/github-webhook/`
3. In the Jenkins panel, and from security/credentials define one item with **username and password**. Paste your username and and token there. 



## 7- Jenkins Items

### shared workspace

We set this address

```
/var/lib/jenkins/workspace/shared-workspace
```

for our three parts Freestyle projects.



### We setup these 3 items in Jenkins GUI:

#### 1-Fetch-Github-Repo

Copy this for workspace:

```
/var/lib/jenkins/workspace/shared-workspace
```

```bash
echo "✅ Fetching repo ..."

echo "🚩 current directory is" $WORKSPACE
```



#### 2-Train our Model

Copy this for workspace:

```
/var/lib/jenkins/workspace/shared-workspace
```

```bash
#!/bin/bash

export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"

export MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir"

export PATH="/var/lib/jenkins/.local/bin:$PATH"

python3 -m venv .venv

# python3 -m venv .venv;
# creates a virtual environment directory named .venv inside the current workspace (/var/lib/jenkins/workspace/shared-workspace/.venv),
# not on the "Jenkins controller VM" in any global sense

source .venv/bin/activate

pip install dvc[s3] pandas scikit-learn mlflow==3.17.0 joblib boto3

dvc repro

echo "✅ Now we send the latest changes of our data to our remote storage"
echo "🚀"
dvc push
```



#### 3-Update-Repo

Copy this for workspace:

```
/var/lib/jenkins/workspace/shared-workspace
```

```bash
git checkout -b Jenkins-$BUILD_NUMBER

git config --global user.email "YOUR_EMAIL"
git config --global user.name "YOUR_USERNAME"

git add .

git commit -m "This has been commited from Jenkins with $BUILD_NUMBER" 

git push https://YOUR_USERNAME:GITHUB_ACCESS_TOKEN@github.com/fozouni/YOUR_REPO_NAME.git HEAD:Jenkins-$BUILD_NUMBER
```

**Note:** `HEAD:main` specifies **what to push and where**:

- `HEAD` = the current commit/branch you're on locally
- `Jenkins-$BUILD_NUMBER` = the target branch on the remote repository

So it's pushing your current local commit to the `main` branch on GitHub. Without it, git would use default push behavior (which might not be what you want).

> 🚩 Before the first commit, touch a `.gitignore` file locally and paste the following directories in there
>
> ```bash
> __pycache__
> .venv/
> ```

## 8- Pull to your local System

```bash
git pull

git branch -a

# Since one branch hgas been created in GitHub we should do this in our local system to have that branch

git checkout -b Jenkins-1 origin/Jenkins-1
```



|                       Congratulation!                        |
| :----------------------------------------------------------: |
| 🚀 **Now pushing to the GitHub private repo, you will trigger your ML pipeline to be run** 🚀 |

