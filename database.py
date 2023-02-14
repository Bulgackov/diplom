from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

import sqlalchemy as sq
from sqlalchemy.orm import relationship
from model.base import Base


class Candidate(Base):
    __tablename__ = 'candidate'

    id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    screen_name = sq.Column(sq.String)
    photos = relationship('Photo', backref='candidate')
    users = relationship('User', secondary='user_to_candidate')
    
    import sqlalchemy as sq
from model.base import Base


class Photo(Base):
    __tablename__ = 'photo'

    # "<type><owner_id>_<media_id>"
    id = sq.Column(sq.String, primary_key=True)
    photo_id = sq.Column(sq.Integer)
    candidate_id = sq.Column(sq.Integer, sq.ForeignKey('candidate.id'))
    likes_count = sq.Column(sq.Integer)
    comments_count = sq.Column(sq.Integer)
    
    import sqlalchemy as sq
from sqlalchemy.orm import relationship
from model.base import Base


class User(Base):
    __tablename__ = 'user'

    id = sq.Column(sq.Integer, primary_key=True)
    token = sq.Column(sq.String)
    candidates = relationship('Candidate', secondary='user_to_candidate')
    
    import sqlalchemy as sq
from model.base import Base


user_to_candidate = sq.Table(
    'user_to_candidate', Base.metadata,
    sq.Column('user_id', sq.Integer, sq.ForeignKey('user.id')),
    sq.Column('candidate_id', sq.Integer, sq.ForeignKey('candidate.id')),
)
