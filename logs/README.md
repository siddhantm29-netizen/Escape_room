# Application diagnostic logs

Automatic logs are saved under `logs/` on the repository's **app-logs branch**:

[View saved logs](https://github.com/siddhantm29-netizen/Escape_room/tree/app-logs/logs)

The branch is created automatically after the app administrator configures `GITHUB_LOG_TOKEN` in Streamlit Secrets. See [setup and privacy details](../docs/LOGGING.md).

Each event has a separate JSON file. Exports contain only timestamps, version, mode, known action/object, result, processing stage, duration and HTTP status. Keys, credentials, chat, model prose, puzzle answers and final codes must never appear in these files.

A separate log branch prevents automatic log commits from redeploying the game or resetting other players. Do not upload raw browser/network dumps. Repository logs are public when the repository is public.
