
import os
from typing import Dict
from dotenv import load_dotenv

import yfinance as yf
from fastapi import FastAPI
from pydantic import BaseModel

from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# Load environment variables from .env file
load_dotenv()

# --- Tool Definitions ---

@tool
def get_stock_price(ticker: str) -> dict:
    """Get current stock price and percentage change."""
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "ticker": ticker,
        "price": info.get("currentPrice", 0),
        "change_percent": info.get("regularMarketChangePercent", 0)
    }

@tool
def get_dividend_yield(ticker: str) -> float:
    """Get dividend yield percentage."""
    stock = yf.Ticker(ticker)
    return stock.info.get("dividendYield", 0) * 100

@tool
def get_market_cap(ticker: str) -> float:
    """Get market capitalization in billions."""
    stock = yf.Ticker(ticker)
    return stock.info.get("marketCap", 0) / 1e9

tools = [get_stock_price, get_dividend_yield, get_market_cap]

# --- Agent and Prompt Setup ---

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an experienced financial analyst with deep knowledge of:
    - Stock and financial market analysis
    - Investment valuation
    - Interpretation of financial indicators
    - Investment strategies

    You have access to tools that provide real-time data on:
    - Stock prices
    - Dividend yield
    - Market cap

    When responding:
    1. Use the available tools to get up-to-date data.
    2. Provide clear and objective analysis.
    3. Explain the numbers in terms investors can understand.
    4. When relevant, contextualize the data (e.g., compare with industry averages).
    5. Be precise with values and always mention the currency where applicable.

    For Brazilian stocks, use the correct ticker format (e.g., PETR4.SA, VALE3.SA).
    For US stocks, use only the symbol (e.g., AAPL, MSFT, GOOGL).

    Be professional, but approachable. Your goal is to help the user better understand their investments.
    """),
    ("human", "{messages}")
])

# --- LLM and Agent Executor ---

llm = ChatOpenAI(model="gpt-4o-mini")
agent_executor = create_react_agent(model=llm, tools=tools, prompt=prompt)

# --- FastAPI Application ---

app = FastAPI(
    title="Financial Analysis Agent",
    description="An API for answering financial questions using a LangChain agent.",
    version="1.0.0"
)

class Query(BaseModel):
    messages: str

@app.post("/ask", summary="Ask the financial agent a question")
def ask_agent(query: Query) -> Dict:
    """
    Receives a financial question, invokes the agent, and returns the analysis.
    """
    result = agent_executor.invoke({
        "messages": query.messages,
    })
    # The final response is in the last message of the output
    final_response = result["messages"][-1].content
    return {"answer": final_response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
