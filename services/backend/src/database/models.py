from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from src.database.session import Base
from src.utils import ErrorTypeEnum
from src.utils import LevelTypeEnum


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String)
    session_id = Column(String, default='')
    level = Column(Enum(LevelTypeEnum), default=LevelTypeEnum.a2)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship(
        'Messages', back_populates='user', cascade='all, delete-orphan',
    )
    achievements = relationship(
        'Achievements',
        secondary='user_achievements',
        back_populates='users',
    )


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text_original = Column(Text)
    text_corrected = Column(Text)
    explanation = Column(Text)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('Users', back_populates='messages')
    errors = relationship(
        'Errors', back_populates='message',
        cascade='all, delete-orphan',
    )


class Errors(Base):
    __tablename__ = 'errors'

    id = Column(Integer, primary_key=True)
    msg_id = Column(BigInteger, ForeignKey('messages.id'))
    type = Column(Enum(ErrorTypeEnum), nullable=False)
    subtype = Column(String)
    original = Column(String)
    corrected = Column(String)

    message = relationship('Messages', back_populates='errors')


class Achievements(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, unique=True)
    title = Column(String, default='Title')
    description = Column(Text, default='Description')

    users = relationship(
        'Users',
        secondary='user_achievements',
        back_populates='achievements',
    )


class UserAchievements(Base):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    achievement_id = Column(Integer, ForeignKey('achievements.id'))
    earned_at = Column(DateTime, default=datetime.utcnow)
