# Docker Volume Types

[toc]

## 1. Named Volume
```yaml
services:
  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```
Managed by Docker, easy to identify (`myproject_redis-data`), persists across `down`.



## 2. Anonymous Volume

```yaml
services:
  redis:
    image: redis:alpine
    volumes:
      - /data  # Just a path, no name, inside the container.
      # We do not named the host machine's volume. So docker automatically set a hashed name.
```
Managed by Docker but no name (random hash), harder to track, removed with `down -v`.

> 🔴 `down -v` → **both** named and anonymous volumes will be deleted.
>
> ```powershell
> # get the list of volumes
> docker volume ls
> ```



## 3. Bind Mount

```yaml
services:
  redis:
    image: redis:alpine
    volumes:
      - ./data:/data
```
Maps a host folder directly, useful for local dev (e.g. live code sync), not managed by Docker.



> **Named Volumes is the Best for Production Env.** They're Docker-managed, portable, easy to back up/inspect, and don't depend on host filesystem paths.



## Summarize:

- **`./redis-data`**  is a bind mount. It means same folder, relative to the compose file's location.

- **`redis-data`** (bare name) NOT declared under top-level `volumes:` (last lines) give us error, not treated as a relative path.

  ```powershell
  PS C:\Users\User\Desktop> docker compose up
  
  service "redis" refers to undefined volume redis-data: invalid compose project
  ```




## Some top level keys in compose file

```yaml
services:    # defines your containers (web, redis, db, etc.) — ✅ 
volumes:     # declares named volumes for persistent data  — ✅
networks:    # declares custom networks for container communication  — ✅

configs:     # non-sensitive config files shared with containers  — 🟨
secrets:     # sensitive data (passwords, keys) — Docker manages securely — 🟨

# ✅ means very important and widely used
# 🟨 means often used, not always or much
```



## One Important Note

**Question:** Why after copying file `requirements.txt` again we run `COPY . .`?

```yaml
FROM python:3.12-alpine

WORKDIR /code

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

RUN apk add --no-cache gcc musl-dev linux-headers

# HERE 👇
COPY requirements.txt . # COPY . .

RUN pip install -r requirements.txt

# HERE 👇
COPY . .  # app.py edit

EXPOSE 5000

CMD ["flask", "run", "--debug"]
```



### Why copy `requirements.txt` separately first

Docker builds images in **layers**, one per instruction. Each layer is **cached** based on the instruction and the content it depends on. If nothing changed for a given layer, Docker reuses the cached layer instead of re-running it.

If you only edited your Python source code (`app.py`, templates, etc.), Docker sees that `requirements.txt` is unchanged, reuses the cached `pip install` layer, and skips straight to copying your updated code.

**AND THIS IS FASCINATING 🚀.**
