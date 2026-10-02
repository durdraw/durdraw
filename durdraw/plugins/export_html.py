import pathlib
import pdb
import struct

durdraw_plugin_version = 2

# Plugin information
durdraw_plugin = {
    "name": "HTML",
    "author": "",
    "version":  1,   # Plugin verison, if applicable
    "provides": ["transform_movie", "export_movie"],
    "type": ["export"],
    "desc": "Exports frame to HTML"
}

opts  = {
    #"file name": ""
}

def transform_movie(dur, opts, mov):
    dur._ui.save(saveFormat="html")
    return mov
