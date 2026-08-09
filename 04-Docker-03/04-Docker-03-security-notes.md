# Container and Image Security in Docker

[toc]

## 1- Image Security

![](.\Screens\Pictures\Image security.png)

### i: Base Image Hygiene (cleanliness)

- Prefer minimal, official, actively maintained base images (`python:3.12-slim`, `distroless`, `alpine` where compatible with ML libs).

- Pin base images by **digest**, not just tag {**latest**, **3.10.1**, **digest**}
   For example `FROM python@sha256:...` 

  Note that **tags are mutable but digests aren't**. 

  ```powershell
  # Find the digest of the tag you currently trust
  
  docker pull python:3.13
  
  docker inspect --format='{{index .RepoDigests 0}}'  python:3.13
  
  # Tag-based (mutable and may be risky)
  FROM  python:3.13
  
  # Digest-based (immutable, reproducible & safer)
  FROM python@sha256:36f5673...0ddbbb72e01b2930d7c12f19
  ```

  > **Why pin images by digest:**
  >
  > The short answer: **defense in depth**. Pinning the digest protects you even if the “immutable tag” promise is broken. Whether by accident, a registry compromise, or a man-in-the-middle attack. It is  possible that someone get access to this registry and change the content of python:3.13.1 and create a new digest. But if we get our desired image by digest this will be never happen. 
  
- Avoid `latest` tag in production and training pipelines.



### ii: Regularly rebuild images 

Regularly rebuild images to pull in upstream security patches; a "frozen" image silently rots.

```bash
# If we do not have a Dockerfile
docker pull mongo:8.0
# docker pull fetches whatever mongo:8.0 currently points to (with latest patches)

# If we have a Dockerfile
docker build --no-cache -t myapp-mongo:8.0 .
# --no-cache forces your build to actually use that fresh base instead of a cached old layer.
```

**Before-Re-Pull:**

```bash
# I have mongo:8.0 for a duration of time.
PS C:\Users\User> docker inspect mongo:8.0
[
    {
        "Id": "sha256:7281281f68a3b9eba843d8c65af4fa88ae90d584577f595baedc1b18c7ae2f38",
        "RepoTags": [
            "mongo:8.0"
        ],
        "RepoDigests": [
            🔴"mongo@sha256:3ce3de7f40e914034b03b7dec654005ab54f7dc8306937e44ec6760d9e9409a1"
        ],
        "Comment": "buildkit.dockerfile.v0",
🔴      "Created": "2026-07-02T02:31:22.625350578Z",
```

**After-Re-Pull:**

```bash
# After passing some times, again I pull mongo:8.0 and inspect. See this
PS C:\Users\User> docker inspect mongo:8.0
[
    {
        "Id": "sha256:c040b3a6249f5a9994729bb2a670ea5eb31c196122ffeb314ffc5c1ebc9192f5",
        "RepoTags": [
            "mongo:8.0"
        ],
        "RepoDigests": [
              🔴"mongo@sha256:5351bff2b5d1563e3fa603a74b9be85ef9323e10aeb0b45cea933a93876e77fd"
        ],
        "Comment": "buildkit.dockerfile.v0",
🔴      "Created": "2026-07-22T22:13:30.094611084Z",
```



### iii: Vulnerability Scanning

- Scan images in CI before push: **Trivy and Docker Scout** are two options.


  **We should install Trivy first:**

  ```powershell
  winget install AquaSecurity.Trivy
  # or just upgrade
  
  winget upgrade --id AquaSecurity.Trivy
  
  # My Trivy Version Rightnow
  PS C:\Users\User> trivy --version
  Version: 0.73.0
  Vulnerability DB:
    Version: 2
    UpdatedAt: 2026-07-25 07:31:15.040814353 +0000 UTC
    NextUpdate: 2026-07-26 07:31:15.040814092 +0000 UTC
    DownloadedAt: 2026-07-25 08:57:01.2574519 +0000 UTC
  ```

> ✅ See all executables in this address
> `C:\Users\User\AppData\Local\Microsoft\WinGet\Packages`

Scan for:
- OS package CVEs (✅ Trivy's core strength)

- Language-level dependency CVEs (pip, conda, npm) (✅ Trivy scans lockfiles/package manifests too)

- Known-malicious or typosquatted packages (critical for ML: `torch` vs `pytorch`-lookalikes, etc.) {⚠️ Trivy does NOT detect this, it only matches known CVEs against known package names. Typosquatting needs separate tools (e.g. `pip-audit`, OSS registry checks, or dedicated typosquat detectors)}.

  **Typosquatting** = publishing a malicious package with a name very similar to a popular one, hoping developers mistype or misread it (e.g. `pytorch` instead of `torch`, or `request` instead of `requests`). If someone installs it by mistake, they run the attacker's code instead.

Fail builds on critical/high severity findings above your org's risk threshold.


```bash
trivy image --exit-code 1 --severity CRITICAL,HIGH
```



### iv: Re-scan images

Re-scan images already in the registry periodically. New CVEs are disclosed after the fact.
(✅ Trivy can scan registry images directly, just schedule it (cron/CI))

```bash
trivy image mongo:8.0
# Give error

trivy image --db-repository ghcr.io/aquasecurity/trivy-db mongo:8.0
# This is ok in Iran

trivy image --db-repository ghcr.io/aquasecurity/trivy-db mongo:8.0 --severity CRITICAL,HIGH
# This will only filter those BAD vulns
```


  **Output-in-my-Laptop-for-CRITICAL-ones**

  ```bash
  PS C:\Users\User> trivy image --db-repository ghcr.io/aquasecurity/trivy-db mongo:8.0 --severity CRITICAL
  
  2026-07-25T12:32:30+03:30       INFO    Adding schema version to the DB repository for backward compatibility   repository="ghcr.io/aquasecurity/trivy-db:2"
  2026-07-25T12:32:30+03:30       INFO    [vuln] Vulnerability scanning is enabled
  2026-07-25T12:32:30+03:30       INFO    [secret] Secret scanning is enabled
  2026-07-25T12:32:30+03:30       INFO    [secret] If your scanning is slow, please try '--scanners vuln' to disable secret scanning
  2026-07-25T12:32:30+03:30       INFO    [secret] Please see https://trivy.dev/docs/v0.72/guide/scanner/secret#recommendation for faster secret detection
  2026-07-25T12:32:31+03:30       INFO    Detected OS     family="ubuntu" version="24.04"
  2026-07-25T12:32:31+03:30       INFO    [ubuntu] Detecting vulnerabilities...   os_version="24.04" pkg_num=119
  2026-07-25T12:32:31+03:30       INFO    Number of language-specific files       num=10
  2026-07-25T12:32:31+03:30       INFO    [gobinary] Detecting vulnerabilities...
  2026-07-25T12:32:31+03:30       INFO    [node-pkg] Detecting vulnerabilities...
  2026-07-25T12:32:31+03:30       WARN    Using severities from other vendors for some vulnerabilities. Read https://trivy.dev/docs/v0.72/guide/scanner/vulnerability#severity-selection for details.
  
  Report Summary
  
  ┌──────────────────────────┬──────────┬─────────────────┬─────────┐
  │          Target          │   Type   │ Vulnerabilities │ Secrets │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ mongo:8.0 (ubuntu 24.04) │  ubuntu  │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ opt/js-yaml/package.json │ node-pkg │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/bsondump         │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongodump        │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongoexport      │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongofiles       │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongoimport      │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongorestore     │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongostat        │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/bin/mongotop         │ gobinary │        0        │    -    │
  ├──────────────────────────┼──────────┼─────────────────┼─────────┤
  │ usr/local/bin/gosu       │ gobinary │        1        │    -    │
  └──────────────────────────┴──────────┴─────────────────┴─────────┘
  Legend:
  - '-': Not scanned
  - '0': Clean (no security findings detected)
  
  
  usr/local/bin/gosu (gobinary)
  =============================
  Total: 1 (CRITICAL: 1)
  
  ┌─────────┬────────────────┬──────────┬────────┬───────────────────┬──────────────────────────────┬──────────────────────────────────────────────────────────┐
  │ Library │ Vulnerability  │ Severity │ Status │ Installed Version │        Fixed Version         │                          Title                           │
  ├─────────┼────────────────┼──────────┼────────┼───────────────────┼──────────────────────────────┼──────────────────────────────────────────────────────────┤
  │ stdlib  │ CVE-2025-68121 │ CRITICAL │ fixed  │ v1.24.6           │ 1.24.13, 1.25.7, 1.26.0-rc.3 │ crypto/tls: crypto/tls: Incorrect certificate validation │
  │         │                │          │        │                   │                              │ during TLS session resumption                            │
  │         │                │          │        │                   │                              │ https://avd.aquasec.com/nvd/cve-2025-68121               │
  └─────────┴────────────────┴──────────┴────────┴───────────────────┴──────────────────────────────┴──────────────────────────────────────────────────────────┘
  
  ```



## 2- Docker Hardened Images (DHI)

![](.\Screens\Pictures\DHI.png)

Docker Hardened Images (DHI) are minimal, security-focused container images that strip out unnecessary tools and packages, cutting image size and known vulnerabilities by 10x or more compared to standard images.

DHIs come in **dev** (for building) and **runtime** (for production) variants, are free under Apache 2.0, and include built-in SBOMs and signed provenance for supply-chain security.

👉 https://docs.docker.com/dhi/get-started/

### Sample output for scanning with docker scout



![](.\Screens\docker scout sample.png)



### Comparing two images, one hardened and one usual with scout



```powershell
docker login dhi.io

docker pull dhi.io/python:3.13

docker run --rm dhi.io/python:3.13 python -c "print('Hello from DHI')"
```



```powershell
docker scout compare dhi.io/python:3.13 `
    --to python:3.13 `
    --platform linux/amd64 `
    --ignore-unchanged
```

> ✅ All DHIs are not free. Go to [this URL](https://hub.docker.com/hardened-images/catalog) to see some one them that free of charge.



![](.\Screens\docker scout comparing.png)



> - Those `?` marks mean **"unknown/unspecified severity"**, vulnerabilities that Scout detected but couldn't confidently classify into Critical/High/Medium/Low (usually because the CVE database entry lacks a CVSS score or the data is incomplete/pending).
>
>   ​	So in the above report:
>
>   - **DHI image:** 2 unknown-severity vulns
>   - **Regular image:** 48 unknown-severity vulns
>
> - **Translation of the screen:**
>
>   - **12x smaller** (38 MB vs 466 MB); faster pulls, less disk space.
>   - **6x fewer packages**;  less bloat, smaller attack surface.
>   - **Zero critical vulnerabilities** in the DHI version vs 2 in the regular one.
>   - Way fewer vulnerabilities across every severity level (this is because DHI strips out unnecessary packages/tools that usually carry these CVEs).



## 3- Secrets in Images

![](.\Screens\Pictures\Avoid Secret Insertion.png)

- ⛔ Never `COPY` the following items into an image layer, **even if deleted in a later layer, they persist in image history.**
  
  - `.env`,
  - API keys
  -  cloud credentials
  -  SSH keys
  - Hugging Face/W&B tokens

  
  ```bash
  # BAD 🤯 
  COPY .env .env
  ```
  
  **Note:** Even if you later `RUN rm .env`, it's still recoverable from the layer history. Add `.env` to `.dockerignore` instead (or see the following instructions).
  
  **Secrets in build image phase:**

- ✅ **Use build-time secrets properly:** `--mount=type=secret` ([BuildKit](https://docs.docker.com/build/buildkit/)).

  **SEE DIRECTORY `Dockerfile-Examples` IN SOURCE CODES.** In this directory we will see three docker file

  1. One that has hard-coded API keys. 
  2. One that we inject the token during image build process.
  3. And one using buildkit.
     

  

  **Secrets in runtime phase:**
  
  ```dockerfile
  # 1- Dockerfile; don't touch the token or model at build time:
  
  FROM python:3.12-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY src/ ./src/
  COPY download_model.py .
  
  # No model, no token here, only code
  CMD ["sh", "-c", "python download_model.py && uvicorn src.app:app --host 0.0.0.0 --port 8000"]
  ```
  
  ```python
  # 2- download_model.py; reads token from environment at runtime:
  
  import os
  from huggingface_hub import snapshot_download
  
  token = os.environ["HF_TOKEN"]
  
  snapshot_download(repo_id="your-org/your-model", token=token, local_dir="./models")
  ```
  
  ```powershell
  # 3- Build; completely clean, no secret involved:
  
  docker build -t myapp .
  ```
  
  ```powershell
  # 4- Run; token passed only now, at runtime, never baked into the image:
  
  docker run -e HF_TOKEN=$env:HF_TOKEN -p 8000:8000 myapp
  ```
  
  ```powershell
  # OPTIONAL: Or better, avoid even putting it in shell history, use a local env file excluded from git (.env.local must be in .gitignore and .dockerignore.)
  
  docker run --env-file .env.local -p 8000:8000 myapp
  ```



------

> **If only the image build needs the token** ===> use **BuildKit secrets**.
> **If the application needs the token at runtime** ===> use **runtime secrets**

------



- Audit with tools like `docker history --no-trunc` or `dive` to inspect layer contents.

  ```powershell
  docker history --no-trunc mongo:8.0
  # Output is not user friendly 
  ```

  Or install **dive** for a visual layer-by-layer inspector (It is tiny and light):

  ```powershell
  # Output is Good and user friendly 
  winget install --id wagoodman.dive
  
  # My Dive Version
  PS C:\Users\User> dive --version
  dive 0.13.1
  
  dive mongo:8.0
  ```

  

  ![](.\Screens\dive-for-mongo.png)

**Note:** In dive report, `Image efficiency score` more than 90% is acceptable and GOOD.



## 4- Multi-Stage Builds (MSB)

![](.\Screens\Pictures\Multi Stage Building.png)

- Use multi-stage builds to keep build tools, compilers, and source secrets out of the final image.

- Example pattern for ML:
  
  **Stage 1**: train/build dependencies.
  **Stage 2**: copy only the compiled model artifact + runtime deps into a slim final stage.
  
  
  
- MSB Reduces attack surface and image size significantly.

  ```dockerfile
  # Stage 1: build/train (has compilers, dev tools, secrets)
  
  #FROM ... AS builder ===> defines a build stage.
  FROM python:3.12 AS builder
  
  WORKDIR /build
  COPY requirements-train.txt .
  RUN pip install --no-cache-dir -r requirements-train.txt
  COPY train.py .
  RUN --mount=type=secret,id=hf_token \
      python train.py --token-file /run/secrets/hf_token
      
  # 🔴 produces /build/model.onnx
  
  # Stage 2: slim runtime (final image, only this ships to prod).
  
  # For final image we use slim version
  FROM python:3.12-slim
  WORKDIR /app
  COPY requirements-runtime.txt .
  RUN pip install --no-cache-dir -r requirements-runtime.txt
  
  #COPY --from=builder ... ===> copies artifacts from that stage into next stage.
  COPY --from=builder /build/model.onnx ./model.onnx
  
  COPY src/ ./src/
  CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

**Key point:** only `COPY --from=builder` pulls specific files across --- compilers, training deps, secrets, and intermediate cache in Stage 1 never reach the final image. Check with `docker history myimage`. **SEE DIRECTORY `Dockerfile-Examples` IN SOURCE CODES.**

  

## 5- Dockerfile Best Practices

![](.\Screens\Pictures\Dockerfile best practices.png)

- Run as a **non-root user** (`USER appuser`). Never leave containers running as root unless strictly required.
  

  ```dockerfile
  RUN useradd -m appuser
  
  USER appuser
  
  #USER root
  ```
  
  
  
-  **A runtime hardening feature:** Set `read-only` root filesystem where possible (`--read-only` at runtime + explicit writable volumes for what's needed, e.g., `/tmp`, model cache dirs).


  ```powershell
  # (/tmp and cache dirs need explicit writable tmpfs/volumes since app can't write elsewhere. Note that tmpfs comes from "temporary file system").
  
  docker run `
    --read-only `
    --tmpfs /tmp `
    --tmpfs /app/cache `
    myimage
  
  #/tmp/file.txt       ✅
  #/app/cache/a.bin    ✅
  #/app/main.py        ❌
  ```

  > Normally, when you run a container:
  >
  > ```
  > docker run myimage
  > ```
  >
  > the container can **write files** almost anywhere inside its own filesystem.
  >
  > For example:
  >
  > ```
  > /tmp/log.txt        ✅
  > /app/config.json    ✅
  > /root/test.txt      ✅
  > ```
  >
  > But with `--read-only`
  >
  > ```
  > docker run --read-only myimage
  > ```
  >
  > the container's filesystem becomes **read-only**. Now these fail:
  >
  > ```
  > /app/config.json    ❌
  > /root/test.txt      ❌
  > /tmp/log.txt        ❌
  > ```
  >
  > This improves security because:
  >
  > - Malware can't easily modify application files.
  > - Attackers can't drop scripts or binaries into the container.
  > - Your application can't accidentally overwrite its own code.

  

- Use `.dockerignore` to exclude `.git`, credentials, local datasets, notebooks with output cells (can leak data/secrets).

  ```dockerfile
  # contet of ".dockerignore" file
  # Put this file to your Dockerfile — prevents accidental COPY . from grabbing secrets/datasets.
  
  .git
  .env
  *.ipynb
  data/
  *.pem
  ```

  

- Avoid `ADD` with remote URLs. Use `COPY` for local files. If you must download a remote file, use `curl` or `wget` and verify its checksum.
  

  ```dockerfile
  # BAD
  ADD https://example.com/model.bin /app/model.bin
  
  # GOOD
  RUN curl -fsSL https://example.com/model.bin -o model.bin \
      && echo "expectedsha256  model.bin" | sha256sum -c -
      
  # Downloads the file
  # Verifies its SHA-256 checksum.
  # Fails the build if the file has been modified or corrupted   
  # -c = check a checksum against an expected value.
  # - = read the expected checksum from standard input
  
  # OR EVEN BETTER
  RUN curl -fsSL https://github.com/org/project/releases/download/v1.2.3/model.bin -o model.bin && \
      echo "7f83b165...  model.bin" | sha256sum -c -
  ```
  
  
  
- Explicitly pin package versions (`pip install torch==2.3.1`) to avoid dependency confusion.
  

  ```dockerfile
  # BAD
  RUN pip install torch
  
  # GOOD
  RUN pip install torch==2.3.1
  ```

- Verify the integrity of downloaded **model weights or datasets** by validating their checksum (or digital signature if provided).

```dockerfile
RUN curl -fsSL https://huggingface.co/.../model.safetensors -o model.safetensors \
    && echo "abc123...  model.safetensors" | sha256sum -c -
```



## 6- Runtime Security and Image Provenance

![](.\Screens\Pictures\Runtime Security.png)

### i: Image Provenance

**Image Provenance = Knowing where a Docker image came from, how it was built, and what it contains.**

- Generate and attach **SBOMs** (Software Bill of Materials). This is critical for tracking ML dependency chains (PyPI packages have had real supply-chain compromises). An **SBOM** is basically an inventory of everything inside your image/app: for example, packages, libraries, versions, etc. It lets you answer: **“What software components are inside this image, and are any of them vulnerable?”**
  
  
  ```powershell
  # With docker scout
  docker scout sbom fozouni/absenteeism:first_try --format cyclonedx > sbom.json
  
  
  # With Trivy
  # NOte that your Dokcer should be up and running and image exists locally.
  trivy image fozouni/absenteeism:first_try --format cyclonedx --output sbom-v2.json
  
  
  trivy sbom --db-repository ghcr.io/aquasecurity/trivy-db sbom-v2.json
  
  #1- Reads sbom-v2.json.
  #2- Downloads/updates the Trivy vulnerability database from GHCR.
  #3- Matches the packages/components in the SBOM against that DB.
  #4- Reports the known vulnerabilities/security issues it finds.
  ```
  
  
  
  > **Note for your Prod. Env.:**
  > Use **Trivy** ===> strong open-source, CI/CD-friendly, easy to automate, supports SBOM generation **and** vulnerability scanning.
  >
  > Use **Docker Scout** ===> excellent if your organization is already heavily invested in Docker Hub/Docker Desktop and wants Docker-native vulnerability insights.
  
  
  
  **In production CI pipeline**:
  
  ```powershell
  # The actual CI gate that fails the build (CVE gate)
  # command 1
  trivy image --db-repository ghcr.io/aquasecurity/trivy-db mongo:8.0 --severity CRITICAL,HIGH --exit-code 1
  # In running the above command, if HIGH/CRITICAL vulnerabilities are found, then Trivy give us the exit code number 1 😎
  
  # command 2
  trivy image mongo:8.0 --format cyclonedx --output sbom-mongo.json
  
  # command 3
  trivy sbom sbom-mongo.json
  ```
  



> **Above commands in a nutshell:**
>
> **Command 1:** 🔴 **CVE Gate**: scans the Docker image and fails the CI/CD step if HIGH/CRITICAL vulnerabilities exist.
>
> **Command 2:**  📋 **SBOM Generator**: examines the Docker image and creates an SBOM listing its components/packages.
>
> **Command 3:** 🔍 **SBOM Scanner**: reads the existing SBOM and checks its components against Trivy's vulnerability database.



### ii: Runtime Security (runtime security hardening technique)

- Drop all Linux capabilities by default, add back only what's needed:
  `--cap-drop=ALL --cap-add=<specific>`
  
  ➡️`--cap-drop=ALL` **Remove all capabilities from the container.**
  
  ➡️`--cap-add=NET_BIND_SERVICE` **Allow that specific capability.**
  
  
  > This follows the **Principle of Least Privilege**. Give the container only the permissions it needs. Nothing more.
  
  
  
- Never run with `--privileged`. **This disables most container isolation.**
  

  ```powershell
  # BAD; full host access, defeats containerization
  docker run --privileged myapp
  
  # GOOD; request only the specific device/capability you need
  # Give this container access to the specific NVIDIA GPU device /dev/nvidia0.
  docker run --device=/dev/nvidia0 myapp
  
  
  #Host
  # ├── /dev/nvidia0  <=== ✅ container can access
  # ├── /dev/sda      <=== ❌ not exposed
  # ├── /dev/random   <=== ❌ not exposed
  # └── other devices <=== ❌ not exposed
  ```
  
  
  **Regarding the last two items:**
  
  |          |       `--cap-drop/--cap-add`       |         `--device`          |
  | :------: | :--------------------------------: | :-------------------------: |
  | Controls | **Linux permissions/capabilities** | **Access to a host device** |
  | Example  |    `--cap-add=NET_BIND_SERVICE`    |   `--device=/dev/nvidia0`   |
  
  
  
- Avoid mounting the Docker socket (`/var/run/docker.sock`) into containers. This is equivalent to giving root on the host.

  ```powershell
  # BAD; container can control the whole host via Docker API
  
  docker run -v /var/run/docker.sock:/var/run/docker.sock myapp
  ```

  **Note:** If a container needs Docker access, avoid mounting the raw Docker socket. Use a safer, restricted approach such as a **scoped Docker API proxy**.

  ```
  Container ==========> /var/run/docker.sock (🔥Full Docker control)
  
  
  Container ==========> API Proxy ==========> Docker daemon
                            |
                            --- Only allowed operations, for example: pull/start/inspect                         
  ```

  

  > **Note:** The Docker socket is the communication channel to the **Docker daemon**. If a container can freely talk to the Docker daemon, it can potentially:
  >
  > - start other containers.
  > - mount host directories into containers.
  > - access sensitive host files.
  > - effectively gain **root-level control of the host**.
  >
  > So this is dangerous and avoid it.

  

- Use `--security-opt=no-new-privileges` to prevent privilege escalation via setuid binaries.

  ```powershell
  # ALWAYS include this unless you have a good reason not to
  
  docker run --security-opt=no-new-privileges myapp
  ```

  **Note:** A `setuid` binary such as `sudo` normally has mechanisms that can change privileges. But
   `no-new-privileges` prevents that privilege increase and this is perfect.
  
  **✅ BEST_POSSIBLE**_**FOR_PROD_CI/CD**:
  
  ```powershell
  docker run --cap-drop=ALL --security-opt=no-new-privileges -u appuser myapp
  				#1-👆  				#2-👆					#3-👆
  ```
  
  
  
  > These three (#1, #2 and #3) controls address **different layers**:
  >
  > |               Option               |                 Meaning                 |
  > | :--------------------------------: | :-------------------------------------: |
  > |          `--cap-drop=ALL`          |       🔒 Remove Linux capabilities       |
  > | `--security-opt=no-new-privileges` | 🚫 Prevent gaining additional privileges |
  > |            `-u appuser`            |   👤 Don't run the application as root   |
  
  
  
  🔴 **Note regarding the last part:**
  Startups/less mature teams often skip these until an audit, incident, or compliance requirement forces it. Regulated industries (finance, healthcare) and larger tech companies enforce them by default via policy engines ([Kyverno](https://kyverno.io/)), not developer discipline alone.



## Final advice

Real protection comes from keeping everything up to date. The best defense is:

- **Patch** the vulnerable component (update the base image, libraries, etc.).

- Harden the configuration (hide banners and **exact versions** of your techs, minimize exposed information).

  > We must try those techs in our stack don't expose their exact versions. When bots for the first time come to our service and find out about these hiding, easily they will be going to the next destination and don't stay on our server much.

- Scan continuously (like you’re doing with **Trivy**).



## Quick Checklist Before Shooting 🚀

- [ ] Pin base images by digest
- [ ] Scan images in CI (Trivy/Scout) + fail on critical CVEs
- [ ] No secrets in layers; use BuildKit secret mounts
- [ ] Multi-stage builds
- [ ] Use DHI if there is a hardened image
- [ ] Non-root `USER`, `--cap-drop=ALL`, no `--privileged`
- [ ] No Docker socket mounted into containers

