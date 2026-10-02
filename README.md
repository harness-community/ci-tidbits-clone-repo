# CI | Tidbits | Clone Repo Securely

> **Bite-sized how-to** | ~10 min setup

---

## What is a secure clone?

CI has to fetch application code before it can build or test it. The unsafe shortcut is to put a token in the pipeline:

```sh
# Do not do this. The token lands in YAML, shell history, and step logs.
git clone https://<USER>:ghp_xxxxx@github.com/your-org/your-repo.git
```

A Harness **connector** is a reusable login. The pipeline stores a `connectorRef`. The personal access token stays in a Harness secret. At runtime Harness clones the repo and masks the secret in logs.

This tidbit uses one GitHub connector to clone **this** repo into a Harness Cloud build, then checks that the workspace has the app and that the git remote URL has no embedded credential.

| Piece | Role |
|---|---|
| Text secret `github-pat` | GitHub PAT (or fine-grained token) |
| GitHub connector `githubconnector` | Uses that secret over HTTPS |
| Pipeline codebase | `connectorRef: githubconnector` and `cloneCodebase: true` |
| Verify step | Fails if the remote URL contains a token |
| App step | Runs the unit tests that arrived with the clone |

Docs: [codebase configuration](https://developer.harness.io/docs/continuous-integration/use-ci/codebase-configuration/create-and-configure-a-codebase/), [connectors](https://developer.harness.io/harness-platform/3.0/in-harness-3.0/connectors).

---

## Prerequisites

Before you start, make sure you have:

- A Harness account with a **Project** (note its org + project identifiers).
- Harness Cloud build credits (default on Harness-hosted runners). No delegate is required for this pipeline.
- A GitHub account and a PAT (or fine-grained token) that can read your fork of this repo. `Contents: Read` is enough.

---

## Step 1 — Fork this repo

Fork the repo into your own GitHub account so the connector can read it. The application under `app/` is the code the pipeline fetches. No local Python setup is required.

```
.
├── .harness/
│   └── pipeline.yaml       ← CI stage; cloneCodebase uses the connector
├── connectors/
│   └── github.yaml         ← GitHub connector (secret id only)
├── app/
│   ├── __init__.py
│   └── main.py             ← sample app the clone must deliver
├── tests/
│   └── test_main.py
└── README.md
```

---

## Step 2 — Secret and connector

1. **Secret.** Project Settings → Secrets → Text. Id `github-pat`. Paste the GitHub token. Do not commit the token, and do not put it in pipeline YAML.

2. **GitHub connector.** Project Settings → Connectors → New Connector → GitHub, or paste [`connectors/github.yaml`](./connectors/github.yaml). Replace every `# REPLACE:` line.

   - URL `https://github.com`, connection type **Account** (so `repoName` is chosen by the pipeline, not baked into the connector).
   - Authentication: **Username** and **Token** → secret `github-pat`.
   - **Connect through Harness Platform** (`executeOnDelegate: false`). That is what Harness Cloud uses to clone.
   - Test the connection against a repository the token can read (your fork).

---

## Step 3 — Import the pipeline

1. Go to **Pipelines → Create a Pipeline** and open the YAML editor.
2. Paste [`.harness/pipeline.yaml`](./.harness/pipeline.yaml).
3. Set `projectIdentifier` and `orgIdentifier` to yours.
4. Save.

`connectorRef` is `githubconnector` — the identifier from the connector YAML, not a URL and not a token.

---

## Step 4 — Run the pipeline (expect a GREEN build)

1. Click **Run**.
2. For **Repository Name**, enter your fork: `your-user/ci-tidbits-clone-repo`.
3. Keep branch `main`. Click **Run Pipeline**.

Harness clones the repo with the connector **before** the steps run. Then:

- **Verify connector clone** lists the workspace, requires `app/main.py`, and fails if `git remote -v` contains `@` credentials or a `ghp_` / `github_pat_` token.
- **Run cloned app** executes `python -m unittest tests.test_main` and prints the greeting from the cloned `app/main.py`.

**Green is the correct outcome.** The build fetched code with a credential that never appeared in Git.

---

## Pipeline YAML reference

The full pipeline lives at [`.harness/pipeline.yaml`](./.harness/pipeline.yaml). Key shape:

```yaml
properties:
  ci:
    codebase:
      connectorRef: githubconnector
      repoName: <+input>
      build:
        type: branch
        spec:
          branch: main
stages:
  - stage:
      name: Clone
      type: CI
      spec:
        cloneCodebase: true
        runtime:
          type: Cloud
          spec: {}
        execution:
          steps:
            - step:
                name: Verify connector clone
                type: Run
                spec:
                  command: |-
                    test -f app/main.py
                    git remote -v
```

`cloneCodebase: true` is the clone. You do not add a `git clone` command. A later [Git Clone step](https://developer.harness.io/docs/continuous-integration/use-ci/codebase-configuration/git-clone-step/) is only for a *second* repository in the same stage.

---

## Common Issues & Tips

**Connector test fails.** Confirm secret id `github-pat`, the GitHub username, and that the token can read the test repo. For Harness Cloud, the connector must connect through the Harness Platform (`executeOnDelegate: false`).

**Clone step fails with "repository not found" or 404.** `repoName` must be `owner/name` of the fork, not the connector URL. An Account connector does not imply a repository.

**Verify step fails on the remote URL.** Something cloned with a token embedded in the URL (`https://user:token@github.com/...`). Point `connectorRef` at `githubconnector` and leave the clone to `cloneCodebase`.

**Do not print `git config`.** A credential helper or `http.extraheader` can hold the token for the clone. `git remote -v` is the check; dumping config can leak the secret into the build log.

**Public repo, no token.** A public repository can still use this connector. The point of the tidbit is that the pipeline never carries the credential, which is what you need the moment the repo is private.

---

## What's next?

- **Private repo.** Flip the fork to private and re-run. The same secret and connector keep working; the YAML does not change.
- **Second repository.** Add a `GitClone` step with its own `connectorRef` when one stage needs application code and a separate manifest or library repo.
- **GitHub App.** Swap the PAT for a GitHub App connector when you want short-lived installation tokens instead of a long-lived PAT.
- **SSH.** Use an SSH Git connector and a Harness SSH key secret when the provider does not allow HTTPS tokens.

---

## Resources

- [Configure a codebase](https://developer.harness.io/docs/continuous-integration/use-ci/codebase-configuration/create-and-configure-a-codebase/)
- [Git Clone step](https://developer.harness.io/docs/continuous-integration/use-ci/codebase-configuration/git-clone-step/)
- [Add and use text secrets](https://developer.harness.io/docs/platform/secrets/add-use-text-secrets)
- [Connectors](https://developer.harness.io/harness-platform/3.0/in-harness-3.0/connectors)
