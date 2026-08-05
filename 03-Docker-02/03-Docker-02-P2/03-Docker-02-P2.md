# Commit, Save and Load, run direct command and Docker Network

[toc]

## Commit changes in a running container

First of all, note that this process gives us a new image.

```bash
docker commit CONTAINER_ID fozouni/web:v1

# Now run this command to see the result
docker images
```



## Save and Load docker images

```bash
docker save -o [filename].tar [image]

docker save -o [filename].tar [image1] [image2] [image3] [...]

docker load -i [filename]
```



## See shells inside container

```bash
docker exec CONTAINER_ID cat /etc/shells
```

everything after `docker exec CONTAINER_ID` is a command running inside the container. For example

```bash
docker compose exec web env | grep REDIS
```

get the `env` from `web` service and grep for us the REDIS value.



## Docker Network Drivers

Do not need to know and practice with all, but if we know these concepts it's good for our understanding.

|   Driver    |                   What it is                   |                         Typical use                          |
| :---------: | :--------------------------------------------: | :----------------------------------------------------------: |
| **bridge**  |   Private virtual network on one Docker host   |               ✅ Default for most applications                |
|  **host**   |   Container uses the host's network directly   |           High-performance apps, monitoring agents           |
|  **none**   |              No networking at all              | Maximum isolation, batch jobs, **for jobs that security matter much** |
| **overlay** | Virtual network spanning multiple Docker hosts |              Docker Swarm, multi-host clusters               |
| **macvlan** | Container gets its own IP on the physical LAN  |           Legacy applications, network appliances            |
| **ipvlan**  |     Similar to macvlan but more efficient      |                   Large-scale deployments                    |



### Bridge

```
Container A ──┐
              ├── Docker Bridge ── Host
Container B ──┘
```

- Containers talk to each other.
- Isolated from the outside.
- Use `ports:` to expose services.





