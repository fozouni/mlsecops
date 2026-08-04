# Some Basic Commands of Docker

[toc]

## Set up the registry mirror of Docker 

In the `setting > docker engine` path set the following item:

```json
{
  "registry-mirrors": [
    "https://docker.arvancloud.ir/"
  ]
}
```

> Mine 👇👇👇
>
> ```bash
> "registry-mirrors": [
>  "https://docker.iranserver.com"
> ]
> 
> # or you can use both as follows
> 
> "registry-mirrors": [
>     "https://docker.iranserver.com",
>     "https://docker.arvancloud.ir/"
>   ]
> ```

Docker will first check if the image is available on ` https://docker.arvancloud.ir/`. If the image is found there, it will be downloaded from that mirror instead of the default Docker Hub. This is a good job for Iranian citizens which are banned!

## Commands

```powershell
docker version

docker login

docker ps --all

docker pull hello-world

docker run hello-world

docker run --name hello-container hello-world 

docker rm <CONTAINER ID 1> <CONTAINER ID 2> 

docker images | findstr redis

docker rm --volumes redis

docker rmi redis

🛑 see the following note please.
```

```bash
PS C:\Users\User> docker rmi --help

Usage:  docker rmi [OPTIONS] IMAGE [IMAGE...]

Remove one or more images

Aliases:
  docker image rm, docker image remove, docker rmi

Options:
  -f, --force      Force removal of the image
      --no-prune   Do not delete untagged parent
```



## Pulling and Pushing in Docker 

```powershell
docker tag hello-world fozouni/hello-mlsecops:v1

docker push fozouni/hello-mlsecops:v1

🚀 Done. All guys can use it!
```



## Separating a long command in cli

```bash
# in windows 
docker `
> image `
> ls

# in linux
docker \
> image \
> ls 
```



## Go inside the running container

```bash
docker pull fozouni/absenteeism:first_try

docker run -d -p 8502:8501 fozouni/absenteeism:first_try
# port 8501 will goes to 8502 on our local machine

docker exec -it <CONTAINER ID> bash

cd /
cat /etc/os-release 

docker run -d <CONTAINER ID>
# -d, --detach Run container in background and print container ID

docker logs <CONTAINER ID> 

docker rm $(docker ps -q -a)
```



## A magic command

```bash
# Open yor Powershel in admin mode. Then

net stop hns

net start hns

# These commands will remove the port conflict error.  
```



## Three different approaches for using Docker 

1. Docker desktop 🔴
2. Docker desktop while you tick the WSL integration 🟡
3. Docker on your WSL 🟢

Generally, **Docker on WSL can offer the best performance**, followed by Docker Desktop with WSL integration, and then Docker Desktop without WSL integration. But if you have **enough compute recourses,** go on with Docker desktop. It's OK. 
