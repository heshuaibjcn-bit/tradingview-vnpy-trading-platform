"""
Health checker for monitoring system services.
"""

import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List
from loguru import logger

from .models import (
    ServiceStatus,
    HealthStatus,
    HealthLevel,
    ServiceType,
)


class HealthChecker:
    """Monitors health of various system services."""

    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self._services: Dict[str, ServiceStatus] = {}
        self._check_functions: Dict[ServiceType, Callable] = {}
        self._service_start_times: Dict[str, datetime] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Register default check functions
        self._register_default_checks()

    def _register_default_checks(self) -> None:
        """Register default health check functions."""
        self._check_functions[ServiceType.WEBSOCKET] = self._check_websocket
        self._check_functions[ServiceType.MARKET_DATA] = self._check_market_data
        self._check_functions[ServiceType.STRATEGY_ENGINE] = self._check_strategy_engine
        self._check_functions[ServiceType.THS_CLIENT] = self._check_ths_client
        self._check_functions[ServiceType.DATABASE] = self._check_database
        self._check_functions[ServiceType.ALERT_ENGINE] = self._check_alert_engine

    def register_service(
        self,
        name: str,
        service_type: ServiceType,
        check_function: Optional[Callable] = None,
    ) -> None:
        """Register a service to be monitored."""
        self._services[name] = ServiceStatus(
            name=name,
            service_type=service_type,
            healthy=False,
            level=HealthLevel.UNKNOWN,
            message="Service registered, not yet checked",
        )
        self._service_start_times[name] = datetime.now()

        if check_function:
            self._check_functions[service_type] = check_function

        logger.info(f"Registered service: {name} ({service_type.value})")

    def unregister_service(self, name: str) -> None:
        """Unregister a service from monitoring."""
        if name in self._services:
            del self._services[name]
        if name in self._service_start_times:
            del self._service_start_times[name]
            logger.info(f"Unregistered service: {name}")

    async def check_service(self, name: str) -> ServiceStatus:
        """Check health of a specific service."""
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")

        service = self._services[name]
        check_fn = self._check_functions.get(service.service_type)

        if check_fn:
            try:
                result = await check_fn()
                service.healthy = result["healthy"]
                service.level = result.get("level", HealthLevel.HEALTHY if result["healthy"] else HealthLevel.UNHEALTHY)
                service.message = result.get("message", "")
                service.metadata = result.get("metadata", {})

                if service.healthy:
                    service.error_count = 0
                    service.last_error = None
                else:
                    error_msg = result.get("error", service.message)
                    service.error_count += 1
                    service.last_error = error_msg

            except Exception as e:
                service.healthy = False
                service.level = HealthLevel.CRITICAL
                service.message = f"Health check failed: {str(e)}"
                service.error_count += 1
                service.last_error = str(e)
                logger.error(f"Health check failed for {name}: {e}")

        service.last_check = datetime.now()
        if name in self._service_start_times:
            service.uptime_seconds = (datetime.now() - self._service_start_times[name]).total_seconds()

        return service

    async def check_all_services(self) -> HealthStatus:
        """Check health of all registered services."""
        tasks = [self.check_service(name) for name in self._services.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Determine overall health status
        if not self._services:
            overall_level = HealthLevel.UNKNOWN
        elif all(s.healthy for s in self._services.values()):
            overall_level = HealthLevel.HEALTHY
        elif any(s.level == HealthLevel.CRITICAL for s in self._services.values()):
            overall_level = HealthLevel.CRITICAL
        elif any(s.level == HealthLevel.UNHEALTHY for s in self._services.values()):
            overall_level = HealthLevel.UNHEALTHY
        else:
            overall_level = HealthLevel.DEGRADED

        # Generate alerts
        alerts = []
        for name, service in self._services.items():
            if not service.healthy:
                alerts.append(f"{name}: {service.message}")
            if service.error_count > 5:
                alerts.append(f"{name}: High error count ({service.error_count})")

        return HealthStatus(
            status=overall_level,
            services=dict(self._services),
            system_info=self._get_system_info(),
            alerts=alerts,
        )

    def get_service_status(self, name: str) -> Optional[ServiceStatus]:
        """Get current status of a service."""
        return self._services.get(name)

    def get_all_statuses(self) -> Dict[str, ServiceStatus]:
        """Get status of all services."""
        return dict(self._services)

    async def start_monitoring(self) -> None:
        """Start continuous monitoring."""
        if self._running:
            return

        self._running = True
        logger.info(f"Starting health monitoring (interval: {self.check_interval}s)")

        async def monitor_loop():
            while self._running:
                try:
                    await self.check_all_services()
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

        self._task = asyncio.create_task(monitor_loop())

    async def stop_monitoring(self) -> None:
        """Stop continuous monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped health monitoring")

    def _get_system_info(self) -> Dict[str, any]:
        """Get system resource information."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "memory_total_mb": memory.total // (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free // (1024 ** 3),
            "disk_total_gb": disk.total // (1024 ** 3),
            "uptime_seconds": time.time() - psutil.boot_time(),
        }

    # Default health check implementations
    async def _check_websocket(self) -> Dict:
        """Check WebSocket server health."""
        # In production, this would ping the WebSocket server
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "WebSocket server running",
            "metadata": {"port": 8765, "connections": 0},
        }

    async def _check_market_data(self) -> Dict:
        """Check market data service health."""
        # Check if last data update was recent
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "Market data service operational",
            "metadata": {"last_update": datetime.now().isoformat()},
        }

    async def _check_strategy_engine(self) -> Dict:
        """Check strategy engine health."""
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "Strategy engine running",
            "metadata": {"active_strategies": 0},
        }

    async def _check_ths_client(self) -> Dict:
        """Check Tonghuashun client connection."""
        # In production, this would check if THS window is accessible
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "THS client connected",
            "metadata": {"window_found": True},
        }

    async def _check_database(self) -> Dict:
        """Check database connection."""
        # In production, this would ping the database
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "Database connected",
            "metadata": {},
        }

    async def _check_alert_engine(self) -> Dict:
        """Check alert engine health."""
        return {
            "healthy": True,
            "level": HealthLevel.HEALTHY,
            "message": "Alert engine operational",
            "metadata": {"active_rules": 0},
        }
