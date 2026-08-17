# Gitleaks Demo

[toc]

## Install and prerequisite 

```bash
winget install --id Gitleaks.Gitleaks -e --source winget
# or just update
winget upgrade --id Gitleaks.Gitleaks -e

gitleaks version
# mine is 8.30.1

mkdir gitleaks-demo

cd gitleaks-demo

git init
```

Copy and paste file `commands.md` from previous discussions into this repo.

Now do the following tasks:

```
git add .

git commit -m "first commit"

gitleaks detect --source . --verbose
```

And the magic will happen.



## Automate this process

Create one file `pre-push` on the address `.git/hook/` of your project. The content of the file is as follows:

```
#!/bin/sh
echo "Running gitleaks scan before push..."
gitleaks detect --source . --verbose --redact

if [ $? -ne 0 ]; then
  echo ""
  echo "❌ Gitleaks found potential secrets. Push aborted."
  echo "Fix or remove the secrets above before pushing."
  exit 1
fi

echo "✅ No secrets found. Proceeding with push."
exit 0
```

Now if you wanted to push to GitHub you will see the following message:

```powershell
PS C:\Users\User\Desktop\gitleaks-demo> git push -u origin main
Running gitleaks scan before push...

    ○
    │╲
    │ ○
    ○ ░
    ░    gitleaks

Finding:     SLACK_TOKEN = "REDACTED
Secret:      REDACTED
RuleID:      slack-bot-token
Entropy:     4.964297
File:        config.py
Line:        7
Commit:      8065178dfc2a41ddfad59cccfd4df7426e852608
Author:      fozouni
Email:       fozouni@hotmail.com
Date:        2026-08-04T13:39:42Z
Fingerprint: 8065178dfc2a41ddfad59cccfd4df7426e852608:config.py:slack-bot-token:7
Link:        https://github.com/fozouni/gitleaks-demo/blob/8065178dfc2a41ddfad59cccfd4df7426e852608/config.py#L7

Finding:     GITHUB_TOKEN = "REDACTED
Secret:      REDACTED
RuleID:      github-pat
Entropy:     4.821928
File:        config.py
Line:        6
Commit:      8065178dfc2a41ddfad59cccfd4df7426e852608
Author:      fozouni
Email:       fozouni@hotmail.com
Date:        2026-08-04T13:39:42Z
Fingerprint: 8065178dfc2a41ddfad59cccfd4df7426e852608:config.py:github-pat:6
Link:        https://github.com/fozouni/gitleaks-demo/blob/8065178dfc2a41ddfad59cccfd4df7426e852608/config.py#L6

5:15PM INF 2 commits scanned.
5:15PM INF scanned ~372 bytes (372 bytes) in 310ms
5:15PM WRN leaks found: 2

❌ Gitleaks found potential secrets. Push aborted.
Fix or remove the secrets above before pushing.
error: failed to push some refs to 'https://github.com/fozouni/gitleaks-demo.git'
PS C:\Users\User\Desktop\gitleaks-demo> 
```

## Some good commands and config

Now suppose that in our repo there is some files that contain some secrets that is not important, and we wanted to share them. Simply we can create one file `.gitleaks.toml` on the root of our project with the following content, for example:

```toml
title = "gitleaks config"

[extend]
useDefault = true

[[allowlists]]
description = "Ignore known false positives in teaching examples"

paths = [
  "04-Docker-03/Dockerfile-Examples/Good-Docker-Image/good-commands.md",
  "04-Docker-03/04-Docker-03-P2-and-P3/Dockerfile-Examples/Good-Docker-Image/good-commands.md",
  "04-Docker-03/Dockerfile-Examples/Bad-Docker-Images-2/commands.md"
]
```

Now run this before pushing to check if you have problem or not:

```powershell
gitleaks detect --verbose

gitleaks detect --config .gitleaks.toml
```

Now if there is not any problem, run `git push`.



## Do for all your local Projects

We can config `gitleaks` to check all local repo on our system. But at this moment, we only focus on the approach for each repo, not globally. 

## ⛔ What Hapens if gitleaks detect a real token that we forgot to discard from our repo

In this situation, if we commit our repo and find out that there is acritical token or secret on the repo, we should not push our repo. First of all, we must delete the latest commit that contains the file with hardcoded token. Then, after deleteing this secret, we can now push safely to github. 

Note that we can use a file like `pre-push` on the `.git/hooks/` address named `pre-commit` that before commiting anything, will check and detect secrets for us. The file `pre-commit` is on the `gitleaks-s7` directory. Feel free to test this and enjoy the most possible security.

