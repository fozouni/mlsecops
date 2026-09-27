# Provisioning a Real-World Cluster of Kubernetes by Kubeadm ⚓

1. First go to the AbrArvan panel and create three servers in the `eu-west1` region. 

2. Name servers like this:
   i: master
   ii: worker-1
   iii: worker-2

3. Wait a little and then copy the IPs.

4. Now fill in the IPs in this config file

   ```bash
   StrictHostKeyChecking no
       
   Host master
       HostName IP-OF-MASTER
       User ubuntu
       IdentityFile ~/.ssh/ar-arvan-privatekey.pem    
   
   Host worker-1
       HostName IP-OF-WORKER-1
       User ubuntu
       IdentityFile ~/.ssh/ar-arvan-privatekey.pem
   
   Host worker-2
       HostName IP-OF-WORKER-2
       User ubuntu
       IdentityFile ~/.ssh/ar-arvan-privatekey.pem
   ```

5. Put the above config file at this address for example `~/.ssh/` of your Linux.

6. From now on simply with command `ssh master` we can go inside master server. Similarly for workers we can do. 

7. From your local system SCP some files into servers:

   ```bash
   cd to the root of project
   
   scp  setup-master.sh ubuntu@master:/home/ubuntu/
   
   scp  setup-worker.sh ubuntu@worker-1:/home/ubuntu/
   
   scp  setup-worker.sh ubuntu@worker-2:/home/ubuntu/
   ```

8. Now SSH into your servers and run these commands:

   ```bash
   # from master
   sudo ./setup-master.sh
   
   # from worker-1
   sudo ./setup-worker
   
   # from worker-2
   sudo ./setup-worker
   ```

   🚩 In the above scripts, instead of Docker we will install `Containerd`, because Kubernetes has deprecated Docker as a runtime since v1.20 (fully removed in v1.24+), favoring lightweight CRI-compliant runtimes like `Containerd`.
   
9. At this time you should copy the config file from `.kube` directory of master by running this command:

   ```bash
   scp ubuntu@master:/home/ubuntu/.kube/config ./config
   ```

10. Copy the `config` file to the directory `C:\Users\User\.kube`. Note that in this directory, there is one config file. Rename the old config file to something like `config-minikube`. Now if you run 

    ```bash
    kubectl get nodes
    ```

    we should see the list of our servers that at this stage is just master one.

11. At the home directory of the master node, a file has been generated named `k8s-join-command.txt`. Cat this file and copy its contents. Now go to workers and do this:

    ```bash
    sudo $(cat k8s-join-command.txt)
    ```

    At this point if you get `kubectl get nodes` we should see the three servers. 

| DONE . Now everything is ready to do our job. DONE 🚀 |
| :--------------------------------------------------: |





