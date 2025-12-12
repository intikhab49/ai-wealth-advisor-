"""LangChain agent configuration and execution chains."""
import os
import sys
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Lazy imports for LangChain (only load when needed)
# This prevents import errors when using Gemini instead of OpenAI
_langchain_loaded = False

def _load_langchain():
    """Load LangChain modules on demand."""
    global _langchain_loaded
    if _langchain_loaded:
        return
    try:
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain_openai import ChatOpenAI
        from langchain.tools import Tool
        from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain.schema import SystemMessage, HumanMessage, AIMessage
        globals()['AgentExecutor'] = AgentExecutor
        globals()['create_openai_tools_agent'] = create_openai_tools_agent
        globals()['ChatOpenAI'] = ChatOpenAI
        globals()['Tool'] = Tool
        globals()['ChatPromptTemplate'] = ChatPromptTemplate
        globals()['MessagesPlaceholder'] = MessagesPlaceholder
        globals()['SystemMessage'] = SystemMessage
        globals()['HumanMessage'] = HumanMessage
        globals()['AIMessage'] = AIMessage
        _langchain_loaded = True
    except ImportError as e:
        print(f"⚠️ LangChain not available: {e}")
        _langchain_loaded = False

from agent.prompts import SYSTEM_PROMPT
from agent.memory import FinancialMemory
from tools.risk_assessment import calculate_portfolio_risk_tool, assess_risk_tolerance_tool
from tools.diversification import analyze_diversification_tool, suggest_rebalancing_tool
from tools.strategy import design_strategy_tool
from config.settings import settings


class WealthAdvisorAgent:
    """
    Main agent class that orchestrates financial analysis tools.
    """
    
    def __init__(self, user_id: str = "default"):
        """
        Initialize the wealth advisor agent.
        
        Args:
            user_id: Unique identifier for conversation memory
        """
        # Load LangChain modules first
        _load_langchain()
        
        self.user_id = user_id
        self.memory = FinancialMemory(user_id=user_id)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create agent
        self.agent_executor = self._create_agent()
    
    def _create_tools(self) -> List[Any]:
        """Create LangChain tools from financial functions."""
        tools = [
            Tool(
                name="calculate_portfolio_risk",
                func=calculate_portfolio_risk_tool,
                description="""Calculate risk metrics for a portfolio including VaR, Sharpe ratio, and volatility.
                Input should be a JSON string array of holdings, each with: symbol, name, value, asset_class.
                Optional fields: sector, geography, annual_return, volatility.
                Example: '[{"symbol": "VTI", "name": "Total Stock ETF", "value": 50000, "asset_class": "equity"}]'"""
            ),
            Tool(
                name="assess_risk_tolerance",
                func=assess_risk_tolerance_tool,
                description="""Assess user's risk tolerance based on questionnaire responses.
                Input should be a JSON string with: age, income, investment_experience (none/beginner/intermediate/advanced),
                time_horizon (years), loss_reaction (sell_all/sell_some/hold/buy_more), goal (preservation/income/growth/aggressive_growth).
                Example: '{"age": 35, "time_horizon": 20, "loss_reaction": "hold", "goal": "growth"}'"""
            ),
            Tool(
                name="analyze_diversification",
                func=analyze_diversification_tool,
                description="""Analyze portfolio diversification across asset classes, sectors, and geographies.
                Input should be a JSON string array of holdings with: symbol, value, asset_class, sector, geography.
                Example: '[{"symbol": "AAPL", "value": 10000, "asset_class": "equity", "sector": "technology", "geography": "US"}]'"""
            ),
            Tool(
                name="suggest_rebalancing",
                func=suggest_rebalancing_tool,
                description="""Suggest trades to rebalance portfolio to target allocation.
                Input should be a JSON string array of current holdings with symbol, value, asset_class.
                Returns recommended buy/sell trades."""
            ),
            Tool(
                name="design_investment_strategy",
                func=design_strategy_tool,
                description="""Design a personalized investment strategy based on risk profile and goals.
                Input should be a JSON string with: risk_profile (conservative/moderate/aggressive/very_aggressive),
                goals (array with goal_type, target_amount, years), current_portfolio_value, monthly_contribution.
                Example: '{"risk_profile": "moderate", "goals": [{"goal_type": "retirement", "target_amount": 1000000, "years": 25}]}'"""
            ),
        ]
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )
    
    def _get_chat_history(self) -> List:
        """Convert memory to LangChain message format."""
        messages = []
        for msg in self.memory.get_recent_messages(limit=10):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        return messages
    
    def chat(self, user_input: str) -> str:
        """
        Process user input and return agent response.
        
        Args:
            user_input: User's message/query
        
        Returns:
            Agent's response string
        """
        # Add user message to memory
        self.memory.add_message("user", user_input)
        
        # Get relevant context from memory
        context = self.memory.get_context_for_query(user_input)
        
        # Enhance input with context if available
        enhanced_input = user_input
        preferences = self.memory.get_preferences()
        if preferences:
            pref_str = ", ".join([f"{k}: {v}" for k, v in preferences.items()])
            enhanced_input = f"[User profile: {pref_str}]\n\n{user_input}"
        
        try:
            # Run agent
            result = self.agent_executor.invoke({
                "input": enhanced_input,
                "chat_history": self._get_chat_history(),
            })
            
            response = result.get("output", "I apologize, I couldn't process that request.")
            
        except Exception as e:
            response = f"I encountered an error: {str(e)}. Please try rephrasing your question."
        
        # Add response to memory
        self.memory.add_message("assistant", response)
        
        return response
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user's financial preferences."""
        self.memory.save_preferences(preferences)
    
    def update_portfolio(self, portfolio: Dict[str, Any]):
        """Update user's portfolio data."""
        self.memory.save_portfolio(portfolio)
    
    def get_memory_summary(self) -> str:
        """Get summary of stored user data."""
        return self.memory.get_memory_summary()
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.memory.clear_history()


def create_wealth_agent(user_id: str = "default") -> WealthAdvisorAgent:
    """
    Factory function to create a wealth advisor agent.
    
    Args:
        user_id: Unique identifier for the user
    
    Returns:
        Configured WealthAdvisorAgent instance
    """
    return WealthAdvisorAgent(user_id=user_id)


# Simple demo mode without OpenAI (for testing)
class DemoWealthAdvisorAgent:
    """Demo agent that works without OpenAI API key."""
    
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
            # Extract or use default questionnaire
            response = assess_risk_tolerance_tool(json.dumps({
                "age": 35, "time_horizon": 20, 
                "loss_reaction": "hold", "goal": "growth"
            }))
        elif "diversif" in user_lower:
            # Demo portfolio
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

Try asking me:
- "Assess my risk tolerance"
- "Analyze my portfolio diversification"
- "Design an investment strategy for retirement"
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


# Gemini-powered agent (FREE!)
class GeminiWealthAdvisorAgent:
    """
    Wealth advisor agent using Google Gemini (FREE tier).
    Get API key at: https://aistudio.google.com/apikey
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.memory = FinancialMemory(user_id=user_id)
        
        # Import Gemini client
        try:
            from ai.gemini_client import GeminiClient
            self.gemini = GeminiClient()
        except ImportError:
            self.gemini = None
        
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
        if not self.gemini or not self.gemini.is_available:
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
            response = self.gemini.generate_with_tools(
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
        else:
            return """👋 Hello! I'm your Wealth Management AI Assistant.

⚠️ **Gemini API not configured.** To enable full AI chat:
1. Get free API key at: https://aistudio.google.com/apikey
2. Add to .env: GOOGLE_API_KEY=your_key_here
3. Run: pip install google-generativeai

I can still help with:
• "Assess my risk tolerance"
• "Analyze my portfolio diversification"
• "Design an investment strategy"
"""
    
    def update_preferences(self, preferences: Dict[str, Any]):
        self.memory.save_preferences(preferences)
    
    def update_portfolio(self, portfolio: Dict[str, Any]):
        self.memory.save_portfolio(portfolio)
    
    def get_memory_summary(self) -> str:
        return self.memory.get_memory_summary()
    
    def clear_conversation(self):
        self.memory.clear_history()
