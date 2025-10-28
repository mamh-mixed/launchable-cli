"""
Defines a series of "converter" functions used in @option(type=...) to bind options/arguments
for common scenarios.

Exposed from the args4p package.
"""
from pathlib import Path
from typing import IO, Callable, Optional


def path(exists: bool = False,
         file_okay: bool = True,
         dir_okay: bool = True,
         resolve_path: bool = False, ) -> Callable[[str], Path]:
    '''
      Use it as @option(type=path(...)) to convert an option value/argument to a Path object.
    '''
    def convert(value: str) -> Path:
        p = Path(value)
        if resolve_path:
            p = p.resolve()
        if exists and not p.exists():
            raise ValueError(f'Path {p} does not exist')
        if not file_okay and p.is_file():
            raise ValueError(f'Path {p} is a file, but a directory is expected')
        if not dir_okay and p.is_dir():
            raise ValueError(f'Path {p} is a directory, but a file is expected')
        return p

    return convert


def floatType(min: Optional[float] = None, max: Optional[float] = None) -> Callable[[str], float]:
    '''
      Use it as @option(type=floatType(...)) to convert an option value/argument to a float.
    '''
    def convert(value: str) -> float:
        try:
            f = float(value)
        except ValueError:
            raise ValueError(f'\'{value}\' is not a valid float')
        if min is not None and f < min:
            raise ValueError(f'\'{value}\' cannot be smaller than {min}')
        if max is not None and f > max:
            raise ValueError(f'\'{value}\' cannot be larger than {max}')
        return f

    return convert


def intType(min: Optional[int] = None, max: Optional[int] = None) -> Callable[[str], int]:
    '''
      Use it as @option(type=intType(...)) to convert an option value/argument to an int.
    '''
    def convert(value: str) -> int:
        try:
            i = int(value)
        except ValueError:
            raise ValueError(f'\'{value}\' is not a valid integer')
        if min is not None and i < min:
            raise ValueError(f'\'{value}\' cannot be smaller than {min}')
        if max is not None and i > max:
            raise ValueError(f'\'{value}\' cannot be larger than {max}')
        return i

    return convert


def fileText(mode: str = "r") -> Callable[[str], IO]:
    '''
      Open a file specified by argument/option for reading/writing
    '''
    def convert(value: str) -> IO:
        return open(value, mode)
    return convert
