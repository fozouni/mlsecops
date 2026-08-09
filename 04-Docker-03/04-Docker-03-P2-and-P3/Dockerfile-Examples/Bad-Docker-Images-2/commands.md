```powershell
docker build `
  --build-arg HF_TOKEN=hf_123456789_SECRET `
  -t insecure-2:latest .
```

```powershell
docker history insecure-2:latest

docker inspect insecure-2:latest
```



> Note: 
> `docker history` → reads the **image's layer history**.
> docker inspect` → reads the **image's metadata/configuration**.



## Output

```powershell
PS E:\MLSecOps\Contents\04-MLSecOps-Docker-03-Security\04-Docker-03-P2\Dockerfile-Examples\Bad-Docker-Images-2> docker history  insecure-2:latest
IMAGE          CREATED              CREATED BY                                      SIZE      COMMENT
31452068d295   About a minute ago   CMD ["sh"]                                      0B        buildkit.dockerfile.v0
<missing>      About a minute ago   RUN |1 HF_TOKEN=hf_123456789_SECRET /bin/sh …   0B        buildkit.dockerfile.v0
<missing>      About a minute ago   ARG HF_TOKEN=hf_123456789_SECRET                0B        buildkit.dockerfile.v0
<missing>      7 weeks ago          CMD ["/bin/sh"]                                 0B        buildkit.dockerfile.v0
<missing>      7 weeks ago          ADD alpine-minirootfs-3.24.1-x86_64.tar.gz /…   8.42MB    buildkit.dockerfile.v0
```

