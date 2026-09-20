# FindInFilesWalker 🔍

**Find in Files finally gets the preview it deserved.**

VS Code has Peek View, IntelliJ has Find Usages popup, and
Vim has quickfix-plus-preview setups. There you iterate over find-in-files
results, see the match highlighted live in the actual editable file, hop to the
next one, keep moving. Sublime Text has been missing it and this plugin
emulates this behavior. 

## What it does

Run a search, then walk your results one match at a time. Each match
opens live and editable in a pane right next to your results list -
not a read-only peek, an actual view into the real file, so you can
fix a typo or tweak a line without ever leaving the flow. Step forward,
step backward, and when you're done, close everything you opened in
one shot, or keep just the file you landed on.

- **Walk matches** ⬆️⬇️ - jump to the next or previous result with arrows and see it
  highlighted in context immediately
- **Live, not locked** ✏️ - the preview is the real file, fully editable,
  not a frozen readout
- **Clean up in one move** 🧹 - close every file you opened while walking,
  or keep just the one you're still working in
- **Drop-in on any Find Results view** ⚡ - works whether you opened your
  search the usual way or through the dedicated window flow

## Why this took so long

Honestly, unclear - Find in Files is one of the most-used features in
the editor, and "preview the match without losing my results" is an
old, well-worn idea everywhere else code gets searched. I intend 
this package to be the fix that was overdue.

## Getting started 🚀

Install via Package Control, run a Find in Files search as usual, and
hit `Enter` to walk the results right there, or `Ctrl+Enter` to run the
same search in a fresh window - no extra setup required.

Once you're walking, step through matches with the arrow keys (or
`Ctrl+Enter` / `Shift+Ctrl+Enter`).

When you're done, `Primary+Shift+W` closes everything the walk opened - or,
focused on the file you want to keep, it closes everything else instead.

## Shortcuts ⌨️

|      Shortcut      |                       Does                       |         Context          |        Command         |           Args          |
|--------------------|--------------------------------------------------|--------------------------|------------------------|-------------------------|
| `Enter`            | Run search in this window                        | Find in Files panel      | `open_walker_window`   | `{"new_window": false}` |
| `Ctrl+Enter`       | Run search in a new window                       | Find in Files panel      | `open_walker_window`   | `{"new_window": true}`  |
| `Ctrl+Enter`       | Next match                                       | Results view             | `walk_matches`         | `{"action": "next"}`    |
| `Shift+Ctrl+Enter` | Previous match                                   | Results view             | `walk_matches`         | `{"action": "prev"}`    |
| `Down`             | Next match                                       | Results view             | `walk_matches`         | `{"action": "next"}`    |
| `Up`               | Previous match                                   | Results view             | `walk_matches`         | `{"action": "prev"}`    |
| `Primary+Shift+W`  | Close other walked files and the results view    | Focused on a walked file | `keep_one_walked_file` | -                       |
| `Primary+Shift+W`  | Close all walked files and keep the results view | Focused on Find Results  | `close_walked_files`   | -                       |

`Primary` is `Cmd` on macOS, `Ctrl` on Windows/Linux.

## Manual installation 📦

1. Open Preferences > Browse Packages
2. In the Packages folder, either:
   - Clone this repo: `git clone https://github.com/aletez/find_in_files_walker.git` or download the ZIP and unpack it
   - Rename the folder to `FindInFilesWalker`

Keybindings work immediately.

## Command names 🔌

The command names for your own binding:

- `open_walker_window` opens the dedicated window. Arrows work immediately.
- `walk_matches` selects the next (`"args": {"action": "next"}`) or the previous (`"args": {"action": "prev"}`)
outlined region in the Find Results and opens the same location in the original file 
in the right panel.
- `close_walked_files` closes the target files and leaves Find Results open.
- `keep_one_walked_file` closes the Find Results and the target files beside the 
one with focus (on top) in the right panel.

The last two are natively bound to the same `primary+shift+w` and the plugin 
recognizes the case by view's settings. 


## Platform support 💻

Tested on macOS, ST ver. 4200. Windows and Linux are WIP.