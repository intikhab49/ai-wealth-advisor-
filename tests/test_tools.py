"""Tests for financial analysis tools."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.risk_assessment import (
    calculate_portfolio_risk,
    assess_risk_tolerance,
    calculate_portfolio_risk_tool,
    RiskLevel,
)
from tools.diversification import (
    analyze_diversification,
    suggest_rebalancing,
    analyze_diversification_tool,
)
from tools.strategy import design_strategy, design_strategy_tool


class TestRiskAssessment:
    """Tests for risk assessment functions."""
    
    def test_calculate_portfolio_risk_basic(self):
        """Test basic portfolio risk calculation."""
        holdings = [
            {"symbol": "VTI", "value": 50000, "asset_class": "equity"},
            {"symbol": "BND", "value": 30000, "asset_class": "bond"},
        ]
        
        result = calculate_portfolio_risk(holdings)
        
        assert result.total_value == 80000
        assert result.var_95 > 0
        assert result.sharpe_ratio != 0
        assert 0 < result.volatility < 1
    
    def test_calculate_portfolio_risk_empty(self):
        """Test with empty portfolio."""
        result = calculate_portfolio_risk([])
        
        assert result.total_value == 0
        assert result.var_95 == 0
    
    def test_assess_risk_tolerance_conservative(self):
        """Test conservative risk profile."""
        questionnaire = {
            "age": 65,
            "time_horizon": 3,
            "investment_experience": "none",
            "loss_reaction": "sell_all",
            "goal": "preservation"
        }
        
        result = assess_risk_tolerance(questionnaire)
        
        assert result.risk_level == RiskLevel.CONSERVATIVE
        assert result.recommended_equity_allocation <= 0.30
    
    def test_assess_risk_tolerance_aggressive(self):
        """Test aggressive risk profile."""
        questionnaire = {
            "age": 25,
            "time_horizon": 30,
            "investment_experience": "advanced",
            "loss_reaction": "buy_more",
            "goal": "aggressive_growth"
        }
        
        result = assess_risk_tolerance(questionnaire)
        
        assert result.risk_level in [RiskLevel.AGGRESSIVE, RiskLevel.VERY_AGGRESSIVE]
        assert result.recommended_equity_allocation >= 0.70
    
    def test_risk_tool_function(self):
        """Test the LangChain tool function."""
        portfolio_json = json.dumps([
            {"symbol": "AAPL", "value": 10000, "asset_class": "equity"}
        ])
        
        result = calculate_portfolio_risk_tool(portfolio_json)
        
        assert "Portfolio Risk Assessment" in result
        assert "Value at Risk" in result


class TestDiversification:
    """Tests for diversification analysis."""
    
    def test_analyze_diversification_well_diversified(self):
        """Test well-diversified portfolio."""
        holdings = [
            {"symbol": "VTI", "value": 40000, "asset_class": "equity", "sector": "diversified", "geography": "US"},
            {"symbol": "VXUS", "value": 20000, "asset_class": "equity", "sector": "diversified", "geography": "International"},
            {"symbol": "BND", "value": 25000, "asset_class": "bond", "sector": "bonds", "geography": "US"},
            {"symbol": "VNQ", "value": 10000, "asset_class": "real_estate", "sector": "reit", "geography": "US"},
            {"symbol": "GLD", "value": 5000, "asset_class": "commodity", "sector": "gold", "geography": "Global"},
        ]
        
        result = analyze_diversification(holdings)
        
        assert result.overall_score > 50
        assert result.asset_class_score > 40
        assert "LOW" in result.concentration_risk
    
    def test_analyze_diversification_concentrated(self):
        """Test concentrated portfolio."""
        holdings = [
            {"symbol": "AAPL", "value": 80000, "asset_class": "equity", "sector": "technology", "geography": "US"},
            {"symbol": "MSFT", "value": 20000, "asset_class": "equity", "sector": "technology", "geography": "US"},
        ]
        
        result = analyze_diversification(holdings)
        
        assert result.asset_class_score < 30  # Low diversification
        assert "HIGH" in result.concentration_risk or "MODERATE" in result.concentration_risk
    
    def test_suggest_rebalancing(self):
        """Test rebalancing suggestions."""
        # Portfolio heavy in equity
        holdings = [
            {"symbol": "VTI", "value": 90000, "asset_class": "equity"},
            {"symbol": "BND", "value": 10000, "asset_class": "bond"},
        ]
        
        trades = suggest_rebalancing(holdings)
        
        # Should suggest selling equity and buying bonds
        assert len(trades) > 0
        
        sell_equity = any(t.action == "sell" and "equity" in t.symbol.lower() for t in trades)
        buy_bond = any(t.action == "buy" and "bond" in t.symbol.lower() for t in trades)
        
        assert sell_equity or buy_bond


class TestStrategy:
    """Tests for investment strategy design."""
    
    def test_design_strategy_moderate(self):
        """Test moderate strategy design."""
        result = design_strategy(
            risk_profile="moderate",
            goals=[{"goal_type": "retirement", "target_amount": 1000000, "years": 25}],
            current_portfolio_value=50000,
            monthly_contribution=1000
        )
        
        assert result.strategy_name == "Balanced Growth"
        assert 0.4 <= result.recommended_allocation.get("equity", 0) <= 0.6
        assert result.monthly_savings_needed > 0
        assert len(result.action_items) > 0
    
    def test_design_strategy_conservative(self):
        """Test conservative strategy design."""
        result = design_strategy(
            risk_profile="conservative",
            goals=[{"goal_type": "income_generation", "target_amount": 500000, "years": 10}],
        )
        
        assert result.strategy_name == "Capital Preservation"
        assert result.recommended_allocation.get("bond", 0) >= 0.4
    
    def test_strategy_tool_function(self):
        """Test the LangChain tool function."""
        request_json = json.dumps({
            "risk_profile": "aggressive",
            "goals": [{"goal_type": "wealth_building", "target_amount": 2000000, "years": 30}],
            "monthly_contribution": 2000
        })
        
        result = design_strategy_tool(request_json)
        
        assert "Investment Strategy" in result
        assert "Recommended Asset Allocation" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
