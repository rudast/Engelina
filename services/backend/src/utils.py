from __future__ import annotations

import enum


class ErrorTypeEnum(enum.Enum):
    spelling = 'Spelling'
    grammar = 'Grammar'
    punctuation = 'Punctuation'
    style = 'Style'


class LevelTypeEnum(enum.Enum):
    a1 = 'A1'
    a2 = 'A2'
    b1 = 'B1'
    b2 = 'B2'
    c1 = 'C1'
    c2 = 'C2'
