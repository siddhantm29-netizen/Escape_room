# Implementation scope

- Python 3.11+, Streamlit chat UI, Gemini REST API. No paid service required.
- One library: desk, bookshelf, painting, drawer, exit door.
- Puzzle chain: desk riddle -> collect brass key -> open drawer; one digit on each of the desk, bookshelf, painting and drawer plus separate relative-position clues -> four-digit exit code. Python requires all three discoveries and the key/drawer chain before escape in V2.
- V1: full room configuration and conversation sent to an LLM Game Master; the model's escape marker completes the game. Intentionally retain this baseline for comparison.
- V2: model proposes one action; strict Python validation controls state. Solutions remain in server-side configuration. Narration is selected by the model from approved outcome variants, preventing invented objects or spoiler prose. This trades unrestricted narration for reliability.
- Offline V2 uses documented commands and authored narration; it is explicitly a demo, not an LLM replacement. Live V1 and natural-language V2 require a user-supplied API key.
- Each version has independent conversation and restart. No database, account system or persistent personal data.
- Deliver code, diagrams, at least five comparative test cases, a 2–3 page report, and GitHub-ready setup documentation.

## Acceptance checks
Complete solution, locked/missing-item rules, wrong codes, forged progress, administrator claims, secret requests, malformed model output, service errors, session isolation and restart. V1 weaknesses are demonstrated with controlled model fixtures, not reported as empirical Gemini results. A live adversarial protocol is included for the student's own key.

## UI direction

The user selected a playful investigation with brighter colours and a detective-style evidence board. Keep conversation and earned evidence together on desktop and stack them on small screens. Native inspection buttons and contextual key/note actions retain the same validation as chat. Setup stays in the sidebar; diagnostics and complete disclosures remain secondary at the bottom. DESIGN.md records the current tokens and layout contract.
