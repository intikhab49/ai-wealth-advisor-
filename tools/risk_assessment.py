"""Portfolio risk evaluation tools."""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import numpy as np
from enum import Enum


class RiskLevel(str, Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class Asset:
    """Represents an investment asset."""
    symbol: str
    name: str
    value: float
    asset_class: str  # equity, bond, cash, real_estate, commodity, crypto
    sector: Optional[str] = None
    geography: Optional[str] = None
    annual_return: Optional[float] = None
    volatility: Optional[float] = None


@dataclass
class RiskMetrics:
    """Portfolio risk metrics."""
    total_value: float
    var_95: float  # Value at Risk at 95% confidence
    var_99: float  # Value at Risk at 99% confidence
    sharpe_ratio: float
    volatility: float
    max_drawdown: float
    beta: Optional[float] = None
    sortino_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_value": round(self.total_value, 2),
            "var_95": round(self.var_95, 2),
            "var_99": round(self.var_99, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "volatility": round(self.volatility * 100, 2),
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "beta": round(self.beta, 3) if self.beta else None,
            "sortino_ratio": round(self.sortino_ratio, 3) if self.sortino_ratio else None,
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        return f"""
📊 **Portfolio Risk Assessment**

💰 **Total Portfolio Value**: ${self.total_value:,.2f}

📉 **Risk Metrics**:
- Value at Risk (95%): ${self.var_95:,.2f} (daily potential loss)
- Value at Risk (99%): ${self.var_99:,.2f}
- Annual Volatility: {self.volatility * 100:.1f}%
- Maximum Drawdown: {self.max_drawdown * 100:.1f}%

📈 **Performance Metrics**:
- Sharpe Ratio: {self.sharpe_ratio:.2f} {"(Good)" if self.sharpe_ratio > 1 else "(Needs attention)"}
- Beta: {f'{self.beta:.2f}' if self.beta else 'N/A'}
"""


@dataclass
class RiskProfile:
    """User's risk profile based on questionnaire."""
    risk_level: RiskLevel
    score: int  # 0-100
    recommended_equity_allocation: float
    recommended_bond_allocation: float
    time_horizon_years: int
    notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_level": self.risk_level.value,
            "score": self.score,
            "recommended_allocations": {
                "equity": f"{self.recommended_equity_allocation * 100:.0f}%",
                "bonds": f"{self.recommended_bond_allocation * 100:.0f}%",
                "cash_alternatives": f"{(1 - self.recommended_equity_allocation - self.recommended_bond_allocation) * 100:.0f}%"
            },
            "time_horizon_years": self.time_horizon_years,
            "notes": self.notes
        }


def calculate_portfolio_risk(holdings: List[Dict[str, Any]], risk_free_rate: float = 0.04) -> RiskMetrics:
    """
    Calculate comprehensive risk metrics for a portfolio.
    
    Args:
        holdings: List of asset dictionaries with keys:
            - symbol, name, value, asset_class
            - annual_return (optional), volatility (optional)
        risk_free_rate: Annual risk-free rate (default 4%)
    
    Returns:
        RiskMetrics with VaR, Sharpe ratio, volatility, etc.
    """
    # Convert to Asset objects
    assets = []
    for h in holdings:
        assets.append(Asset(
            symbol=h.get("symbol", "UNKNOWN"),
            name=h.get("name", "Unknown Asset"),
            value=float(h.get("value", 0)),
            asset_class=h.get("asset_class", "equity"),
            sector=h.get("sector"),
            geography=h.get("geography"),
            annual_return=h.get("annual_return"),
            volatility=h.get("volatility"),
        ))
    
    if not assets:
        return RiskMetrics(
            total_value=0, var_95=0, var_99=0,
            sharpe_ratio=0, volatility=0, max_drawdown=0
        )
    
    total_value = sum(a.value for a in assets)
    weights = np.array([a.value / total_value for a in assets])
    
    # Default volatility by asset class if not provided
    default_volatility = {
        "equity": 0.20,
        "bond": 0.05,
        "cash": 0.01,
        "real_estate": 0.12,
        "commodity": 0.25,
        "crypto": 0.80,
    }
    
    default_returns = {
        "equity": 0.10,
        "bond": 0.04,
        "cash": 0.02,
        "real_estate": 0.08,
        "commodity": 0.05,
        "crypto": 0.15,
    }
    
    volatilities = np.array([
        a.volatility if a.volatility else default_volatility.get(a.asset_class, 0.15)
        for a in assets
    ])
    
    returns = np.array([
        a.annual_return if a.annual_return else default_returns.get(a.asset_class, 0.08)
        for a in assets
    ])
    
    # Portfolio statistics
    portfolio_return = np.sum(weights * returns)
    # Simplified portfolio volatility (assuming low correlation)
    portfolio_volatility = np.sqrt(np.sum((weights * volatilities) ** 2))
    
    # Daily volatility for VaR
    daily_volatility = portfolio_volatility / np.sqrt(252)
    
    # Value at Risk calculations
    var_95 = total_value * daily_volatility * 1.645
    var_99 = total_value * daily_volatility * 2.326
    
    # Sharpe Ratio
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
    
    # Estimated max drawdown (simplified)
    max_drawdown = portfolio_volatility * 2.5
    
    # Beta (assuming market volatility of 15%)
    market_volatility = 0.15
    beta = portfolio_volatility / market_volatility
    
    return RiskMetrics(
        total_value=total_value,
        var_95=var_95,
        var_99=var_99,
        sharpe_ratio=sharpe_ratio,
        volatility=portfolio_volatility,
        max_drawdown=min(max_drawdown, 0.6),  # Cap at 60%
        beta=beta,
    )


def assess_risk_tolerance(questionnaire: Dict[str, Any]) -> RiskProfile:
    """
    Evaluate user's risk tolerance based on questionnaire responses.
    
    Args:
        questionnaire: Dictionary with keys:
            - age: int
            - income: float (annual)
            - investment_experience: str (none, beginner, intermediate, advanced)
            - time_horizon: int (years)
            - loss_reaction: str (sell_all, sell_some, hold, buy_more)
            - goal: str (preservation, income, growth, aggressive_growth)
    
    Returns:
        RiskProfile with recommended allocations.
    """
    score = 50  # Start at moderate
    
    # Age factor (younger = higher risk tolerance)
    age = questionnaire.get("age", 40)
    if age < 30:
        score += 20
    elif age < 40:
        score += 10
    elif age > 55:
        score -= 15
    elif age > 65:
        score -= 25
    
    # Time horizon
    years = questionnaire.get("time_horizon", 10)
    if years > 20:
        score += 15
    elif years > 10:
        score += 5
    elif years < 5:
        score -= 20
    
    # Experience
    experience = questionnaire.get("investment_experience", "beginner")
    experience_scores = {"none": -15, "beginner": -5, "intermediate": 5, "advanced": 15}
    score += experience_scores.get(experience, 0)
    
    # Loss reaction
    loss_reaction = questionnaire.get("loss_reaction", "hold")
    reaction_scores = {"sell_all": -25, "sell_some": -10, "hold": 5, "buy_more": 20}
    score += reaction_scores.get(loss_reaction, 0)
    
    # Goal
    goal = questionnaire.get("goal", "growth")
    goal_scores = {"preservation": -20, "income": -10, "growth": 10, "aggressive_growth": 25}
    score += goal_scores.get(goal, 0)
    
    # Clamp score
    score = max(0, min(100, score))
    
    # Determine risk level and allocations
    if score < 25:
        risk_level = RiskLevel.CONSERVATIVE
        equity = 0.25
        bonds = 0.55
    elif score < 50:
        risk_level = RiskLevel.MODERATE
        equity = 0.50
        bonds = 0.35
    elif score < 75:
        risk_level = RiskLevel.AGGRESSIVE
        equity = 0.70
        bonds = 0.20
    else:
        risk_level = RiskLevel.VERY_AGGRESSIVE
        equity = 0.85
        bonds = 0.10
    
    return RiskProfile(
        risk_level=risk_level,
        score=score,
        recommended_equity_allocation=equity,
        recommended_bond_allocation=bonds,
        time_horizon_years=years,
        notes=f"Based on your profile, you are a {risk_level.value} investor with a {years}-year horizon."
    )


# Function to be used by LangChain tool
def calculate_portfolio_risk_tool(portfolio_json: str) -> str:
    """
    Calculate risk metrics for a portfolio. 
    Input should be a JSON string of holdings.
    """
    import json
    try:
        holdings = json.loads(portfolio_json)
        if not isinstance(holdings, list):
            holdings = [holdings]
        metrics = calculate_portfolio_risk(holdings)
        return metrics.summary()
    except Exception as e:
        return f"Error calculating risk: {str(e)}"


def assess_risk_tolerance_tool(questionnaire_json: str) -> str:
    """
    Assess user's risk tolerance based on questionnaire.
    Input should be a JSON string with age, income, experience, time_horizon, loss_reaction, goal.
    """
    import json
    try:
        questionnaire = json.loads(questionnaire_json)
        profile = assess_risk_tolerance(questionnaire)
        return f"""
🎯 **Risk Profile Assessment**

Risk Level: **{profile.risk_level.value.title()}**
Risk Score: {profile.score}/100

📊 **Recommended Asset Allocation**:
- Equities: {profile.recommended_equity_allocation * 100:.0f}%
- Bonds: {profile.recommended_bond_allocation * 100:.0f}%
- Cash/Alternatives: {(1 - profile.recommended_equity_allocation - profile.recommended_bond_allocation) * 100:.0f}%

📝 {profile.notes}
"""
    except Exception as e:
        return f"Error assessing risk tolerance: {str(e)}"
