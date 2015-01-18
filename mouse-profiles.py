#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014
# Author: Vladislav Samsonov <vvladxx@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it 
# under the terms of either or both of the following licenses:
#
# 1) the GNU Lesser General Public License version 3, as published by the 
# Free Software Foundation; and/or
# 2) the GNU Lesser General Public License version 2.1, as published by 
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the applicable version of the GNU Lesser General Public 
# License for more details.
#
# You should have received a copy of both the GNU Lesser General Public 
# License version 3 and version 2.1 along with this program.  If not, see 
# <http://www.gnu.org/licenses/>
#

import json
from os import path
import os
from gi.repository import Gio as gio
from gi.repository import GLib as glib
from gi.repository import Wnck as wnck
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator

kConfigDirPath =  path.join(path.expanduser('~'), '.config/mouse-profiles')
kProfilesFilename = 'profiles.json'
kCheckIntervalSecs = 4
defaultScreen = wnck.Screen.get_default()
mouseSettings = gio.Settings('org.gnome.settings-daemon.peripherals.mouse')
mediaKeys = gio.Settings('org.gnome.settings-daemon.plugins.media-keys')
profiles = None
defaultProfile = 0
currentProfile = 0
menuItems = []
windowNameTriggers = {}

del wnck

def handle_eintr():
	import signal
	signal.signal(signal.SIGINT, signal.SIG_DFL)
	del signal

def read_config():
	try: os.makedirs(kConfigDirPath)
	except: pass
	configfile = path.join(kConfigDirPath, kProfilesFilename)
	return json.loads(open(configfile, 'r').read())

def reload_config(w):
	global profiles
	profiles = read_config()

def apply_profile(n):
	os.system(profiles[n]['additional-shell-command'])
	global currentProfile
	currentProfile = n
	mouseSettings.set_double('motion-acceleration', profiles[n]['motion-acceleration'])
	mouseSettings.set_int('motion-threshold', profiles[n]['motion-threshold'])
	custom_keybindings = []
	for i in xrange(len(profiles[n]['custom-keybindings'])):
		custom_keybindings.append('/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom%d/' % i)
	mediaKeys.set_strv('custom-keybindings', custom_keybindings)
	for i in xrange(len(profiles[n]['custom-keybindings'])):
		custom = gio.Settings.new_with_path('org.gnome.settings-daemon.plugins.media-keys.custom-keybinding', '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom%d/' % i)
		custom.set_string('binding', profiles[n]['custom-keybindings'][i]['binding'])
		custom.set_string('command', profiles[n]['custom-keybindings'][i]['command'])
		custom.set_string('name', profiles[n]['custom-keybindings'][i]['name'])

def menuitem_activate(w, num):
	if w.get_active():
		apply_profile(num)

revertProfile = None

def time_handler(): # will be called every kCheckIntervalSecs seconds
	name = defaultScreen.get_active_window().get_name()
	global revertProfile
	if name in windowNameTriggers:
		if revertProfile == None:
			revertProfile = currentProfile
		windowNameTriggers[name].set_active(True)
	elif revertProfile != None:
		menuItems[revertProfile].set_active(True)
		revertProfile = None
	return True

def time_handler_once(): # will be called once to setup things
	apply_profile(defaultProfile)
	menuItems[defaultProfile].set_active(True)
	return False

def main():
	ind = appindicator.Indicator.new('unity-mouse-profiles', 'gpm-mouse-100', appindicator.IndicatorCategory.APPLICATION_STATUS)
	ind.set_status(appindicator.IndicatorStatus.ACTIVE)
	menu = gtk.Menu()
	header = gtk.MenuItem('Профили')
	header.set_sensitive(False)
	menu.append(header)
	menu.append(gtk.SeparatorMenuItem())
	rgroup = []
	for i in range(len(profiles)):
		p = profiles[i]
		menu_item = gtk.RadioMenuItem.new_with_label(rgroup, p['name'])
		rgroup = menu_item.get_group()
		menu.append(menu_item)
		menu_item.connect('activate', menuitem_activate, i)
		if hasattr(p, 'default') and p['default'] == True:
			global defaultProfile
			defaultProfile = i
		try:
			windowNameTriggers[str(p['trigger']['window-name'])] = menu_item
		except KeyError: pass
		menuItems.append(menu_item)
	menu.append(gtk.SeparatorMenuItem())
	reloadconf = gtk.MenuItem('Обновить конфигурацию')
	reloadconf.connect('activate', reload_config)
	menu.append(reloadconf)
	menu.show_all()
	ind.set_menu(menu)
	glib.timeout_add_seconds(kCheckIntervalSecs, time_handler)
	glib.timeout_add(150, time_handler_once)
	gtk.main()

if __name__ == '__main__':
	handle_eintr()
	profiles = read_config()
	main()