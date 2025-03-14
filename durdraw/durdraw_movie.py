from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
import json
import pdb
import re
from typing import List, Tuple, NamedTuple, Iterable
import line_profiler

import durdraw.log as log
from durdraw.durdraw_undo import UndoRegister

def init_list_colorMap(width, height):
    """ Builds a color map consisting of a list of lists """
    #return [[list([1,0]) * width] * height]
    colorMap = []
    dummyColor = [8, 0]
    for h in range(0, height):
        colorMap.append([])
        for w in range(0, width):
            colorMap[h].append(dummyColor)
    return colorMap

def convert_dict_colorMap(oldMap, width, height):
    """ Converts the old {[x,y] = (1,0)} color map
    into new format: [x, y] = [1, 0] """
    newMap = init_list_colorMap(width, height)
    for x in range(0, height):
        for y in range(0, width):
            newMap[x][y] = list(oldMap[(x, y)])   # wtf was I thinking
    #print(f"New color map: {newMap}")   # DEBUG
    return newMap

def convert_movie_16_to_256_color_palette(mov):
    """ Takes movie with old 16 color palette, converts it to look
    correct with 256 color palette. Returns converted movie? """
    fixer = {   # conversion table for the palettes
            # old and bad:
            # dim: 1 = white, 2 = cyan, 3 = purple, 4 = blue, 5 = brown, 6 = green, 7 = red, 8 = black
            # bright: 9 = white, 10 = cyan, 11 = purple, 12 = blue, 13 = brown, 14 = green, 15 = red, 16 = bright grey 
            # new and good:
            # 
            9: 15,  # bright white
            10: 14, # bright cyan
            11: 13, # bright purple
            12: 12, # bright blue, 
            13: 11, # bright yellow
            14: 10, # bright green
            15: 9, # bright red
            16: 242 # bright gray
        }
    for frame in mov.frames:
        # apply the fixer{} mapping to the frame's color map
        # looks something like: frame.colorMap[posY, posX]
        # returns a tuple, not a list. yeegh
        pass
        #for line in frame:

class Frame():
    """Frame class - single canvas size frame of animation. a traditional drawing.
    """

    @line_profiler.profile
    def __init__(self, width, height):
        """ Initialize frame, content[x][y] grid """
        # it's a bunch of rows of ' 'characters.
        self.content = []
        self.colorMap = {}
        self.newColorMap = init_list_colorMap(width, height)   # [[1,0], [3, 1], ...]
        self.sizeX = width
        self.width = width
        self.sizeY = height
        self.height = height
        self.delay = 0  # delay == # of sec to wait at this frame.

        # Generate character arrays for frame contents, fill it
        # with ' ' (space) characters
        for x in range(0, height):
            self.content.append([])
            for y in range(0, width):
                self.content[x].append(' ')

        self.initOldColorMap()
        #self.initColorMap()
        #self.newColorMap = convert_dict_colorMap(self.colorMap, width, height)
        self.setDelayValue(0)

        self.log = log.getLogger('frame')
        self.log.info('frame initialized', {'width': width, 'height': height})

    def setDelayValue(self, delayValue):
        self.delay = delayValue

    @line_profiler.profile
    def initOldColorMap(self):
        """ Builds a dictionary mapping X/Y to a FG/BG color pair """
        self.colorMap = {}
        for x in range(0, self.sizeY):
            for y in range(0, self.sizeX):
                self.colorMap.update( {(x,y):(1,0)} )  # tuple keypair (xy), tuple value (fg and bg)

    @line_profiler.profile
    def initColorMap(self, fg=7, bg=0):
        """ Builds a list of lists """
        return [[[fg,0] * self.sizeY] * self.sizeX]

class PixelCoord(NamedTuple):
    x: int
    y: int

class MouseCoord(NamedTuple):
    pixel: PixelCoord
    frame: int

class MovieState(NamedTuple):
    sizeX: int
    sizeY: int

class FrameContent(NamedTuple):
    content:   List[str]
    fg_colors: List[int]
    bg_colors: List[int]

class FrameState(NamedTuple):
    delay:      int
    frame_n:    int
    rows:       Tuple[Tuple[FrameContent]]
    start:      PixelCoord
    end:        PixelCoord

class FileState(NamedTuple):
    mouse:  MouseCoord = None
    movie:  MovieState = None
    frames: Tuple[FrameState] = tuple()

class UndoStates(NamedTuple):
    previous: FileState
    current:  FileState

@dataclass
class FrameSegment:
    content:     list
    fg_colors:   list
    bg_colors:   list
    frame_start: PixelCoord
    frame_end:   PixelCoord
    width:       int = field(init=False)
    height:      int = field(init=False)

    def __post_init__(self):
        self.log = log.getLogger('frame_segment')
        self.width = self.frame_end.x - self.frame_start.x + 1
        self.height = self.frame_end.y - self.frame_start.y + 1

    @staticmethod
    @line_profiler.profile
    def from_frame(frame: Frame, start_x: int, start_y: int, end_x: int, end_y: int) -> FrameSegment:
        'Extract a segment from the frame'
        start = PixelCoord(x=start_x, y=start_y)
        end = PixelCoord(x=end_x, y=end_y)
        color_map = [row[start.x:end.x+1] for row in frame.newColorMap[start.y:end.y+1]]
        return FrameSegment(
            content     = [row[start.x:end.x+1] for row in frame.content[start.y:end.y+1]],
            fg_colors   = [[el[0] for el in row] for row in color_map],
            bg_colors   = [[el[1] for el in row] for row in color_map],
            frame_start = start,
            frame_end   = end,
        )

    @line_profiler.profile
    def _pixel_coords(self) -> Iterable[PixelCoord]:
        for y in range(self.start.y, self.end.y+1):
            for x in range(self.start.x, self.end.x+1):
                yield PixelCoord(x, y)

    @staticmethod
    @line_profiler.profile
    def flip_matrix(matrix, width, height, horizontal=False, vertical=False):
        xrange, yrange, new_matrix = range(width), range(height), []

        for y, rev_y in zip(yrange, reversed(yrange)):
            new_matrix.append([])
            for x, rev_x in zip(xrange, reversed(xrange)):
                new_matrix[y].append(matrix[rev_y if vertical else y][rev_x if horizontal else x])
        return new_matrix

    @line_profiler.profile
    def flip(self, horizontal=False, vertical=False) -> FrameSegment:
        'Flip the contents horizontally and/or vertically'
        self.content = FrameSegment.flip_matrix(
            self.content,
            self.width, self.height,
            horizontal, vertical
        )
        self.fg_colors = FrameSegment.flip_matrix(
            self.fg_colors,
            self.width, self.height,
            horizontal, vertical
        )
        self.bg_colors = FrameSegment.flip_matrix(
            self.bg_colors,
            self.width, self.height,
            horizontal, vertical
        )

    @line_profiler.profile
    def delete(self):
        self.fill(char=' ', fg=self.appState.defaultFgColor, bg=self.appState.defaultBgColor)

    @line_profiler.profile
    def fill(self, char: str, fg: int = None, bg: int = None) -> FrameSegment:
        'Fill the contents with a character and color'
        self.fillChar(char)
        self.fillColor(fg, bg)

    @line_profiler.profile
    def fillColor(self, fg: int = None, bg: int = None) -> FrameSegment:
        'Fill the contents with a color'
        if fg is not None:
            self.fg_colors = [[fg] * self.width] * self.height
        if bg is not None:
            self.bg_colors = [[bg] * self.width] * self.height

    @line_profiler.profile
    def fillChar(self, char: str) -> FrameSegment:
        'Fill the contents with a character'
        self.content = [[char] * self.width] * self.height

class Movie():
    """ Contains an array of Frames, options to add, remove, copy them """
    @line_profiler.profile
    def __init__(self, opts):
        self.frameCount = 0  # total number of frames
        self.currentFrameNumber = 0
        self.sizeX = opts.sizeX     # Number of columns
        self.sizeY = opts.sizeY     # Number of lines
        self.opts = opts
        self.frames = []
        self.layers = {}    # Key can be a layer #, or something special. eg: "masks
        self.addEmptyFrame()
        self.currentFrameNumber = self.frameCount
        self.currentFrame = self.frames[self.currentFrameNumber - 1]

        self.undo_register = UndoRegister()

        self.log = log.getLogger('movie')
        self.log.info('movie initialized', {'sizeX': self.sizeX, 'sizeY': self.sizeY})

    @line_profiler.profile
    def applyFrameState(self, state: FrameState, width: int, height: int):
        # TODO: Optimize this - store the chars/fg/bg in a more convenient format
        for i, row in enumerate(state.rows):
            # update the frame chars
            self.frames[state.frame_n].content[i+state.start.y][state.start.x:state.end.x] = row.content
            # update the frame colors
            self.frames[state.frame_n].newColorMap[i+state.start.y][state.start.x:state.end.x] = list(zip(row.fg_colors, row.bg_colors))
            # remove any extra columns caused by adding a canvas column
            while len(self.frames[state.frame_n].content[i+state.start.y]) > width:
                self.frames[state.frame_n].content[i+state.start.y].pop()
                self.frames[state.frame_n].newColorMap[i+state.start.y].pop()

        # remove any extra rows caused by adding a canvas row
        while len(self.frames[state.frame_n].content) > height:
            self.frames[state.frame_n].content.pop()
        if state.delay:
            self.frames[state.frame_n].delay = state.delay

    @line_profiler.profile
    def applyStates(self, state: FileState):
        for frame_state in state.frames:
            self.applyFrameState(frame_state, width=state.movie.sizeX, height=state.movie.sizeY)

        self.sizeX = state.movie.sizeX
        self.sizeY = state.movie.sizeY

    @line_profiler.profile
    def setChar(self, frame_n, x, y, c, color):
        # self.log.debug('setChar', {'frame': frame_n, 'x': x, 'y': y, 'c': c, 'color': color})
        self.frames[frame_n].content[y][x] = c
        self.frames[frame_n].newColorMap[y][x] = list(color)

    def _segment_row_state(self, segment, y):
        return FrameContent(
            content   = segment.content[y],
            fg_colors = segment.fg_colors[y],
            bg_colors = segment.bg_colors[y],
        )

    def _frame_row_state(self, frame, y, start_x, end_x):
        return FrameContent(
            frame.content[y][start_x:end_x],
            # separate the colors into fg and bg
            *zip(*frame.newColorMap[y][start_x:end_x]),
        )

    @line_profiler.profile
    def _frame_states(self, start_x, start_y, end_x, end_y, frame_numbers, delay=None) -> [tuple, tuple]:
        'Returns old pixel states and new pixel states, both as tuples of PixelState'
        self.log.debug('getting frame states', {'start_x': start_x, 'start_y': start_y, 'frame_numbers': frame_numbers})
        for frame_n in range(frame_numbers[0], frame_numbers[1]+1):
            rows = (self._frame_row_state(self.frames[frame_n], y, start_x, end_x) for y in range(start_y, end_y+1))
            yield FrameState(
                delay   = self.frames[frame_n].delay,
                rows    = tuple(rows),
                frame_n = frame_n,
                start   = PixelCoord(x=start_x, y=start_y),
                end     = PixelCoord(x=end_x, y=end_y),
            )

    @line_profiler.profile
    def _segment_frame_states(self, start_x, start_y, segment, frame_numbers, delay=None) -> [tuple, tuple]:
        'Returns old pixel states and new pixel states, both as tuples of PixelState'
        self.log.debug('getting frame states', {'start_x': start_x, 'start_y': start_y, 'frame_numbers': frame_numbers})
        for frame_n in range(frame_numbers[0], frame_numbers[1]+1):
            yield FrameState(
                delay   = delay if delay else self.frames[frame_n].delay,
                rows    = tuple(self._segment_row_state(segment, y) for y in range(segment.height)),
                frame_n = frame_n,
                start   = PixelCoord(x=start_x, y=start_y),
                end     = PixelCoord(x=start_x + segment.width, y=start_y + segment.height),
            )

    @line_profiler.profile
    def new_states(self, start_x, start_y, segment, frame_numbers, delay=None) -> [Iterable[FrameState], Iterable[FrameState]]:
        return list(self._segment_frame_states(start_x, start_y, segment, frame_numbers, delay))

    @line_profiler.profile
    def current_states(self, start_x, start_y, end_x, end_y, frame_numbers) -> [Iterable[FrameState], Iterable[FrameState]]:
        return list(self._frame_states(start_x, start_y, end_x, end_y, frame_numbers))

    @line_profiler.profile
    def frame_states(self, start_x, start_y, segment, frame_numbers, delay=None) -> [Iterable[FrameState], Iterable[FrameState]]:
        return (
            self.current_states(start_x, start_y, start_x + segment.width, start_y + segment.height, frame_numbers),
            self.new_states(start_x, start_y, segment, frame_numbers, delay),
        )

    @line_profiler.profile
    def addFrame(self, frame):
        """ takes a Frame object, adds it into the movie """
        self.frames.append(frame)
        self.frameCount += 1
        return True

    def addEmptyFrame(self):
        newFrame = Frame(self.sizeX, self.sizeY)
        self.frames.append(newFrame)
        self.frameCount += 1
        return True

    def insertCloneFrame(self):
        """ clone current frame after current frame """
        newFrame = Frame(self.sizeX, self.sizeY)
        self.frames.insert(self.currentFrameNumber, newFrame)
        newFrame.content = deepcopy(self.currentFrame.content)
        newFrame.colorMap = deepcopy(self.currentFrame.colorMap)
        newFrame.newColorMap = deepcopy(self.currentFrame.newColorMap)
        self.frameCount += 1
        return True

    def deleteCurrentFrame(self):
        if (self.frameCount == 1):
            del self.frames[self.currentFrameNumber - 1]
            # deleted the last frame, so make a blank one
            newFrame = Frame(self.sizeX, self.sizeY)
            self.frames.append(newFrame)
            self.currentFrame = self.frames[self.currentFrameNumber - 1]
        else:
            del self.frames[self.currentFrameNumber - 1]
            self.frameCount -= 1
            if (self.currentFrameNumber != 1):
                self.currentFrameNumber -= 1
            self.currentFrame = self.frames[self.currentFrameNumber - 1]
        return True

    def moveFramePosition(self, startPosition, newPosition):
        """ move the frame at startPosition to newPosition """
        # use push and pop to remove and insert it
        fromIndex = startPosition - 1
        toIndex = newPosition - 1
        self.frames.insert(toIndex, self.frames.pop(fromIndex))

    def gotoFrame(self, frameNumber):
        if frameNumber > 0 and frameNumber < self.frameCount + 1:
            self.currentFrameNumber = frameNumber
            self.currentFrame = self.frames[self.currentFrameNumber - 1]
            return True # succeeded
        else:
            return False # failed - invalid input

    def nextFrame(self):
        if (self.currentFrameNumber == self.frameCount):    # if at last frame..
            self.currentFrameNumber = 1     # cycle back to the beginning
            self.currentFrame = self.frames[self.currentFrameNumber - 1] # -1 bcuz frame 1 = self.frames[0]
        else:
            self.currentFrameNumber += 1
            self.currentFrame = self.frames[self.currentFrameNumber - 1]

    def prevFrame(self):
        if (self.currentFrameNumber == 1):
            self.currentFrameNumber = self.frameCount
            self.currentFrame = self.frames[self.currentFrameNumber - 1]
        else:
            self.currentFrameNumber -= 1
            self.currentFrame = self.frames[self.currentFrameNumber - 1]

    def hasMultipleFrames(self):
        if len(self.frames) > 1:
            return True
        else:
            return False

    def growCanvasWidth(self, growth):
        self.sizeX += growth
        self.opts.sizeX += growth
        #self.width += growth

    def shrinkCanvasWidth(self, shrinkage):
        self.sizeY = self.sizeY - shrinkage
        self.opts.sizeY = self.opts.sizeY - shrinkage
        #self.width = self.width - shrinkage

    @line_profiler.profile
    def search_and_replace_color_pair(self, old_color, new_color, frange=None):
        if frange != None:  # apply to all frames in range
            for frameNum in range(frange[0] - 1, frange[1]):
            #for frame in self.frames:
                frame = self.frames[frameNum]
                line_num = 0
                col_num = 0
                for line in frame.newColorMap:
                    for pair in line:
                        if pair == old_color:
                            try:
                                frame.newColorMap[line_num][col_num] = new_color
                            except:
                                pdb.set_trace()
                            #found = True
                        col_num += 1
                    line_num += 1
                    col_num = 0
        else:   # only apply to current frame
            frame = self.currentFrame
            line_num = 0
            col_num = 0
            for line in frame.newColorMap:
                for pair in line:
                    if pair == old_color:
                        try:
                            frame.newColorMap[line_num][col_num] = new_color
                        except:
                            pdb.set_trace()
                        #found = True
                    col_num += 1
                line_num += 1
                col_num = 0


    @line_profiler.profile
    def search_and_replace_color(self, old_color :int, new_color :int):
        found = False
        for frame in self.frames:
            line_num = 0
            for line in frame.newColorMap:
                for pair in line:
                    if pair[0] == old_color:
                        frame.newColorMap[line_num][0] = new_color
                        found = True
                    if pair[1] == old_color:
                        frame.newColorMap[line_num][1] = new_color
                        found = True
                line_num += 1

    def search_and_replace(self, caller, search_str: str, replace_str: str):
        #search_list = list(search)
        found = False

        frame_num = 0
        line_num = 0
        for frame in self.frames:
            line_num = 0
            for line in frame.content:
                line_str = ''.join(line)
                if search_str in line_str:
                    # do regexp way, to keep justification
                    match = re.search(f"{search_str}\\s*", line_str)
                    if match:
                        # Calculate the exact width to replace
                        width = match.end() - match.start()
                        # Trim or pad replace_str to fit in the calculated width
                        replace_with = replace_str[:width].ljust(width)
                        # Substitute in the line
                        line_str = line_str[:match.start()] + replace_with + line_str[match.end():]

                    else:
                        # if that fails, do old way
                        if len(search_str) < len(replace_str):
                            #line_str = line_str.replace(search_str.ljust(len(replace_str)), replace_str)
                            line_str = line_str.replace(search_str, replace_str)
                        else:
                            line_str = line_str.replace(search_str, replace_str.ljust(len(search_str)))
                    # inject modified line back into frame
                    line = list(line_str)
                    frame.content[line_num] = line
                    found = True
                line_num += 1
            frame_num += 1
        return found


    @line_profiler.profile
    def search_for_string(self, search_str: str, caller=None):
        #search_list = list(search)
        found = False
        frame_num = 0
        line_num = 0
        for frame in self.frames:
            line_num = 0
            for line in frame.content:
                line_str = ''.join(line)
                if search_str in line_str:
                    column_num = line_str.index(search_str) + 1
                    frame_num += 1
                    found = True
                    return {"line": line_num, "col": column_num, "frame": frame_num}
                line_num += 1
            frame_num += 1
        return found    # should be false if execution reaches this point


    @line_profiler.profile
    def change_palette_16_to_256(self):
        # Convert from blue to bright white by reducing their value by 1
        for frame in self.frames:
            line_num = 0
            col_num = 0
            for line in frame.newColorMap:
                for pair in line:
                    if pair[0] == 1:    # black
                        pair[0] = 16
                    elif pair[0] == 16:    # bright white
                        pair[0] = 15
                    elif pair[0] == 15:    # bright yellow
                        pair[0] = 14
                    elif pair[0] == 14:    # bright purple
                        pair[0] = 13
                    elif pair[0] == 13:    # bright red
                        pair[0] = 12
                    elif pair[0] == 12:    # bright cyan
                        pair[0] = 11
                    elif pair[0] == 11:    # bright green
                        pair[0] = 10
                    elif pair[0] == 10:    # bright blue
                        pair[0] = 9
                    elif pair[0] == 9:    # bright black
                        pair[0] = 8
                    elif pair[0] == 8:    # grey
                        pair[0] = 7
                    elif pair[0] == 7:    # brown
                        pair[0] = 6
                    elif pair[0] == 6:    # purple
                        pair[0] = 5
                    elif pair[0] == 5:    # red
                        pair[0] = 4
                    elif pair[0] == 4:    # cyan
                        pair[0] = 3
                    elif pair[0] == 3:    # green
                        pair[0] = 2
                    elif pair[0] == 2:    # blue
                        pair[0] = 1
                    col_num += 1

    @line_profiler.profile
    def change_palette_256_to_16(self):
        # Convert from blue to bright white by reducing their value by 1
        for frame in self.frames:
            line_num = 0
            col_num = 0
            for line in frame.newColorMap:
                for pair in line:
                    if pair[0] == 16:    # black
                        pair[0] = 1
                    elif pair[0] == 15:    # bright white
                        pair[0] = 16
                    elif pair[0] == 14:    # bright yellow
                        pair[0] = 15
                    elif pair[0] == 13:    # bright purple
                        pair[0] = 14
                    elif pair[0] == 12:    # bright red
                        pair[0] = 13
                    elif pair[0] == 11:    # bright cyan
                        pair[0] = 12
                    elif pair[0] == 10:    # bright green
                        pair[0] = 11
                    elif pair[0] == 9:    # bright blue
                        pair[0] = 10
                    elif pair[0] == 8:    # bright black
                        pair[0] = 9
                    elif pair[0] == 7:    # grey
                        pair[0] = 8
                    elif pair[0] == 6:    # brown
                        pair[0] = 7
                    elif pair[0] == 5:    # purple
                        pair[0] = 6
                    elif pair[0] == 4:    # red
                        pair[0] = 5
                    elif pair[0] == 3:    # cyan
                        pair[0] = 4
                    elif pair[0] == 2:    # green
                        pair[0] = 3
                    elif pair[0] == 1:    # blue
                        pair[0] = 2
                    col_num += 1


    @line_profiler.profile
    def contains_high_colors(self):
        """ Returns True if any color above 16 is used, False otherwise """
        for frame in self.frames:
            for line in frame.newColorMap:
                for pair in line:
                    if pair[0] > 16:
                        return True
        return False

    @line_profiler.profile
    def contains_background_colors(self):
        """ Return true if any background color is set other than black or default """
        for frame in self.frames:
            for line in frame.newColorMap:
                for pair in line:
                    if pair[1] > 0:
                        return True
        return False

    def strip_backgrounds(self):
        """ Change all background colors to 0, or default background """
        for frame in self.frames:
            for line in frame.newColorMap:
                for pair in line:
                    pair[1] = 0
        return True

    @line_profiler.profile
    def strip_unprintable_characters(self):
        """ Remove all non-printable characters from canvas """
        #frame_num = 0
        for frame in self.frames:
            line_num = 0
            col_num = 0
            for line in frame.content:
                for char in line:
                    if char.isprintable():
                        pass
                    else:   # Not a printable character, so replace it with a ' '
                        #line_str = line_str.replace(search_str, replace_str.ljust(len(search_str)))
                        #line = list(line_str)
                        frame.content[line_num][col_num] = ' '
                    col_num += 1
                col_num = 0
                line_num += 1
        return True

    def shift_right(self):
        """ Shift all frames to the right, wrapping the last frame back to the front """
        # a.insert(0,a.pop())
        self.frames.insert(0, self.frames.pop())
        return True

    def shift_left(self):
        """ Shift all frames to the left, wrapping the first frame around to the back end """
        # fnord.append(fnord.pop(0))
        self.frames.append(self.frames.pop(0))
        return True

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)


