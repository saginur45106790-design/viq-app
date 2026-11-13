import time
from sqlalchemy import Column, Integer, BigInteger, String, Text, Boolean, ForeignKey, UniqueConstraint, CheckConstraint, LargeBinary, Index
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

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    body = Column(Text, default='')
    href = Column(String(200), default='#wallet')
    read = Column(Boolean, default=False, nullable=False)
    created = Column(BigInteger, default=now)

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    __table_args__ = (UniqueConstraint('user_id','task_id'),)

class TicketMessage(Base):
    __tablename__ = 'ticket_messages'
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    body = Column(Text, nullable=False)
    created = Column(BigInteger, default=now)

class IdempotencyBinding(Base):
    __tablename__ = 'idempotency_bindings'
    key = Column(String(180), primary_key=True)
    fingerprint = Column(String(64), nullable=False)
    created = Column(BigInteger, default=now)

# Explicitly installed by manage.py for existing v1 databases as well.
V2_INDEXES = [
    Index('ix_v2_tasks_category_active',Task.category,Task.active,Task.id),
    Index('ix_v2_submissions_queue',Submission.status,Submission.created),
    Index('ix_v2_tickets_user_status',Ticket.user_id,Ticket.status),
    Index('ix_v2_ledger_user_kind_time',Ledger.user_id,Ledger.kind,Ledger.created),
    Index('ix_v2_signal_recipient',Signal.room_id,Signal.recipient,Signal.id),
    Index('ix_v2_signal_sender_time',Signal.sender,Signal.created),
    Index('ix_v2_logins_user_expiry',Login.user_id,Login.expires),
]

# v3 uses additive tables so existing accounts and money are preserved.
class TaskRule(Base):
    __tablename__ = 'task_rules'
    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    platform = Column(String(30), default='')
    proof_type = Column(String(20), nullable=False)
    sample_url = Column(Text, default='')
    sample_data = Column(LargeBinary)
    sample_mime = Column(String(80))

class TaskReservation(Base):
    __tablename__ = 'task_reservations'
    task_id = Column(Integer, ForeignKey('tasks.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires = Column(BigInteger, nullable=False)

class RewardSnapshot(Base):
    __tablename__ = 'reward_snapshots'
    submission_id = Column(Integer, ForeignKey('submissions.id'), primary_key=True)
    reward = Column(BigInteger, nullable=False)
    referral = Column(BigInteger, nullable=False)

class WithdrawalCommission(Base):
    __tablename__ = 'withdrawal_commissions'
    ticket_id = Column(Integer, ForeignKey('tickets.id'), primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(BigInteger, nullable=False)

class LiveSession(Base):
    __tablename__ = 'live_sessions'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    rate = Column(BigInteger, nullable=False)
    seconds = Column(Integer, default=0, nullable=False)
    last_tick = Column(BigInteger, default=now, nullable=False)
    witnessed = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default='active', nullable=False)
    note = Column(Text, default='')
    created = Column(BigInteger, default=now, nullable=False)

class MediaAsset(Base):
    __tablename__='media_assets'
    id=Column(Integer,primary_key=True)
    owner_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    mime=Column(String(80),nullable=False)
    data=Column(LargeBinary,nullable=False)
    created=Column(BigInteger,default=now)

class Clip(Base):
    __tablename__='clips'
    id=Column(Integer,primary_key=True)
    title=Column(String(160),nullable=False)
    caption=Column(Text,default='')
    asset_id=Column(Integer,ForeignKey('media_assets.id'),nullable=False)
    active=Column(Boolean,default=True)
    created=Column(BigInteger,default=now)

class WatchSession(Base):
    __tablename__='watch_sessions'
    user_id=Column(Integer,ForeignKey('users.id'),primary_key=True)
    clip_id=Column(Integer,ForeignKey('clips.id'),nullable=False)
    token=Column(String(80),nullable=False)
    seconds=Column(Integer,default=0,nullable=False)
    position=Column(Integer,default=0,nullable=False)
    last_tick=Column(BigInteger,default=now)
    started=Column(BigInteger,default=now)

class WatchedClip(Base):
    __tablename__='watched_clips'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    clip_id=Column(Integer,ForeignKey('clips.id'),nullable=False)
    created=Column(BigInteger,default=now)
    __table_args__=(UniqueConstraint('user_id','clip_id'),)

class Operation(Base):
    __tablename__='operations'
    key=Column(String(180),primary_key=True)
    fingerprint=Column(String(64),nullable=False)
    result=Column(Text,nullable=False)
    created=Column(BigInteger,default=now)

class Currency(Base):
    __tablename__='currencies'
    code=Column(String(3),primary_key=True)
    name=Column(String(80),nullable=False)
    flag=Column(String(12),nullable=False)
    symbol=Column(String(12),nullable=False)
    rate=Column(BigInteger,default=0,nullable=False) # paisa per whole unit
    enabled=Column(Boolean,default=False,nullable=False)

class Holding(Base):
    __tablename__='holdings'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    code=Column(String(3),ForeignKey('currencies.code'),nullable=False)
    units=Column(BigInteger,default=0,nullable=False) # millionths
    cost=Column(BigInteger,default=0,nullable=False)
    __table_args__=(UniqueConstraint('user_id','code'),CheckConstraint('units >= 0'),CheckConstraint('cost >= 0'))

class CurrencyTrade(Base):
    __tablename__='currency_trades'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    code=Column(String(3),nullable=False)
    side=Column(String(8),nullable=False)
    units=Column(BigInteger,nullable=False)
    amount=Column(BigInteger,nullable=False)
    rate=Column(BigInteger,nullable=False)
    created=Column(BigInteger,default=now)

class LiveProfile(Base):
    __tablename__='live_profiles'
    user_id=Column(Integer,ForeignKey('users.id'),primary_key=True)
    name=Column(String(80),nullable=False)
    bio=Column(String(300),default='')
    avatar_id=Column(Integer,ForeignKey('media_assets.id'))

class CoinWallet(Base):
    __tablename__='coin_wallets'
    user_id=Column(Integer,ForeignKey('users.id'),primary_key=True)
    balance=Column(BigInteger,default=0,nullable=False)
    __table_args__=(CheckConstraint('balance >= 0'),)

class CoinEntry(Base):
    __tablename__='coin_entries'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    delta=Column(BigInteger,nullable=False)
    reference=Column(String(180),unique=True,nullable=False)
    note=Column(Text,default='')
    created=Column(BigInteger,default=now)

class Seat(Base):
    __tablename__='seats'
    id=Column(Integer,primary_key=True)
    room_id=Column(Integer,ForeignKey('rooms.id'),nullable=False)
    number=Column(Integer,nullable=False)
    user_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    __table_args__=(UniqueConstraint('room_id','number'),UniqueConstraint('room_id','user_id'),CheckConstraint('number >= 1 AND number <= 10'))

class RoomMessage(Base):
    __tablename__='room_messages'
    id=Column(Integer,primary_key=True)
    room_id=Column(Integer,ForeignKey('rooms.id'),nullable=False,index=True)
    sender=Column(Integer,ForeignKey('users.id'),nullable=False)
    body=Column(String(1000),default='')
    kind=Column(String(20),default='text')
    recipient=Column(Integer,ForeignKey('users.id'))
    gift=Column(String(30),default='')
    amount=Column(BigInteger,default=0)
    created=Column(BigInteger,default=now)

class Listing(Base):
    __tablename__='listings'
    id=Column(Integer,primary_key=True)
    seller_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    category=Column(String(20),nullable=False,index=True)
    title=Column(String(160),nullable=False)
    description=Column(Text,nullable=False)
    url=Column(Text,default='')
    image_id=Column(Integer,ForeignKey('media_assets.id'),nullable=False)
    price=Column(BigInteger,nullable=False)
    status=Column(String(20),default='live',nullable=False)
    created=Column(BigInteger,default=now)

class Deal(Base):
    __tablename__='deals'
    id=Column(Integer,primary_key=True)
    listing_id=Column(Integer,ForeignKey('listings.id'),nullable=False)
    buyer_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    seller_id=Column(Integer,ForeignKey('users.id'),nullable=False)
    category=Column(String(20),nullable=False,index=True)
    title=Column(String(160),nullable=False)
    amount=Column(BigInteger,nullable=False)
    status=Column(String(24),default='pending',nullable=False)
    created=Column(BigInteger,default=now)

class DealMessage(Base):
    __tablename__='deal_messages'
    id=Column(Integer,primary_key=True)
    deal_id=Column(Integer,ForeignKey('deals.id'),nullable=False,index=True)
    sender=Column(Integer,ForeignKey('users.id'),nullable=False)
    body=Column(Text,nullable=False)
    created=Column(BigInteger,default=now)
