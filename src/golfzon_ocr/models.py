"""
SQLAlchemy models for the Golfzon League database.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class League(Base):
    """League model representing a golf league."""
    __tablename__ = 'leagues'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    teams = relationship("Team", back_populates="league", cascade="all, delete-orphan")
    weekly_scores = relationship("WeeklyScore", back_populates="league", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<League(id={self.id}, name='{self.name}')>"


class Team(Base):
    """Team model representing a team within a league."""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    league = relationship("League", back_populates="teams")
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', league_id={self.league_id})>"


class Player(Base):
    """Player model representing a player assigned to a team."""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    weekly_scores = relationship("WeeklyScore", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', team_id={self.team_id})>"


class WeeklyScore(Base):
    """Weekly score model representing a player's score for a specific week."""
    __tablename__ = 'weekly_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    league_id = Column(Integer, ForeignKey('leagues.id'), nullable=False)
    week_number = Column(Integer, nullable=False)
    date = Column(DateTime, nullable=False)
    gross_score = Column(Integer, nullable=False)
    handicap = Column(Float, nullable=False)
    strokes_given = Column(Float, nullable=False)
    net_score = Column(Float, nullable=False)
    num_holes = Column(Integer, nullable=False)  # 9 or 18
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship("Player", back_populates="weekly_scores")
    league = relationship("League", back_populates="weekly_scores")
    
    def __repr__(self):
        return f"<WeeklyScore(id={self.id}, player_id={self.player_id}, week={self.week_number}, net_score={self.net_score})>"


class OcrCorrection(Base):
    """OCR correction model for storing learned text corrections."""
    __tablename__ = 'ocr_corrections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ocr_text = Column(String(200), nullable=False, index=True)
    corrected_text = Column(String(200), nullable=False)
    pattern_type = Column(String(50), nullable=False, default='name')  # 'name', 'score', 'handicap'
    frequency = Column(Integer, nullable=False, default=1)  # Number of times this correction has been used
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<OcrCorrection(id={self.id}, '{self.ocr_text}' -> '{self.corrected_text}', freq={self.frequency})>"

