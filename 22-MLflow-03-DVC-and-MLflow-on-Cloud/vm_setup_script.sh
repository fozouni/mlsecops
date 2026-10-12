#!/bin/bash

set -e 

echo "🚀 Starting VM setup ..."

echo "🚀 Updating system packages ..."
sudo DEBIAN_FRONTEND=noninteractive apt update 

echo "🚀 Installing system packages ..."
sudo DEBIAN_FRONTEND=noninteractive apt install -y python3-pip python3.12-venv postgresql-16

echo ""
echo ""
echo "ENJOY 😎"