#!/bin/bash
set -e

echo "🚀 Starting VM setup ..."

sudo DEBIAN_FRONTEND=noninteractive apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-venv postgresql-16

python3 -m venv .venv

.venv/bin/pip install -r requirements-server.txt

sudo -u postgres psql -v ON_ERROR_STOP=1 <<EOF
CREATE USER mlflow_user WITH PASSWORD 'c9e4f401065060100f03ad43bb2d35b4';
CREATE DATABASE mlflow_db OWNER mlflow_user;
\c mlflow_db
ALTER SCHEMA public OWNER TO mlflow_user;
EOF

echo ""
echo "ENJOY 😎"