#    nautilus-compare: An context menu extension for Nautilus file manager
#    Copyright (C) 2011  Guido Tabbernuk <boamaod@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import urllib
import gettext
import locale
import xdg.BaseDirectory
import ConfigParser

from gi.repository import Nautilus, GObject, Gio

APP = 'nautilus-compare'
SETTINGS_MAIN = 'Settings'
DIFF_PATH = 'diff_engine_path'
DIFF_PATH_3WAY = 'diff_engine_path_3way'
DIFF_PATH_MULTI = 'diff_engine_path_multi'
COMPARATORS = 'defined_comparators'
PREDEFINED_ENGINES = ['', 'diffuse', 'fldiff', 'kdiff3', 'kompare', 'meld', 'tkdiff']
DEFAULT_DIFF_ENGINE = "meld"
CONFIG_FILE = os.path.join(xdg.BaseDirectory.xdg_config_home, APP + ".conf")

class NautilusCompareExtension(GObject.GObject, Nautilus.MenuProvider):
	'''Class for Nautilus extension itself'''

	for_later = None
	diff_engine = DEFAULT_DIFF_ENGINE
	diff_engine_3way = DEFAULT_DIFF_ENGINE
	diff_engine_multi = ""

	def __init__(self):
		'''Load config'''

		self.config = ConfigParser.ConfigParser()
		sections = self.config.read(CONFIG_FILE)

		try:
			self.diff_engine = self.config.get(SETTINGS_MAIN, DIFF_PATH)
			self.diff_engine_3way = self.config.get(SETTINGS_MAIN, DIFF_PATH_3WAY)
			self.diff_engine_multi = self.config.get(SETTINGS_MAIN, DIFF_PATH_MULTI)
			self.engines = eval(self.config.get(SETTINGS_MAIN, COMPARATORS))
		except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
			try:
				self.config.add_section(SETTINGS_MAIN)
			except ConfigParser.DuplicateSectionError:
				pass
			self.config.set(SETTINGS_MAIN, DIFF_PATH, self.diff_engine)
			self.config.set(SETTINGS_MAIN, DIFF_PATH_3WAY, self.diff_engine_3way)
			self.config.set(SETTINGS_MAIN, DIFF_PATH_MULTI, self.diff_engine_multi)
			self.config.set(SETTINGS_MAIN, COMPARATORS, self.engines)
			with open(CONFIG_FILE, 'wb') as f:
				self.config.write(f)

	def _open_comparator(self, paths):
		if len(paths) == 1:
			self.for_later = paths[0]
			return

		args = ""
		for path in paths:
			args += "\"%s\" " % path

		cmd = None
		if len(paths) == 2:
			cmd = (self.diff_engine + " " + args + "&")
		elif len(paths) == 3 and len(self.diff_engine_3way.strip()) > 0:
			cmd = (self.diff_engine_3way + " " + args + "&")
		elif len(self.diff_engine_multi.strip()) > 0:
			cmd = (self.diff_engine_multi + " " + args + "&")

		if cmd is not None:
			os.system(cmd)
		
	def menu_activate_cb(self, menu, paths):
		self._open_comparator(paths)

	def valid_file(self, file):
		if file.get_uri_scheme() == 'file' and file.get_file_type() in (Gio.FileType.DIRECTORY, Gio.FileType.REGULAR, Gio.FileType.SYMBOLIC_LINK):
			return True
		else:
			return False

	def get_file_items(self, window, files):
		paths = []
		for file in files:
			if self.valid_file(file):
				path = urllib.unquote(file.get_uri()[7:])
				paths.append(path)

		# no files selected
		if len(paths) < 1:
			return

		# initialize i18n
		locale.setlocale(locale.LC_ALL, '')
		gettext.bindtextdomain(APP)
		gettext.textdomain(APP)
		_ = gettext.gettext

		item1 = None
		item2 = None
		item3 = None

		# for paths with remembered items
		new_paths = list(paths)

		# exactly one file selected
		if len(paths) == 1:

			# and one was already selected for later comparison
			if self.for_later is not None:

				# we don't want to compare file to itself
				if self.for_later not in paths:
					item1 = Nautilus.MenuItem(
						name="NautilusCompareExtension::CompareTo",
						label=_('Compare to ') + self.for_later,
						tip=_("Compare to the file remembered before")
					)

					# compare the one saved for later to the one selected now
					new_paths.insert(0, self.for_later)

			# if only one file selected, we offer to remember it for later anyway
			item3 = Nautilus.MenuItem(
				name="NautilusCompareExtension::CompareLater",
				label=_('Compare Later'),
				tip=_("Remember file for later comparison")
			)

		# can always compare, if more than one selected
		else:
			# if we have already remembered one file and add some more, we can do n-way compare
			if self.for_later is not None:
				if self.for_later not in paths:
					# if multi compare enabled and in case of 2 files selected 3way compare enabled
					if len(self.diff_engine_multi.strip()) > 0 or (len(paths) == 2 and len(self.diff_engine_3way.strip()) > 0):
						item1 = Nautilus.MenuItem(
							name="NautilusCompareExtension::MultiCompare",
							label=_('Compare to ') + self.for_later,
							tip=_("Compare selected files to the file remembered before")
						)
						# compare the one saved for later to the ones selected now
						new_paths.insert(0, self.for_later)

			# if multi compare enabled, we can compare any number
			# if there are two files selected we can always compare
			# if three files selected and 3-way compare is on, we can do it
			if len(self.diff_engine_multi.strip()) > 0 or len(paths) == 2 or (len(paths) == 3 and len(self.diff_engine_3way.strip()) > 0):
				item2 = Nautilus.MenuItem(
					name="NautilusCompareExtension::CompareWithin",
					label=_('Compare'),
					tip=_("Compare selected files")
				)

		if item1: item1.connect('activate', self.menu_activate_cb, new_paths)
		if item2: item2.connect('activate', self.menu_activate_cb, paths)
		if item3: item3.connect('activate', self.menu_activate_cb, paths)

		items = [item1, item2, item3]

		while None in items:
			items.remove(None)

		return items


