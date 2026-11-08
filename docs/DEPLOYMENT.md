# Deploy from GitHub to Streamlit Community Cloud

GitHub Pages cannot run a Python server. This project runs on Streamlit Community Cloud, with source code kept in your GitHub repository.

## What each workflow does

1. **Game checks** (`.github/workflows/ci.yml`) runs on pushes to `main`, pull requests and manual runs. It installs dependencies on Python 3.12, checks dependency compatibility and Python syntax, runs unit and Streamlit page tests, and audits known dependency vulnerabilities. It needs no Gemini key. A failed step makes the workflow fail.
2. **Streamlit deployment** is managed by Streamlit Community Cloud. There is no additional deploy workflow or deploy token in GitHub Actions. Once connected, Streamlit watches the selected branch and updates the running application when it changes. Streamlit does not wait for the test workflow; check the workflow result before updating a hosted branch. For stricter control, require **Game checks / test** on pull requests to `main` in repository branch protection.

## First deployment

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with your GitHub account.
2. Choose **Create app**, then deploy from an existing GitHub repository.
3. Set these values:

   | Field | Value |
   |---|---|
   | Repository | `siddhantm29-netizen/Escape_room` |
   | Branch | `main` |
   | Main file path | `app.py` |
   | Python version in Advanced settings | `3.12` |

4. Choose an available app URL and select **Deploy**.
5. Wait for the build to finish, then open the resulting `https://…streamlit.app` address. Add that actual address to your GitHub repository's **About → Website** field. Do not use the repository URL as the playable game URL.

The existing `requirements.txt` and `.streamlit/config.toml` are used automatically. No Docker image, build command, paid hosting or database is needed. Initial deployment requires your Streamlit account; no cloud app has been created by the local verification steps.

## Gemini keys

The default public deployment uses **each visitor's own key**: enable **Use Gemini** and enter it in the password field. The key is retained only for that session and is not committed to GitHub. The offline Version 2 demo requires no key.

There is deliberately no shared-key fallback, including environment variables or cloud secrets. Do not add a shared Gemini API key to deployment settings. Each visitor must provide their own key to enable AI mode. The app does not write keys to cookies, local storage, logs, files or a database. Refreshing creates a fresh Streamlit session with an empty key field; **Clear API key** clears it without resetting puzzle progress. Streamlit may retain a disconnected session in server memory briefly while cleaning it up, but the new session cannot reuse its key. Browser password-manager storage is controlled separately by the visitor's browser.

Messages are sent to Google in AI mode. A visitor's quota and any enabled Google billing belong to that visitor's account. Offline mode makes no model requests. A disclaimer explaining these points is displayed at the bottom of the page.

## Optional automatic diagnostic uploads

Configure `GITHUB_LOG_TOKEN` in Streamlit Secrets using the [logging setup guide](LOGGING.md). This is a server-side GitHub token, separate from per-player Gemini keys. It writes only diagnostic files on the `app-logs` branch, leaving the deployment branch unchanged.

## Hosting smoke check

- Open the hosted page and send `examine desk` in offline Version 2.
- Attempt `open drawer` before collecting a key; it must stay locked.
- Complete the walkthrough in `WALKTHROUGH.md`; victory must disable input.
- Restart; inventory and progress must clear.
- Open a second private browser session; it must start with independent progress.
- With your own key, test the Gemini connection, then examine the desk in each version. A connection test alone does not validate a complete live game.
- Check the app's Streamlit logs if the deployment fails. `401/403` concerns key access; `404` the model ID; `429` quota; `5xx` a provider/gateway issue.

Sessions are in memory. A cloud reboot, session disconnection or fresh session can reset progress; durable saves are outside this assignment's scope. To roll back, revert the problematic GitHub commit and let Community Cloud redeploy.

## Official references

- [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Cloud secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
