"""Asset diversification analysis tools."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json


@dataclass
class DiversificationScore:
    """Diversification analysis results."""
    overall_score: float  # 0-100
    sector_score: float
    geography_score: float
    asset_class_score: float
    concentration_risk: str
    recommendations: List[str]
    breakdown: Dict[str, Dict[str, float]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "sector_diversification": round(self.sector_score, 1),
            "geography_diversification": round(self.geography_score, 1),
            "asset_class_diversification": round(self.asset_class_score, 1),
            "concentration_risk": self.concentration_risk,
            "recommendations": self.recommendations,
            "breakdown": self.breakdown
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        score_emoji = "🟢" if self.overall_score >= 70 else "🟡" if self.overall_score >= 40 else "🔴"
        
        recommendations_text = "\n".join([f"• {r}" for r in self.recommendations[:5]])
        
        # Format breakdown
        breakdown_text = ""
        for category, allocations in self.breakdown.items():
            breakdown_text += f"\n**{category.title()}**:\n"
            for item, pct in sorted(allocations.items(), key=lambda x: -x[1])[:5]:
                breakdown_text += f"  - {item}: {pct:.1f}%\n"
        
        return f"""
{score_emoji} **Diversification Analysis**

📊 **Overall Score**: {self.overall_score:.0f}/100

**Category Scores**:
- Asset Class Diversification: {self.asset_class_score:.0f}/100
- Sector Diversification: {self.sector_score:.0f}/100
- Geographic Diversification: {self.geography_score:.0f}/100

⚠️ **Concentration Risk**: {self.concentration_risk}

📈 **Portfolio Breakdown**:
{breakdown_text}

💡 **Recommendations**:
{recommendations_text}
"""


@dataclass 
class Trade:
    """Recommended trade for rebalancing."""
    action: str  # buy, sell
    symbol: str
    name: str
    amount: float
    reason: str


def analyze_diversification(holdings: List[Dict[str, Any]]) -> DiversificationScore:
    """
    Assess portfolio diversification across sectors, geography, and asset classes.
    
    Args:
        holdings: List of asset dictionaries with:
            - symbol, name, value, asset_class
            - sector (optional), geography (optional)
    
    Returns:
        DiversificationScore with analysis and recommendations.
    """
    if not holdings:
        return DiversificationScore(
            overall_score=0, sector_score=0, geography_score=0,
            asset_class_score=0, concentration_risk="No holdings",
            recommendations=["Add investments to begin diversification"],
            breakdown={}
        )
    
    total_value = sum(float(h.get("value", 0)) for h in holdings)
    if total_value == 0:
        return DiversificationScore(
            overall_score=0, sector_score=0, geography_score=0,
            asset_class_score=0, concentration_risk="No value",
            recommendations=["Portfolio has no value"],
            breakdown={}
        )
    
    # Calculate allocations
    asset_class_alloc = defaultdict(float)
    sector_alloc = defaultdict(float)
    geography_alloc = defaultdict(float)
    
    for h in holdings:
        weight = float(h.get("value", 0)) / total_value * 100
        
        asset_class = h.get("asset_class", "unknown")
        asset_class_alloc[asset_class] += weight
        
        sector = h.get("sector", "unknown")
        sector_alloc[sector] += weight
        
        geography = h.get("geography", "unknown")
        geography_alloc[geography] += weight
    
    # Score calculations (using entropy-like measure)
    def calculate_diversity_score(allocations: Dict[str, float]) -> float:
        """Higher score = more diversified."""
        if len(allocations) <= 1:
            return 0
        
        values = list(allocations.values())
        max_weight = max(values)
        num_categories = len(values)
        
        # Penalize heavy concentration
        concentration_penalty = max(0, (max_weight - 40) * 1.5)
        
        # Bonus for more categories
        category_bonus = min(num_categories * 10, 30)
        
        # Base score from evenness
        ideal_weight = 100 / num_categories
        deviation = sum(abs(v - ideal_weight) for v in values) / num_categories
        evenness_score = max(0, 50 - deviation)
        
        return min(100, max(0, evenness_score + category_bonus - concentration_penalty))
    
    asset_class_score = calculate_diversity_score(dict(asset_class_alloc))
    sector_score = calculate_diversity_score(dict(sector_alloc))
    geography_score = calculate_diversity_score(dict(geography_alloc))
    
    # Overall score (weighted average)
    overall_score = (asset_class_score * 0.4 + sector_score * 0.35 + geography_score * 0.25)
    
    # Concentration risk assessment
    max_holding_weight = max(float(h.get("value", 0)) / total_value * 100 for h in holdings)
    max_sector_weight = max(sector_alloc.values()) if sector_alloc else 0
    
    if max_holding_weight > 50 or max_sector_weight > 60:
        concentration_risk = "HIGH - Significant concentration in single positions"
    elif max_holding_weight > 25 or max_sector_weight > 40:
        concentration_risk = "MODERATE - Some concentration present"
    else:
        concentration_risk = "LOW - Well diversified"
    
    # Generate recommendations
    recommendations = []
    
    if len(asset_class_alloc) < 3:
        recommendations.append("Consider adding more asset classes (bonds, real estate, commodities)")
    
    if asset_class_alloc.get("equity", 0) > 80:
        recommendations.append("High equity allocation - consider adding bonds for stability")
    
    if asset_class_alloc.get("cash", 0) > 30:
        recommendations.append("High cash position - consider deploying to growth assets")
    
    if geography_alloc.get("unknown", 0) > 50 or len(geography_alloc) < 2:
        recommendations.append("Add international exposure for geographic diversification")
    
    if max_holding_weight > 20:
        recommendations.append("Consider reducing largest positions to below 20% each")
    
    if sector_alloc.get("technology", 0) > 40:
        recommendations.append("Heavy tech concentration - diversify into other sectors")
    
    if not recommendations:
        recommendations.append("Portfolio is well diversified - maintain current allocation")
    
    return DiversificationScore(
        overall_score=overall_score,
        sector_score=sector_score,
        geography_score=geography_score,
        asset_class_score=asset_class_score,
        concentration_risk=concentration_risk,
        recommendations=recommendations,
        breakdown={
            "asset_class": dict(asset_class_alloc),
            "sector": dict(sector_alloc),
            "geography": dict(geography_alloc),
        }
    )


def suggest_rebalancing(
    current_holdings: List[Dict[str, Any]],
    target_allocation: Optional[Dict[str, float]] = None
) -> List[Trade]:
    """
    Generate rebalancing recommendations to reach target allocation.
    
    Args:
        current_holdings: Current portfolio holdings
        target_allocation: Target asset class allocation (default: balanced)
    
    Returns:
        List of Trade recommendations
    """
    if target_allocation is None:
        # Default balanced allocation
        target_allocation = {
            "equity": 0.60,
            "bond": 0.25,
            "cash": 0.05,
            "real_estate": 0.05,
            "commodity": 0.05,
        }
    
    total_value = sum(float(h.get("value", 0)) for h in current_holdings)
    if total_value == 0:
        return []
    
    # Current allocation
    current_alloc = defaultdict(float)
    for h in current_holdings:
        asset_class = h.get("asset_class", "unknown")
        current_alloc[asset_class] += float(h.get("value", 0)) / total_value
    
    trades = []
    
    for asset_class, target_pct in target_allocation.items():
        current_pct = current_alloc.get(asset_class, 0)
        diff = target_pct - current_pct
        
        if abs(diff) < 0.02:  # Less than 2% difference, skip
            continue
        
        amount = abs(diff * total_value)
        
        if diff > 0:
            trades.append(Trade(
                action="buy",
                symbol=asset_class.upper(),
                name=f"{asset_class.title()} ETF",
                amount=amount,
                reason=f"Increase {asset_class} allocation from {current_pct*100:.1f}% to {target_pct*100:.1f}%"
            ))
        else:
            trades.append(Trade(
                action="sell",
                symbol=asset_class.upper(),
                name=f"{asset_class.title()} holdings",
                amount=amount,
                reason=f"Reduce {asset_class} allocation from {current_pct*100:.1f}% to {target_pct*100:.1f}%"
            ))
    
    return trades


# LangChain tool functions
def analyze_diversification_tool(portfolio_json: str) -> str:
    """
    Analyze portfolio diversification.
    Input should be a JSON string of holdings with symbol, value, asset_class, sector, geography.
    """
    try:
        holdings = json.loads(portfolio_json)
        if not isinstance(holdings, list):
            holdings = [holdings]
        score = analyze_diversification(holdings)
        return score.summary()
    except Exception as e:
        return f"Error analyzing diversification: {str(e)}"


def suggest_rebalancing_tool(portfolio_json: str) -> str:
    """
    Suggest rebalancing trades for a portfolio.
    Input should be a JSON string of holdings.
    """
    try:
        holdings = json.loads(portfolio_json)
        if not isinstance(holdings, list):
            holdings = [holdings]
        trades = suggest_rebalancing(holdings)
        
        if not trades:
            return "✅ Portfolio is well-balanced. No rebalancing needed."
        
        result = "📊 **Rebalancing Recommendations**\n\n"
        for trade in trades:
            emoji = "🟢" if trade.action == "buy" else "🔴"
            result += f"{emoji} **{trade.action.upper()}** ${trade.amount:,.2f} of {trade.name}\n"
            result += f"   Reason: {trade.reason}\n\n"
        
        return result
    except Exception as e:
        return f"Error generating rebalancing suggestions: {str(e)}"
