# Durdraw Plugin
# Type: Transform Movie
# Name: Repeat |> -> |>|>

# Durdraw plugin format version
durdraw_plugin_version = 1

# Plugin information
durdraw_plugin = {
    'name': 'Repeat',
    'author': 'Sam Foster, samfoster@gmail.com',
    'version': 1,   # Plugin version, if applicable
    'provides': ['transform_movie'],
    "type": ["effect"],
    'desc': 'Duplicate all frames and append them to the end. |> -> |>|>'
}

opts = {
    'count': 1,
}

def transform_movie(mov, appState=None, opts=opts):
    count = opts.get('count', 1) if opts else 1
    original_frame_count = mov.frameCount

    for _ in range(count):
        for i in range(1, original_frame_count + 1):
            mov.gotoFrame(i)
            mov.insertCloneFrame()
            mov.moveFramePosition(i + 1, mov.frameCount)

    mov.gotoFrame(1)
    return mov
