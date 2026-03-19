"""
Trading System Agents Module

This module implements an Agency-Agents architecture for the trading system,
providing a unified, message-based communication framework for all system
components.

Core Components:
- BaseAgent: Abstract base class for all agents
- AgentMessageBus: Message routing and communication
- AgentRegistry: Agent registration and health monitoring
- TradingAgency: Main controller for the agent system

Example:
    >>> from agents import TradingAgency
    >>> from agents.strategy_agent import StrategyAgent
    >>> from agents.market_agent import MarketDataAgent
    >>>
    >>> agency = TradingAgency()
    >>> agency.register_agent(StrategyAgent(strategy_engine))
    >>> agency.register_agent(MarketDataAgent(market_fetcher))
    >>> await agency.start()
"""

from .base import BaseAgent, AgentStatus, AgentMessage
from .message_bus import AgentMessageBus
from .registry import AgentRegistry, AgentInfo
from .agency import TradingAgency
from .messages import MessageType, create_message

__all__ = [
    # Core components
    "BaseAgent",
    "AgentStatus",
    "AgentMessage",
    "AgentMessageBus",
    "AgentRegistry",
    "AgentInfo",
    "TradingAgency",
    "MessageType",
    "create_message",
]

__version__ = "1.0.0"
