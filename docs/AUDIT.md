# Deployment-readiness audit — 8 November 2026

## Bugs reproduced and fixed

- Malformed Gemini candidate/part shapes could raise an uncaught error and crash the page. These now produce a safe error.
- An interrupted HTTP response could escape the network-error handler. It is now handled without a page crash.
- A model-proposed `open door` action could supply a code absent from the player's message. It now follows the same explicit-input check as `unlock door`.
- Substring checks could accept `book` inside `notebook`, or the correct four digits inside a longer incorrect number. Answers and codes now require whole-word/whole-value boundaries.
- Whitespace-only API keys enabled requests. They are now treated as empty.
- The live-mode caption implied a verified connection even before a request succeeded. It now simply identifies live API mode.

## Privacy and hallucination changes

Each player supplies their own key. The application no longer accepts a shared environment/API-secret key. Refreshing creates a new session without the previous key; a Clear API key button clears it without deleting puzzle progress. Keys are not written to cookies, browser storage, logs, files or the game transcript. Browser password managers are outside the app's control. Streamlit can retain disconnected sessions briefly in server memory for cleanup.

Version 2 uses temperature 0.0 for both model requests. Its Python validator and approved narration remain the enforcement boundary. Version 1 retains temperature 0.2 and its intentionally weaker conversational baseline for the assignment.

The footer now explains key handling, Google transmission, account quotas/billing, sensitive information and temporary game progress.

## Dependency and hosting checks

The previous Streamlit 1.50/Pillow 11.3 dependency set had known advisories. Updated to Streamlit 1.67.0 and Pillow 13.0.0 after reviewing official release notes and compatibility requirements. The current app requires Python 3.11+; Python 3.12 is the tested cloud configuration. A fresh requirements audit found **no known vulnerabilities** on the audit date. This does not guarantee the absence of undiscovered vulnerabilities.

38 automated tests pass on the current Python 3.12 environment. They include the entire offline solution, mocked live V1/V2 page flows, errors, restart, independent visitors, key clearing and fresh-session key isolation. Dependency compatibility and Python syntax checks also pass. The local server health endpoint returns OK. The updated disclaimer and key controls were observed in a browser; a browser refresh check was interrupted, so fresh-session isolation is established by AppTest rather than claimed as a completed browser refresh test.

The new Game checks workflow runs installation, dependency compatibility, syntax, all tests and vulnerability auditing on GitHub. Streamlit Community Cloud deploys separately from the connected repository; see DEPLOYMENT.md. No cloud app has been created by this audit.

## Limits

The user's earlier live Gemini connection check succeeded. This audit uses controlled API responses and does not claim a full live-model playthrough or a measured prompt-injection failure rate. No guarantee of zero bugs or zero model misunderstanding is made. Version 1's model-authoritative behavior is an intentional comparison baseline, not equivalent to Version 2 validation.

The original course report records the earlier implementation milestone. This audit and the current README record the latest test count, dependency versions and deployment setup.

## Puzzle revision

The later puzzle revision distributes digits across the desk, bookshelf, painting and locked drawer. Relative-position clues determine their order. Hints no longer provide direct answer cues or assemble the code. The full suite now contains 42 passing tests; the previous code is explicitly rejected.
