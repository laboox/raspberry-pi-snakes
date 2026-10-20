import collections
import enum


class Effect(enum.Enum):
    NONE = "none"
    FLASH = "flash"


ColorEffect = Effect

# Types
Direction = collections.namedtuple("Direction", ["x", "y"])
Point = collections.namedtuple("Point", ["x", "y"])
Color = collections.namedtuple("Color", ["g", "r", "b", "effect"], defaults=[Effect.NONE])
