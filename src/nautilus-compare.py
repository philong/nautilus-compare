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

from gi.repository import Nautilus, GObject, Gio

APP = 'nautilus-compare'

class NautilusCompareExtension(GObject.GObject, Nautilus.MenuProvider):

	for_later = None

	def __init__(self):
		pass

	def _open_comparator(self, paths):
		if len(paths) == 1:
			self.for_later = paths[0]
			return

		args = ""
		for path in paths:
			args += "\"%s\" " % path
		cmd = ("meld " + args + "&")
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
		gettext.bindtextdomain(APP)
		gettext.textdomain(APP)
		_ = gettext.gettext

		item1 = None
		item2 = None

		# exactly one file selected
		if len(paths) == 1:

			# and one was already selected for later comparison
			if self.for_later is not None:

				# we don't want to compare file to itself
				if paths[0] != self.for_later:
					item1 = Nautilus.MenuItem(
						name="NautilusCompareExtension::CompareTo",
						label=_('Compare to ') + self.for_later,
						tip=_("Compare to the file remembered before")
					)

					# compare the one saved for later to the one selected now
					paths.insert(0, self.for_later)

			# if only one file selected, we offer to remember it for later anyway
			item2 = Nautilus.MenuItem(
				name="NautilusCompareExtension::CompareLater",
				label=_('Compare later'),
				tip=_("Remember file for later comparison")
			)

		# can always compare, if more than one selected
		else:
			item1 = Nautilus.MenuItem(
				name="NautilusCompareExtension::CompareWithin",
				label=_('Compare'),
				tip=_("Compare selected files")
			)

		if item1: item1.connect('activate', self.menu_activate_cb, paths)
		if item2: item2.connect('activate', self.menu_activate_cb, [paths[-1]])

		items = [item1, item2]

		for item in items:
			if item is None: items.remove(item)

		return items

