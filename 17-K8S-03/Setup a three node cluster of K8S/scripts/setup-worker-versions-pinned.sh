#!/bin/bash

# 🚩 From time to time, you may need to revise this script.

# 🚩 This script is used in making our worker nodes ready. 

# 🚩 Pinned Versions (exact as of my installation on November 13, 2025)

CONTAINERD_VERSION="2.1.5-1~ubuntu.22.04~jammy"  
K8S_MINOR_VERSION="1.34"  
K8S_VERSION="1.34.2" 
K8S_PKG_VERSION="1.34.2-1.1"  

# 🟢 Exit on any error
# The below command exits on any command failure
# (e.g., curl for GPG keys/repos fails on 404/expired URL), printing
# the exact error (e.g., "curl: (22) The requested URL returned error: 404")
set -e  

echo "Starting Kubernetes worker node setup (pinned to Containerd ${CONTAINERD_VERSION}, K8s ${K8S_VERSION}). JUST WAIT 😎"

# 🚩 Step 1: Disable Swap

echo "Step 1: Disabling swap..."
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

echo "Swap disabled. Verify with 'free -h'."

# 🚩 Enable IP Forwarding (Required on all nodes to pass preflight checks during join)

echo "Enabling IP forwarding (persistent)..."
sysctl net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p
echo "IP forwarding enabled. Verify with 'cat /proc/sys/net/ipv4/ip_forward' (should be 1)."

# 🚩 Step 2: Install Containerd Runtime

echo "Step 2: Installing containerd ${CONTAINERD_VERSION}..."
apt-get update
apt-get install -y ca-certificates curl gnupg

# 🚩 Add Docker's GPG key and repository for containerd.io (non-interactive overwrite)

install -m 0755 -d /etc/apt/keyrings
yes | curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y containerd.io=${CONTAINERD_VERSION}

# 🚩 Configure containerd

containerd config default | tee /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sed -i 's/cri\/sandbox_image = ""/sandbox_image = "registry.k8s.io\/pause:3.10"/' /etc/containerd/config.toml

systemctl restart containerd
systemctl enable containerd
echo "Containerd ${CONTAINERD_VERSION} installed and configured. Verify with 'ctr version'."

# 🚩 Step 3: Install kubeadm, kubelet, and kubectl

echo "Step 3: Installing kubeadm, kubelet, and kubectl ${K8S_VERSION}..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg

# 🚩 Download Kubernetes GPG key (non-interactive; series-level repo)

yes | curl -fsSL https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR_VERSION}/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# 🚩 Add Kubernetes APT repository (pinned to series ${K8S_MINOR_VERSION})

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR_VERSION}/deb/ /" | tee /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y kubelet=${K8S_PKG_VERSION} kubeadm=${K8S_PKG_VERSION} kubectl=${K8S_PKG_VERSION}

# 🚩 Hold versions to prevent upgrades

apt-mark hold kubelet kubeadm kubectl

# 🚩 Enable kubelet

systemctl enable --now kubelet

echo "Kube tools ${K8S_VERSION} installed. Verify with 'kubectl version --client'."

echo "Setup complete! Now run the 'kubeadm join' command from the master node's init output on this worker."
echo ""
echo "After successful join (and on master, verify with 'kubectl get nodes'), assign the worker role label:"
echo "On the master node, run: kubectl label node <worker-node-name> node-role.kubernetes.io/worker="
echo "Example: kubectl label node worker-1 node-role.kubernetes.io/worker="
echo "This will update thes ROLES column from '<none>' to 'worker'. Repeat for each worker."
echo "If a node is NotReady, check logs: kubectl describe node <worker-node-name>"
echo "You can add any line or command here to be used later"
echo ""
echo ""
echo "🟢🟢🟢 DONE!"