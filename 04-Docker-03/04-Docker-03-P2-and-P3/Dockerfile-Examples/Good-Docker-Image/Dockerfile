# syntax=docker/dockerfile:1

FROM alpine

RUN --mount=type=secret,id=api_key \
    cat /run/secrets/api_key

CMD ["sh"]



# RUN --mount=type=secret,id=api_key \
#     API_KEY=$(cat /run/secrets/api_key) python app.py


# 1- BuildKit mounts the secret temporarily

# 2- "cat /run/secrets/api_key" reads it

# 3- Creates an environment variable only for this command "API_KEY=secret-value"

# 4- Runs "python app.py"

# So inside app.py we have: 

# import os

# token = os.environ["API_KEY"]

# After the RUN finishes:

# ❌ API_KEY is gone
# ❌ /run/secrets/api_key is gone
# ❌ The final image does not contain the secret

# If app.py needs the API key when the container is running,
# you would inject it differently (runtime secret/env), not with BuildKit.
