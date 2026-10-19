# Durdraw Plugin
# Type: Transform Movie
# Name: Plasma Overlay

import math

# Durdraw plugin format version
durdraw_plugin_version = 1

# Plugin information
durdraw_plugin = {
    "name": "Plasma Overlay",
    "author": "",
    "version": 1,
    "provides": ["transform_movie"],
    "type": ["effect"],
    "desc": "Overlays a swirling plasma color effect on existing frames."
}

opts = {
    'min color': 1,
    'max color': 255,
}


def transform_movie(mov, appState=None, opts=opts):
    """Applies a plasma color effect to existing frames, preserving original characters."""
    # Use existing frame count
    steps = mov.frameCount
    
    # Color setup
    color_mode = appState.colorMode if appState else "16"
    
    min_color = opts.get('min color', 1)
    max_color_setting = opts.get('max color', 255)
    max_color = max_color_setting if color_mode == "256" else min(max_color_setting, 15)
    
    # Swap if bounds were supplied in reverse
    if min_color > max_color:
        min_color, max_color = max_color, min_color

    color_range = max_color - min_color
    
    for step in range(steps):
        frame = mov.frames[step]  # Work with existing frame
        time = step / steps * 2 * math.pi  # Phase over movie length
        
        for y in range(mov.sizeY):
            for x in range(mov.sizeX):
                # Plasma effect: combine sine waves (-1.0 to 1.0)
                value = (
                    math.sin(x * 0.1 + time) +              # Horizontal wave
                    math.sin(y * 0.1 + time * 1.5) +       # Vertical wave
                    math.sin((x + y) * 0.05 + time * 0.5)  # Diagonal wave
                ) / 3.0  # Average for smooth gradient
                
                # Correct linear mapping into [min_color, max_color]
                fg_color = int(min_color + (value + 1.0) * color_range / 2.0)
                fg_color = max(min_color, min(max_color, fg_color))  # Clamp range
                
                # Only update foreground color, keep original character and background color
                frame.newColorMap[y][x] = [fg_color, frame.newColorMap[y][x][1]]
    
    return mov

from durdraw.durdraw_movie import Frame  # Adjust import path as needed