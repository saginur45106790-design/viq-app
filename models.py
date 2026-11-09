import time
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()
def now(): return int(time.time())

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(254), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    password = Column(Text, nullable=False)
    role = Column(String(20), default='user', nullable=False)
    blocked = Column(Boolean, default=False, nullable=False)
    balance = Column(BigInteger, default=0, nullable=False)
    held = Column(BigInteger, default=0, nullable=False)
    referrer = Column(Integer, ForeignKey('users.id'))
    created = Column(BigInteger, default=now)
    __table_args__ = (CheckConstraint('balance >= 0'), CheckConstraint('held >= 0'))

class Login(Base):
    __tablename__ = 'logins'
    token = Column(String(64), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    csrf = Column(String(64), nullable=False)
    expires = Column(BigInteger, nullable=False)

class Attempt(Base):
    __tablename__ = 'attempts'
    id = Column(Integer, primary_key=True)
    key = Column(String(64), index=True)
    created = Column(BigInteger, default=now, index=True)

class Category(Base):
    __tablename__ = 'categories'
    slug = Column(String(30), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default='')
    enabled = Column(Boolean, default=True)

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String(50), primary_key=True)
    value = Column(Text, default='')

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    category = Column(String(30), ForeignKey('categories.slug'), nullable=False)
    title = Column(String(160), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(Text, default='')
    reward = Column(BigInteger, nullable=False)
    referral = Column(BigInteger, nullable=False, default=0)
    slots = Column(Integer, nullable=False)
    used = Column(Integer, nullable=False, default=0)
    min_seconds = Column(Integer, default=0, nullable=False)
    deadline = Column(BigInteger, default=0)
    active = Column(Boolean, default=True)
    created = Column(BigInteger, default=now)
    __table_args__ = (CheckConstraint('reward >= 0'), CheckConstraint('used >= 0 AND used <= slots'))

class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    status = Column(String(20), default='started', nullable=False)
    proof = Column(Text, default='')
    note = Column(Text, default='')
    started = Column(BigInteger, default=now)
    created = Column(BigInteger, default=now)
    __table_args__ = (UniqueConstraint('user_id', 'task_id'),)

class Attachment(Base):
    __tablename__ = 'attachments'
    id = Column(Integer, primary_key=True)
    submission_id = Column(Integer, ForeignKey('submissions.id'), unique=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mime = Column(String(100))
    data = Column(LargeBinary, nullable=False)

class Ledger(Base):
    __tablename__ = 'ledger'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)
    held_delta = Column(BigInteger, default=0, nullable=False)
    kind = Column(String(50), nullable=False)
    reference = Column(String(160), unique=True, nullable=False)
    note = Column(Text, default='')
    created = Column(BigInteger, default=now)

class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    kind = Column(String(30), nullable=False)
    amount = Column(BigInteger, default=0, nullable=False)
    details = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    note = Column(Text, default='')
    receipt = Column(String(160), unique=True)
    idem = Column(String(100), unique=True, nullable=False)
    created = Column(BigInteger, default=now)

class ExchangeRoute(Base):
    __tablename__ = 'exchange_routes'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    rate = Column(Integer, default=10000, nullable=False)
    fee = Column(BigInteger, default=0, nullable=False)
    unit = Column(String(20), default='BDT')
    enabled = Column(Boolean, default=True)

class Audit(Base):
    __tablename__ = 'audit'
    id = Column(Integer, primary_key=True)
    actor = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    detail = Column(Text)
    created = Column(BigInteger, default=now)

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    kind = Column(String(20), nullable=False)
    host_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    guest_id = Column(Integer, ForeignKey('users.id'))
    active = Column(Boolean, default=True)
    audio_only = Column(Boolean, default=False)

class Peer(Base):
    __tablename__ = 'peers'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    seen = Column(BigInteger, default=now)
    __table_args__ = (UniqueConstraint('room_id', 'user_id'),)

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    sender = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient = Column(Integer, ForeignKey('users.id'), nullable=False)
    payload = Column(Text, nullable=False)
    created = Column(BigInteger, default=now)
