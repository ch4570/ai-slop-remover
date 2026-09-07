# Haneul notes

This synthetic local notes editor helps an operator find and revise Korean notes.
Preserve a compact list beside the editor and stack them below 640px.

| Role | CSS token | Value | Use |
| --- | --- | --- | --- |
| Canvas | `--canvas` | `#f4f7fb` | Page |
| Surface | `--surface` | `#ffffff` | List and editor |
| Text | `--text` | `#172b45` | Headings and body |
| Action | `--action` | `#245ab5` | Primary button and focus |
| Error | `--error` | `#a52b25` | Failed save feedback |
| Gap | `--gap` | `16px` | Related control spacing |

Use the platform system font, visible labels and focus, and wrapping Korean text.
Preserve drafts during failed saves. Success means localStorage has been updated;
there is no server or synchronization. Do not invent either.
