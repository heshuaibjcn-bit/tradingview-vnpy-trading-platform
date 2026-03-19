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

# Global agency instance (set by main.py)
_agency_instance = None


def set_agency(agency):
    """Set the global agency instance"""
    global _agency_instance
    _agency_instance = agency


def get_agency():
    """Get the global agency instance"""
    return _agency_instance


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
    # Global functions
    "set_agency",
    "get_agency",
]

__version__ = "1.0.0"

# Dynamic agents support
from .dynamic import (
    DynamicAgentManager,
    AgentTemplate,
    DynamicAgentConfig,
    AgentRegistrationResult,
    get_dynamic_agent_manager,
    init_dynamic_agent_manager,
)

__all__.extend([
    "DynamicAgentManager",
    "AgentTemplate",
    "DynamicAgentConfig",
    "AgentRegistrationResult",
    "get_dynamic_agent_manager",
    "init_dynamic_agent_manager",
])

# Batch processing support
from .batch_processor import (
    BatchConfig,
    BatchStats,
    MessageBatcher,
    BatchMessageBus,
    create_batch_message_bus,
)

__all__.extend([
    "BatchConfig",
    "BatchStats",
    "MessageBatcher",
    "BatchMessageBus",
    "create_batch_message_bus",
])
