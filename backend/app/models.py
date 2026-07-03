from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "Users"

    UserId = Column(Integer, primary_key=True, index=True)
    Username = Column(String(50), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    Role = Column(String(20), nullable=False, default="analyst")
    CreatedAt = Column(DateTime, server_default=func.now())


class Transaction(Base):
    __tablename__ = "Transactions"

    TransactionId = Column(Integer, primary_key=True, index=True)
    AccountId = Column(String(50), nullable=False)
    Amount = Column(DECIMAL(18, 2), nullable=False)
    Currency = Column(String(10), nullable=False)
    CountryCode = Column(String(5), nullable=False)
    TransactionType = Column(String(30), nullable=False)
    Timestamp = Column(DateTime, nullable=False)
    UploadedAt = Column(DateTime, server_default=func.now())
    UploadedBy = Column(Integer, ForeignKey("Users.UserId"))

class FraudScore(Base):
    __tablename__ = "FraudScores"

    ScoreId = Column(Integer, primary_key=True, index=True)
    TransactionId = Column(Integer, ForeignKey("Transactions.TransactionId"))
    FraudScore = Column(DECIMAL(5, 2), nullable=False)
    TopFeatures = Column(String(500))
    ScoredAt = Column(DateTime, server_default=func.now())


class AMLAlert(Base):
    __tablename__ = "AMLAlerts"

    AlertId = Column(Integer, primary_key=True, index=True)
    TransactionId = Column(Integer, ForeignKey("Transactions.TransactionId"))
    RuleTriggered = Column(String(50), nullable=False)
    Severity = Column(String(10), nullable=False)
    CreatedAt = Column(DateTime, server_default=func.now())


class SanctionedEntity(Base):
    __tablename__ = "SanctionedEntities"

    EntityId = Column(Integer, primary_key=True, index=True)
    Name = Column(String(350), nullable=False, index=True)
    CountryCode = Column(String(5))
    Program = Column(String(100))
    Source = Column(String(20), default="OFAC_SDN")