from enum import Enum, auto


class States(Enum):
    WAITING_PHOTO = auto()
    WAITING_NAME = auto()
    WAITING_ANSWER = auto()
    WAITING_TRANSITION = auto()
