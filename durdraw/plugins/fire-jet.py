# Durdraw Plugin
# Type: Transform Movie
# Name: Fire

import math
import random
from copy import deepcopy
from durdraw.durdraw_movie import Frame

# Durdraw plugin format version
durdraw_plugin_version = 1

# Plugin information
durdraw_plugin = {
    "name": "Fire Jet",
    "author": "",
    "version": 1,
    "provides": ["transform_movie"],
    "type": ["effect"],
    "desc": "Renders demoscene-style tight fire along object contours over existing frames."
}

opts = {
    "intensity": 0.83,    # Heat emission probability
    "spot heat": 17.0,   # Base flame thermal intensity
    "height limit": 2,   # Max pixel reach from source character
    "cooling": 0.91,     # Damping factor per step (lower = tighter flame)
    "angle": 0,          # Direction in degrees (0 = Up/12 o'clock, 90 = Right/3 o'clock, etc.)
}

# Color palette (256-mode vs 16-mode)
_COLOURS_256 = [235, 52, 88, 124, 160, 196, 202, 208, 214, 220, 226]


def _step_fire_physics(buffer, orig_frame, mov_size_x, mov_size_y, intensity, spot_heat, cooling, height_limit, dx, dy):
    """Evolves sub-pixel heat buffer with directional convection and decay."""
    h_buf = len(buffer)
    w_buf = len(buffer[0])
    
    # 1. Reseed heat directly at source characters
    for y in range(mov_size_y):
        for x in range(mov_size_x):
            if orig_frame.content[y][x] != ' ':
                if random.random() < intensity:
                    # Sub-pixel variance around spot_heat
                    heat_val = spot_heat * random.uniform(0.85, 1.15)
                    buffer[y + 1][x + 1] = max(buffer[y + 1][x + 1], heat_val)

    # 2. Sub-pixel Convection & Cooling Diffusion
    new_buffer = [[0.0 for _ in range(w_buf)] for _ in range(h_buf)]
    
    for y in range(1, h_buf - 1):
        for x in range(1, w_buf - 1):
            # Sample source heat relative to direction vector (dx, dy)
            src_x = x - dx
            src_y = y - dy
            
            # Bilinear/neighbor sampling around the fractional source location
            x_low = max(0, min(w_buf - 1, int(math.floor(src_x))))
            x_high = max(0, min(w_buf - 1, int(math.ceil(src_x))))
            y_low = max(0, min(h_buf - 1, int(math.floor(src_y))))
            y_high = max(0, min(h_buf - 1, int(math.ceil(src_y))))
            
            b_self = buffer[y][x]
            b_flow = (buffer[y_low][x_low] + buffer[y_low][x_high] + 
                      buffer[y_high][x_low] + buffer[y_high][x_high]) / 4.0
            
            b_left = buffer[y][x - 1]
            b_right = buffer[y][x + 1]
            
            # Weighted thermal average biased along the direction vector
            thermal_avg = (b_self * 0.25) + (b_flow * 0.45) + (b_left * 0.15) + (b_right * 0.15)
            
            # Apply fractional cooling decay
            decayed = thermal_avg * cooling
            
            # Sub-pixel noise flicker
            if decayed > 0.5:
                decayed -= random.uniform(0.0, 0.4)
                
            new_buffer[y][x] = max(0.0, decayed)

    # Copy evolved state back
    for y in range(h_buf):
        for x in range(w_buf):
            buffer[y][x] = new_buffer[y][x]


def transform_movie(mov, appState=None, opts=opts):
    """Applies steady-state contour fire effect over existing frames in-place."""
    if not mov or not hasattr(mov, 'frames') or mov.frameCount == 0:
        return mov

    intensity = opts.get("intensity", 0.83)
    spot_heat = float(opts.get("spot heat", 17.0))
    height_limit = opts.get("height limit", 2)
    cooling = float(opts.get("cooling", 0.91))
    angle_deg = float(opts.get("angle", 0.0))

    colour_mode = appState.colorMode if appState else "16"
    colours = _COLOURS_256 if colour_mode == "256" else [0, 1, 9]

    # Convert angle (0 = UP) to screen space drift unit vectors (dx, dy)
    # Screen coordinates: +x is right, +y is down, so straight up is (0, -1)
    rad = math.radians(angle_deg)
    dx = math.sin(rad)
    dy = -math.cos(rad)

    # Floating point heat buffer (+2 padding for boundary protection)
    buf_w = mov.sizeX + 2
    buf_h = mov.sizeY + 2
    buffer = [[0.0 for _ in range(buf_w)] for _ in range(buf_h)]

    # --- PRE-WARM EQUILIBRIUM STEP ---
    # Run 15 physics steps on Frame 0 data without outputting frames
    first_frame = mov.frames[0]
    for _ in range(15):
        _step_fire_physics(
            buffer, first_frame, mov.sizeX, mov.sizeY,
            intensity, spot_heat, cooling, height_limit, dx, dy
        )

    # Process existing frames sequentially
    for frame_idx in range(mov.frameCount):
        orig_frame = deepcopy(mov.frames[frame_idx])
        rendered_frame = Frame(mov.sizeX, mov.sizeY)

        # Clear background canvas
        for y in range(mov.sizeY):
            for x in range(mov.sizeX):
                rendered_frame.content[y][x] = ' '
                rendered_frame.newColorMap[y][x] = [0, 0]

        # Step heat simulation for this frame
        _step_fire_physics(
            buffer, orig_frame, mov.sizeX, mov.sizeY,
            intensity, spot_heat, cooling, height_limit, dx, dy
        )

        # Map sub-pixel heat values to character canvas
        for y in range(mov.sizeY):
            for x in range(mov.sizeX):
                heat = buffer[y + 1][x + 1]
                if heat > 0.8:
                    # Normalize heat against palette
                    norm_heat = min(1.0, heat / spot_heat)
                    colour_idx = int(norm_heat * (len(colours) - 1))
                    
                    rendered_frame.content[y][x] = '█'
                    rendered_frame.newColorMap[y][x] = [colours[colour_idx], 0]

        # Save frame in place
        mov.frames[frame_idx] = rendered_frame

    return mov
