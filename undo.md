# Undo Register

- [Undo Register](#undo-register)
  - [Preface](#preface)
  - [Implementation](#implementation)
    - [Current system](#current-system)
    - [Thinking about an "undo" record](#thinking-about-an-undo-record)
    - [Challenges](#challenges)
    - [Basic Framework](#basic-framework)
      - ["do" an action (push)](#do-an-action-push)
      - ["undo" an action](#undo-an-action)
      - ["redo" an action](#redo-an-action)
      - [Some examples](#some-examples)
        - [1. Insert Char](#1-insert-char)
        - [2. Flip Segment](#2-flip-segment)
  - [POC](#poc)
    - [1. Low-Level Undo Register](#1-low-level-undo-register)
      - [POC](#poc-1)
      - [Unit Tests](#unit-tests)
    - [2. Partial implementation in durdraw](#2-partial-implementation-in-durdraw)
  - [Demo/UX Testing](#demoux-testing)
    - [How to grok?](#how-to-grok)
  - [Progress/Operation Support](#progressoperation-support)
  - [Opportunities / Out of Scope](#opportunities--out-of-scope)
  - [Undo usages](#undo-usages)

## Preface

> [!IMPORTANT]
> This proposal is:
> - ✔️ a prototype/proof of concept of the main ideas detailed below
>
> It is not
> - ✘ a set-in-stone/inflexible idea
> - ✘ a completely-polished representation of the final implementation

There may be inconsistencies in implementation that I missed or left until after this discussion, as otherwise I could be working on this forever before sharing it 😛

I've taken a while to slowly amble through discovering this project on a deeper level, I tried a few different directions before settling on this one as a good starting point for discussion. I see this proposal as having 2 main components

1. the **technical details**/low-level implementation of the undo register, how items are exchanged between the undo/redo buffers
2. the **code framework** that creates and assembles the new state objects needed for each operation

_(Item number 1 took me only a few days to work on, and item number 2 has taken 2-3 months)_

---

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
> The current undo system can result in a durdraw movie file of `500KB` taking **1-2 seconds delay** for each character inserted, and using `1.5GB` of memory in **less than 40 characters inserted**.

### Thinking about an "undo" record

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

### Challenges

A major change required by this new system is that for every user action that is stored in the undo register, the "reverse" of that operation must now be implemented.

The `ui_curses` (aka god) is the beating heart of durdraw, and ties together
- the canvas
  - and animation frame system, both editing and playing
- menu systems/displays
- user input
- pixel manipulation/updates

There is a separate `movie` module that houses the classes for 
- `frame` holds a grid of characters, a grid of ANSI colour pairs, and some other related values
- `movie` holds a colletion of frames, and some other related values

However, the actual logic to do all of the pixel updating is in `ui_curses`

TODO: up to here

### Basic Framework

#### "do" an action (push)

1. user performs action in UI
2. the UI function will
   1. create an object containing the current (`old/before`) state of all effected pixels/frames/movie
      1. e.g. for a segment flip, storing the pixel chars/colours for the segment area
   2. perform the operation, updating the canvas/frames/movie
   3. create an object containing the current (`new/after`) state of all effected pixels/frames/movie
   4. create an undo object containing the _old_ and _new_ states
   5. and push this undo object to the undo register

#### "undo" an action

1. user presses undo
2. undo object is popped from the undo register
3. using the `old/before` state in that undo object
   1. Apply any pixel changes
      1. For each frame that was changed
   2. Apply any other changes
      1. e.g. cursor position, canvas size

#### "redo" an action

1. user presses redo
2. redo object is popped from the redo register
3. using the `new/after` state in that redo object
   1. Apply any pixel changes
      1. For each frame that was changed
   2. Apply any other changes
      1. e.g. cursor position, canvas size

| [diagram](https://link.excalidraw.com/readonly/svgZcqp0b4R5EClbbkdh) |
|-----|
| ![image](https://github.com/user-attachments/assets/eea5445d-292f-42c5-9327-85da1e0560c1) |

#### Some examples

- [1. Insert Char](#1-insert-char)
- [2. Flip Segment](#2-flip-segment)

##### 1. Insert Char

Current implementation:

```python
def insertChar(c, bg, fg, fraange, x, y, moveCursor = False, pushUndo=True):
    # push the initial state onto the undo register
    # figure out the cursor
    for frame in frange:
      # for position (x,y)
        # update the char
        # update the colour
    # move the cursor
```

New implementation:

TODO: up to here!

```python
```

##### 2. Flip Segment

Lets look at a basic example of a segment flip operation

```python

```


---

## POC

There are 2 main demos/POCs that I've worked on as part of this

1. [1. Low-Level Undo Register](#1-low-level-undo-register)
2. [2. Partial implementation in durdraw](#2-partial-implementation-in-durdraw)

---

### 1. Low-Level Undo Register

I've come up with an implementation that utilises the `deque` data structure from the `collections` module. This is a double-ended queue that allows for fast appends and pops from either end. This is ideal for the undo/redo system, as we only need to deal with items that are on the *very end* of the buffers.

`deque` is actually ~`O(1)` for appends and pops from either end, which I can demonstrate in ipython:

```python
from collections import deque

def undo(u, r, n):
    for _ in range(n):
        r.appendleft(u.pop())
        u.append(r.popleft())

# let's use a small example initially
a, b = deque(range(10)), deque()
%timeit undo(a, b, 10)
# -> 416 ns ± 0.332 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)

# now lets make it 10_000x larger
a, b = deque(range(100_000)), deque(range(100_000))
%timeit undo(a, b, 10)
# -> 416 ns ± 1.15 ns per loop (mean ± std. dev. of 7 runs, 1,000,000 loops each)
```

#### POC

Initially I wrote a very rudimentary [POC script](./poc.py) to test the undo/redo functionality. It's an oversimplified version of durdraw, with the proposed undo system bolted on.   
You can essentially type out a bunch of stuff and use the arrow keys, and then press (and hold!) 'u/r' to undo/redo.

- There is line profiling attached to almost every function, you can run with `LINE_PROFILE=1 ./poc.py` to see where time is being spent.
- You can also enable debug logs by uncommenting them and setting the log level to `'DEBUG'`

#### Unit Tests

Additionally, check out the unit tests in `test/durdraw/test_undo.py` which show the different state changes that happen in the undo register.

---

### 2. Partial implementation in durdraw

On this branch ([`undo-register-proposal-implement-ops`](https://github.com/tmck-code/durdraw/tree/undo-register-proposal-implement-ops)), I've implemented **13/37** operations from the total list (see [Progress/Operation Support](#progressoperation-support)).

These involve:

- changing/updating individual pixels
- segments (updating many pixels across >=1 frames)
  - single frame: flipping
  - multi-frame: flipping, deleting, filling, colouring
- adding columns to the canvas (updating pixels in >1 frames + movie state)

---

## Demo/UX Testing

How to test? This is a great example I've been using for comparison:

> [!TIP]
> _run `tail -f durdraw.log` in a separate terminal to see debug logs as they happen_

1. checkout to this branch in the durdraw repo
2. Download [goto80-goto20.ans](https://16colo.rs/pack/impure77/raw/goto80-goto20.ans) from 16colo.rs
3. run `DEBUG=true ./start-durdraw goto80-goto20.ans`
4. create 10 animation frames by cloning the current one 9 times (pressing `ESC, n` 9 times)
5. save this as a durdraw file (e.g. `goto.dur`)
6. exit durdraw
7. run `DEBUG=true ./start-durdraw goto.dur`
8. start typing and using the operations listed in [Progress/Operation Support](#progressoperation-support)
   1. press `u` to undo, `r` to redo
9. now, to compare, switch to the `master` branch and repeat steps 7-8

### How to grok?

- Reading this doc is a good start, and then trying out the UI as detailed above [Demo/UX Testing](#demoux-testing). After that, reading the following areas of code:

1. the low-level undo register
   1. [`durdraw/durdraw_undo.py`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_undo.py#L117-L170)
   2. and the tests in [`test/durdraw/test_undo.py`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/test/durdraw/test_undo.py)
2. the `FileState` object defined in [`durdraw/durdraw_movie.py`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_movie.py#L107-L138)
3. the methods in [`durdraw/durdraw_movie.py`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_movie.py#L249-L321) that apply pixel & frame changes using `FileState` objects
4. the methods in `durdraw/durdraw_ui_curses.py` that create the `FileState` objects as they perform their operations before pushing the objects to the undo register, e.g.
   1. [`insertChar`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_movie.py#L249-L321)
   2. [`startSelecting`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_ui_curses.py#L6794-L7010)
      1. for flipping, only 1 undo record is pushed when the user finally presses enter, rather than 1 record per flip
   3. [`addCol`](https://github.com/tmck-code/durdraw/blob/f0ee417f846ceab1e02ca954eed574f7b41b2546/durdraw/durdraw_ui_curses.py#L6606-L6650)


---

## Progress/Operation Support

*These are all the operations that need to be supported by the undo system.*

> [!IMPORTANT]
> Current Completion: **13/37 (35%)**

- [ ] Changing pixels
  - [ ] Backspace
  - [ ] Delete Key Pop
  - [ ] Insert Color
  - [ ] Replace Color Under Cursor
  - [ ] Reverse Delete
  - [x] Insert Char
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

---

## Opportunities / Out of Scope

TODO: up to here!

---

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
