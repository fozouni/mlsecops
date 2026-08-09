```powershell
docker build -t insecure .
```

```powershell
docker inspect insecure-1:latest

docker history --no-trunc insecure-1:latest
```



> Note: 
> `docker history` → reads the **image's layer history**.
> `docker inspect` → reads the **image's metadata/configuration**.



## Result

```powershell
PS E:\MLSecOps\Contents\04-MLSecOps-Docker-03-Security\04-Docker-03-P2\Dockerfile-Examples\Bad-Docker-Images-1> docker inspect insecure-1:latest
[
    {
        "Id": "sha256:d650f61ae75a36171ae125fe18e2025b98959ff04279b3dbfbc1266b8ee0f0a3",
        "RepoTags": [
            "insecure-1:latest"
        ],
        "RepoDigests": [],
        "Comment": "buildkit.dockerfile.v0",
        "Created": "2026-06-16T00:01:29.967161902Z",
        "Config": {
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
              🔴  "API_KEY=my-super-secret-key"
            ],
            "Cmd": [
                "sh"
            ],
            "WorkingDir": "/",
            "ArgsEscaped": true
        },
        "Architecture": "amd64",
        "Os": "linux",
        "Size": 8415579,
        "GraphDriver": {
            "Data": {
                "MergedDir": "/var/lib/docker/overlay2/8a04d09c4a6c842753e84358a67a56835e1d79d61d4d452980fecd7c7de5284b/merged",
                "UpperDir": "/var/lib/docker/overlay2/8a04d09c4a6c842753e84358a67a56835e1d79d61d4d452980fecd7c7de5284b/diff",
                "WorkDir": "/var/lib/docker/overlay2/8a04d09c4a6c842753e84358a67a56835e1d79d61d4d452980fecd7c7de5284b/work"
            },
            "Name": "overlay2"
        },
        "RootFS": {
            "Type": "layers",
            "Layers": [
                "sha256:34884abbe92863fce933ed7c39c0e045631af0ed86d5cc0dfbdf9fdca426ce3c"
            ]
        },
        "Metadata": {
            "LastTagTime": "2026-08-07T11:28:54.423910036Z"
        }
    }
]
```

