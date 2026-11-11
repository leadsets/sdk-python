import sys

if sys.version_info >= (3, 12):
    from typing import Unpack
else:  # pragma: no cover
    from typing_extensions import Unpack

__all__ = ["Unpack"]
