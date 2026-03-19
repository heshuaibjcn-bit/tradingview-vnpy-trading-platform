"""
Dynamic Agent Registration Manager

Enables runtime dynamic addition and removal of agents.
"""

import importlib
import sys
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional, Type
from datetime import datetime
from dataclasses import dataclass, asdict
from loguru import logger
import json

from agents.base import BaseAgent, AgentStatus
from agents.registry import AgentRegistry
from agents.agency import TradingAgency
from agents.messages import MessageType


@dataclass
class AgentTemplate:
    """Agent template definition"""
    template_id: str
    name: str
    description: str
    agent_class_path: str  # e.g., "agents.market_agent.MarketDataAgent"
    default_config: Dict[str, Any]
    dependencies: List[str]
    parameters_schema: Dict[str, Any]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DynamicAgentConfig:
    """Dynamic agent configuration"""
    agent_id: str
    template_id: str
    name: str
    config: Dict[str, Any]
    enabled: bool = True
    auto_start: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRegistrationResult:
    """Result of agent registration"""
    success: bool
    agent_id: str
    message: str
    error: Optional[str] = None
    agent_info: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DynamicAgentManager:
    """
    Manages dynamic agent registration and lifecycle
    """

    def __init__(
        self,
        agency: TradingAgency,
        templates_dir: str = "agents/templates",
        configs_dir: str = "agents/dynamic",
    ):
        """
        Initialize dynamic agent manager

        Args:
            agency: TradingAgency instance
            templates_dir: Directory containing agent templates
            configs_dir: Directory for dynamic agent configs
        """
        self.agency = agency
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.configs_dir = Path(configs_dir)
        self.configs_dir.mkdir(parents=True, exist_ok=True)

        # Agent templates
        self._templates: Dict[str, AgentTemplate] = {}

        # Dynamic agent configs
        self._agent_configs: Dict[str, DynamicAgentConfig] = {}

        # Registered agents
        self._registered_agents: Dict[str, BaseAgent] = {}

        # Registration history
        self._registration_history: List[AgentRegistrationResult] = []

        # Load templates
        self._load_templates()

        # Load saved agent configs
        self._load_agent_configs()

        logger.info(
            f"DynamicAgentManager initialized "
            f"(templates={len(self._templates)}, "
            f"configs={len(self._agent_configs)})"
        )

    def _load_templates(self) -> None:
        """Load agent templates from directory"""
        template_files = list(self.templates_dir.glob("*.json"))

        for file_path in template_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                template = AgentTemplate(
                    template_id=data['template_id'],
                    name=data['name'],
                    description=data['description'],
                    agent_class_path=data['agent_class_path'],
                    default_config=data.get('default_config', {}),
                    dependencies=data.get('dependencies', []),
                    parameters_schema=data.get('parameters_schema', {}),
                    created_at=data.get('created_at', datetime.now().isoformat()),
                )

                self._templates[template.template_id] = template
                logger.info(f"Loaded agent template: {template.template_id}")

            except Exception as e:
                logger.error(f"Failed to load template {file_path}: {e}")

    def _load_agent_configs(self) -> None:
        """Load saved agent configurations"""
        config_files = list(self.configs_dir.glob("*.json"))

        for file_path in config_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                config = DynamicAgentConfig(**data)

                # Only load enabled configs
                if config.enabled and config.auto_start:
                    logger.info(f"Found dynamic agent config: {config.agent_id}")

                self._agent_configs[config.agent_id] = config

            except Exception as e:
                logger.error(f"Failed to load agent config {file_path}: {e}")

    def _save_agent_config(self, config: DynamicAgentConfig) -> None:
        """Save agent configuration to file"""
        file_path = self.configs_dir / f"{config.agent_id}.json"

        with open(file_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)

        logger.debug(f"Saved agent config: {config.agent_id}")

    def _delete_agent_config(self, agent_id: str) -> None:
        """Delete agent configuration file"""
        file_path = self.configs_dir / f"{agent_id}.json"

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted agent config: {agent_id}")

    def _import_agent_class(self, class_path: str) -> Type[BaseAgent]:
        """
        Import agent class from path

        Args:
            class_path: Module path to agent class

        Returns:
            Agent class
        """
        try:
            # Split module and class name
            module_path, class_name = class_path.rsplit('.', 1)

            # Import module
            module = importlib.import_module(module_path)

            # Get class
            agent_class = getattr(module, class_name)

            if not issubclass(agent_class, BaseAgent):
                raise ValueError(f"{class_name} is not a BaseAgent subclass")

            return agent_class

        except Exception as e:
            logger.error(f"Failed to import agent class {class_path}: {e}")
            raise

    def _resolve_dependencies(self, dependencies: List[str]) -> bool:
        """
        Resolve agent dependencies

        Args:
            dependencies: List of agent IDs

        Returns:
            True if all dependencies are available
        """
        for dep_id in dependencies:
            if dep_id not in self._registered_agents:
                logger.warning(f"Dependency not found: {dep_id}")
                return False

            agent = self._registered_agents[dep_id]

            if agent.status != AgentStatus.RUNNING:
                logger.warning(f"Dependency not running: {dep_id}")
                return False

        return True

    def register_template(self, template: AgentTemplate) -> bool:
        """
        Register an agent template

        Args:
            template: AgentTemplate to register

        Returns:
            True if successful
        """
        try:
            # Save template to file
            file_path = self.templates_dir / f"{template.template_id}.json"

            with open(file_path, 'w') as f:
                json.dump(template.to_dict(), f, indent=2)

            self._templates[template.template_id] = template

            logger.info(f"Registered agent template: {template.template_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register template: {e}")
            return False

    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """Get agent template by ID"""
        return self._templates.get(template_id)

    def get_templates(self) -> List[AgentTemplate]:
        """Get all agent templates"""
        return list(self._templates.values())

    def delete_template(self, template_id: str) -> bool:
        """Delete an agent template"""
        if template_id in self._templates:
            del self._templates[template_id]

            # Delete template file
            file_path = self.templates_dir / f"{template_id}.json"
            if file_path.exists():
                file_path.unlink()

            logger.info(f"Deleted agent template: {template_id}")
            return True

        return False

    async def register_agent(
        self,
        agent_id: str,
        template_id: str,
        config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        auto_start: bool = True,
    ) -> AgentRegistrationResult:
        """
        Register and start a dynamic agent

        Args:
            agent_id: Unique agent ID
            template_id: Template ID to use
            config: Agent configuration (overrides template defaults)
            name: Agent name (defaults to template name)
            auto_start: Whether to start the agent automatically

        Returns:
            Registration result
        """
        try:
            # Get template
            template = self.get_template(template_id)
            if not template:
                return AgentRegistrationResult(
                    success=False,
                    agent_id=agent_id,
                    message=f"Template not found: {template_id}",
                    error="Template not found"
                )

            # Merge configs
            final_config = template.default_config.copy()
            if config:
                final_config.update(config)

            # Resolve dependencies
            if not self._resolve_dependencies(template.dependencies):
                return AgentRegistrationResult(
                    success=False,
                    agent_id=agent_id,
                    message="Dependencies not satisfied",
                    error="Dependencies not met"
                )

            # Import agent class
            agent_class = self._import_agent_class(template.agent_class_path)

            # Create agent instance
            agent = agent_class(
                name=name or template.name,
                **final_config
            )

            # Register with agency
            self.agency.register_agent(agent)

            # Start agent if requested
            if auto_start:
                await agent.start()

            # Store in registered agents
            self._registered_agents[agent_id] = agent

            # Save configuration
            agent_config = DynamicAgentConfig(
                agent_id=agent_id,
                template_id=template_id,
                name=name or template.name,
                config=final_config,
                enabled=True,
                auto_start=auto_start,
            )
            self._save_agent_config(agent_config)
            self._agent_configs[agent_id] = agent_config

            # Get agent info
            agent_info = self.agency.get_agent_status(agent_id) or {}

            result = AgentRegistrationResult(
                success=True,
                agent_id=agent_id,
                message=f"Successfully registered agent: {agent_id}",
                agent_info=agent_info,
            )

            logger.info(f"Registered dynamic agent: {agent_id} from template {template_id}")

        except Exception as e:
            error_msg = f"Failed to register agent: {str(e)}"
            logger.error(error_msg)

            result = AgentRegistrationResult(
                success=False,
                agent_id=agent_id,
                message=error_msg,
                error=str(e),
            )

        # Store in history
        self._registration_history.append(result)

        if len(self._registration_history) > 100:
            self._registration_history = self._registration_history[-100:]

        return result

    async def unregister_agent(
        self,
        agent_id: str,
        force: bool = False,
    ) -> AgentRegistrationResult:
        """
        Unregister and remove a dynamic agent

        Args:
            agent_id: Agent ID to unregister
            force: Force removal even if dependencies exist

        Returns:
            Registration result
        """
        try:
            # Check if agent exists
            if agent_id not in self._registered_agents:
                return AgentRegistrationResult(
                    success=False,
                    agent_id=agent_id,
                    message=f"Agent not found: {agent_id}",
                    error="Agent not found"
                )

            agent = self._registered_agents[agent_id]

            # Check if other agents depend on this one
            if not force:
                for config in self._agent_configs.values():
                    if config.enabled and agent_id in self.get_template(config.template_id).dependencies:
                        return AgentRegistrationResult(
                            success=False,
                            agent_id=agent_id,
                            message=f"Agent is depended upon by: {config.agent_id}",
                            error="Has dependents"
                        )

            # Stop agent
            if agent.is_running:
                await agent.stop()

            # Unregister from agency
            self.agency.unregister_agent(agent_id)

            # Remove from registered agents
            del self._registered_agents[agent_id]

            # Delete config
            del self._agent_configs[agent_id]
            self._delete_agent_config(agent_id)

            result = AgentRegistrationResult(
                success=True,
                agent_id=agent_id,
                message=f"Successfully unregistered agent: {agent_id}",
            )

            logger.info(f"Unregistered dynamic agent: {agent_id}")

        except Exception as e:
            error_msg = f"Failed to unregister agent: {str(e)}"
            logger.error(error_msg)

            result = AgentRegistrationResult(
                success=False,
                agent_id=agent_id,
                message=error_msg,
                error=str(e),
            )

        # Store in history
        self._registration_history.append(result)

        return result

    def get_registered_agents(self) -> List[Dict[str, Any]]:
        """Get all dynamically registered agents"""
        agents = []

        for agent_id, config in self._agent_configs.items():
            if config.enabled and agent_id in self._registered_agents:
                agent = self._registered_agents[agent_id]
                agents.append({
                    "agent_id": agent_id,
                    "template_id": config.template_id,
                    "name": config.name,
                    "config": config.config,
                    "status": agent.status.value,
                    "is_running": agent.is_running,
                    "is_dynamic": True,
                })

        return agents

    def get_registration_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AgentRegistrationResult]:
        """Get registration history"""
        history = self._registration_history[-limit:]

        if agent_id:
            history = [r for r in history if r.agent_id == agent_id]

        return history

    def get_status(self) -> Dict[str, Any]:
        """Get manager status"""
        return {
            "total_templates": len(self._templates),
            "total_configs": len(self._agent_configs),
            "registered_agents": len(self._registered_agents),
            "templates_dir": str(self.templates_dir),
            "configs_dir": str(self.configs_dir),
            "timestamp": datetime.now().isoformat(),
        }


# Global instance
_manager: Optional[DynamicAgentManager] = None


def get_dynamic_agent_manager() -> Optional[DynamicAgentManager]:
    """Get global dynamic agent manager"""
    return _manager


def init_dynamic_agent_manager(
    agency: TradingAgency,
    templates_dir: str = "agents/templates",
    configs_dir: str = "agents/dynamic",
) -> DynamicAgentManager:
    """Initialize global dynamic agent manager"""
    global _manager
    _manager = DynamicAgentManager(
        agency=agency,
        templates_dir=templates_dir,
        configs_dir=configs_dir,
    )
    return _manager
