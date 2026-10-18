# MLflow Security Stuffs

[toc]

## 🔨 Configure DVC to Use ArvanCloud Object Storage

```
#config.local file content
[core]
    remote = arvancloud-remote

['remote "arvancloud-remote"']
    url = s3://YOUR_BUCKET_NAME/dvc_data
    endpointurl = https://s3.ir-thr-at1.arvanstorage.ir
    access_key_id = YOUR_ACCESS_KEY
    secret_access_key = YOUR_SECRET_KEY
```



## 🔨 Configure MLflow to Use ArvanCloud Object Storage

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir" 

# Start the MLflow Tracking Server
mlflow server \
    --backend-store-uri postgresql+psycopg2://mlflow_user:c9e4f401065060100f03ad43bb2d35b4@localhost/mlflow_db \
    --default-artifact-root s3://YOUR_BUCKET_NAME/mlflow_artifacts \
    --host 0.0.0.0 \
    --port 5000 \
    --allowed-hosts "*" \
    --cors-allowed-origins "http://YOUR_SERVER_IP:5000"
    
```



## 🔨 Configure vscode before doing anything

```bash
$env:AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
$env:AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
$env:MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir"
```



## ✅ Export these on the server for serving script

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export MLFLOW_S3_ENDPOINT_URL="https://s3.ir-thr-at1.arvanstorage.ir" 
export MLFLOW_TRACKING_URI=http://YOUR_SERVER_IP:5000  
export MODEL_VERSION=2
```

**Now**

```bash
python3 serve.py
```



## ✅ Check if the model works

```bash
curl -X POST http://YOUR_SERVER_IP:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"rows": [[13.2, 2.8, 2.5, 18, 100, 2.5, 2.4, 0.3, 1.8, 5, 1.0, 3, 1000]]}'
  
  
curl -X POST http://YOUR_SERVER_IP:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"rows": [[12.0, 0.92, 2.0, 19.0, 86, 2.42, 2.26, 0.3, 1.43, 2.5, 1.38, 3.12, 278]]}'
```



## ✅ Change the model file

```bash
python3 tamper.py 2 break

python3 serve.py
# won't work
```



## ✅ Setup systemd for mlflow

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
ExecStart=/home/ubuntu/.venv/bin/mlflow server --backend-store-uri ${MLFLOW_BACKEND_URI} --default-artifact-root s3://YOUR_BUCKET_NAME/mlflow_artifacts --host 0.0.0.0 --port 5000 --allowed-hosts "*" --cors-allowed-origins "http://YOUR_SERVER_IP:5000"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

> 1- With `Wants=network-online.target` plus `After=network-online.target`, MLflow tries to start only once the network is ready.
>
> 2- `After=postgresql.service` is about order. It tells systemd to start MLflow only after PostgreSQL has been started, because MLflow needs the database to be running.
>
> 3- `>/dev/null` yields that nothing printed on terminal

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mlflow
```



## ✅ Enable mlflow Auth

```bash
pip install 'mlflow[auth]'

# 🚩 Add the two secrets
echo "MLFLOW_FLASK_SERVER_SECRET_KEY=$(openssl rand -hex 32)" >> /etc/mlflow.env
echo "MLFLOW_AUTH_ADMIN_PASSWORD=38449b5002c6979ae516e73f16" >> /etc/mlflow.env

# 🚩 Turn on the auth and restart

sed -i 's|ExecStart=/home/ubuntu/.venv/bin/mlflow server |ExecStart=/home/ubuntu/.venv/bin/mlflow server --app-name basic-auth |' /etc/systemd/system/mlflow.service

# sed -i 's|OLD|NEW|' file

systemctl daemon-reload
systemctl restart mlflow
```



## ✅ Now check from vscode

```powershell
$env:MLFLOW_TRACKING_USERNAME = "admin"
$env:MLFLOW_TRACKING_PASSWORD = "38449b5002c6979ae516e73f16"

dvc repro
```

