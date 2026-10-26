# FastAPI-01- What it is and Some Security issues

[toc]

## Introduction

FastAPI is a Python web framework for building **HTTP APIs**, indeed code that listens on a port, receives JSON, and returns JSON. 

Three things make FastAPI the right tool for **ML serving**:

1️⃣ **Type-driven validation**: You declare the *shape* of a request as a Python class. FastAPI uses that declaration to
(a) parse the JSON,
(b) reject anything that does not match,
(c) generate API docs.

2️⃣ **Dependency injection:** A function decorated with `Depends(...)` runs *before* your route handler and can stop the request early (return `401`, `403`, `429`, …). Auth, rate limits, and scope checks are all written this way. **No security logic is scattered inside the model code**.

3️⃣ **It runs on ASGI:**  The same protocol used by modern Python servers. You start it with `uvicorn file:app` and it is production-grade enough that a bad request cannot take the process down.



## `src/01-naive.py` code

Run the `src/01-naive.py` code and then test it as the following block says:

```bash
# 200, works
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '[5.1,3.5,1.4,0.2]'; echo

# 422, input is not a list and is object
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'; echo

# 422, wrong length: broken
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[1,2,3]}'; echo

# 422, extra field: silently ignored
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2],"is_admin":true}'; echo
```

Output should be like this:

```powershell
(.fastapi) PS E:\MLSecOps\Contents\FastAPI-01> pip freeze > 'requirements-fastapi.txt'
(.fastapi) PS E:\MLSecOps\Contents\FastAPI-01> python 01_naive.py                     
INFO:     Started server process [11272]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:45532 - "POST /predict HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:48690 - "POST /predict HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:48560 - "POST /predict HTTP/1.1" 422 Unprocessable Content
```

> 🚩**What the 422 means:** FastAPI is reading `{"features":[5.1,3.5,1.4,0.2]}` as a **list** because `features: list[float]` in your function signature is treated by FastAPI as the **whole request body**, not a field named `features`. So it wants a bare JSON list like `[5.1, 3.5, 1.4, 0.2]`, not an object.
>
> 🚩 Use `jq` to have a more beautiful output
>
> ```bash
> curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
>      -d '{"features":[5.1,3.5,1.4,0.2],"is_admin":true}' | jq .
> ```
>
> Output will be like this:
>
> ```bash
> amin@ubuntu24:~$ curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
>      -d '{"features":[5.1,3.5,1.4,0.2],"is_admin":true}' | jq .
> {
>   "detail": [
>     {
>       "type": "extra_forbidden",
>       "loc": [
>         "body",
>         "is_admin"
>       ],
>       "msg": "Extra inputs are not permitted",
>       "input": true
>     }
>   ]
> }
> ```



## `src/02-validate.py` code

| **This version will reject wrong-shaped input.** |
| :----------------------------------------------: |

Run the `src/02-validate.py` code and then test it as the following block says:

```bash
# Object form now works ===> {"label":0}
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'; echo

# Wrong length ===> 422
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[1,2,3]}'; echo

# Extra field ===> 422 (extra="forbid")
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2],"is_admin":true}'; echo

# Bare list no longer accepted ===> 422 (now the body must be an object)
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '[5.1,3.5,1.4,0.2]'; echo
```



> 🚩 **One thing to notice on the 422s:** The response **echoes your input back** (`"input": {...}`). That's a leak (see the following snippet) and it's what the next code will fix.
>
> ```bash
> # This is a leak
> amin@ubuntu24:~$ curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
> -d '[5.1,3.5,1.4,0.2]'; echo
> {"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":[5.1,3.5,1.4,0.2]}]}
> ```



## `src/03-safe_errors.py` code

| Rejecting **bad values** plus **not leaking** the input. |
| :------------------------------------------------------: |

Run the `src/03-safe_errors.py` code and then test it as the following block says:

```bash
# Valid ===> {"label":0}
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'; echo

# Wrong length ===> 422, NO "input" field in the response
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[1,2,3]}'; echo

# Extra field ===> 422, NO "input" echoed
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2],"is_admin":true}'; echo

# NaN ===> Sever error
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
     --data-binary '{"features":[NaN,1,2,3]}'; echo
```

> `03_safe_errors_v2` do not have this server error
>
> ```bash
> # NaN -> 422 (was 500, now fixed)
> curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
>   --data-binary '{"features":[NaN,1,2,3]}'; echo
>   
> curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
>   --data-binary '{"features":[-2,-1,2,3]}'; echo  
> ```



## `src/04-auth.py` code

| Requiring **identity** |
| :--------------------: |

Run the `src/04-auth.py` code and then test it as the following block says:

```bash
# No token ===> 401
curl -s -o /dev/null -w "no token: %{http_code}\n" -X POST localhost:8000/predict \
     -H 'Content-Type: application/json' -d '{"features":[5.1,3.5,1.4,0.2]}'

# Get a token
TOKEN=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
echo "token: $TOKEN"

# With token ===> {"label":0,"user":"alice"}
curl -s -X POST localhost:8000/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'; echo

# Tampered token ===> 401
curl -s -o /dev/null -w "tampered: %{http_code}\n" -X POST localhost:8000/predict \
     -H "Authorization: Bearer ${TOKEN%??}xx" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'

# Wrong password ===> 401
curl -s -o /dev/null -w "bad pw:   %{http_code}\n" -X POST localhost:8000/token \
     -d 'username=alice&password=wrong'

# Validation still works with auth ===> 422, no "input"
curl -s -X POST localhost:8000/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[1,2,3]}'; echo
```



## `src/05-scopes.py` code

| Requiring **permission** |
| :----------------------: |

**src/04-auth.py:**
"you must be **logged in**". It means, valid token = access.
**src/05-scopes.py:**
"you must be logged in **AND allowed to do this**". It means, valid token + **correct scope** = access.

Run the `src/05-scopes.py` code and then test it as the following block says:

```bash
# Alice asks for admin too. She only gets "predict".
ALICE=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123&scope=predict+admin')
echo "alice grants: $ALICE"
ALICE_TOK=$(echo "$ALICE" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Alice /predict ===> 200
curl -w "alice /predict: %{http_code}\n" -X POST localhost:8000/predict \
     -H "Authorization: Bearer $ALICE_TOK" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'

# Alice /admin/model-info ===> 403  (valid token, wrong scope)
curl -w "alice /admin:   %{http_code}\n" localhost:8000/admin/model-info \
     -H "Authorization: Bearer $ALICE_TOK"

# Admin gets both
ADMIN_TOK=$(curl -s -X POST localhost:8000/token \
            -d 'username=admin&password=admin-secret-123&scope=predict+admin' | \
            python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -w "\nadmin /predict: %{http_code}\n" -X POST localhost:8000/predict \
     -H "Authorization: Bearer $ADMIN_TOK" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'

curl -w "\n%{http_code}\n" localhost:8000/admin/model-info \
     -H "Authorization: Bearer $ADMIN_TOK"
```

> 1- Even if an attacker somehow got a token claiming `scopes:["admin"]` for `alice`, the server *re-intersects* with `USERS["alice"][1] == {"predict"}` ===> `effective == {"predict"}` ===> `403`. Never trust the token's scopes alone.
>
> 2- A scope = **a permission label** on a token.
>
> ​	a: **Token carries scopes.** When `/token` issues a JWT, it includes `"scopes": ["predict"]`.
>
> ​	b: **Route demands a scope.** `Security(current_user, scopes=["predict"])` says *"this route needs `predict`."*
>
> ​	c: **FastAPI checks.** If the token's scopes don't include what the route demands it gives `403`.



## `src/06-limits.py` code

| Protecting **availability** |
| :-------------------------: |

Run the `src/06-limits.py` code and then test it as the following block says:

```bash
# We will hit the rate limit, 5 requests per 60 s per IP.
for i in $(seq 1 7); do
  curl -s -o /dev/null -w "req $i: %{http_code}\n" -X POST localhost:8000/token \
       -d 'username=alice&password=alice-secret-123'
done


# We will send 1 MB. So the middleware said > 16 KB and then gives 413
head -c 1000000 /dev/zero | tr '\0' 'x' > /tmp/big.txt
curl -w "1MB: %{http_code}\n" -X POST localhost:8000/predict \
     -H 'Content-Type: application/json' --data-binary @/tmp/big.txt
     
     
# wait for 60s so the rate-limit bucket clears, then:
TOKEN=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -X POST localhost:8000/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'; echo
```

> **Two things to notice:**
>
> 1. `/token` itself is rate-limited, otherwise an attacker floods logins.
> 2. The rate-limit bucket is **in-memory** and **per IP**. Restart the server (`Ctrl+C`, rerun) and the bucket resets. In production: Redis or the gateway, and limit **per user** too, not just per IP.



## `src/final.py` code

🚩 The **security patterns** in this code are production-worthy. It has a correct architecture, but not a deployable artifact.

**`src/final.py` = `src/06-limits.py` +**
**proper password hashing + security headers + docs off + safe 500 + `/health` + `issue()` helper.**

### Attack own app 

#### 1. Happy path

```bash
TOKEN=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
echo "token: $TOKEN"

curl -s -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}' localhost:8000/predict; echo
```

#### 2. Privilege escalation attempt

```bash
"asking is not equals getting"
# The following first command send a request to fastapi to get the token.
ESC=$(curl -s -X POST localhost:8000/token \
      -d 'username=alice&password=alice-secret-123&scope=predict+admin')

ESC_TOK=$(echo "$ESC" | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])'

curl -s -w "alice -> /admin: %{http_code}\n" \
     localhost:8000/admin/model-info -H "Authorization: Bearer $ESC_TOK"
     
curl -s -X POST localhost:8000/predict \
     -H "Authorization: Bearer $ESC_TOK" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}' \
     -w "\nalice -> /predict: %{http_code}\n"    
     
# Expected: "scope": "predict" only. alice ===> /admin: 403. Why? Server-side set(claims.scopes) & user.scopes.
```

#### 3. Token forgery (imitation)

```bash
# We modified the token's contents (pretend admin), rebuilt the string, but couldn't sign it. So the server returns 401.

FORGED=$(python3 - "$TOKEN" <<'EOF'
import sys, json, base64
h, p, _ = sys.argv[1].split(".")
payload = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
payload["sub"] = "admin"
new_p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
print(f"{h}.{new_p}.AAAA")
EOF
)

echo $FORGED

curl -s -w "forged: %{http_code}\n" localhost:8000/predict \
     -H "Authorization: Bearer $FORGED" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'
```

#### 4. Resource abuse

```bash
# Fresh token in THIS shell
# The attacker wants 40 requests. The server answers the first 30, then refuses the rest with 429.

TOKEN=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
echo "token: $TOKEN"

# Confirm it works
curl -s -w "sanity: %{http_code}\n" -X POST localhost:8000/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}'

# Now the loop (still same shell, same $TOKEN)
for i in $(seq 1 40); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8000/predict \
       -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
       -d '{"features":[5.1,3.5,1.4,0.2]}'
done; echo
```

#### 5. Break a control, remove the scope re-check

First comment the following block in the `final.py` code.

```python
effective = set(claims.get("scopes", [])) & user.scopes
for need in security_scopes.scopes:
    if need not in effective:
        raise HTTPException(403, "Insufficient scope")
```

**removing 4 lines of code gives `alice` admin access and this dangerous.**

```bash
TOKEN=$(curl -s -X POST localhost:8000/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s -w "\nstatus: %{http_code}\n" localhost:8000/admin/model-info \
     -H "Authorization: Bearer $TOKEN"
```

## Test our final code

🚩 **Who can read `/admin/model-info`?**

```python
from fastapi.testclient import TestClient
from importlib import import_module

final = import_module("07-final")
client = TestClient(final.app)

def test_alice_cannot_read_admin_info():
    tok = final.issue(final.USERS["alice"], ["predict"])
    r = client.get("/admin/model-info", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403
    
def test_admin_can_read_model_info():
    tok = final.issue(final.USERS["admin"], ["predict", "admin"])
    r = client.get("/admin/model-info", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200    
```

Now run

```bash
pytest -q

#or

pytest -v
```

> - **With the block restored:** `PASSED`.
> - **With the block commented out:** `FAILED`. That is the point.



## Summary

| File  |                          Defence                           |                Attack it stops                |
| :---- | :--------------------------------------------------------: | :-------------------------------------------: |
| 01    |                           (none)                           |                   baseline                    |
| 02    |      Pydantic schema (`extra="forbid"`, exact length)      |          unknown fields, wrong shape          |
| 03    |         `allow_inf_nan=False`, bounds, custom 422          | `NaN`, huge values, data leak, crash-on-error |
| 04    |          JWT (pinned `alg`, `iss`, `aud`, `exp`)           |    unauthenticated calls, tampered tokens     |
| 05    |               Scopes + server-side re-check                |             privilege escalation              |
| 06    |                   Body size + rate limit                   |             floods, 1 MB payloads             |
| final | All of the above + security headers, safe logs, global 500 |                   combined                    |