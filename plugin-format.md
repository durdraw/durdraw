Durdraw Plugin Format Specification, Durdraw Extension API: draft 0.2

Durdraw 0.30.0 and higher allows users to add their own features and extensions through a Plugins API.

Users can create the following plug-in types:

Effects
Export
Menu Items

Durdraw plugins are Python scripts with the .py file extension.  They can be placed in ~/.durdraw/plugins/ and will be loaded when Durdraw starts.

The script contains some metadata to register itself. For example:

```python
# Durdraw plugin format version
durdraw_plugin_version = 2

# Plugin information
durdraw_plugin = {
    "name": "Random Colors",
    "author": "Author name, email@address.com",
    "version":  1,   # Version of the specific plugin
    "provides": ["transform_movie"],
    "type": ["effect"],
    "desc": "Fill canvas with random Colors."
}
```

To provide optional paramaters, include the "opts" {} dict. Durdraw will prompt the user to specify these options, or will use the defaults you provide. These options are then passed back into the plugin. For example:

```python
opts = {
    'min color': 1,
    'max color': 255,
}
```

Most plug-ins work by providing a function called transform_movie(), which returns a Movie object that becomes the new canvas, like so:

```python
def transform_movie(dur, opts, mov):
    ...
    return mov
```

transform_movie() is passed 3 objects:
    * dur - an object containing general Durdraw API methods
    * opts - The user-provided options to the plugin
    * mov - The canvas/movie obbject (a collection of frames)


```python
opts = {
    'min color': 1,
    'max color': 255,
}
```

The following methods are provided by Durdraw, and can be used in plugins:

dur.color_mode() - The current color mode, "16" or "256"
dur.suspend_curses() - suspend curses, so another TUI can be loaded
dur.resume_curses() - resume curses, so the plugin can return to Durdraw
dur.notify(message, pause=True) - Send a notification message to the user. pause optionally keeps the message up on the screen until the user presses a key.
dur.color_picker(message=None) - Opens the color picker for the user, returns an integer containing the selected color value. Optionally message contains a message to show the user while the color picker is open.
dur.playback_range() - Returns a tuple containing the playback range set in the UI.
dur.Frame() - returns a new empty Frame object.
dur.Movie() - returns a new empty Frame object.

mov.frames[] is a list of Frame objets, which make up the currently loaded movie.
mov.addFrame(frame) - Takes a Frame object and appends it to the end of the movie
mov.insertFrame(frame) - Takes a frame object and inserts it after the "current" frame (the frame in the user's canvas)
mov.addEmptyFrame() - Appends an empty frame to the movie
mov.insertCloneFrame() - Clones current frame and adds it after the current frame
mov.deleteCurrentFrame() - Deletes the current frame
mov.moveFramePosition(startPosition, newPosition) - Moves the frame at startPosition to newPosition
mov.gotoFrame(frameNumber) - frameNumber becomes the current frame
mov.nextFrame() - Go to the next frame (next frame becomes current frame), or wrap around to the first frame if current frame is the last frame in the movie
mov.prevFrame() - Go to the previous frame (previous frame becomes current frame), or wrap around to the last frame if current frame is the first frame
mov.growCanvasWidth(growthSize) - add growthSize number of columns to the canvas (affects all frames)
mov.shrinkCanvasWidth(shrinkSize) - Shrinks the canvas by removing rightmost shrinkSize number of columns
mov.hasMultipleFrames() returns True if the movie has multiple frames, or False if there is only one frame
appState.colorMode: "16" if in 16-color mode, "256" if in 256-color mode.
mov.sizeX - Width (columns) of movie/canvas
mov.sizeY - Height (lines) of movie/canvas

Frame.sizeX - Width (columns) of frame
Frame.sizeY - Height (lines) of frame
Frame.content - The unicode characters in the frame (without color data)
frame.content[line][col] - read or write to the character at index line and column
Frame.newColorMap - The color data in the frame (without character data)
Frame.newColorMap[line][col] - read or write to the color at index line and column
Frame.setDelayValue() - takes a float, and sets the timing delay for the specified frame.

Here is an example that places random letters and colors on all frames of the movie:


```python
# Durdraw Plugin
# Type: Transform Movie
# Name: Random Letters

import random
import string

# Durdraw plugin format version
durdraw_plugin_version = 2

# Plugin information
durdraw_plugin = {
    "name": "random letters and colors",
    "author": "Sam Foster, samfoster@gmail.com",
    "version":  1,   # Plugin verison, if applicable
    "provides": ["transform_movie"],
    "type": ["effect"],
    "desc": "Fill canvas with random letters and colors."
}

opts = {
    'min color': 1,
    'max color': 255
}

def transform_movie(dur, opts, mov):
    frame_num = 0
    for frame in mov.frames:
        mov.frames[frame_num] = randomizer(dur, frame)
        frame_num += 1
    return mov

def randomizer(dur, frame):
    # fill canvas with random letters.
    line_num = 0
    while line_num < frame.sizeY:
        col_num  = 0
        #for col in line:
        while col_num < frame.sizeX:
            frame.content[line_num][col_num] = random.choice(string.ascii_letters)
            col_num += 1
        line_num += 1

    # Fill canvas with random colors.
    if dur.color_mode() == "256":
        min_color = opts['min color']
        max_color = opts['max color']
        bg_color = 0
    else:
        min_color = 1
        max_color = 15
        bg_color = 0
    line_num = 0
    while line_num < frame.sizeY:
        col_num  = 0
        while col_num < frame.sizeX:
            # Fg colr
            frame.newColorMap[line_num][col_num][0] = random.randrange(min_color, max_color + 1)
            # Bg colr
            frame.newColorMap[line_num][col_num][1] = 0
            col_num += 1
        line_num += 1
    return frame
```

