from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, BigInteger
from sqlalchemy.sql import func
from app.db.database import Base


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, default=1)
    enabled = Column(Boolean, default=True)
    status = Column(String, default="healthy")
    cost_per_1k = Column(Float, default=0.0)
    region = Column(String, default="local")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    rate_limit = Column(Integer, default=60)
    monthly_budget = Column(Float, default=5.0)
    spent = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    ts = Column(BigInteger, nullable=False)
    key_name = Column(String, nullable=False)
    prompt = Column(String, nullable=False)
    provider = Column(String, default="-")
    model = Column(String, default="-")
    status = Column(Integer, nullable=False)
    cached = Column(Boolean, default=False)
    tokens = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    reply = Column(String, default="")