# Buildkit read from file

```powershell
docker build `
  --secret id=api_key,src=api_key.txt `
  -t secure .
  
# or

docker buildx build `
	--secret id=api_key,src=api_key.txt `  #gitleaks:allow
	-t securex .  
```



> In modern Docker Desktop, `docker build` is BuildKit-powered by default. `docker buildx build` is the explicit BuildKit command and is preferred when using advanced BuildKit features.



```powershell
docker inspect secure

docker history secure
#or
docker history --no-trunc secure
```



## Output

```powershell
PS E:\MLSecOps\Contents\04-MLSecOps-Docker-03-Security\04-Docker-03-P2\Dockerfile-Examples\Good-Docker-Image> docker history secure
IMAGE          CREATED          CREATED BY                                      SIZE      COMMENT
c4f0a93a101b   21 seconds ago   CMD ["sh"]                                      0B        buildkit.dockerfile.v0
<missing>      21 seconds ago   RUN /bin/sh -c cat /run/secrets/api_key > /t…   0B        buildkit.dockerfile.v0
<missing>      7 weeks ago      CMD ["/bin/sh"]                                 0B        buildkit.dockerfile.v0
<missing>      7 weeks ago      ADD alpine-minirootfs-3.24.1-x86_64.tar.gz /…   8.42MB    buildkit.dockerfile.v0
```

