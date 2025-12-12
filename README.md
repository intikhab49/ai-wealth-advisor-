Wealth AI Assistant

A smart financial assistant that analyzes portfolios, assesses risks, and suggests investment strategies using LangChain and Microsoft Fabric. Features include risk metrics (VaR, Sharpe ratio), diversification analysis, and AI-powered recommendations. Built with Python, Flask, and ChromaDB for conversational memory. Provides real-time portfolio insights and data-driven investment guidance.

## Features

- **Portfolio Risk Assessment**: Calculate VaR, Sharpe ratio, volatility, max drawdown
- **Diversification Analysis**: Assess sector, geography, asset class diversification
- **Investment Strategy**: AI-powered personalized strategy recommendations
- **Conversational Memory**: ChromaDB vector store for context-aware recommendations
- **Modern Chat UI**: Real-time chatbot interface with visualizations

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the application
python api/app.py
```

Open `http://localhost:5000` in your browser.

## Environment Variables

```
OPENAI_API_KEY=your_openai_key
AZURE_TENANT_ID=your_tenant_id (optional, for MS Fabric)
AZURE_CLIENT_ID=your_client_id (optional)
```

## Project Structure

```
wealth_advisor/
├── config/settings.py      # Configuration
├── tools/                  # Financial analysis tools
├── agent/                  # LangChain agent
├── data/                   # Data layer
├── api/                    # Flask backend
└── ui/                     # Chat interface
```
