# Demo guide (contains puzzle solutions)

For offline play select Version 2 and leave Use Gemini off. Enter one command at a time:

1. `examine desk` — read the spine/leaves riddle.
2. `solve desk book` — reveal the brass key.
3. `take key` — add it to inventory.
4. `open drawer` — use the collected key.
5. `examine drawer` — read the symbol-to-number instruction.
6. `examine bookshelf` — record oak 7, moon 3, star 1, sun 9.
7. `examine painting` — read the order: oak, moon, star, sun.
8. `unlock door 7319` — escape, provided all prerequisites are complete.

You may examine the painting or bookshelf earlier. The desk, key and drawer chain stays ordered. `look`, `inventory` and `hint` work at any time before escape.

For a short presentation: introduce V1, explain that its system prompt carries the rules, then switch to V2. Attempt `open drawer` and `unlock door 7319` in a fresh V2 session to show rejection. Complete the walkthrough, inspect public state and restart. For a genuine AI comparison, enable Gemini with your own key and use the protocol in TEST_CASES.md. Do not present controlled fixtures as live responses.
