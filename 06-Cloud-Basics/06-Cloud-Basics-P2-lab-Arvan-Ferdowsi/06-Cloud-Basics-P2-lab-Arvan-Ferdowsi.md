# ArvanCloud and Abr Ferdowsi

## Some useful Links

------

🚩 https://www.arvancloud.ir/fa

🚩 https://ferdowsi.cloud/fa

#### All SDK (Software Development Kit) documents

🚩 https://docs.arvancloud.ir/fa/developer-tools/sdk/

#### Upload to Bucket

🚩 https://docs.arvancloud.ir/fa/developer-tools/sdk/object-storage/upload-object/

#### Install s3Browser

🚩 https://www.arvancloud.ir/help/fa/object-s3browser/

------

## Setup our Cloud Instance

Move the `.pem` file in `~/amin/.ssh` for example. Then run the following command:

```bash
chmod 400 ar-arvan-privatekey.pem
```

From the directory which contains  this `.pem` file, run the following command:

```bash
ssh -i ar-arvan-privatekey.pem ubuntu@188.213.199.74
```

> **Help of SSH:**
>
> ```
> amin@ubuntu24:~$ ssh --help
> unknown option -- -
> usage: ssh [-46AaCfGgKkMNnqsTtVvXxYy] [-B bind_interface] [-b bind_address]
>            [-c cipher_spec] [-D [bind_address:]port] [-E log_file]
>            [-e escape_char] [-F configfile] [-I pkcs11] 🔴[-i identity_file]🔴
>            [-J destination] [-L address] [-l login_name] [-m mac_spec]
>            [-O ctl_cmd] [-o option] [-P tag] [-p port] [-R address]
>            [-S ctl_path] [-W host:port] [-w local_tun[:remote_tun]]
>            destination [command [argument ...]]
>        ssh [-Q query_option]
> ```



## One more convenient approach for SSH-ing

On the address `~/.ssh/` of your Linux create a file named `config` with the following lines:

```yaml
Host ferdowsi # write the name of your Server
    HostName 185.239.2.65 # The IP address of your Server
    User ubuntu # Default username is ubuntu
    Port 22 # Default port of SSH
    IdentityFile ~/.ssh/id_rsa # Address of your private key on your laptop
```

Now easily from cli just run the following command:

```bash
ssh ferdowsi

# ENJOY 🚀
```



## Check if our server has some tools or not

```bash
which python3

sudo apt update

sudo apt install python3-pip -y

which pip3

pip list
```

## One mirror for installation by pip

If the above `pip install` did not work, use the following mirror: 

```bash
pip install boto3==1.43.6 --index-url https://mirrors.aliyun.com/pypi/simple/
```

