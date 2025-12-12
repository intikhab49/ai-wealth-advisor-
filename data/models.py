"""Data models for wealth management."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Holding:
    """Individual investment holding."""
    symbol: str
    name: str
    value: float
    asset_class: str
    sector: Optional[str] = None
    geography: Optional[str] = None
    shares: Optional[float] = None
    cost_basis: Optional[float] = None
    purchase_date: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "value": self.value,
            "asset_class": self.asset_class,
            "sector": self.sector,
            "geography": self.geography,
            "shares": self.shares,
            "cost_basis": self.cost_basis,
            "purchase_date": self.purchase_date,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Holding":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Portfolio:
    """User's investment portfolio."""
    user_id: str
    holdings: List[Holding] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def total_value(self) -> float:
        return sum(h.value for h in self.holdings)
    
    @property
    def asset_allocation(self) -> Dict[str, float]:
        if not self.holdings or self.total_value == 0:
            return {}
        
        allocation = {}
        for h in self.holdings:
            allocation[h.asset_class] = allocation.get(h.asset_class, 0) + h.value
        
        return {k: v / self.total_value for k, v in allocation.items()}
    
    def add_holding(self, holding: Holding):
        self.holdings.append(holding)
        self.updated_at = datetime.now().isoformat()
    
    def remove_holding(self, symbol: str):
        self.holdings = [h for h in self.holdings if h.symbol != symbol]
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "holdings": [h.to_dict() for h in self.holdings],
            "total_value": self.total_value,
            "asset_allocation": self.asset_allocation,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Portfolio":
        holdings = [Holding.from_dict(h) for h in data.get("holdings", [])]
        return cls(
            user_id=data["user_id"],
            holdings=holdings,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


@dataclass
class UserPreferences:
    """User's financial preferences and profile."""
    user_id: str
    risk_tolerance: Optional[str] = None  # conservative, moderate, aggressive
    investment_goals: List[str] = field(default_factory=list)
    time_horizon_years: Optional[int] = None
    age: Optional[int] = None
    income_range: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "risk_tolerance": self.risk_tolerance,
            "investment_goals": self.investment_goals,
            "time_horizon_years": self.time_horizon_years,
            "age": self.age,
            "income_range": self.income_range,
        }
