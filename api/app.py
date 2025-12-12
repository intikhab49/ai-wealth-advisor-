"""Flask API for Wealth Management Chatbot."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, Any
import json

from config.settings import settings


app = Flask(__name__, static_folder='../ui', static_url_path='')
CORS(app)

# Store agent instances per user session
agents: Dict[str, Any] = {}


def get_agent(user_id: str):
    """Get or create agent for user."""
    if user_id not in agents:
        # Check which model to use
        if settings.primary_model == "openrouter" or (settings.google_api_key and settings.primary_model == "gemini"):
            # Use Generic Agent (Gemini/OpenRouter) - from separate file with no LangChain deps
            from agent.gemini_agent import GeminiWealthAdvisorAgent
            agents[user_id] = GeminiWealthAdvisorAgent(user_id)
        elif settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            # Use OpenAI - from chains.py (has LangChain deps)
            from agent.chains import create_wealth_agent
            agents[user_id] = create_wealth_agent(user_id)
        else:
            # Use demo agent (works without any API key)
            from agent.gemini_agent import DemoWealthAdvisorAgent
            agents[user_id] = DemoWealthAdvisorAgent(user_id)
    return agents[user_id]


@app.route('/')
def index():
    """Serve the chatbot UI."""
    return send_from_directory('../ui', 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Wealth Management AI Chatbot",
        "openai_configured": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here")
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process user message through the AI agent.
    
    Request body:
        {
            "message": "User's message",
            "user_id": "optional user identifier"
        }
    
    Response:
        {
            "response": "Agent's response",
            "user_id": "User identifier"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        user_message = data['message']
        user_id = data.get('user_id', 'default')
        
        # Get agent and process message
        agent = get_agent(user_id)
        response = agent.chat(user_message)
        
        return jsonify({
            "response": response,
            "user_id": user_id
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/risk-assessment', methods=['POST'])
def risk_assessment():
    """
    Direct portfolio risk assessment endpoint.
    
    Request body:
        {
            "portfolio": [
                {"symbol": "VTI", "value": 50000, "asset_class": "equity"},
                ...
            ]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'portfolio' not in data:
            return jsonify({"error": "Portfolio data is required"}), 400
        
        from tools.risk_assessment import calculate_portfolio_risk
        
        holdings = data['portfolio']
        result = calculate_portfolio_risk(holdings)
        
        return jsonify({
            "success": True,
            "metrics": result.to_dict(),
            "summary": result.summary()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/diversification', methods=['POST'])
def diversification_analysis():
    """
    Direct diversification analysis endpoint.
    """
    try:
        data = request.get_json()
        
        if not data or 'portfolio' not in data:
            return jsonify({"error": "Portfolio data is required"}), 400
        
        from tools.diversification import analyze_diversification
        
        holdings = data['portfolio']
        result = analyze_diversification(holdings)
        
        return jsonify({
            "success": True,
            "analysis": result.to_dict(),
            "summary": result.summary()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/strategy', methods=['POST'])
def investment_strategy():
    """
    Direct investment strategy endpoint.
    """
    try:
        data = request.get_json()
        
        from tools.strategy import design_strategy
        
        result = design_strategy(
            risk_profile=data.get('risk_profile', 'moderate'),
            goals=data.get('goals', []),
            current_portfolio_value=float(data.get('current_portfolio_value', 0)),
            monthly_contribution=float(data.get('monthly_contribution', 0))
        )
        
        return jsonify({
            "success": True,
            "strategy": result.to_dict(),
            "summary": result.summary()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/preferences', methods=['POST'])
def update_preferences():
    """
    Update user financial preferences.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        preferences = data.get('preferences', {})
        
        agent = get_agent(user_id)
        agent.update_preferences(preferences)
        
        return jsonify({
            "success": True,
            "message": "Preferences updated"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio', methods=['POST'])
def update_portfolio():
    """
    Update user's portfolio data.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        portfolio = data.get('portfolio', {})
        
        agent = get_agent(user_id)
        agent.update_portfolio(portfolio)
        
        return jsonify({
            "success": True,
            "message": "Portfolio updated"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory', methods=['GET'])
def get_memory():
    """
    Get user's stored data summary.
    """
    try:
        user_id = request.args.get('user_id', 'default')
        agent = get_agent(user_id)
        summary = agent.get_memory_summary()
        
        return jsonify({
            "success": True,
            "summary": summary
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/clear', methods=['POST'])
def clear_conversation():
    """
    Clear conversation history.
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default')
        
        if user_id in agents:
            agents[user_id].clear_conversation()
        
        return jsonify({
            "success": True,
            "message": "Conversation cleared"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏦 Wealth Management AI Chatbot")
    print("="*60)
    print(f"📍 Server running at: http://localhost:{settings.flask_port}")
    print(f"🤖 OpenAI configured: {bool(settings.openai_api_key and settings.openai_api_key != 'your_openai_api_key_here')}")
    print("="*60 + "\n")
    
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug
    )
