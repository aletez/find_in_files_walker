"""
FindInFilesWalker - Sublime Text plugin

Two-column window: results on the left, live editable preview of the
selected match on the right. WalkMatchesCommand works on any "Find
Results" view - bind "next"/"prev" for the full experience without
OpenWalkerWindowCommand.
"""

import sublime
import sublime_plugin
import re
import time


def _get_result_views(window):
	"""The window's views named "Find Results" (usually zero or one)."""
	return [view for view in window.views() if view.name() == "Find Results"]


# Matches the "5 matches across 2 files"/"0 matches" summary line
# find_in_files appends when done - is_loading() isn't reliable here.
_RESULTS_DONE_RE = re.compile(r"\d+ match(es)?( (across|in) \d+ files?)?\s*$")


def _results_view_ready(view):
	content = view.substr(sublime.Region(0, view.size()))
	endline_match = bool(_RESULTS_DONE_RE.search(content))
	return endline_match


def _prepare_walk(window, deadline):
	"""Poll for a loaded "Find Results" view, then init/preview it."""
	result_views = _get_result_views(window)
	if result_views and _results_view_ready(result_views[0]):
		func_init = lambda: result_views[0].run_command(
			"walk_matches", {"action": "init"}
		)
		sublime.set_timeout(func_init, 0)
		return

	if time.time() >= deadline:
		return

	sublime.set_timeout(lambda: _prepare_walk(window, deadline), 10)


class OpenWalkerWindowCommand(sublime_plugin.WindowCommand):
	"""
	Runs the search here, then either walks it in place or clones the
	finished "Find Results" view into a fresh window, per the
	"open_new_window" setting.
	"""

	def is_enabled(self):
		"""Only available while the "find_in_files" panel is active."""
		panel = sublime.active_window().active_panel()
		return panel == "find_in_files"

	def name(self):
		return "walker_open"

	def run(self, new_window):
		self.window.run_command("show_panel", {"panel": "find_in_files"})
		self.window.run_command("find_all")
		deadline = time.time() + 1.0
		self._wait_for_results(deadline, new_window)

	def _wait_for_results(self, deadline, new_window):
		result_views = _get_result_views(self.window)
		if result_views and _results_view_ready(result_views[0]):
			self._on_results_ready(result_views[0], new_window)
			return

		if time.time() >= deadline:
			return

		sublime.set_timeout(lambda: self._wait_for_results(deadline, new_window), 10)

	def _on_results_ready(self, results_view, new_window):
		if not new_window:
			deadline = time.time() + 1.0
			_prepare_walk(self.window, deadline)
			return

		content = results_view.substr(sublime.Region(0, results_view.size()))
		region_tuples = [
			(r.a, r.b) for r in results_view.get_regions("match")
		]
		syntax = results_view.settings().get("syntax")
		original_project = self.window.project_data()

		# Avoid a leftover view satisfying the next run's readiness check
		results_view.set_scratch(True)  # scratch = no "save changes?" prompt
		results_view.close()

		# No listener needed: diff window ids before/after to find the new one
		# (also no bribing, threatening, or asking the window nicely - just counting)
		existing_ids = set(w.id() for w in sublime.windows())
		sublime.run_command("new_window")
		deadline = time.time() + 1.0
		self._wait_for_new_window(
			existing_ids, content, region_tuples, syntax, original_project, deadline
		)

	def _wait_for_new_window(
		self, existing_ids, content, region_tuples, syntax, original_project, deadline
	):
		"""Find the new window by diffing ids seen before new_window."""
		new_windows = [w for w in sublime.windows() if w.id() not in existing_ids]
		if new_windows:
			self._clone_into_window(
				new_windows[0], content, region_tuples, syntax, original_project
			)
			return

		if time.time() >= deadline:
			return

		sublime.set_timeout(
			lambda: self._wait_for_new_window(
				existing_ids, content, region_tuples, syntax, original_project,
				deadline,
			),
			10,
		)

	def _clone_into_window(
		self, window, content, region_tuples, syntax, original_project
	):
		if original_project:
			window.set_project_data(original_project)

		new_view = window.new_file()
		new_view.set_name("Find Results")
		new_view.set_scratch(True)  # generated content, no save prompt needed
		if syntax:
			new_view.assign_syntax(syntax)
		new_view.run_command("append", {"characters": content})
		new_view.add_regions(
			"match",
			[sublime.Region(a, b) for a, b in region_tuples],
			scope="text",
			icon="",
			flags=sublime.DRAW_NO_FILL,
		)



		deadline = time.time() + 1.0
		_prepare_walk(window, deadline)


class WalkMatchesCommand(sublime_plugin.TextCommand):
	"""
	Runs in the "Find Results" view: indexes matches and lets the user
	walk them while previewing each file/line. Works on any results
	view, not just ones OpenWalkerWindowCommand opened; "next"/"prev"
	index on demand, so no separate "init" binding is needed.
	"""

	def name(self):
		return "walker_walk"


	def is_enabled(self):
		"""Only available in Find Results panel."""        
		return self.view.name() == "Find Results"


	def run(self, edit, action):
		"""action: "next"/"prev" step and preview; "init" indexes and
		previews the first match, used internally to pre-warm a view."""
		deadline = time.time() + 1.0
		if action == "init":
			self._wait_to_init_walk(deadline)
		elif action == "next":
			self.step_to_match(forward=True)
		elif action == "prev":
			self.step_to_match(forward=False)

	def _wait_to_init_walk(self, deadline):
		"""Poll until the results view is loaded, then index its matches
		and preview the first one."""
		result_views = _get_result_views(self.view.window())
		if result_views and not result_views[0].is_loading():
			def func_init_and_preview():
				self.init_walk(result_views[0].id())
				self.step_to_match(forward=True)

			sublime.set_timeout(func_init_and_preview, 0)
			return

		if time.time() >= deadline:
			print("I can't see the loaded Find Results view")
			return

		sublime.set_timeout(lambda: self._wait_to_init_walk(deadline), 10)

	def init_walk(self, results_view_id):
		"""Index match regions into "walk_locations" and set up the
		two-column layout with results pinned to the left."""
		results_view = next(
			view
			for view in sublime.active_window().views()
			if view.id() == results_view_id
		)

		match_regs = results_view.get_regions("match")
		if not match_regs:
			print("No match regions found in Find Results")
			return

		target_file_locations = self.target_locations(match_regs, results_view)
		full_locations = self.get_full_locations(
			results_view, match_regs, target_file_locations
		)
		results_view.settings().set("walk_locations", full_locations)

		window = results_view.window()
		window.set_layout(
			{
				"cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
				"cols": [0.0, 0.5, 1.0],
				"rows": [0.0, 1.0],
			}
		)

		window.set_view_index(self.view, 0, -1)
		window.focus_view(results_view)

	def step_to_match(self, forward=True):
		"""Select and preview the next/previous match from here."""
		match_regs = self.view.get_regions("match")

		if not self.view.settings().get("walk_locations"):
			self.init_walk(results_view_id=self.view.id())
		locations = self.view.settings().get("walk_locations")
		try:
			if len(match_regs) != len(locations):
				self.init_walk(results_view_id=self.view.id())
		except TypeError as e:
			raise e

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
		"""Open target_file at (row, col) on the right"""
		target_view = sublime.active_window().open_file(
			fname=f"{target_file}:{row}:{col}",
			flags=\
			sublime.ENCODED_POSITION|\
			sublime.FORCE_GROUP,
			group=1,
		)
		sublime.active_window().set_view_index(target_view, 1, 0)

		deadline = time.time() + 1.0
		self._highlight_walked_region(target_view, length, deadline)

	def _highlight_walked_region(self, target_view, length, deadline):
		"""Once loaded, flag closable if needed and outline the match."""
		if not target_view.is_loading():
			mark_me = lambda: target_view.settings().set(
				"walked_closable",
				True,
			)
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
			target_view.window().focus_view(self.view)  # keep focus on results, not preview
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
		"""Convert reg_local's position to (line, column, length) in the
		target file: subtract the 6-char gutter per line (7 with the
		newline) that results_view prefixes but the target file lacks."""
		# "   12  some line" - 6-char line-number gutter, stripped to get the real column
		# 6 and 7: the two numbers this whole plugin quietly rests its weight on
		first_col_dirty = results_view.rowcol(reg_local.begin())[1]
		first_col = first_col_dirty - 6

		length = reg_local.size()
		reg_a, reg_b = reg_local.to_tuple()
		number_of_newlines = abs(
			self.view.rowcol(reg_a)[0] - self.view.rowcol(reg_b)[0]
		)
		# Each extra line in a multi-line match carries its own gutter + newline (7 chars)
		length = length - number_of_newlines * 7

		return [target_line, first_col, length]

	def target_locations(self, match_regs, results_view):
		"""{region_start: [line, column, length]} via row_col_length."""
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
		"""Prefix each location with its file name, by walking file
		headers and match regions together in document order."""
		match_files = results_view.find_by_selector(
			"entity.name.filename.find-in-files"
		)

		clues = sorted(match_files + match_regs)

		locations = dict()
		cur_file = match_files[0]  # overwritten immediately - clues start with a header
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

	def name(self):
		return "walker_close_files"


	def is_enabled(self):
		"""Only available in Find Results panel
		when walked views are still open."""
		is_find_results = self.view.name() == "Find Results"
		print("is_find_results->\n", is_find_results)
		is_alone_view = len(sublime.active_window().views()) == 1
		print("is_alone_view->\n", is_alone_view)
		enabled = is_find_results and not is_alone_view
		print("enabled->\n", enabled)
		return enabled

	def run(self, edit):
		for target_view in sublime.active_window().views():
			closable = target_view.settings().get("walked_closable")
			target_view.settings().erase("walked_closable")
			if closable:
				target_view.close()

		sublime.active_window().set_layout(
			{"cells": [[0, 0, 1, 1]], "cols": [0.0, 1.0], "rows": [0.0, 1.0]}
		)


class KeepOneWalkedFileCommand(sublime_plugin.TextCommand):
	"""Closes results and walked files except the focused one;
	collapses to a single column with that file kept open."""

	def name(self):
		return "walker_close_files_keep_one"


	def is_enabled(self):
		"""Only available in a walked view
		when other walked views are still open."""
		is_walked = self.view.settings().get("walked_closable")
		is_alone_view = len(sublime.active_window().views()) == 1
		return is_walked and not is_alone_view


	def run(self, edit):
		result_views = [
			v for v in sublime.active_window().views()
			if v.name() == "Find Results"
		]
		if result_views:
			result_views[0].close()
		else:
			print("No Find Results view among the window's views")


		for v in sublime.active_window().views():
			if v.settings().get("walked_closable") and v != self.view:
				v.close()

		sublime.active_window().set_view_index(self.view, 0, -1)
		sublime.active_window().set_layout( {
				"cells": [[0, 0, 1, 1]],
				"cols": [0.0, 1.0],
				"rows": [0.0, 1.0]
			} )
		sublime.active_window().focus_view(self.view)