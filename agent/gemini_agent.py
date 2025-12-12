"""Gemini and Demo agents - No LangChain dependencies."""
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.prompts import SYSTEM_PROMPT
from agent.memory import FinancialMemory
from tools.risk_assessment import calculate_portfolio_risk_tool, assess_risk_tolerance_tool
from tools.diversification import analyze_diversification_tool, suggest_rebalancing_tool
from tools.strategy import design_strategy_tool


class GeminiWealthAdvisorAgent:
    """
    Wealth advisor agent using Google Gemini or OpenRouter.
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.memory = FinancialMemory(user_id=user_id)
        
        # Import settings
        from config.settings import settings
        
        self.client = None
        
        # Initialize client based on settings
        if settings.primary_model == "openrouter":
            try:
                from ai.openrouter_client import OpenRouterClient
                self.client = OpenRouterClient()
            except ImportError:
                print("Failed to import OpenRouterClient")
        elif settings.primary_model == "gemini":
            try:
                from ai.gemini_client import GeminiClient
                self.client = GeminiClient()
            except ImportError:
                print("Failed to import GeminiClient")
            
        # Fallback if specific client failed but we might have defaults
        if not self.client:
             # Try Gemini as fallback default if configured
             if os.getenv("GOOGLE_API_KEY"):
                 try:
                    from ai.gemini_client import GeminiClient
                    self.client = GeminiClient()
                 except: pass
        
        # Tool mapping
        self.tools = {
            "calculate_portfolio_risk": calculate_portfolio_risk_tool,
            "assess_risk_tolerance": assess_risk_tolerance_tool,
            "analyze_diversification": analyze_diversification_tool,
            "suggest_rebalancing": suggest_rebalancing_tool,
            "design_investment_strategy": design_strategy_tool,
        }
    
    def chat(self, user_input: str) -> str:
        """Process user input using Gemini AI."""
        import json
        
        self.memory.add_message("user", user_input)
        
        # If Gemini not available, fall back to demo mode
        if not self.client or not self.client.is_available:
            return self._demo_response(user_input)
        
        # Build system prompt
        system_prompt = """You are WealthAdvisor, an expert AI financial assistant.

You have these tools available:
1. calculate_portfolio_risk - Analyze portfolio VaR, Sharpe ratio, volatility
2. assess_risk_tolerance - Evaluate user's investor profile
3. analyze_diversification - Check portfolio diversification
4. suggest_rebalancing - Recommend trades to rebalance
5. design_investment_strategy - Create personalized investment plans

When you need to use a tool, respond with:
TOOL: <tool_name>
INPUT: <json_input>

Be helpful, professional, and provide actionable advice."""

        # Get preferences context
        preferences = self.memory.get_preferences()
        if preferences:
            pref_str = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
            user_input = f"[User profile: {pref_str}]\n\n{user_input}"
        
        try:
            response = self.client.generate_with_tools(
                user_input, 
                self.tools, 
                system_prompt
            )
        except Exception as e:
            response = f"Error: {str(e)}"
        
        self.memory.add_message("assistant", response)
        return response
    
    def _demo_response(self, user_input: str) -> str:
        """Fallback demo response when Gemini is not configured."""
        import json
        user_lower = user_input.lower()
        
        if "risk" in user_lower and ("assess" in user_lower or "tolerance" in user_lower):
            return assess_risk_tolerance_tool(json.dumps({
                "age": 35, "time_horizon": 20, 
                "loss_reaction": "hold", "goal": "growth"
            }))
        elif "diversif" in user_lower:
            return analyze_diversification_tool(json.dumps([
                {"symbol": "VTI", "value": 50000, "asset_class": "equity", "sector": "diversified", "geography": "US"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond", "sector": "bonds", "geography": "US"},
            ]))
        elif "strateg" in user_lower:
            return design_strategy_tool(json.dumps({
                "risk_profile": "moderate",
                "goals": [{"goal_type": "retirement", "target_amount": 1000000, "years": 25}],
            }))
        elif "rebalanc" in user_lower:
            return suggest_rebalancing_tool(json.dumps([
                {"symbol": "VTI", "value": 60000, "asset_class": "equity"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond"},
            ]))
        elif "portfolio" in user_lower and "risk" in user_lower:
            return calculate_portfolio_risk_tool(json.dumps([
                {"symbol": "VTI", "value": 50000, "asset_class": "equity"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond"},
            ]))
        else:
            return """👋 Hello! I'm your Wealth Management AI Assistant.

⚠️ **Gemini API not configured.** To enable full AI chat:
1. Get free API key at: https://aistudio.google.com/apikey
2. Add to .env: GOOGLE_API_KEY=your_key_here

I can still help with these commands:
• "Assess my risk tolerance"
• "Analyze my portfolio diversification"
• "Design an investment strategy"
• "Suggest rebalancing for my portfolio"
• "What's the risk level of my portfolio?"
"""
    
    def update_preferences(self, preferences: Dict[str, Any]):
        self.memory.save_preferences(preferences)
    
    def update_portfolio(self, portfolio: Dict[str, Any]):
        self.memory.save_portfolio(portfolio)
    
    def get_memory_summary(self) -> str:
        return self.memory.get_memory_summary()
    
    def clear_conversation(self):
        self.memory.clear_history()


class DemoWealthAdvisorAgent:
    """Demo agent that works without any API key."""
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.memory = FinancialMemory(user_id=user_id)
    
    def chat(self, user_input: str) -> str:
        """Process input using tools directly (no LLM)."""
        import json
        user_lower = user_input.lower()
        
        self.memory.add_message("user", user_input)
        
        # Simple keyword matching for demo
        if "risk" in user_lower and ("assess" in user_lower or "tolerance" in user_lower):
            response = assess_risk_tolerance_tool(json.dumps({
                "age": 35, "time_horizon": 20, 
                "loss_reaction": "hold", "goal": "growth"
            }))
        elif "diversif" in user_lower:
            response = analyze_diversification_tool(json.dumps([
                {"symbol": "VTI", "value": 50000, "asset_class": "equity", "sector": "diversified", "geography": "US"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond", "sector": "bonds", "geography": "US"},
                {"symbol": "AAPL", "value": 15000, "asset_class": "equity", "sector": "technology", "geography": "US"},
            ]))
        elif "strateg" in user_lower:
            response = design_strategy_tool(json.dumps({
                "risk_profile": "moderate",
                "goals": [{"goal_type": "retirement", "target_amount": 1000000, "years": 25}],
                "current_portfolio_value": 50000,
                "monthly_contribution": 1000
            }))
        elif "rebalanc" in user_lower:
            response = suggest_rebalancing_tool(json.dumps([
                {"symbol": "VTI", "value": 60000, "asset_class": "equity"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond"},
            ]))
        elif "portfolio" in user_lower and "risk" in user_lower:
            response = calculate_portfolio_risk_tool(json.dumps([
                {"symbol": "VTI", "value": 50000, "asset_class": "equity"},
                {"symbol": "BND", "value": 20000, "asset_class": "bond"},
            ]))
        else:
            response = """👋 Hello! I'm your Wealth Management AI Assistant.

I can help you with:
• **Portfolio Risk Assessment** - Analyze your portfolio's risk metrics
• **Risk Tolerance Assessment** - Determine your investor profile
• **Diversification Analysis** - Check if your portfolio is well-diversified
• **Investment Strategy** - Get personalized investment recommendations
• **Rebalancing** - Get suggestions to rebalance your portfolio

Try asking me:
- "Assess my risk tolerance"
- "Analyze my portfolio diversification"
- "Design an investment strategy for retirement"
- "Suggest rebalancing for my portfolio"
- "What's the risk level of my portfolio?"
"""
        
        self.memory.add_message("assistant", response)
        return response
    
    def update_preferences(self, preferences: Dict[str, Any]):
        self.memory.save_preferences(preferences)
    
    def update_portfolio(self, portfolio: Dict[str, Any]):
        self.memory.save_portfolio(portfolio)
    
    def get_memory_summary(self) -> str:
        return self.memory.get_memory_summary()
    
    def clear_conversation(self):
        self.memory.clear_history()
