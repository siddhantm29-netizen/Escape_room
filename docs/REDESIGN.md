# Playful investigation redesign

The user chose brighter colours and a detective-style evidence board. The app remains a Python/Streamlit game and does not use Bootstrap. Native Streamlit controls and scoped responsive CSS provide the layout without a new runtime dependency.

## What changed

- Conversation, input and known-object inspection controls form the investigation workspace.
- The evidence board sits beside it on larger screens and below it on narrow screens. It shows only earned clues, in discovery order, on source-specific coloured sheets.
- Actual clue count, inventory and exit state are grouped with the evidence. No invented figures or decorative clue ordering were added.
- Context controls collect the revealed key and read the accessible drawer note using the same Python rules as chat.
- Setup and instructions remain in the sidebar. Diagnostics, state inspection and the complete existing privacy notice remain at the bottom; a short privacy summary is always visible.
- The interface uses external semantic CSS tokens, system font fallbacks, accessible native controls and no additional external font/image service.

The direction and responsive contract are recorded in DESIGN.md. The new presentation helper is `escape_room/interface.py`; business rules and the Gemini boundary remain in their existing modules.

## Verification

- All **83 automated tests** pass, including all previous behavior/privacy checks and the new quick-action controls.
- A browser test reproduced a rapid-action bug: clicking Collect brass key and immediately submitting Open drawer could discard the earlier action. The app now processes pending actions in order; both a reproduction test and a browser retest confirm the fix.
- Browser checks at **320, 375, 768, 1280 and 1920 pixels** found no horizontal overflow in the main content. Main columns stack at the narrow sizes and sit side by side at desktop sizes.
- At 375 × 812, the heading stays below the framework toolbar, the chat viewport is 280 pixels high, and the composer ends inside the viewport. The native fixed-height wrapper required a scoped flex-basis override as well as a height rule.
- Keyboard navigation activates native controls and produces a visible 3-pixel solid focus outline. The tested custom text colour pairs have a minimum contrast ratio of **5.85:1**.
- Browser play verified inspection, a direct riddle answer, key collection, drawer opening, note collection, the full notebook, victory, disabled completion controls and restart.
- The avoid-ai-design scan reports **0 source findings** on the actual CSS. Hallmark's static app-scope scan reports **0 failures, 0 reflex findings and 0 warnings**.

The source scanners do not understand all generated Streamlit markup. Their counts are CSS-source checks, complemented by the browser observations above; they are not an automated accessibility certification or a guarantee for every device. Hallmark's Puppeteer renderer was not used; browser checks used the available computer-use tooling. Live Gemini language quality was not re-evaluated during this visual redesign; existing mocked integration tests passed.

## Design skill merge

The installed `avoid-ai-design` skill now combines guidance from funboy322/avoid-ai-design and nutlope/hallmark, with their original licences, pinned source revisions, reference material and reusable scanners. The merged workflow keeps subject-based design, pattern detection and usability checks while resolving conflicts: theme catalogues are optional, app screens do not inherit marketing page layouts, privacy and behavior tests remain authoritative, and the active browser tooling is respected. No hooks, provider integrations or global browser packages were activated.

The skill passed the bundled skill validator. Its retained avoid-ai-design scanner passed all 11 upstream unit tests. See the installed skill's SOURCES.md for provenance and merge decisions.
