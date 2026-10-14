# Deploying MLflow and DVC on ArvanCloud

[toc]

## High Level Design of this task



![](.\HLD\HLD.drawio.png)

## Step 0: Prereqsites 

Before you begin, ensure you have the following:

1. **ArvanCloud Account:** An active account with ArvanCloud.

2. **Python Environment:** A Python environment with `mlflow`, `dvc`, `boto3`, `psycopg2-binary` and `s3fs` installed.

   ```bash
   scp -i ~/.ssh/ar-arvan-privatekey.pem  vm_setup_script.sh ubuntu@37.32.13.17:~/
   
   sudo apt update && sudo apt upgrade -y
   
   sudo apt install -y python3-pip postgresql
   
   pip install mlflow dvc boto3 s3fs psycopg2-binary
   ```
   
   

## Step 1: Set Up ArvanCloud Object Storage (S3 Compatible)

ArvanCloud's Object Storage is S3-compatible, which makes it straightforward to integrate with MLflow and DVC.

**Create a Bucket:**

- Log in to your ArvanCloud console.
- Navigate to the "Object Storage" service.
- Create a new bucket. Choose a unique name (e.g., `mlflow-bucket-INITIALs`) and select an appropriate region.

## Step 2: Configure DVC to Use ArvanCloud Object Storage

DVC will use your ArvanCloud bucket as its remote storage for data and model versions.

1. **Configure S3 Credentials and Endpoint:** DVC needs to know your ArvanCloud credentials and the custom endpoint. You can configure this globally or per-project.

   - **Per-Project (Recommended for specific projects):** Edit your `.dvc/config.local`. file to add the following lines:

     ```
     [core]
         remote = arvancloud-remote
     
     ['remote "arvancloud-remote"']
         url = s3://YOUR-BUCKET-NAME/dvc_data
         endpointurl = https://s3.ir-thr-at1.arvanstorage.ir
         access_key_id = YOUR-ACCESS-KEY
         secret_access_key = YOUR-SECRET-KEY
     ```

     **🚩 Security Note:** Storing credentials directly in `config` is not ideal for production.
     🚩  In `s3://my-bucket-name/dvc_data/`: 
     
     - **Bucket:** `my-bucket-name`
     - **Prefix:** `dvc_data/`
     - **Full S3 URI:** `s3://my-bucket-name/dvc_data/`
     - **Key:** `dvc_data/models/model.pkl`
     - **Value:** The content of file `model.pkl`
     
     

3. **Push DVC Data:** Now you can push your DVC-tracked data to ArvanCloud:

   ```bash
   # install this on your local machine
   pip install dvc-s3
   
   git init
   dvc init
   touch .gitignore ; echo -e "nMLflow-3\nvm_setup_script.sh" >> .gitignore
   
   dvc push
   
   #after any change
   dvc status
   dvc commit
   dvc push
   
   #delete some files
   dvc pull
   ```



## Step 3: Configure MLflow to Use ArvanCloud Object Storage

MLflow needs a backend store for metadata (runs, parameters, metrics) and an artifact store for models, plots, etc.

### Remote MLflow Tracking Server with ArvanCloud Backend and Artifact Store

For a more robust setup, especially for collaborative projects, you'll want a centralized MLflow Tracking Server. This server will store both metadata and artifacts in your ArvanCloud bucket.

This requires deploying a server. ArvanCloud offers various compute services (e.g., Virtual Servers, Kubernetes Service).

1. **Choose a Compute Service:**

   - **ArvanCloud Virtual Servers:** The simplest way to get started. Provision a VM, install Python, MLflow, and run the server.

2. **Database for Backend Store:** MLflow needs a database for its backend store (metadata). While SQLite works for local testing, for a remote server, you'll need a proper database like PostgreSQL or MySQL. ArvanCloud might offer managed database services, or you can install one on your VM.

   - **Example (PostgreSQL on a VM):** Install PostgreSQL on your ArvanCloud VM. Create a database and a user for MLflow.

     ```bash
     sudo -u postgres psql;
     
     CREATE DATABASE mlflow_db;
     
     #Linux cli
     openssl rand -base64 15 | head -c 20 ; echo
     
     CREATE USER mlflow_user WITH PASSWORD 'm/kEI58YmP/DtyRfIcbIl';
     
     GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow_user;
     
     ALTER DATABASE mlflow_db OWNER TO mlflow_user;
     
     \c mlflow_db
     
     ALTER SCHEMA public OWNER TO mlflow_user;
     
     \q
     ```

3. **Run MLflow Tracking Server:** On your ArvanCloud VM, run the MLflow server command:

   ```bash
   export AWS_ACCESS_KEY_ID="YOUR-ACCESS-KEY"
   export AWS_SECRET_ACCESS_KEY="YOUR-SECRET-KEY"
   export MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir" 
   
   # Start the MLflow Tracking Server
   mlflow server \
       --backend-store-uri postgresql+psycopg2://mlflow_user:m/kEI58YmP/DtyRfIcbIl@localhost/mlflow_db \
       --default-artifact-root s3://YOUR-BUCKET-NAME/mlflow_artifacts \
       --host 0.0.0.0 \
       --port 5000 \
       --allowed-hosts "*" \
       --cors-allowed-origins "http://YOUR-SERVER-IP:5000"
   ```

   - 🚩 `--host 0.0.0.0` makes the server accessible externally. Ensure your VM's firewall rules allow inbound traffic on port `5000`.
   - 🚩 You can see the docs of `tracking server` here: https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/

   - 🚩 **`mlflow ui` vs `mlflow server`**:

   |        Aspect        |          `mlflow ui`           |           `mlflow server`           |
   | :------------------: | :----------------------------: | :---------------------------------: |
   |     **Purpose**      |   Development/local tracking   |        Production deployment        |
   | **Backend Storage**  | SQLite database at `mlflow.db` |  PostgreSQL, MySQL, SQLite, MSSQL   |
   | **Artifact Storage** |     Local filesystem only      |   S3, Azure Blob, GCS, NFS, etc.    |
   |  **Authentication**  |              None              | 🔴Built-in authentication (optional) |
   |   **Scalability**    |      Single user/process       |    Multi-process, load balancing    |
   |     **Use Case**     | Local experiments, quick setup |   Team collaboration, production    |

   

4. **Accessing the Remote Tracking Server:** Once the server is running, you can point your`MLFLOW_TRACKING_URI` to its public IP address or domain name. But first, on your local machine export these variables:

   ```bash
   $env:AWS_ACCESS_KEY_ID="YOUR-ACCESS-KEY"
   $env:AWS_SECRET_ACCESS_KEY="YOUR-SECRET-KEY"
   $env:MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir"
   ```

   Now, run your python scripts just add this line on them `mlflow.set_tracking_uri("http://YOUR_ARVANCLOUD_SERVER_IP:5000")`.

   

### Now check the PostgreSQL

Want to see inside the database?

```bash
psql -h localhost -U mlflow_user -d mlflow_db

\dt

SELECT * FROM experiments;
```



