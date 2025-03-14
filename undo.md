# Undo Register

- [Undo Register](#undo-register)
  - [Undo usages](#undo-usages)
    - [Summarised](#summarised)
  - [Feature List](#feature-list)
  - [Implementation](#implementation)
    - [Current system](#current-system)
    - [Considerations and Challenges](#considerations-and-challenges)
    - [Basic Framework](#basic-framework)
      - ["do" an action (push)](#do-an-action-push)
      - ["undo" an action](#undo-an-action)
      - ["redo" an action](#redo-an-action)
    - [Low-Level Undo Register](#low-level-undo-register)
  - [Opportunities](#opportunities)
  - [POC](#poc)
  - [Progress/Operation Support](#progressoperation-support)
  - [Questions](#questions)
  - [Proposal](#proposal)


## Undo usages

| undo method | file | Line | Function |
| --- | --- | --- | --- |
`push()` | durdraw/durdraw_ui_curses.py | 1097 | `def transform_bounce(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 1107 | `def transform_repeat(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 1117 | `def transform_reverse(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 1126 | `def moveCurrentFrame(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 1386 | `def apply_neofetch_keys(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 2614 | `def mainLoop(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 3372 | `def replaceColorUnderCursor(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 3427 | `def cloneToNewFrame(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 3437 | `def appendEmptyFrame(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 3611 | `def getDelayValue(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 3630 | `def deleteCurrentFramePrompt(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 5314 | `def loadFromFile(self, shortfile, loadFormat):  # shortfile = non full path filename` |
`push()` | durdraw/durdraw_ui_curses.py | 6446 | `def addColToCanvas(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 6459 | `def delColFromCanvas(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 6475 | `def addLineToCanvas(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 6487 | `def delLineFromCanvas(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 6501 | `def addCol(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6524 | `def delCol(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6543 | `def delLine(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6564 | `def addLine(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6582 | `def startSelecting(self, firstkey=None, mouse=False):   # firstkey is the key the user was` |
`push()` | durdraw/durdraw_ui_curses.py | 6853 | `def askHowToPaste(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 6876 | `def pasteFromClipboard(self, startPoint=None, clipBuffer=None, frange=None, transparent=False, pushUndo=True):` |
`push()` | durdraw/durdraw_ui_curses.py | 6927 | `def copySegmentToAllFrames(self, startPoint, height, width, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6972 | `def flipSegmentVertical(self, startPoint, height, width, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6984 | `def flipSegmentHorizontal(self, startPoint, height, width, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 6995 | `def deleteSegment(self, startPoint, height, width, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 7011 | `def fillSegment(self, startPoint, height, width, frange=None, fillChar=\"X\"):` |
`push()` | durdraw/durdraw_ui_curses.py | 7027 | `def colorSegment(self, startPoint, height, width, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 764 | `def backspace(self):` |
`push()` | durdraw/durdraw_ui_curses.py | 774 | `def deleteKeyPop(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 790 | `def reverseDelete(self, frange=None):` |
`push()` | durdraw/durdraw_ui_curses.py | 807 | `def insertColor(self, fg=1, bg=0, frange=None, x=None, y=None, pushUndo=True):` |
`push()` | durdraw/durdraw_ui_curses.py | 823 | `def insertChar(self, c, fg=1, bg=0, frange=None, x=None, y=None, moveCursor = False, pushUndo=True):` |
`push()` | durdraw/durdraw_ui_curses.py | 878 | `def clearCanvas(self, prompting = False):` |
`push()` | durdraw/durdraw_undo.py | 10 | `def __init__(self, ui, appState = None):` |
`push()` | durdraw/durdraw_undo.py | 42 | `def undo(self):` |
`undo()` | durdraw/durdraw_ui_curses.py | 1126 | `def moveCurrentFrame(self):` |
`undo()` | durdraw/durdraw_ui_curses.py | 2584 | `def clickedUndo(self):` |
`undo()` | durdraw/durdraw_ui_curses.py | 6582 | `def startSelecting(self, firstkey=None, mouse=False):   # firstkey is the key the user was` |
`redo()` | durdraw/durdraw_ui_curses.py | 2592 | `def clickedRedo(self):` |

### Summarised

## Feature List

1. pixel-level undo/redo
   - Should be able to store and update pixel states, e.g. chars and colours
2. (?) action/state-level undo/redo
    - Allow undo/redo for actions that are not pixel/char/colour changes
    - e.g. cursor position, selected area, durations/other metadata
    - some of these may be stored in tandem with other changes, e.g. a pixel change and a cursor move
3. Multi-pixel (or multi-anything) operations
    - Ensure that multi-pixel operations (e.g. flipping, colour fill) are correctly undone/redone all at once.
    - This will probably take the form of storing `n` pixel changes in each undo/redo action

*Misc requirements:*

- All pixel/other state should be updated correctly from undo/redo actions
  - cursor position
  - pixel char/colour
  - selected area
  - durations/other metadata
- Goes without saying
  - This should all be _fast_, which I'm pretty confident will be the case (#TODO some basic proof and big Os).
  - This should be _efficient_, leaving room for very large projects and scaling/extending in future.
  - This should all be _small_, as any speed increase at the cost of memory will not really be a victory.

## Implementation

### Current system

The current undo system relies on [`pickle.dump`](https://docs.python.org/3/library/pickle.html#pickle.dump) to serialize the entire `durdraw` UI object. The key advantage of this approach is the simplicity of use - any UI method can `push` the picked state onto the queue, and there is no implementation required for how to undo an action, only the initial operation itself!

This approach has some performance drawbacks, however, which make durdraw a little sluggish to use at times.

- the size of the pickled state mainly depends on the dimensions, and **_the number of frames_**
- pickling the entire UI happens on many operations
- this includes insertChar (i.e. typing), which is the most common operation
- this can result in a sluggish experience for the user as even simple typing is slow
- this problem grows over time as each new redo is added to the stack

>[!CAUTION]
> This can result in a durdraw movie file of `500KB` taking **1-2 seconds delay** for each character inserted, and using `1.5GB` of memory in **less than 40 characters inserted**.

### Considerations and Challenges

Given that almost all durdraw performance is tied to the undo system, it's clear that a new system is needed that will
allow durdraw to more effectively scale to very large projects.

> [!IMPORTANT]
> This efficiency is entirely dictated by the size of each undo record.   
> In order to achieve this, I am proposing a system that will store only the changes made by each operation, rather than the entire state of the UI.

See [Progress/Operation Support](#progressoperation-support) for the complete list of operations that need to be implemented. Some examples of the types of changes include:

- pixel char and/or colour changes
  - for one frame or many
- the cursor position
- the canvas size

A major change required by this new system is that for every user action that is stored in the undo register, the "reverse" of that operation must now be implemented.

Each existing action should be routed (where appropriate) through the Frame/Movie classes. These classes are best placed
to recognise when state has changed and correspondingly update the undo state.

~~In addition to the existing Frame/Movie classes, it could be handy to introduce something like a Pixel class that could keep track of its own state,
and the main undo list could just consist of references to the individual pixel & index of the change inside that pixel. I'm unsure how this would interact with things like the existing colour map #TODO investigate.~~   
*^ I am now thinking that, at this stage, this change to Frames/pixels is not neccessary to be able to implement the new undo system, and it risks changing too much at once (e.g. the underlying way that chars and colours are set in durdraw via the content and colour map)*

### Basic Framework

#### "do" an action (push)

1. user performs action in UI
2. the UI function will
   1. create an object containing the current (_old_/_before_) state of all effected pixels/frames/movie
      1. e.g. for a segment flip, storing the pixel chars/colours for the segment area
   2. perform the operation, updating the canvas/frames/movie
   3. create an object containing the current (_new_/_after_) state of all effected pixels/frames/movie
   4. create an undo object containing the _old_ and _new_ states
   5. and push this undo object to the undo register

#### "undo" an action

1. user presses undo
2. undo object is popped from the undo register
3. using the _old_/_before state /in that undo object
   1. Apply any pixel changes
      1. For each frame that was changed
   2. Apply any other changes
      1. e.g. cursor position, canvas size

#### "redo" an action

1. user presses redo
2. redo object is popped from the redo register
3. using the _new_/_after state /in that redo object
   1. Apply any pixel changes
      1. For each frame that was changed
   2. Apply any other changes
      1. e.g. cursor position, canvas size

| [diagram](https://link.excalidraw.com/readonly/svgZcqp0b4R5EClbbkdh) |
|-----|
| ![image](https://github.com/user-attachments/assets/eea5445d-292f-42c5-9327-85da1e0560c1) |

### Low-Level Undo Register

Initially, I've come up with an implementation that utilises the `deque` data structure from the `collections` module. This is a double-ended queue that allows for fast appends and pops from either end. This is ideal for the undo/redo system, as we only need to deal with items that are on the *very end* of the buffers.

`deque` is actually ~`O(1)` for appends and pops from either end, which I can demonstrate in ipython:

```python
In [1]: from collections import deque

In [2]: def undo(u, r, n):
   ...:     for _ in range(n):
   ...:         r.appendleft(u.pop())
   ...:         u.append(r.popleft())
   ...:

In [3]: a, b = deque(range(10)), deque()

In [4]: %timeit undo(a, b, 10)
# 416 ns ± 0.332 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

In [5]: a, b = deque(range(100_000)), deque(range(100_000))

In [6]: %timeit undo(a, b, 10)
# 416 ns ± 1.15 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
```

---

## Opportunities

These are ideas that are not part of this proposal, but could be explored in future.

- It would be possible to serialize the undo/redo buffers to a local file in the event of a crash, and restore the state on next launch ala vim.

## POC

I wrote a [POC script](./poc.py) to test the undo/redo functionality. It's an oversimplified version of durdraw, with the proposed undo system bolted on.   
You can essentially type out a bunch of stuff and use the arrow keys, and then press (and hold!) 'u/r' to undo/redo.

- There is line profiling attached to almost every function, you can run with `LINE_PROFILE=1 ./poc.py` to see where time is being spent.
- You can also enable debug logs by uncommenting them and setting the log level to `'DEBUG'`

On another note, here are some logs from the very rough POC implementation in durdraw

```json
{"timestamp":"2024-12-12T19:39:38.509133+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:38.827779+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 115, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:39.521499+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 115, 7, 0), (0, 0, 100, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:40.639585+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"undo","data":{"undoBuf":"deque([(0, 0, 115, 7, 0)])","redoBuf":"deque([(0, 0, 115, 7, 0)])"}}
{"timestamp":"2024-12-12T19:39:44.620562+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:44.641024+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0), (0, 0, 106, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:44.646262+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0), (0, 0, 106, 7, 0), (0, 0, 115, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:44.659840+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0), (0, 0, 106, 7, 0), (0, 0, 115, 7, 0), (0, 0, 97, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:44.709905+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0), (0, 0, 106, 7, 0), (0, 0, 115, 7, 0), (0, 0, 97, 7, 0), (0, 0, 100, 7, 0)])","redoBuf":"deque([])"}}
{"timestamp":"2024-12-12T19:39:44.763499+11:00","level":"DEBUG","name":"durdraw.undo_register","msg":"push","data":{"undoBuf":"deque([(0, 0, 115, 7, 0), (0, 0, 107, 7, 0), (0, 0, 106, 7, 0), (0, 0, 115, 7, 0), (0, 0, 97, 7, 0), (0, 0, 100, 7, 0), (0, 0, 104, 7, 0)])","redoBuf":"deque([])"}}
```

## Progress/Operation Support

*These are all the operations that need to be supported by the undo system.*

- [ ] Changing pixels
  - [ ] Backspace
  - [ ] Delete Key Pop
  - [ ] Insert Color
  - [ ] Replace Color Under Cursor
  - [ ] Reverse Delete
  - [x] Insert Char
- [ ] Frame/Animation
  - [ ] Append Empty Frame
  - [ ] Clone To New Frame
  - [ ] Delete Current Frame Prompt
  - [ ] Move Current Frame
  - [ ] Transform Bounce
  - [ ] Transform Repeat
  - [ ] Transform Reverse
- [ ] Movie/High-level
  - [ ] Apply Neofetch Keys
  - [ ] Clear Canvas
  - [ ] Get Delay Value
  - [ ] Load From File
- [ ] Adding/Removing columns & lines
  - [ ] Add Line
  - [ ] Add Line To Canvas
  - [ ] Delete Column
  - [ ] Delete Column From Canvas
  - [ ] Delete Line
  - [ ] Delete Line From Canvas
  - [x] Add Column
  - [x] Add Column To Canvas
- [ ] Box selections
  - [ ] Copy Segment To All Frames
  - [ ] Cut Segment
  - [x] Brush Segment
  - [x] Color Segment
  - [x] Delete Segment
  - [x] Fill Segment
  - [x] Flip Segment Horizontal
  - [x] Flip Segment Vertical
  - [x] Paste From Clipboard
  - [x] Start Selecting
- [x] Undo/Redo
  - [x] Clicked Redo
  - [x] Clicked Undo

## Questions

- Clarify: Why is the colour map stored separately to the content? I don't want to miss anything due to lack of understanding.
- What is the largest file (frames * width * height) that should be supported?
- Have I missed any major operations or functionality?

## Proposal

I've now done enough digging and poking that I'm ready to sketch out a rough proposal for review/confirmation before I start getting really stuck in. This will require quite a few LOC to be changed, so I definitely want to make sure I'm on the right track before I start and avoid any horrific oversights.

1. Introduce the new undo "registry" (exact name pending?)
2. Move a lot (all/most?) of the "pixel manipulation" functions from `durdraw_ui_curses` to the `Frame` and `Movie` classes in `durdraw_movie`.
     1. When doing this, take the opportunity to add tests for as many operations as I have the energy for.
     2. This has the benefit of reducing the LOC in ui_curses which will benefit our squishy human brains.
3. Implement [all operations listed above](#progressoperation-support) in the new undo system.

> *Exact implementation still pending! e.g.*
> - *Do I store tuples containing the actual function, or a string value that can be used with a mapping dict to get that function? What are the implications and performance considerations of each?*
> - *Do I use ChainMap or similar instead of a deque for the undo/redo buffers?*
> *These are pretty low-level considerations that I haven't set in stone yet, but the overall plan and interface is becoming clearer.*
