# Durdraw Plugin
# Type: Transform Movie
# Name: Fire

import random
from copy import deepcopy

# Durdraw plugin format version
durdraw_plugin_version = 2

# Plugin information
durdraw_plugin = {
    "name": "Fire",
    "author": "",
    "version": 2,
    "provides": ["transform_movie"],
    "type": ["effect"],
    "desc": "Renders steady fire effects over non-space chars across existing frames."
}

opts = {
    "intensity": 0.6,  # Heat re-seeding probability
    "spot heat": 16,   # Thermal heat intensity for flame height
}

# Color palette (256-mode, reds to yellow)
_COLOURS_256 = [235, 52, 88, 124, 160, 196, 202, 208, 214, 220, 226]


def transform_movie(dur, opts, mov):
    """Renders steady fire effects under/around non-space chars on existing movie frames."""
    if not mov or not hasattr(mov, 'frames') or len(mov.frames) == 0:
        return mov

    # Options & settings
    intensity = opts.get("intensity", 0.6)
    spot_heat = opts.get("spot heat", 16)

    # Use Durdraw API method for color mode
    color_mode = dur.color_mode()
    colours = _COLOURS_256 if color_mode == "256" else [0, 1, 9]

    # Dimensions using Movie API methods
    width = mov.width
    height = mov.height

    # Persistent Heat Buffer initialized once across the entire movie sequence
    buffer = [[0 for _ in range(width)] for _ in range(height + 2)]

    # Initial heat seeding based on Frame 1 source content
    first_frame = mov.frames[0]
    for y in range(height):
        for x in range(width):
            if first_frame.content[y][x] != ' ':
                if y < height - 1:
                    buffer[y + 1][x] = spot_heat
                if x > 0:
                    buffer[y][x - 1] = spot_heat // 2
                if x < width - 1:
                    buffer[y][x + 1] = spot_heat // 2

    # Process each existing frame sequentially
    for frame_idx in range(len(mov.frames)):
        orig_frame = deepcopy(mov.frames[frame_idx])
        frame = mov.frames[frame_idx]

        # 1. Clear current frame content using Frame properties/methods
        for y in range(frame.height()):
            for x in range(frame.width()):
                frame.content[y][x] = ' '
                frame.colorMap[y][x] = [0, 0]

        # 2. Reseed heat steadily from current frame non-space content
        for y in range(height):
            for x in range(width):
                if orig_frame.content[y][x] != ' ' and random.random() < intensity:
                    if y < height - 1:
                        buffer[y + 1][x] = random.randint(spot_heat // 2, spot_heat)
                    if x > 0:
                        buffer[y][x - 1] = random.randint(0, spot_heat // 2)
                    if x < width - 1:
                        buffer[y][x + 1] = random.randint(0, spot_heat // 2)

        # 3. Cooling step (heat dissipation & averaging)
        for y in range(height):
            new_row = buffer[y].copy()
            for x in range(width):
                new_val = buffer[y][x]
                count = 1
                if y < height - 1:
                    new_val += buffer[y + 1][x]
                    count += 1
                if x > 0:
                    new_val += buffer[y][x - 1]
                    count += 1
                if x < width - 1:
                    new_val += buffer[y][x + 1]
                    count += 1
                new_row[x] = max(0, new_val // count)
            buffer[y] = new_row

        # 4. Render flames onto current frame
        max_heat = max(max(row) for row in buffer) or 1
        for y in range(height):
            for x in range(width):
                heat = buffer[y][x]
                if heat > 0:
                    colour_idx = min(len(colours) - 1, (heat * len(colours)) // max_heat)
                    frame.content[y][x] = '█'
                    frame.colorMap[y][x] = [colours[colour_idx], 0]

    return mov
