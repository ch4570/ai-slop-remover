Improve this local Korean notes editor using the supplied AI Slop Remover skill set.
Make searching and saving predictable and preserve the existing Haneul brand in
DESIGN.md. In particular, failed saves must preserve the draft and offer a working
retry without claiming success; completing Korean IME composition with Enter must
not save; typing a search must not create one browser history entry per keystroke.
Preserve ordinary search, editing, successful local persistence, labels and keyboard
access. Verify what you can and state any unverified behavior honestly.

Edit only index.html, app.js, style.css, and DESIGN.md in this fixture copy. Keep the
DOM IDs, the storage key `haneul-eval-notes`, note IDs, and the failure checkbox
behavior stable so independent checks can exercise the same public contract.
Use no new dependencies, network requests, or backend. Do not edit evaluation checks.
