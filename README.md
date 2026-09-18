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
hit `alt+enter` to open a Walker Window and start walking results
immediately - no extra setup required. You can also use the Walker Window
menu under `...` on the right side of the Find in Files panel or choose
the command "Open File Walker Window" from the Palette.

You can walk the results with arrows or with `alt+enter` for next
and `shift+alt+enter` for previous.

After you're done but want to keep one target file or the Find Results file open,
just focus the view and hit `super+shift+w`. If you don't, add a `primary+w`
after that.

## Manual installation 📦

1. Open Preferences > Browse Packages
2. In the Packages folder, either:
   - Clone this repo: `git clone https://github.com/aletez/find_in_files_walker.git`
   - Or download the ZIP, unpack it, rename the folder to `FindInFilesWalker`

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

The last two are natively bound to the same `super+shift+w` and the plugin 
recognizes the case by view's settings. 


## Platform support 💻

Tested on macOS, ST ver. 4200. Windows and Linux are WIP.