"""
Dynamic Agent Management API

Provides endpoints for dynamic agent registration and management.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from agents.dynamic import get_dynamic_agent_manager, DynamicAgentConfig


router = APIRouter(
    prefix="/api/dynamic-agents",
    tags=["dynamic-agents"],
)


class TemplateCreateRequest(BaseModel):
    """Agent template creation request"""
    template_id: str
    name: str
    description: str
    agent_class_path: str
    default_config: Dict[str, Any] = {}
    dependencies: List[str] = []
    parameters_schema: Dict[str, Any] = {}


class AgentRegisterRequest(BaseModel):
    """Dynamic agent registration request"""
    agent_id: str
    template_id: str
    config: Dict[str, Any] = {}
    name: Optional[str] = None
    auto_start: bool = True


@router.get("/templates")
async def get_templates():
    """
    Get all agent templates

    Returns:
        List of agent templates
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    templates = manager.get_templates()

    return {
        "templates": [t.to_dict() for t in templates],
        "count": len(templates),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Get specific agent template

    Args:
        template_id: Template ID

    Returns:
        Agent template details
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    template = manager.get_template(template_id)

    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return template.to_dict()


@router.post("/templates")
async def create_template(request: TemplateCreateRequest):
    """
    Create a new agent template

    Args:
        request: Template creation request

    Returns:
        Created template
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    from agents.dynamic import AgentTemplate

    template = AgentTemplate(
        template_id=request.template_id,
        name=request.name,
        description=request.description,
        agent_class_path=request.agent_class_path,
        default_config=request.default_config,
        dependencies=request.dependencies,
        parameters_schema=request.parameters_schema,
        created_at=datetime.now().isoformat(),
    )

    success = manager.register_template(template)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create template")

    return template.to_dict()


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    """
    Delete an agent template

    Args:
        template_id: Template ID to delete

    Returns:
        Deletion result
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    success = manager.delete_template(template_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

    return {
        "template_id": template_id,
        "message": "Template deleted",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/register")
async def register_agent(request: AgentRegisterRequest):
    """
    Register a dynamic agent

    Args:
        request: Agent registration request

    Returns:
        Registration result
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    result = await manager.register_agent(
        agent_id=request.agent_id,
        template_id=request.template_id,
        config=request.config,
        name=request.name,
        auto_start=request.auto_start,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.to_dict()


@router.delete("/{agent_id}")
async def unregister_agent(
    agent_id: str,
    force: bool = Query(False, description="Force removal even with dependencies"),
):
    """
    Unregister a dynamic agent

    Args:
        agent_id: Agent ID to unregister
        force: Force removal

    Returns:
        Unregistration result
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    result = await manager.unregister_agent(agent_id, force=force)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return result.to_dict()


@router.get("/agents")
async def get_dynamic_agents():
    """
    Get all dynamically registered agents

    Returns:
        List of dynamic agents
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    agents = manager.get_registered_agents()

    return {
        "agents": agents,
        "count": len(agents),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/history")
async def get_registration_history(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, description="Maximum results"),
):
    """
    Get agent registration history

    Args:
        agent_id: Filter by agent ID
        limit: Maximum results

    Returns:
        Registration history
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    history = manager.get_registration_history(agent_id=agent_id, limit=limit)

    return {
        "history": [h.to_dict() for h in history],
        "count": len(history),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/status")
async def get_manager_status():
    """
    Get dynamic agent manager status

    Returns:
        Manager status
    """
    manager = get_dynamic_agent_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Dynamic agent manager not available")

    status = manager.get_status()

    return status
