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

import gtk
import os
import gettext
import locale
import xdg.BaseDirectory
import ConfigParser

APP = 'nautilus-compare'
SETTINGS_MAIN = 'Settings'
DIFF_PATH = 'diff_engine_path'
DIFF_PATH_3WAY = 'diff_engine_path_3way'
DIFF_PATH_MULTI = 'diff_engine_path_multi'
COMPARATORS = 'defined_comparators'
PREDEFINED_ENGINES = ['', 'diffuse', 'fldiff', 'kdiff3', 'kompare', 'meld', 'tkdiff']
DEFAULT_DIFF_ENGINE = "meld"
CONFIG_FILE = os.path.join(xdg.BaseDirectory.xdg_config_home, APP + ".conf")

# constants only in setup
COMPARATOR_PATH = '/usr/bin'
     
def combo_add_and_select(combo, text):
	'''Convenience function to add/selct item in ComboBoxEntry'''
	combo.append_text(text)
	model=combo.get_model()
	iter=model.get_iter_first()
	while model.iter_next(iter):
		iter=model.iter_next(iter)
	combo.set_active_iter(iter)

class NautilusCompareExtensionSetup:
	'''The main class for setup using PyGTK'''

	diff_engine = DEFAULT_DIFF_ENGINE
	diff_engine_3way = DEFAULT_DIFF_ENGINE
	diff_engine_multi = ""
	engines = PREDEFINED_ENGINES

	config = None

	combo = None
	combo_3way = None
	combo_multi = None

	def cancel_event(self,widget,event,data=None):
		'''This callback quits the program'''
		gtk.main_quit()
		return False

	def changed_cb(self, combo):
		'''Any of the comboboxes has changed, change the data accordingly'''
		model = combo.get_model()
		index = combo.get_active()
		entry = combo.get_child().get_text()
		if len(entry)>0:
			selection=entry
		elif index:
			selection=model[index][0]
		if combo is self.combo:
			self.diff_engine = selection
		elif combo is self.combo_3way:
			self.diff_engine_3way = selection
		elif combo is self.combo_multi:
			self.diff_engine_multi = selection
		return

	def save_event(self,widget,event,data=None):
		'''This callback saves the settings and quits the program.'''
		try:
			self.config.add_section(SETTINGS_MAIN)
		except ConfigParser.DuplicateSectionError:
			pass
		self.config.set(SETTINGS_MAIN, DIFF_PATH, self.diff_engine)
		self.config.set(SETTINGS_MAIN, DIFF_PATH_3WAY, self.diff_engine_3way)
		self.config.set(SETTINGS_MAIN, DIFF_PATH_MULTI, self.diff_engine_multi)

		if self.diff_engine not in self.engines:
			self.engines.append(self.diff_engine)
		if self.diff_engine_3way not in self.engines:
			self.engines.append(self.diff_engine_3way)
		if self.diff_engine_multi not in self.engines:
			self.engines.append(self.diff_engine_multi)

		self.config.set(SETTINGS_MAIN, COMPARATORS, self.engines)
		with open(CONFIG_FILE, 'wb') as f:
			self.config.write(f)

		gtk.main_quit()
		return False

	def __init__(self):
		'''Load config and create UI'''

		self.config = ConfigParser.ConfigParser()
		sections = self.config.read(CONFIG_FILE)
		system_utils = os.listdir(COMPARATOR_PATH)

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
			self.config.set(SETTINGS_MAIN, COMPARATORS, ['', self.diff_engine])
			with open(CONFIG_FILE, 'wb') as f:
				self.config.write(f)

		# add predefined engines which are installed for now
		for engine in PREDEFINED_ENGINES:
			if engine not in self.engines and engine in system_utils:
				self.engines.append(engine)

		self.engines.sort()

		# initialize i18n
		locale.setlocale(locale.LC_ALL, '')
		gettext.bindtextdomain(APP)
		gettext.textdomain(APP)
		_ = gettext.gettext

		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		#self.window.set_position(gtk.WIN_POS_CENTER)
		icon=self.window.render_icon(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_DIALOG)
		self.window.set_icon(icon)
		self.window.set_resizable(False)
		self.window.set_title(_("Nautilus-Compare Preferences"))
		self.window.connect("delete_event",self.cancel_event)
		self.window.set_border_width(15)

		main_vbox = gtk.VBox(False,0)
		self.window.add(main_vbox)

		frame = gtk.Frame(_("Normal Diff"))
		self.combo = gtk.combo_box_entry_new_text()
		for text in self.engines:
			if text == self.diff_engine:
				combo_add_and_select(self.combo, text)
			else:
				self.combo.append_text(text)
		self.combo.connect('changed', self.changed_cb)
		frame.add(self.combo)
		main_vbox.pack_start(frame, True,True, 0)

		frame_3way = gtk.Frame(_("Three-Way Diff"))
		self.combo_3way = gtk.combo_box_entry_new_text()
		for text in self.engines:
			if text == self.diff_engine_3way:
				combo_add_and_select(self.combo_3way, text)
			else:
				self.combo_3way.append_text(text)
		self.combo_3way.connect('changed', self.changed_cb)
		frame_3way.add(self.combo_3way)
		main_vbox.pack_start(frame_3way, True,True, 0)

		frame_multi = gtk.Frame(_("N-Way Diff"))
		self.combo_multi = gtk.combo_box_entry_new_text()
		for text in self.engines:
			if text == self.diff_engine_multi:
				combo_add_and_select(self.combo_multi, text)
			else:
				self.combo_multi.append_text(text)
		self.combo_multi.connect('changed', self.changed_cb)
		frame_multi.add(self.combo_multi)
		main_vbox.pack_start(frame_multi, True, True, 0)

		separator = gtk.HBox(False,5)
		main_vbox.pack_start(separator, False, True, 5)

		confirm_hbox = gtk.HBox(False,0)

		main_vbox.pack_start(confirm_hbox, False, False, 0)
		
		cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
		cancel_button.connect_object("clicked", self.cancel_event, self.window, None)  
		confirm_hbox.pack_start(cancel_button, True, True, 5)

		ok_button = gtk.Button(stock=gtk.STOCK_OK)
		ok_button.connect_object("clicked", self.save_event, self.window, None)  
		confirm_hbox.pack_start(ok_button, True, True, 5)

		self.window.show_all()

	def main(self):
		'''GTK main method'''
		gtk.main()

if __name__ == "__main__":
	program = NautilusCompareExtensionSetup()
	program.main()

