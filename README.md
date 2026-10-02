# CI | Tidbits | Clone Repo Securely

> **Bite-sized how-to** | ~10 min setup

---

## Clone the codebase

Before you can build, push, or deploy an application, the build machine needs a copy of the code. In Harness CI that copy is the pipeline **codebase**: the Git repository a Build stage clones when **Clone Codebase** is enabled.

This tidbit gets that copy with a GitHub connector. `cloneCodebase: true` clones **this** repo into the workspace before any step runs. The pipeline stores `connectorRef`. The token stays in a Harness secret, and Harness masks it in logs.

A Harness GitHub connector requires a username and a personal access token. Anonymous authentication is not available. Create a [fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) and set repository permission **Contents** to **Read-only**. That same token clones a private repository you own. See [Next steps](#next-steps).

| Piece | Role |
|---|---|
| Text secret `github-pat` | GitHub PAT (or fine-grained token) |
| GitHub connector `githubconnector` | Uses that secret over HTTPS |
| `cloneCodebase: true` | Clones the pipeline codebase into the workspace root before any step |
| Verify step | Fails if the remote URL contains a token |
| App step | Runs the unit tests that arrived with the clone |

Docs: [Configure a codebase](https://developer.harness.io/continuous-integration/use-harness-ci/use-harness-ci/codebase-configuration/create-and-configure-a-codebase), [connectors](https://developer.harness.io/harness-platform/3.0/in-harness-3.0/connectors).

---

## Prerequisites

Before you start, make sure you have:

- A Harness account with a **Project** (note its org + project identifiers).
- Harness Cloud build credits (default on Harness-hosted runners). No delegate is required for this pipeline.
- A GitHub [fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) with repository permission **Contents: Read-only**. The connector cannot authenticate anonymously.

---

## Step 1 — Review this repo

The application under `app/` is the code the pipeline fetches. No local Python setup is required. Point **Repository Name** at this public repo: `harness-community/ci-tidbits-clone-repo`.

```
.
├── .harness/
│   └── pipeline.yaml       ← CI stage with cloneCodebase: true
├── connectors/
│   └── github-connector.yaml  ← GitHub connector (secret id only)
├── app/
│   ├── __init__.py
│   └── main.py             ← sample app the clone must deliver
├── tests/
│   └── test_main.py
└── README.md
```

This tidbit creates the Harness secret, the GitHub connector, and the pipeline in the visual editors. The same connector and pipeline are in this repo as YAML: [`connectors/github-connector.yaml`](./connectors/github-connector.yaml) and [`.harness/pipeline.yaml`](./.harness/pipeline.yaml). Apply those files with the [Harness CLI](https://developer.harness.io/docs/platform/automation/cli/install/) or another headless path. The token is not in Git. Create the `github-pat` secret from the CLI by passing the token as the value.

---

## Step 2 — Secret and connector

1. **Token, then secret.** Create a [fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token). Under repository permissions, set **Contents** to **Read-only**. Then in Harness: Project Settings → Secrets → Text. Id `github-pat`. Paste the token. Do not commit the token, and do not put it in pipeline YAML.

2. **GitHub connector.** Project Settings → Connectors → New Connector → GitHub, or paste [`connectors/github-connector.yaml`](./connectors/github-connector.yaml). Replace every `# REPLACE:` line.

   - URL `https://github.com`, connection type **Account** (so `repoName` is chosen by the pipeline, not baked into the connector).
   - Authentication: **Username** and **Token** → secret `github-pat`.
   - **Connect through Harness Platform** (`executeOnDelegate: false`). That is what Harness Cloud uses to clone.
   - Test the connection against a repository the token can read.

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
2. For **Repository Name**, enter `harness-community/ci-tidbits-clone-repo`.
3. Keep branch `main`. Click **Run Pipeline**.

Harness clones the codebase with the connector **before** the steps run. Then:

- **Verify codebase clone** runs in `alpine/git` (the Python image has no `git`). It requires `app/main.py` at the workspace root and fails if `git remote -v` contains `@` credentials or a `ghp_` / `github_pat_` token.
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
```

`cloneCodebase: true` is the clone. You do not add a `git clone` command.

### When you need a Git Clone step

This pipeline does not use one. A [Git Clone step](https://developer.harness.io/continuous-integration/use-harness-ci/use-harness-ci/codebase-configuration/git-clone-step) is for a **second** repository in the same stage — manifests, a library, a Dockerfile that lives somewhere else. It is a step, so it runs when the pipeline reaches it, and it has its own `connectorRef`, `repoName`, and branch. Put it in a `cloneDirectory` other than `/harness`, which is reserved for the codebase checkout.

```yaml
- step:
    type: GitClone
    name: clone second repo
    identifier: clone_second_repo
    spec:
      connectorRef: githubconnector
      repoName: your-org/other-repo
      build:
        type: branch
        spec:
          branch: main
      cloneDirectory: other-repo
```

`cloneCodebase: false` skips the automatic codebase clone on that stage. Use it when the stage should leave the pipeline codebase alone. The connector is still how either path authenticates.

---

## Common Issues & Tips

**Connector test fails.** Confirm secret id `github-pat`, the GitHub username, and that the token can read the test repo. For Harness Cloud, the connector must connect through the Harness Platform (`executeOnDelegate: false`).

**Clone fails with "repository not found" or 404.** `repoName` must be `owner/name`, not the connector URL. An Account connector does not imply a repository.

**Verify step fails on the remote URL.** Something cloned with a token embedded in the URL (`https://user:token@github.com/...`). Point `connectorRef` at `githubconnector` and leave the clone to `cloneCodebase`.

**Do not print `git config`.** A credential helper or `http.extraheader` can hold the token for the clone. `git remote -v` is the check; dumping config can leak the secret into the build log.

**Connector has no anonymous option.** Authentication on the GitHub connector is Username and Token, GitHub App, or OAuth. This tidbit uses Username and Token with secret `github-pat`. The token needs **Contents: Read-only**.

---

## Next steps

- **Private repo.** GitHub does not let you change the visibility of a fork, so this public repo has to stay public. Try the same pipeline on a private repository you own. The PAT needs **Contents** access to that repo. Set **Repository Name** to `owner/name`. The pipeline YAML does not change, and the clone succeeds.
- **Second repository.** Add a Git Clone step (see above) when one stage needs this codebase and another repo.
- **GitHub App.** Swap the PAT for a GitHub App connector when you want short-lived installation tokens instead of a long-lived PAT.
- **SSH.** Use an SSH Git connector and a Harness SSH key secret when the provider does not allow HTTPS tokens.

---

## Resources

- [Create a fine-grained personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) — repository permission **Contents: Read-only**
- [Configure a codebase](https://developer.harness.io/continuous-integration/use-harness-ci/use-harness-ci/codebase-configuration/create-and-configure-a-codebase)
- [Git Clone step](https://developer.harness.io/continuous-integration/use-harness-ci/use-harness-ci/codebase-configuration/git-clone-step)
- [Add and use text secrets](https://developer.harness.io/docs/platform/secrets/add-use-text-secrets)
- [Connectors](https://developer.harness.io/harness-platform/3.0/in-harness-3.0/connectors)
