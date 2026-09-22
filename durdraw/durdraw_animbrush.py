import durdraw.durdraw_movie as durmovie

import pdb

class AnimationBrush:
    def __init__(self):
        self.mov = None
        self.frameNumber = 0
        self.mode = "loop"  # "loop" or "clone"

    def set_mov(self, mov):
        self.mov = mov
        self.frameNumber = 0

    def current_frame(self):
        try:
            frame = self.mov.frames[self.frameNumber]
        except IndexError as E:
            print(f"Exception: {E}")
            pdb.set_trace()
        return frame

    def next_frame(self):
        self.frameNumber += 1
        if self.frameNumber > len(self.mov.frames) - 1:
            self.frameNumber = 0

    def prev_frame(self):
        self.frameNumber = self.frameNumber - 1
        if self.frameNumber < 0:
            self.frameNumber = len(self.mov.frames) - 1

    def set_mode(self, mode): 
        self.mode = mode

    def is_set(self):
        if isinstance(self.mov, durmovie.Movie):
            return True
        else:
            return False
