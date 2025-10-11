"""
Defines a series of "converter" functions used in @option(type=...) to bind options/arguments
for common scenarios.

Exposed from the args4p package.
"""
from pathlib import Path
from typing import Callable


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

