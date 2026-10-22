##########################################################################
##########################################################################
# Description: This script provision the server for Jenkins task as a part of MLSecOps in Action Course
# Author: Mohammad Fozouni (Ph.D.)
# URL: https://m-fozouni.ir/mlsecops
# Date: 21 Oct 2026
##########################################################################
##########################################################################

#!/bin/bash

set -e
# makes the script fail fast. It immediately stops execution if
# any command returns a non-zero exit code (fails).

echo "🚀 Starting VM setup..."
echo "127.0.1.1 $(hostname)" | sudo tee -a /etc/hosts
# The above command yields no warning on the console for HostName related issues

echo "🚀 Updating system packages..."
sudo DEBIAN_FRONTEND=noninteractive apt update && sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y

echo "🚀 Installing system packages (python3-venv, postgresql, openjdk-21-jre)..."

# OpenJDK 21+ JRE is required for Jenkins
sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-venv postgresql-16 openjdk-21-jre

echo "🚀 Installing Python packages..."

python3 -m venv .venv

.venv/bin/pip install -r requirements-server.txt

#🚩🚩🚩  Jenkins
##########################################################################
##########################################################################

echo "🚀 Installing Jenkins..."
# Add the Jenkins GPG key
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key

# Add the Jenkins apt repository
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# Update apt cache and install Jenkins, making sure it's non-interactive
sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y jenkins=2.580.1

echo ""
echo ""
echo "✅ VM setup completed successfully. But let us enable Jenkins also for you 😎"
echo ""
echo ""


echo "🚀 Starting and enabling Jenkins service..."
sudo systemctl start jenkins  
sudo systemctl enable jenkins 

echo "🚀 Jenkins service status:"
sudo systemctl status jenkins --no-pager

# Shows the current status of Jenkins service (running/stopped/failed).
# We added --no-pager to the status command so it doesn't hang waiting for user input in an automated script. 


#🚩🚩🚩  Traefik
##########################################################################
##########################################################################

echo "🚀 We are going to install and config Traefik!"
echo "🚀 Now let's go for setting uo the Traefik VERSION 3.7.15"

# wget https://github.com/traefik/traefik/releases/download/v3.6.5/traefik_v3.6.5_linux_amd64.tar.gz
wget https://github.com/traefik/traefik/releases/download/v3.7.16/traefik_v3.7.16_linux_amd64.tar.gz

sudo tar -xf traefik_v3.7.16_linux_amd64.tar.gz -C /usr/local/bin
# This makes 'traefik' command available system-wide

rm traefik_v3.7.16_linux_amd64.tar.gz

sudo mkdir -p /etc/traefik ; sudo mkdir -p /var/log/traefik
# /etc/traefik: Configuration directory
# /var/log/traefik: Log directory
# -p flag: create parent directories if they don't exist

sudo mv Traefik/*.yml /etc/traefik
# Moves YAML config files to /etc/traefik

sudo useradd --system --no-create-home --shell /bin/false traefik
# --system: Creates a system user (not for human login)
# --no-create-home: Don't create home directory (not needed for service)
# --shell /bin/false: Prevents login/shell access (security measure)
# traefik: Username
# This follows security best practice: run services with minimal privileges

sudo touch /etc/traefik/acme.json
# Creates empty file for storing Let's Encrypt SSL certificates

sudo chmod 600 /etc/traefik/acme.json
# Sets permissions: only owner (traefik) can read/write, no one else (security)
# 600 = owner: read+write, group: none, others: none

sudo chown -R traefik:traefik /etc/traefik
# Recursively changes ownership of /etc/traefik to traefik user
# -R: recursive (applies to all files and subdirectories)

sudo chown -R traefik:traefik /var/log/traefik
# Recursively changes ownership of log directory

sudo chmod 755 /etc/traefik

sudo chmod 644 /etc/traefik/traefik.yml ; sudo chmod 644 /etc/traefik/dynamic.yml


#🚩🚩🚩  PostgreSQL
##########################################################################
##########################################################################
echo "🚀 Create database"

sudo -u postgres psql -v ON_ERROR_STOP=1 <<EOF
CREATE USER mlflow_user WITH PASSWORD 'c9e4f401065060100f03ad43bb2d35b4';
CREATE DATABASE mlflow_db OWNER mlflow_user;
\c mlflow_db
ALTER SCHEMA public OWNER TO mlflow_user;
EOF


echo ""
echo ""
echo "✅ Enjoy youe techy life 😂🚀"
echo ""
echo "🚀 Now you should run 'sudo traefik --configfile=/etc/traefik/traefik.yml' if you wanted to run TRaefik "