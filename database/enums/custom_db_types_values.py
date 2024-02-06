from enum import Enum


class ProductStatusValues(Enum):
    BACKLOG = "BACKLOG"
    CANCELLED = "CANCELLED"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
