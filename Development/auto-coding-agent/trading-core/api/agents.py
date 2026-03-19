"""
Agent Management REST API

Provides REST endpoints for managing the trading system agents.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

# Import agency (will be initialized elsewhere)
from agents import TradingAgency, MessageType


router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
)

# Global agency instance (set by main application)
_agency: Optional[TradingAgency] = None


def set_agency(agency: TradingAgency):
    """Set the global agency instance"""
    global _agency
    _agency = agency


def get_agency() -> TradingAgency:
    """Get the global agency instance"""
    if _agency is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agency not initialized"
        )
    return _agency


@router.get("")
async def list_agents(
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List all registered agents

    Args:
        status: Optional filter by agent status

    Returns:
        Dictionary with list of agents
    """
    agency = get_agency()

    agents = agency.list_agents()

    if status:
        from agents.base import AgentStatus
        try:
            status_enum = AgentStatus(status.lower())
            agents = [
                name for name in agents
                if agency.registry.get_agent(name) and
                agency.registry.get_agent(name).status == status_enum
            ]
        except ValueError:
            pass

    # Get info for each agent
    agents_info = {}
    for name in agents:
        info = agency.get_agent_status(name)
        if info:
            agents_info[name] = info

    return {
        "agents": agents_info,
        "total": len(agents_info),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/{agent_name}")
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific agent

    Args:
        agent_name: Name of the agent

    Returns:
        Agent information
    """
    agency = get_agency()

    agent_info = agency.get_agent_status(agent_name)

    if not agent_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}"
        )

    return {
        "agent": agent_info,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/{agent_name}/start")
async def start_agent(agent_name: str) -> Dict[str, Any]:
    """
    Start a specific agent

    Args:
        agent_name: Name of the agent to start

    Returns:
        Status message
    """
    agency = get_agency()

    agent = agency.registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}"
        )

    if agent.is_running:
        return {
            "message": f"Agent {agent_name} is already running",
            "status": "running",
        }

    try:
        await agent.start()
        return {
            "message": f"Agent {agent_name} started successfully",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error starting agent {agent_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start agent: {str(e)}"
        )


@router.post("/{agent_name}/stop")
async def stop_agent(agent_name: str) -> Dict[str, Any]:
    """
    Stop a specific agent

    Args:
        agent_name: Name of the agent to stop

    Returns:
        Status message
    """
    agency = get_agency()

    agent = agency.registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}"
        )

    if not agent.is_running:
        return {
            "message": f"Agent {agent_name} is not running",
            "status": "stopped",
        }

    try:
        await agent.stop()
        return {
            "message": f"Agent {agent_name} stopped successfully",
            "status": "stopped",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error stopping agent {agent_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop agent: {str(e)}"
        )


@router.post("/{agent_name}/restart")
async def restart_agent(agent_name: str) -> Dict[str, Any]:
    """
    Restart a specific agent

    Args:
        agent_name: Name of the agent to restart

    Returns:
        Status message
    """
    agency = get_agency()

    agent = agency.registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}"
        )

    try:
        result = await agency.restart_agent(agent_name)

        if result:
            return {
                "message": f"Agent {agent_name} restarted successfully",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restart agent"
            )

    except Exception as e:
        logger.error(f"Error restarting agent {agent_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart agent: {str(e)}"
        )


@router.get("/status")
async def get_system_status() -> Dict[str, Any]:
    """
    Get overall system status

    Returns:
        System status information
    """
    agency = get_agency()

    status_info = agency.get_status()
    health_info = agency.get_health_summary()
    bus_stats = agency.get_message_bus_stats()

    return {
        **status_info,
        "health": health_info,
        "message_bus": bus_stats,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health")
async def get_health_summary() -> Dict[str, Any]:
    """
    Get health summary of all agents

    Returns:
        Health summary
    """
    agency = get_agency()

    return agency.get_health_summary()


@router.post("/emergency-stop")
async def emergency_stop(reason: str = "") -> Dict[str, Any]:
    """
    Trigger emergency stop of all agents

    Args:
        reason: Reason for emergency stop

    Returns:
        Status message
    """
    agency = get_agency()

    logger.critical(f"EMERGENCY STOP triggered via API: {reason}")

    await agency.emergency_stop(reason or "Emergency stop triggered via API")

    return {
        "message": "Emergency stop executed",
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/messages/history")
async def get_message_history(
    msg_type: Optional[str] = None,
    sender: Optional[str] = None,
    limit: int = 100,
    source: str = "memory",
) -> Dict[str, Any]:
    """
    Get message history

    Args:
        msg_type: Filter by message type
        sender: Filter by sender
        limit: Maximum number of messages to return
        source: "memory" for in-memory history, "db" for database history

    Returns:
        Message history
    """
    agency = get_agency()

    if source == "db":
        messages = agency.message_bus.get_message_history_from_db(
            msg_type=msg_type,
            sender=sender,
            limit=limit,
        )
    else:
        messages = agency.message_bus.get_message_history(
            msg_type=msg_type,
            sender=sender,
            limit=limit,
        )

    return {
        "messages": [msg.to_dict() for msg in messages],
        "count": len(messages),
        "source": source,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/messages/conversation/{correlation_id}")
async def get_conversation(
    correlation_id: str,
) -> Dict[str, Any]:
    """
    Get conversation history by correlation ID

    Args:
        correlation_id: Correlation ID

    Returns:
        Conversation messages
    """
    agency = get_agency()

    messages = agency.message_bus.get_conversation_history(correlation_id)

    return {
        "messages": [msg.to_dict() for msg in messages],
        "count": len(messages),
        "correlation_id": correlation_id,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/messages/broadcast")
async def broadcast_message(
    msg_type: str,
    content: Dict[str, Any],
    exclude: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Broadcast a message to all agents

    Args:
        msg_type: Type of message
        content: Message content
        exclude: List of agent names to exclude

    Returns:
        Status message
    """
    agency = get_agency()

    await agency.broadcast_message(
        msg_type=msg_type,
        content=content,
        exclude=exclude,
    )

    return {
        "message": "Message broadcasted",
        "msg_type": msg_type,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/messages/{agent_name}")
async def send_to_agent(
    agent_name: str,
    msg_type: str,
    content: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Send a message to a specific agent

    Args:
        agent_name: Name of recipient agent
        msg_type: Type of message
        content: Message content

    Returns:
        Status message
    """
    agency = get_agency()

    agent = agency.registry.get_agent(agent_name)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_name}"
        )

    result = await agency.send_to_agent(
        agent_name=agent_name,
        msg_type=msg_type,
        content=content,
    )

    if result:
        return {
            "message": f"Message sent to {agent_name}",
            "recipient": agent_name,
            "msg_type": msg_type,
            "timestamp": datetime.now().isoformat(),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.get("/subscriptions")
async def get_subscriptions() -> Dict[str, Any]:
    """
    Get all message subscriptions

    Returns:
        Subscription information
    """
    agency = get_agency()

    bus = agency.message_bus

    subscriptions = {}

    for topic in bus._subscriptions.keys():
        subscribers = bus.get_subscribers(topic)
        subscriptions[topic] = list(subscribers)

    return {
        "subscriptions": subscriptions,
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get system metrics

    Returns:
        System metrics
    """
    agency = get_agency()

    bus_stats = agency.get_message_bus_stats()
    health_summary = agency.get_health_summary()
    system_status = agency.get_status()

    # Calculate additional metrics
    total_messages = bus_stats["messages_sent"]
    uptime = system_status.get("uptime_seconds", 0)

    return {
        "uptime_seconds": uptime,
        "total_messages": total_messages,
        "messages_per_second": total_messages / uptime if uptime > 0 else 0,
        "agents": system_status["agents"],
        "health": health_summary,
        "message_bus": bus_stats,
        "timestamp": datetime.now().isoformat(),
    }
