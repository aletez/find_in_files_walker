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
  search the usual way or through the convenient dedicated window flow

## Similar plugins

There is the terrific [FindInFiles-addon](https://packages.sublimetext.io/packages/FindInFiles-addon) by [kaste](https://packages.sublimetext.io/?q=author%3A%22kaste%22). It doesn't support the new_window movement though, which I use primarily.

## Getting started 🚀

Install via Package Control, run a Find in Files search as usual, and
hit `Enter` to walk the results right there, or `ctrl+enter` to run the
same search in a fresh window - no extra setup required.

Once you're walking, step through matches with the arrow keys (or
`ctrl+enter` / `shift+ctrl+enter`).

When you're done, `alt+shift+w` closes everything the walk opened - or,
focused on the file you want to keep, it closes everything else instead.

## Shortcuts ⌨️

|      Shortcut      |       Focus on      |                       Does                       |            Command            |           Args          |
|--------------------|---------------------|--------------------------------------------------|-------------------------------|-------------------------|
| `enter`            | Find in Files panel | Run search in this window                        | `walker_open`                 | `{"new_window": false}` |
| `ctrl+enter`       | Find in Files panel | Run search in a new window                       | `walker_open`                 | `{"new_window": true}`  |
| `ctrl+enter`       | Results view        | Next match                                       | `walker_walk`                 | `{"action": "next"}`    |
| `shift+ctrl+enter` | Results view        | Previous match                                   | `walker_walk`                 | `{"action": "prev"}`    |
| `down`             | Results view        | Next match                                       | `walker_walk`                 | `{"action": "next"}`    |
| `up`               | Results view        | Previous match                                   | `walker_walk`                 | `{"action": "prev"}`    |
| `alt+shift+w`      | A walked file       | Close other walked files and the results view    | `walker_close_files_keep_one` | -                       |
| `alt+shift+w`      | Results view        | Close all walked files and keep the results view | `walker_close_files`          | -                       |

`Primary` is `Cmd` on macOS, `Ctrl` on Windows/Linux.
Both seemingly unconstrained bindings in fact run commands with restrictive `is_enabled` methods for reliability.

## Manual installation 📦

1. Open Preferences > Browse Packages
2. In the Packages folder, either:
   - Clone this repo: `git clone https://github.com/aletez/find_in_files_walker.git` or download the ZIP and unpack it
   - Rename the folder to `FindInFilesWalker`

Keybindings work immediately.

## Command names 🔌

The command names for your own binding:

- `walker_open` opens the dedicated window. Arrows work immediately.
- `walker_walk` selects the next (`"args": {"action": "next"}`) or the previous (`"args": {"action": "prev"}`)
outlined region in the Find Results and opens the same location in the original file 
in the right panel.
- `walker_close_files` closes the target files and leaves Find Results open.
- `walker_close_files_keep_one` closes the Find Results and the target files beside the 
one with focus (on top) in the right panel.

The last two are natively bound to the same `alt+shift+w` and the plugin 
recognizes the case by view's settings. 


## Platform support 💻

Tested on macOS, Windows; ST ver. 4200. Linux is WIP.
