"""Investment strategy recommendation engine."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import json


class GoalType(str, Enum):
    """Investment goal types."""
    RETIREMENT = "retirement"
    EDUCATION = "education"
    HOME_PURCHASE = "home_purchase"
    WEALTH_BUILDING = "wealth_building"
    INCOME_GENERATION = "income_generation"
    EMERGENCY_FUND = "emergency_fund"


@dataclass
class Goal:
    """Investment goal definition."""
    goal_type: GoalType
    target_amount: float
    years_to_goal: int
    current_savings: float = 0
    monthly_contribution: float = 0


@dataclass
class InvestmentPlan:
    """Personalized investment strategy."""
    strategy_name: str
    risk_profile: str
    goals: List[Goal]
    recommended_allocation: Dict[str, float]
    monthly_savings_needed: float
    projected_value: float
    action_items: List[str]
    portfolio_suggestions: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "risk_profile": self.risk_profile,
            "recommended_allocation": self.recommended_allocation,
            "monthly_savings_needed": round(self.monthly_savings_needed, 2),
            "projected_value": round(self.projected_value, 2),
            "action_items": self.action_items,
            "portfolio_suggestions": self.portfolio_suggestions,
        }
    
    def summary(self) -> str:
        """Generate human-readable investment plan."""
        allocation_text = "\n".join([
            f"  • {asset.title()}: {pct*100:.0f}%"
            for asset, pct in sorted(self.recommended_allocation.items(), key=lambda x: -x[1])
        ])
        
        actions_text = "\n".join([f"  {i+1}. {action}" for i, action in enumerate(self.action_items[:5])])
        
        suggestions_text = "\n".join([
            f"  • **{s['name']}** ({s['ticker']}) - {s['allocation']*100:.0f}% allocation"
            for s in self.portfolio_suggestions[:5]
        ])
        
        return f"""
🎯 **Investment Strategy: {self.strategy_name}**

📋 **Profile**: {self.risk_profile}

📊 **Recommended Asset Allocation**:
{allocation_text}

💰 **Financial Projections**:
- Monthly Savings Needed: ${self.monthly_savings_needed:,.2f}
- Projected Portfolio Value: ${self.projected_value:,.2f}

📈 **Suggested Investments**:
{suggestions_text}

✅ **Action Items**:
{actions_text}
"""


# Strategy allocation templates
STRATEGY_TEMPLATES = {
    "conservative": {
        "name": "Capital Preservation",
        "allocation": {
            "equity": 0.25,
            "bond": 0.50,
            "cash": 0.15,
            "real_estate": 0.10,
        },
        "expected_return": 0.05,
    },
    "moderate": {
        "name": "Balanced Growth",
        "allocation": {
            "equity": 0.50,
            "bond": 0.30,
            "real_estate": 0.10,
            "cash": 0.05,
            "commodity": 0.05,
        },
        "expected_return": 0.07,
    },
    "aggressive": {
        "name": "Growth Focus",
        "allocation": {
            "equity": 0.70,
            "bond": 0.15,
            "real_estate": 0.10,
            "commodity": 0.05,
        },
        "expected_return": 0.09,
    },
    "very_aggressive": {
        "name": "Maximum Growth",
        "allocation": {
            "equity": 0.85,
            "bond": 0.05,
            "real_estate": 0.05,
            "crypto": 0.05,
        },
        "expected_return": 0.11,
    },
}

# Investment suggestions by asset class
INVESTMENT_SUGGESTIONS = {
    "equity": [
        {"name": "Total Stock Market ETF", "ticker": "VTI", "type": "US Equity"},
        {"name": "S&P 500 ETF", "ticker": "VOO", "type": "US Large Cap"},
        {"name": "International ETF", "ticker": "VXUS", "type": "International"},
        {"name": "Emerging Markets ETF", "ticker": "VWO", "type": "Emerging"},
    ],
    "bond": [
        {"name": "Total Bond Market ETF", "ticker": "BND", "type": "US Bonds"},
        {"name": "Treasury Bond ETF", "ticker": "TLT", "type": "Long Treasury"},
        {"name": "Corporate Bond ETF", "ticker": "LQD", "type": "Corporate"},
    ],
    "real_estate": [
        {"name": "Real Estate ETF", "ticker": "VNQ", "type": "REIT"},
        {"name": "International REIT", "ticker": "VNQI", "type": "Global REIT"},
    ],
    "commodity": [
        {"name": "Gold ETF", "ticker": "GLD", "type": "Gold"},
        {"name": "Commodity ETF", "ticker": "DJP", "type": "Diversified"},
    ],
    "cash": [
        {"name": "Money Market Fund", "ticker": "VMFXX", "type": "Cash"},
        {"name": "Short-Term Treasury", "ticker": "SHV", "type": "T-Bills"},
    ],
    "crypto": [
        {"name": "Bitcoin ETF", "ticker": "IBIT", "type": "Bitcoin"},
        {"name": "Ethereum ETF", "ticker": "ETHA", "type": "Ethereum"},
    ],
}


def design_strategy(
    risk_profile: str,
    goals: List[Dict[str, Any]],
    current_portfolio_value: float = 0,
    monthly_contribution: float = 0,
) -> InvestmentPlan:
    """
    Create personalized investment strategy based on risk profile and goals.
    
    Args:
        risk_profile: conservative, moderate, aggressive, or very_aggressive
        goals: List of goal dictionaries with goal_type, target_amount, years
        current_portfolio_value: Current investments value
        monthly_contribution: Planned monthly savings
    
    Returns:
        InvestmentPlan with recommended allocation and action items.
    """
    # Get strategy template
    risk_profile = risk_profile.lower().replace(" ", "_")
    if risk_profile not in STRATEGY_TEMPLATES:
        risk_profile = "moderate"
    
    template = STRATEGY_TEMPLATES[risk_profile]
    
    # Parse goals
    parsed_goals = []
    total_target = 0
    min_years = 30
    
    for g in goals:
        goal = Goal(
            goal_type=GoalType(g.get("goal_type", "wealth_building")),
            target_amount=float(g.get("target_amount", 100000)),
            years_to_goal=int(g.get("years", 10)),
            current_savings=float(g.get("current_savings", 0)),
            monthly_contribution=float(g.get("monthly_contribution", 0)),
        )
        parsed_goals.append(goal)
        total_target += goal.target_amount
        min_years = min(min_years, goal.years_to_goal)
    
    if not parsed_goals:
        # Default goal
        parsed_goals = [Goal(
            goal_type=GoalType.WEALTH_BUILDING,
            target_amount=500000,
            years_to_goal=20,
        )]
        total_target = 500000
        min_years = 20
    
    # Adjust allocation based on time horizon
    allocation = template["allocation"].copy()
    if min_years < 5:
        # Short horizon: more conservative
        allocation["equity"] = max(0.20, allocation.get("equity", 0) - 0.20)
        allocation["bond"] = allocation.get("bond", 0) + 0.15
        allocation["cash"] = allocation.get("cash", 0) + 0.05
    
    # Calculate required monthly savings
    expected_return = template["expected_return"]
    months = min_years * 12
    
    if months > 0 and expected_return > 0:
        # Future value calculation
        r = expected_return / 12
        if current_portfolio_value > 0:
            future_current = current_portfolio_value * ((1 + r) ** months)
        else:
            future_current = 0
        
        remaining = max(0, total_target - future_current)
        
        if r > 0:
            # PMT formula for required monthly savings
            monthly_needed = remaining * r / (((1 + r) ** months) - 1)
        else:
            monthly_needed = remaining / months
    else:
        monthly_needed = total_target / 240  # Default 20 years
    
    # Projected value with contributions
    projected = current_portfolio_value
    r = expected_return / 12
    contribution = max(monthly_contribution, monthly_needed)
    for _ in range(months):
        projected = projected * (1 + r) + contribution
    
    # Generate portfolio suggestions
    suggestions = []
    for asset_class, pct in allocation.items():
        if pct > 0 and asset_class in INVESTMENT_SUGGESTIONS:
            for inv in INVESTMENT_SUGGESTIONS[asset_class][:1]:  # Top suggestion per class
                suggestions.append({
                    **inv,
                    "allocation": pct,
                    "amount": projected * pct,
                })
    
    # Generate action items
    action_items = []
    
    if current_portfolio_value == 0:
        action_items.append("Open a brokerage account (Fidelity, Vanguard, or Schwab recommended)")
    
    action_items.append(f"Set up automatic monthly investment of ${contribution:,.0f}")
    
    if allocation.get("equity", 0) > 0.5:
        action_items.append("Consider tax-advantaged accounts (401k, IRA) for equity holdings")
    
    action_items.append("Review and rebalance portfolio quarterly")
    action_items.append("Increase contributions by 1-2% annually if possible")
    
    goal_types = [g.goal_type.value for g in parsed_goals]
    if "retirement" in goal_types:
        action_items.append("Maximize employer 401k match if available")
    if "emergency_fund" in goal_types:
        action_items.append("Keep 3-6 months expenses in high-yield savings")
    
    return InvestmentPlan(
        strategy_name=template["name"],
        risk_profile=risk_profile.replace("_", " ").title(),
        goals=parsed_goals,
        recommended_allocation=allocation,
        monthly_savings_needed=monthly_needed,
        projected_value=projected,
        action_items=action_items,
        portfolio_suggestions=suggestions,
    )


# LangChain tool function
def design_strategy_tool(strategy_request_json: str) -> str:
    """
    Design a personalized investment strategy.
    Input should be a JSON string with:
    - risk_profile: conservative, moderate, aggressive, or very_aggressive
    - goals: list of goals with goal_type, target_amount, years
    - current_portfolio_value (optional)
    - monthly_contribution (optional)
    """
    try:
        request = json.loads(strategy_request_json)
        plan = design_strategy(
            risk_profile=request.get("risk_profile", "moderate"),
            goals=request.get("goals", []),
            current_portfolio_value=float(request.get("current_portfolio_value", 0)),
            monthly_contribution=float(request.get("monthly_contribution", 0)),
        )
        return plan.summary()
    except Exception as e:
        return f"Error designing strategy: {str(e)}"
