You can use the GitHub API to trigger a webhook event called `repository_dispatch` when you want to trigger a workflow for activity that happens outside of GitHub.

```bash
curl -X POST \
  -H "Authorization: token INSERT-HERE-YOUR-GITHUB-TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUr-USER-NAME/YOUR-REPO-NAME/dispatches \
 -d '{"event_type": "trigger-fetch-data"}'

```

