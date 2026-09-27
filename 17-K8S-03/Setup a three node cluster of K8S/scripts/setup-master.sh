#!/bin/bash

# 🚩 From time to time, you may need to revise this script.

# 🚩 This script is used in making our master node ready. 

# 🟢 Exit on any error
# The below command exits on any command failure
# (e.g., curl for GPG keys/repos fails on 404/expired URL), printing
# the exact error (e.g., "curl: (22) The requested URL returned error: 404")
set -e  

echo "Starting Kubernetes master node setup. JUST WAIT 😎"

# 🚩 Step 1: Disable Swap

echo "Step 1: Disabling swap..."
swapoff -a
sed -i '/ swap / s/^/#/' /etc/fstab

echo "Swap disabled. Verify with 'free -h'."

# 🚩 Enable IP Forwarding (Fix for preflight error)

echo "Enabling IP forwarding (persistent)..."
sysctl net.ipv4.ip_forward=1
echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
sysctl -p
echo "IP forwarding enabled. Verify with 'cat /proc/sys/net/ipv4/ip_forward' (should be 1)."

# 🚩 Step 2: Install Containerd Runtime

echo "Step 2: Installing containerd..."
apt-get update
apt-get install -y ca-certificates curl gnupg

# 🚩 Add Docker's GPG key and repository for containerd.io

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y containerd.io

# 🚩 Configure containerd

containerd config default | tee /etc/containerd/config.toml
sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sed -i 's/cri\/sandbox_image = ""/sandbox_image = "registry.k8s.io\/pause:3.10"/' /etc/containerd/config.toml

systemctl restart containerd
systemctl enable containerd
echo "Containerd installed and configured. Verify with 'ctr version'."


# 🚩 Step 3: Install kubeadm, kubelet, and kubectl

echo "Step 4: Installing kubeadm, kubelet, and kubectl (v1.34.x)..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg

# 🚩 Download Kubernetes GPG key

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# 🚩 Add Kubernetes APT repository

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list

apt-get update
apt-get install -y kubelet kubeadm kubectl

# 🚩 Hold versions to prevent upgrades

apt-mark hold kubelet kubeadm kubectl

# 🚩 Enable kubelet

systemctl enable --now kubelet
echo "Kube tools installed. Verify with 'kubectl version --client'."

# 🚩 Step 4: Initialize the Master Node

echo "Step 5: Initializing Kubernetes cluster..."

# 🚩 Pull images (optional, but speeds up if no internet later)
kubeadm config images pull

# 🚩 Initialize with CRI socket

kubeadm init --cri-socket unix:///var/run/containerd/containerd.sock

# 🚩 Save the join command to a file for easy copy-paste

kubeadm token create --print-join-command > ./k8s-join-command.txt
echo "Cluster initialized! The 'kubeadm join' command for workers is saved to /tmp/k8s-join-command.txt."
echo "Copy it and run on worker nodes: cat /tmp/k8s-join-command.txt"

# 🚩 Set up kubeconfig for non-root user (assumes 'ubuntu'; adjust USERNAME if needed)

USERNAME=${SUDO_USER:-ubuntu}
mkdir -p /home/$USERNAME/.kube
cp -i /etc/kubernetes/admin.conf /home/$USERNAME/.kube/config
chown $(id -u $USERNAME):$(id -g $USERNAME) /home/$USERNAME/.kube/config
echo "Kubeconfig set up for user '$USERNAME'. Test with: su - $USERNAME -c 'kubectl get nodes'."

# 🚩 Install Weave Net CNI
# 🟢 Weave Net CNI is a lightweight, easy-to-install networking plugin for Kubernetes#
# that enables pod-to-pod communication across nodes (via VXLAN overlay)

echo "Installing Weave Net CNI..."
su - $USERNAME -c "kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml"
echo "Weave Net applied. Wait ~1-2 min for nodes to be Ready: su - $USERNAME -c 'kubectl get nodes'."

echo "Master setup complete! Monitor with: su - $USERNAME -c 'kubectl get pods --all-namespaces'."
echo "CoreDNS and Weave pods should be Running soon."

echo "You can add any line or command here to be used later"
echo ""
echo ""
echo "🟢🟢🟢 DONE! 🟢🟢🟢"
echo "🍵🍵🍵 Enjoy your day with a cup of coffee 🍵🍵🍵"
echo ""
echo ""