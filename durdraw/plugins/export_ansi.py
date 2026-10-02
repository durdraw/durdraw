import pathlib
import pdb
import struct

durdraw_plugin_version = 2

# Plugin information
durdraw_plugin = {
    "name": "ANSI (Utf-8 or CP437)",
    "author": "",
    "version":  1,   # Plugin verison, if applicable
    "provides": ["transform_movie", "export_movie"],
    "type": ["export"],
    "desc": "Exports frame with CP437 or Utf-8 encoding, and ANSI color escape codes"
}

opts  = {
    #"file name": ""
}

def transform_movie(dur, opts, mov):
    dur._ui.save(saveFormat="ansi")
    return mov
