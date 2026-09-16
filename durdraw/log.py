'''
code taken from: github.com/tmck-code/pp/log/log.py

A module to create loggers with custom handlers and a custom formatter.

usage examples to initialise a logger:
    ```python
    # initialise logger to file:
    logger = getLogger('my_logger', level=logging.DEBUG, filepath='./my_log.log')
    ```

usage examples to log messages:
1. log a basic info message by passing a string:
    ```python
    logger.info('This is a basic info message')
    # {"timestamp": "2024-12-09T15:05:43.904417", "msg": "This is a basic info message", "data": {}}
    ```
2. log a message with additional data by passing a dictionary as the second argument:
    ```python
    logger.info('This is an info message', {'key': 'value'})
    # {"timestamp": "2024-12-09T15:05:43.904600", "msg": "This is an info message", "data": {"key": "value"}}
'''

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from functools import wraps
import curses
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

CRITICAL: int = logging.CRITICAL
ERROR:    int = logging.ERROR
WARNING:  int = logging.WARNING
INFO:     int = logging.INFO
DEBUG:    int = logging.DEBUG

LOG_LEVEL = {
    'CRITICAL': CRITICAL,
    'ERROR':    ERROR,
    'WARNING':  WARNING,
    'INFO':     INFO,
    'DEBUG':    DEBUG,
}

LOG_ROOT_NAME = 'durdraw'
DEFAULT_LOG_FILENAME = 'durdraw.log'
DEFAULT_LOG_DIR = '~/.config/durdraw'
DEFAULT_LOG_FILEPATH = os.path.join(DEFAULT_LOG_DIR, DEFAULT_LOG_FILENAME)
DEFAULT_LOG_LEVEL = 'WARNING'

CURRENT_LOG_LEVEL = DEFAULT_LOG_LEVEL
CURRENT_LOG_FILEPATH = DEFAULT_LOG_FILEPATH
CURRENT_LOG_TZ = timezone.utc
LOGGER_INITIALISED = False


def app_log_filepath(filepath: str = DEFAULT_LOG_FILEPATH) -> str:
    '''
    Return the application log path, always rooted in ~/.config/durdraw.
    A configured path may choose the filename, but not the directory.
    '''
    filepath = os.path.expanduser(filepath or DEFAULT_LOG_FILEPATH)
    filename = Path(filepath).name or DEFAULT_LOG_FILENAME
    return os.path.expanduser(os.path.join(DEFAULT_LOG_DIR, filename))


def _ensure_log_dir(filepath: str) -> None:
    log_dir = os.path.dirname(os.path.expanduser(filepath))
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)


def reset_terminal_to_normal() -> None:
    '''
    Best-effort terminal cleanup for interrupted curses entrypoints.
    '''
    try:
        curses.nocbreak()
    except curses.error:
        pass
    try:
        curses.echo()
    except curses.error:
        pass
    try:
        curses.endwin()
    except curses.error:
        pass

    if sys.stdout.isatty():
        # Disable mouse tracking, leave alternate screen buffers, show cursor,
        # and reset character attributes.
        sys.stdout.write('\033[?1000l\033[?1002l\033[?1003l\033[?1006l')
        sys.stdout.write('\033[?1049l\033[?1047l\033[?47l\033[?25h\033[0m')
        sys.stdout.flush()

    if os.name == 'posix' and sys.stdin.isatty() and shutil.which('stty'):
        subprocess.run(
            ['stty', 'sane'],
            stdin=sys.stdin,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def _json_default(obj: object) -> str:
    'Default JSON serializer, supports most main class types'
    if isinstance(obj, str):       return obj
    if is_dataclass(obj):          return asdict(obj)
    if isinstance(obj, datetime):  return obj.isoformat()
    if hasattr(obj, '__dict__'):   return obj.__dict__
    if hasattr(obj, '__name__'):   return obj.__name__
    if hasattr(obj, '__slots__'):  return {k: getattr(obj, k) for k in obj.__slots__}
    if hasattr(obj, '_asdict'):    return obj._asdict()
    return str(obj)


class LogFormatter(logging.Formatter):
    'Custom log formatter that formats log messages as JSON, aka "Structured Logging".'
    def __init__(self, tz: timezone = timezone.utc, *args, **kwargs):
        self.tz = tz
        super().__init__(*args, **kwargs)

    def format(self, record) -> str:
        'Formats the log message as JSON.'

        kwargs = {}
        if isinstance(record.args, dict):
            kwargs = record.args

        record.msg = json.dumps(
            {
                'timestamp': datetime.now().astimezone(self.tz).isoformat(),
                'level':     record.levelname,
                'name':      record.name,
                'msg':       record.msg,
                'data':      kwargs,
            },
            default=_json_default,
        )
        return super().format(record)


def _getLogger(name: str, level: int = logging.CRITICAL, handlers: list = [], local_tz: bool = False) -> logging.Logger:
    '''
    Creates a logger with the given name, level, and handlers.
    - If no handlers are provided, the logger will not output any logs.
    - This function requires the handlers to be initialized when passed as args.
    - the same log level is applied to all handlers.
    '''

    # create the logger
    logger = logging.getLogger(f'{LOG_ROOT_NAME}.{name}')
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    # add the new handlers
    for handler in handlers:
        handler.setLevel(level)
        logger.addHandler(handler)

    if logger.handlers:
        if local_tz:
            tz = datetime.now().astimezone().tzinfo
        else:
            tz = timezone.utc

        # only set the first handler to use the custom formatter
        logger.handlers[0].setFormatter(LogFormatter(tz=tz))

    return logger


def getLogger(
    name: str,
    level: str = DEFAULT_LOG_LEVEL,
    filepath: str = DEFAULT_LOG_FILEPATH,
    override: bool = False,
    local_tz: bool = False,
) -> logging.Logger:
    '''
    Creates a logger with the given name, level, and handlers.
    - disable the logger by setting the level to logging.CRITICAL
    - the default log level is 'WARNING'
    - the default log file is '~/.config/durdraw/durdraw.log'

    This logger will only create an output file if there is a call to write a log message that matches the log level.
    '''
    global CURRENT_LOG_LEVEL
    global CURRENT_LOG_FILEPATH
    global LOGGER_INITIALISED
    global CURRENT_LOG_TZ

    if not LOGGER_INITIALISED or override:
        # create a root logger
        LOGGER_INITIALISED = True
        CURRENT_LOG_LEVEL = level
        CURRENT_LOG_FILEPATH = os.path.expanduser(filepath)
        if local_tz:
            CURRENT_LOG_TZ = datetime.now().astimezone().tzinfo
        else:
            CURRENT_LOG_TZ = timezone.utc

    _ensure_log_dir(CURRENT_LOG_FILEPATH)
    return _getLogger(
        name,
        level=LOG_LEVEL[CURRENT_LOG_LEVEL],
        handlers=[logging.FileHandler(CURRENT_LOG_FILEPATH, mode='a', delay=True)],
        local_tz=CURRENT_LOG_TZ,
    )

def log_on_crash(func):
    '''
    This is a decorator that can be used to log any exceptions that occur in a function.
    This is mainly intended to wrap around the main() functions/entrypoints to durdraw,
    so that any exceptions that occur can be logged to a file for debugging or support.
    '''
    logger = getLogger('crash', level='ERROR')
    @wraps(func)
    def inner(*args, **kwargs):
        # run the function, return the result, and log any exceptions
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            reset_terminal_to_normal()
            raise SystemExit(130)
        except Exception as e:
            logger.exception(
                'durview crashed',
                {'class': e.__class__.__name__, 'message': str(e)},
                exc_info=True,
            )
            raise e
    return inner
