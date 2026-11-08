# Diagnostic logs and automatic GitHub saving

## What the app records

Each turn, connection check, restart and key-clear action records a UTC timestamp, game version, mode, result, processing stage, processing time and HTTP status. Version 2 also records the validated action kind and canonical object name. It never records API keys, GitHub tokens, player chat, model prose, puzzle answers or final codes. Both field names and values are checked before GitHub upload.

The diagnostic panel at the bottom of the page provides a JSON download, a saved-logs link and a retry control. The latest 200 events remain in the current session's memory. The same metadata is sent to Streamlit server logs for cloud administrators. A disconnected/restarted session can lose unsaved events.

## Enable automatic saving

1. In GitHub, create a **fine-grained personal access token**. Select only `siddhantm29-netizen/Escape_room` under repository access and grant **Contents: Read and write**. Choose an expiry date. Workflow, administration and access to other repositories are not required.
2. In your Streamlit Community Cloud app, open **Settings → Secrets** and add this root-level value:

   ```toml
   GITHUB_LOG_TOKEN = "your_fine_grained_token"
   ```

3. Save the settings and let Streamlit restart. Never put this token in chat, source code, the player's API-key field, or the repository. For local testing only, use `.streamlit/secrets.toml`, which is gitignored, or the `GITHUB_LOG_TOKEN` environment variable.
4. Perform an action. The diagnostic panel should report **Saved to GitHub**. Open **View saved GitHub logs** to verify the uploaded file.

Automatic saving is implemented, but no live token-based upload was performed during development. Until an administrator configures the token, events remain available through session download and server output.

## Where files go

The app creates an **app-logs** branch in the same repository if necessary. Each event is saved in its own JSON file under `logs/`, named `session-<random-session-id>-<event-number>.json`. The random ID changes for a fresh browser session. File contents contain the event's UTC timestamp. The files persist after a browser refresh once GitHub confirms a successful upload.

Logs use a separate branch because committing them to `main` would redeploy the Streamlit app after every action and interrupt players. Game checks run on `main`; log commits on `app-logs` do not run or deploy the game. The main branch also contains `logs/README.md` explaining the location.

The destination repository, branch and allowed filename pattern are fixed in code. The token is used only in an HTTPS authorization header to GitHub's API. No token is included in a URL, export or user-visible error.

## Failures and limits

An upload failure never reverses a game action. The metadata remains downloadable, and up to 200 pending events are retained in the current session. The app retries a small batch on later actions; **Retry log upload** can flush more events. More than 200 pending events during an extended outage can drop the oldest pending metadata, and a session reset loses any pending uploads. The app shows saving errors rather than claiming those events reached GitHub.

GitHub rate limits, token expiry and branch protection can reject uploads. Check that the selected token can create/update the `app-logs` branch. Do not weaken protection on the deployment branch. Per-event commits suit this small course project; a busy public service would need a dedicated log store instead of a Git repository.

Because the repository is public, saved metadata is public. This is explained in the page's footer. Do not manually upload unsanitized browser/network dumps or raw private chat.

## Using logs to improve the game

- A rejected `examine/drawer` action before key collection is expected. An unknown target for the same object suggests a parsing regression.
- Repeated parser errors suggest response-format or interpretation problems. The log identifies the stage without storing the player's sentence.
- HTTP 400/401/403 indicates an authentication/access/request problem; 429 indicates quota/rate limiting; 5xx indicates a provider/gateway problem.
- A narrator fallback means Python already processed the action and displayed its verified result; do not repeat a successful action merely because narration failed.
- Reproduce the issue with a safe test case, add a regression test, fix the underlying rule or parser, then run the full test suite. Logs are evidence for debugging, not instructions to modify game rules automatically.
