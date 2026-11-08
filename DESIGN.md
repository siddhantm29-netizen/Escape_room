# The Last Library: investigation desk

## Purpose and direction

A playable escape room for course students, not a product landing page. The user chose a playful investigation: brighter colours and a detective-style evidence board. The primary task is investigating the library while comparing already discovered evidence.

## Composition

A compact title and scene-setting line lead directly into a two-column investigation desk. Conversation and input sit on the left; the clue notebook sits on the right. Actual clue count, inventory and exit status belong to the notebook. Known-object inspection controls provide reliable ways to explore without revealing clues. On small screens the desk stacks: interaction first, notebook next. Setup and instructions stay in the sidebar; diagnostics, state inspection and the complete privacy disclosure stay secondary at the bottom.

## Visual system

- Ink `#18364A`: body text and headings, based on the case-file reading surface.
- Board `#EDF4F8`: cool, bright work surface; no parchment/terracotta treatment.
- Cabinet `#234E70`: sidebar and principal controls; a solid structural colour rather than an ornamental gradient.
- Signal `#F3C95A`: attention and progress, recalling the brass key without giving it game authority.
- Paper `#FBFDFF`: conversation and ordinary controls.
- Evidence sheets use pale yellow, blue, pink and mint with the same dark ink. Colour distinguishes source notes, never solution position.

Interface type is Trebuchet MS with honest Verdana/sans-serif fallbacks; clue text uses Georgia with a serif fallback, reflecting printed evidence. No external font requests or additional runtime dependencies are required. All CSS colours and font families are declared as semantic tokens.

Use restrained rounded controls and a small offset edge on evidence sheets. Do not add fake browser chrome, decorative numbering, status dots, gradients, background grain, generated library imagery or a landing-page hero. The evidence board itself is the signature: every note is real earned game content, not a decorative prop.

## Behavior and accessibility

Preserve game rules, all widget keys, separate versions, restarts, natural-language input, the four-fragment notebook and the harder clue arrangement. Keep the notebook in discovery order and hide unearned clues. Controls must have visible focus, native disabled behavior and readable contrast. No essential animation. Maintain token-based styling and respect reduced motion. Do not clip overflowing content to mask layout errors.

Keep credentials only in session memory. Do not put action types, selected objects, clues, inventory, answers, chat or progress into diagnostics. Logging privacy and optional GitHub upload behavior are unchanged.

## Sources and audit

Applied the merged avoid-ai-design + Hallmark skill, based on:
- https://github.com/funboy322/avoid-ai-design at `2b7c71836b06cdf6b3d73265b56490c1b75ad5aa`
- https://github.com/nutlope/hallmark at `407fa689f4a276f2fd389208d271d0fef08f5058`

Before: the code scan of extracted inline CSS reported zero findings, but could not see Streamlit's TOML palette or generated layout. The rendered page showed a warm cream/rust palette, repeated uppercase labels, large generic status figures, nested notebook borders and a long single-column chat. These are rendered/contextual observations, not claims of authorship. The redesign retains the useful working notebook, rules and disclosures while recomposing their presentation.

## Confirmed implementation

Conversation height adapts through a scoped native wrapper rule: 336px at larger sizes and 280px on phones. The fixed framework toolbar remains above the content. Keyboard focus is a solid 3px outline. Browser checks cover 320/375/768/1280/1920px without main-content overflow. The full previous game/privacy suite and new interaction checks pass (83 tests); the browser escape and restart flows also pass. Source audits have zero findings on the final CSS, with framework limitations documented in docs/REDESIGN.md.
