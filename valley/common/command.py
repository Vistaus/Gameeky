from enum import StrEnum, auto


class Command(StrEnum):
    SESSION_PORT = auto()
    UPDATES_PORT = auto()
    SCENE_PORT = auto()
    CLIENTS = auto()
    ADDRESS = auto()