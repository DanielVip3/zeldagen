from enum import Enum

# Number of rooms in a dungeon
NUM_ROOMS = 10

# Index of root element in graph
ROOT = 0

# Index of finish element in graph
FINISH = 9

# 0: beginning room (S)
# 1: key room (K)
# 2: normal room (N)
# 3: boss room (F)
class Types(Enum):
    START = 0,
    KEY = 1,
    NORMAL = 2,
    FINISH = 3