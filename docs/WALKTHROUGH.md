# Demo guide (contains puzzle solutions)

The revised puzzle spreads one digit across each of four objects. No single object lists the code or the full symbol order. Hints offer reasoning nudges without providing digits or assembling the order.

For offline play select Version 2 and leave Use Gemini off. Enter one command at a time:

1. `examine desk` — read the spine/leaves riddle. A crescent under the blotter is marked **6**, and the moon follows every other keeper.
2. `solve desk book` — reveal the brass key.
3. `take key` — add it to inventory.
4. `open drawer` — use the collected key.
5. `examine drawer` — find an **oak seal marked 8** and the instruction to follow the keepers' procession, rather than discovery order.
6. `examine bookshelf` — find a **sun marked 4**. Its card says the sun stands immediately before the star.
7. `examine painting` — find a **star marked 2**. The frame says the oak is first.
8. Combine the relations: oak first, moon last, sun immediately before star. The only order is **oak, sun, star, moon**, giving **8426**.
9. `unlock door 8426` — escape, provided all prerequisites are complete.

The desk, bookshelf and painting can be examined in any order. The drawer's digit remains behind the riddle/key chain. The previous code, 7319, is no longer valid. The arrangement is fixed for this revision; it does not randomize during play.

`look`, `inventory` and `hint` work before escape. Hints never print digits or combine the final sequence. For a genuine AI comparison, enable Gemini with your own key and use the protocol in TEST_CASES.md. Do not present controlled fixtures as live responses.
