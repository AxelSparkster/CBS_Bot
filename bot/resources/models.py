from enum import IntEnum


class MatchType(IntEnum):
    NO_MATCH = 0
    CBS = 1
    ROUNDONE = 2


class DifficultyEnum(IntEnum):
    NOV = 1
    ADV = 2
    EXH = 3
    MXM = 5
    # INF = 4i
    # GRV = 4g
    # HVN = 4h
    # VVD = 4v
    # XCD = 4x
