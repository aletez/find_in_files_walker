"""
FindInFilesWalker - Sublime Text plugin

Patches a gap in Sublime's built-in find_in_files: opens "Find Results"
in a dedicated window with a two-column layout, results on the left and
a live, editable preview of the currently selected match on the right.
Includes commands to walk through matches one at a time, and to
close/keep the previewed files once done.

WalkMatchesCommand is self-contained: it works on any "Find Results"
view, not just ones opened via OpenWalkerWindowCommand.
Binding "walk_matches" with "action": "next" (and "prev") directly to
a key in an existing find-in-files results view gets the full walking
experience without going through the dedicated-window flow at all -
no separate "init" binding is needed, since step_to_match calls
init_walk itself the first time it's needed. Using
OpenWalkerWindowCommand at all is therefore facultative:
its "Window" names the one thing it adds over WalkMatchesCommand
alone - unconditionally opening a brand new window - which is only
worth doing when you want the two-column layout in its own window
rather than reusing wherever the results view already lives.
"""

import sublime
import sublime_plugin
import re
import time


def _get_result_views(window):
    """
    Return the window's views named "Find Results".

    In practice there is at most one, so the result is either a
    one-item list or an empty list.
    """
    return [view for view in window.views() if view.name() == "Find Results"]


class FindInFilesWalkerListener(sublime_plugin.EventListener):
    """
    Watches for new windows and, if one was opened to host a walked
    search (see OpenWalkerWindowCommand), replays the search in
    it and sets it up for walking.
    """

    def on_new_window(self, window):
        """
        If this new window was requested by OpenWalkerWindowCommand
        (flagged via the "find_in_files_walker_search_text" window
        setting), take over its setup: copy the project, open the find
        panel, paste in the search text, and run the search. Otherwise
        leave the window alone.
        """
        original_window = None
        search_text = None
        for other_window in sublime.windows():
            search_text = other_window.settings().get(
                "find_in_files_walker_search_text"
            )
            if search_text:
                other_window.settings().erase("find_in_files_walker_search_text")
                original_window = other_window
                break

        # Not a window we requested - leave it as a regular new window
        if not original_window:
            return

        # Copy project folders so the search has the same scope
        original_project = original_window.project_data()
        window.set_project_data(original_project)

        deadline = time.time() + 1.5

        self._wait_for_project_data(window, search_text, deadline, original_project)


    def _wait_for_project_data(self, window, search_text, deadline, original_project):
        """Poll until the both windows have the same folders open."""
        if window.project_data() == original_project:
            sublime.set_timeout(
                lambda:
                window.run_command("show_panel", {"panel": "find_in_files"}),
            0)
            sublime.set_timeout(
                lambda:
                self._wait_for_panel(window, search_text, deadline),
            1)
            return
        if time.time() >= deadline:
            raise TimeoutError

        sublime.set_timeout(
            lambda: self._wait_for_project_data(window, search_text, deadline),
            10
        )



    def _wait_for_panel(self, window, search_text, deadline):
        """Poll until the find_in_files panel is active, then proceed."""
        if window.active_panel() == "find_in_files":
            # Extra tick (timeout=0) so the panel has fully taken focus
            sublime.set_timeout(
                lambda: self._paste_and_run_search(window, search_text, deadline), 0
            )
            return

        if time.time() >= deadline:
            raise TimeoutError

        sublime.set_timeout(
            lambda: self._wait_for_panel(window, search_text, deadline), 10
        )

    def _paste_and_run_search(self, window, search_text, deadline):
        """
        Paste search_text into the (focused) find-in-files search field
        via the clipboard, restoring the clipboard afterwards, then run
        the search and wait for the results view to be ready.
        """
        old_clip = sublime.get_clipboard()
        sublime.set_clipboard(search_text)
        window.run_command("paste")
        sublime.set_clipboard(old_clip)
        # Extra tick (timeout=0) so the paste is applied before searching
        sublime.set_timeout(lambda: window.run_command("find_all"), 0)

        self._prepare_walk(window, deadline)

    def _prepare_walk(self, window, deadline):
        """
        Poll until the "Find Results" view exists and has finished
        loading, then trigger WalkMatchesCommand to index its matches
        and set up the two-column walking layout.
        """
        result_views = _get_result_views(window)
        if result_views and not result_views[0].is_loading():
            func_init = lambda: result_views[0].run_command(
                "walk_matches", {"action": "init"}
            )
            sublime.set_timeout(func_init, 0)
            return

        if time.time() >= deadline:
            raise TimeoutError

        sublime.set_timeout(lambda: self._prepare_walk(window, deadline), 10)


class OpenWalkerWindowCommand(sublime_plugin.WindowCommand):
    """
    Opens a new window that will show "Find Results" on the left and
    a live preview of the selected match on the right. Grabs the
    current search text from the active find-in-files panel and hands
    it off to FindInFilesWalkerListener via a window setting.

    Using this command is facultative: WalkMatchesCommand alone
    already provides the full walking experience on any existing
    "Find Results" view. The "Window" here marks the one thing this
    command adds on top - unconditionally opening a fresh window for
    the walk, rather than setting up the layout wherever the results
    view happens to already be.
    """

    def is_enabled(self):
        """Only available while the "find_in_files" panel is active."""
        panel = sublime.active_window().active_panel()
        return panel == "find_in_files"

    def run(self):
        # (Re)focus the "find" text box so select_all/copy target it
        self.window.run_command("show_panel", {"panel": "find_in_files"})

        # Grab the current search text via the clipboard, then restore it
        self.window.run_command("select_all")
        old_clip = sublime.get_clipboard()
        self.window.run_command("copy")
        search_text = sublime.get_clipboard()
        sublime.set_clipboard(old_clip)

        # Stash the search text for FindInFilesWalkerListener.on_new_window to pick up
        self.window.settings().set("find_in_files_walker_search_text", search_text)

        # Open the window; FindInFilesWalkerListener's on_new_window takes it from here
        sublime.run_command("new_window")


class WalkMatchesCommand(sublime_plugin.TextCommand):
    """
    Runs in the "Find Results" view. Indexes each match's target file
    and location, and lets the user walk through matches while
    previewing the corresponding file/line in the right-hand pane.

    Self-contained: works on ANY "Find Results" view, including one
    that already existed before this plugin got involved - not only
    ones opened via OpenWalkerWindowCommand / FindInFilesWalkerListener.
    "next"/"prev" index matches on demand via init_walk if they
    haven't been indexed yet, so binding just "next" (and "prev") to a
    key - with no separate "init" binding - is enough to get the full
    walking experience on any results view, keymap-space included.
    """

    def run(self, edit, action):
        """
        action:
          "next" - jump to and preview the next match after the current selection
                    (indexes matches first via init_walk if not done yet - the
                    action to bind to a key)
          "prev" - same as "next" but for the previous match
          "init" - wait for the results view to finish loading, then index
                    matches without moving the selection; used internally by
                    FindInFilesWalkerListener to pre-warm a freshly opened
                    results view before handing off control
        """
        deadline = time.time() + 1.0
        if action == "init":
            self._wait_to_init_walk(deadline)
        elif action == "next":
            self.step_to_match(forward=True)
        elif action == "prev":
            self.step_to_match(forward=False)

    def _wait_to_init_walk(self, deadline):
        """Poll until the results view is loaded, then index its matches."""
        result_views = _get_result_views(self.view.window())
        if result_views and not result_views[0].is_loading():
            # Extra tick (timeout=0) for safety before indexing
            sublime.set_timeout(lambda: self.init_walk(result_views[0].id()), 0)
            return

        if time.time() >= deadline:
            print("I can't see the loaded Find Results view")
            return

        sublime.set_timeout(lambda: self._wait_to_init_walk(deadline), 10)

    def init_walk(self, results_view_id):
        """
        Index every match region in the results view (file, row, column,
        length) and stash it on the view as "walk_locations". Also
        arranges the window into the two-column walking layout, with the
        results view pinned to the left column.
        """
        results_view = next(
            view
            for view in sublime.active_window().views()
            if view.id() == results_view_id
        )

        # "match" regions are the highlighted search hits in the results view
        match_regs = results_view.get_regions("match")
        if not match_regs:
            print("No match regions found in Find Results")
            return

        # Map each match region to (file, row, col, length)
        target_file_locations = self.target_locations(match_regs, results_view)
        full_locations = self.get_full_locations(
            results_view, match_regs, target_file_locations
        )
        results_view.settings().set("walk_locations", full_locations)

        # Ensure a left/right two-column layout
        window = results_view.window()
        window.set_layout(
            {
                "cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
                "cols": [0.0, 0.5, 1.0],
                "rows": [0.0, 1.0],
            }
        )

        # If a two-column layout already existed, make sure this view is on the left
        window.set_view_index(self.view, 0, -1)
        window.focus_view(results_view)
        results_view.settings().set("file_in_files_walker", True)

    def step_to_match(self, forward=True):
        """
        Move the selection to the next (forward=True) or previous
        (forward=False) match relative to the current selection, and
        open a preview of that match's target file/location. Only
        meaningful when run against the "Find Results" view.
        """
        match_regs = self.view.get_regions("match")

        # Index the matches if this is the first run, or re-index if the
        # results view has since gained/lost matches (e.g. search re-run)
        if not self.view.settings().get("walk_locations"):
            self.init_walk(results_view_id=self.view.id())
        locations = self.view.settings().get("walk_locations")
        try:
            if len(match_regs) != len(locations):
                self.init_walk(results_view_id=self.view.id())
        except TypeError as e:
            # match_regs or locations still missing after init_walk
            raise e

        # Pick the nearest match in the requested direction from the
        # current selection; report and abort if there isn't one
        selection_end = self.view.sel()[0].end()
        if forward:
            candidates = [r for r in match_regs if r.end() > selection_end]
        else:
            candidates = list(
                reversed([r for r in match_regs if r.end() < selection_end])
            )

        try:
            link = candidates[0]
        except IndexError:
            print("No more matches in that direction")
            return

        self.select_link(link)

        target_file, row, col, length = locations[str(link.begin())]
        self.open_match_preview(target_file, row, col, length)

    def select_link(self, match_region):
        """Select and scroll the results view to the given match region."""
        self.view.sel().clear()
        self.view.sel().add(match_region)
        self.view.show_at_center(match_region)

    def open_match_preview(self, target_file, row, col, length):
        """
        Open target_file at (row, col) in the right-hand group. Mark it "walked_closable" so it can
        be cleaned up later'.
        """

        # FORCE_GROUP clones the view into group 1 instead of hijacking
        # an existing view of this file that may already be in group 0
        target_view = sublime.active_window().open_file(
            fname=f"{target_file}:{row}:{col}",
            flags=sublime.ENCODED_POSITION | sublime.FORCE_GROUP|\
            sublime.SEMI_TRANSIENT|sublime.REPLACE_MRU,
            group=1,
        )

        deadline = time.time() + 1.0
        self._highlight_walked_region(target_view, length, deadline)

    def _highlight_walked_region(self, target_view, length, deadline):
        """
        Poll until target_view has finished loading, then flag it as
        closable (if it wasn't already open) and draw an outline around
        the matched text. Keeps focus on the results view throughout.
        """
        if not target_view.is_loading():
            # Extra tick (timeout=0) for safety before touching settings
            mark_me = lambda: target_view.settings().set("walked_closable", True)
            sublime.set_timeout(mark_me, 0)

            start_point = target_view.sel()[0]
            target_match = sublime.Region(start_point.a, start_point.a + length)
            target_view.add_regions(
                "match",
                [target_match],
                scope="text",
                icon="",
                flags=sublime.DRAW_NO_FILL,
            )
            target_view.window().focus_view(self.view)
            return

        if time.time() >= deadline:
            return

        sublime.set_timeout(
            lambda: self._highlight_walked_region(
                target_view, length, deadline
            ),
            0,
        )

    def row_col_length(self, results_view, target_line, reg_local):
        """
        Convert a match region's position within the results view into
        (target_line, column, length) in the *target file's* coordinates.

        The results view prefixes each match line with a 6-character
        gutter (line number + margin), so 6 is subtracted from the
        column to get the real column in the target file. Likewise,
        when a match spans multiple lines, each extra line carries the
        same 6-character gutter plus a newline (7 chars) that isn't
        part of the actual matched text, so that's subtracted from the
        raw region size to get the true match length.

        :param results_view: The "Find Results" view
        :param target_line: The matched line number in the target file
        :param reg_local: The match's region within results_view
        :return: [target_line, column, length]
        """
        first_col_dirty = results_view.rowcol(reg_local.begin())[1]
        first_col = first_col_dirty - 6

        length = reg_local.size()
        reg_a, reg_b = reg_local.to_tuple()
        number_of_newlines = abs(
            self.view.rowcol(reg_a)[0] - self.view.rowcol(reg_b)[0]
        )
        length = length - number_of_newlines * 7

        return [target_line, first_col, length]

    def target_locations(self, match_regs, results_view):
        """
        For each match region, read the line number shown at the start
        of its line in the results view, and compute its (line, column,
        length) via row_col_length.

        :param match_regs: Match regions in the results view
        :param results_view: The "Find Results" view
        :return: {region_start: [target_line, column, length]}
        """
        target_line_numbers = []
        for reg in match_regs:
            content = results_view.substr(results_view.line(reg))
            number_match = re.match(r"\d+", content.strip())
            if number_match:
                target_line_numbers.append(number_match.group(0))

        return {
            str(reg_local.begin()): self.row_col_length(
                results_view, target_line, reg_local
            )
            for target_line, reg_local in zip(target_line_numbers, match_regs)
        }

    def get_full_locations(self, results_view, match_regs, target_file_locations):
        """
        Prefix each match's (line, column, length) with the file name
        it belongs to, by walking file-name headers and match regions
        together in document order and tracking the most recent header.

        :param results_view: The "Find Results" view
        :param match_regs: Match regions in the results view
        :param target_file_locations: {region_start: [line, column, length]}
        :return: {region_start: [file_name, line, column, length]}
        """
        match_files = results_view.find_by_selector(
            "entity.name.filename.find-in-files"
        )

        # Walk file-name headers and match regions together, in document order
        clues = sorted(match_files + match_regs)

        locations = dict()
        cur_file = match_files[0]
        for clue in clues:
            if clue in match_files:
                cur_file = results_view.substr(clue).strip(":")
            else:
                locations[str(clue.begin())] = [
                    cur_file
                ] + target_file_locations[str(clue.begin())]
        return locations


class CloseWalkedFilesCommand(sublime_plugin.TextCommand):
    """Closes every view opened for walking, and resets the layout."""

    def run(self, edit):
        for target_view in sublime.active_window().views():
            closable = target_view.settings().get("walked_closable")
            target_view.settings().erase("walked_closable")
            if closable:
                target_view.close()

        sublime.active_window().set_layout(
            {"cells": [[0, 0, 1, 1]], "cols": [0.0, 1.0], "rows": [0.0, 1.0]}
        )
        self.view.settings().erase("file_in_files_walker")


class KeepOneWalkedFileCommand(sublime_plugin.TextCommand):
    """
    Closes the "Find Results" view and every walked file except the
    one currently focused in the preview pane, then collapses back to
    a single-column layout with that file kept open.
    """

    def run(self, edit):
        views = sublime.active_window().views()
        if "Find Results" not in map(sublime.View.name, views):
            print("No Find Results view among the window's views")
            return
        results_view = next(v for v in views if v.name() == "Find Results")
        results_view.close()

        target_group = 1
        focused_target_view = sublime.active_window().active_view_in_group(
            target_group
        )

        # Close every walked file except the one still focused
        for v in sublime.active_window().views():
            if v.settings().get("walked_closable") and v != focused_target_view:
                v.close()

        # Move the kept view into group 0 and collapse to one column
        offset = len(sublime.active_window().views_in_group(0))
        sublime.active_window().set_view_index(focused_target_view, 0, offset)
        sublime.active_window().set_layout(
            {"cells": [[0, 0, 1, 1]], "cols": [0.0, 1.0], "rows": [0.0, 1.0]}
        )
        sublime.active_window().focus_view(focused_target_view)
        focused_target_view.settings().erase("walked_closable")