#!/usr/bin/env python3

import curses, os, subprocess

# Durdraw plugin format version
durdraw_plugin_version = 1

# Plugin information
durdraw_plugin = {
    "name": "Jump to Shell",    # Item as it apperas in the menu
    "author": "",
    "version": 1,
    "provides": ["transform_movie"],
    "desc": "Jump out to the shell, similar to Jump to DOS in TheDraw",
    # Menu stuff
    "type": "menu_item",
    "shortcut": "j",       # Keyboard shurtcut when menu is open   
    "location": "Menu"     # Menu for submenu to go in
}

# Plugin options
opts = {
    #'shell': 'bash',
    # 'filename': '',
}

def transform_movie(mov, appState=None, opts=opts):
    curses.def_prog_mode()     # save current tty modes
    curses.endwin()
    #shell = opts['shell']
    shell = os.getenv("SHELL")
    print("Type 'exit' to reutrn to durdraw.")
    subprocess.run(shell)
    input('Press enter to return to Durdraw...')
    #curses.refresh()
    return mov

