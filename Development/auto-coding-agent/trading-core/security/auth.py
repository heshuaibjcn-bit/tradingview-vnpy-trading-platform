"""
Trading authentication and authorization.
"""

from enum import Enum
from typing import Optional, Dict, Set, Callable, Awaitable
from datetime import datetime, timedelta
import hashlib
import asyncio
from loguru import logger


class PermissionLevel(Enum):
    """Permission levels for trading operations."""
    VIEWER = "viewer"  # Can only view
    TRADER = "trader"  # Can place trades
    ADMIN = "admin"  # Full access


class Permission(Enum):
    """Specific permissions."""
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_POSITIONS = "view_positions"
    VIEW_ORDERS = "view_orders"
    PLACE_ORDER = "place_order"
    CANCEL_ORDER = "cancel_order"
    MODIFY_STRATEGY = "modify_strategy"
    START_STRATEGY = "start_strategy"
    STOP_STRATEGY = "stop_strategy"
    EMERGENCY_STOP = "emergency_stop"
    MODIFY_SETTINGS = "modify_settings"
    EXPORT_DATA = "export_data"


# Permission sets by level
PERMISSIONS_BY_LEVEL: Dict[PermissionLevel, Set[Permission]] = {
    PermissionLevel.VIEWER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_POSITIONS,
        Permission.VIEW_ORDERS,
        Permission.EXPORT_DATA,
    },
    PermissionLevel.TRADER: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_POSITIONS,
        Permission.VIEW_ORDERS,
        Permission.PLACE_ORDER,
        Permission.CANCEL_ORDER,
        Permission.EXPORT_DATA,
    },
    PermissionLevel.ADMIN: {
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_POSITIONS,
        Permission.VIEW_ORDERS,
        Permission.PLACE_ORDER,
        Permission.CANCEL_ORDER,
        Permission.MODIFY_STRATEGY,
        Permission.START_STRATEGY,
        Permission.STOP_STRATEGY,
        Permission.EMERGENCY_STOP,
        Permission.MODIFY_SETTINGS,
        Permission.EXPORT_DATA,
    },
}


class TradeAuth:
    """
    Trading authentication and authorization manager.

    Handles password verification and permission checking.
    """

    def __init__(self):
        self._trade_passwords: Dict[str, str] = {}  # user_id -> hashed_password
        self._user_permissions: Dict[str, PermissionLevel] = {}
        self._pending_confirmations: Dict[str, datetime] = {}
        self._confirmation_timeout = 300  # 5 minutes

    def set_trade_password(self, user_id: str, password: str) -> None:
        """Set trading password for a user."""
        self._trade_passwords[user_id] = self._hash_password(password)
        logger.info(f"Trade password set for user {user_id}")

    def verify_trade_password(self, user_id: str, password: str) -> bool:
        """Verify trading password."""
        if user_id not in self._trade_passwords:
            return False

        hashed = self._trade_passwords[user_id]
        return self._verify_password(password, hashed)

    def require_password_confirmation(
        self,
        user_id: str,
        password: str,
        operation: str,
    ) -> bool:
        """
        Require password confirmation for sensitive operations.

        Args:
            user_id: User ID
            password: Password to verify
            operation: Operation description

        Returns:
            True if password verified
        """
        if self.verify_trade_password(user_id, password):
            logger.info(f"Password confirmed for user {user_id}: {operation}")
            return True
        else:
            logger.warning(f"Password verification failed for user {user_id}: {operation}")
            return False

    def set_user_permission(self, user_id: str, level: PermissionLevel) -> None:
        """Set permission level for a user."""
        self._user_permissions[user_id] = level
        logger.info(f"Permission level set for user {user_id}: {level.value}")

    def get_user_permission(self, user_id: str) -> PermissionLevel:
        """Get permission level for a user."""
        return self._user_permissions.get(user_id, PermissionLevel.VIEWER)

    def check_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """
        Check if user has specific permission.

        Args:
            user_id: User ID
            permission: Permission to check

        Returns:
            True if user has permission
        """
        level = self.get_user_permission(user_id)
        user_permissions = PERMISSIONS_BY_LEVEL.get(level, set())
        return permission in user_permissions

    def require_permission(
        self,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """
        Require permission for an operation.

        Raises exception if permission denied.
        """
        if not self.check_permission(user_id, permission):
            raise PermissionError(
                f"User {user_id} does not have permission: {permission.value}"
            )
        return True

    def _hash_password(self, password: str) -> str:
        """Hash password for storage."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self._hash_password(password) == hashed


class TwoFactorAuth:
    """
    Two-factor authentication for sensitive operations.

    Requires both password and confirmation for critical actions.
    """

    def __init__(self, auth: TradeAuth):
        self.auth = auth
        self._pending_confirmations: Dict[str, Dict] = {}
        self._confirmation_timeout = 300  # 5 minutes

    async def initiate_confirmation(
        self,
        user_id: str,
        operation: str,
        details: dict | None = None,
    ) -> str:
        """
        Initiate a two-factor confirmation.

        Args:
            user_id: User ID
            operation: Operation description
            details: Additional details

        Returns:
            Confirmation ID
        """
        confirmation_id = hashlib.sha256(
            f"{user_id}{operation}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        self._pending_confirmations[confirmation_id] = {
            "user_id": user_id,
            "operation": operation,
            "details": details or {},
            "created_at": datetime.now(),
            "confirmed": False,
        }

        logger.info(
            f"2FA initiated: {confirmation_id} for user {user_id}, operation: {operation}"
        )
        return confirmation_id

    async def confirm_operation(
        self,
        confirmation_id: str,
        password: str,
    ) -> bool:
        """
        Confirm an operation with password.

        Args:
            confirmation_id: Confirmation ID
            password: Trading password

        Returns:
            True if confirmed
        """
        if confirmation_id not in self._pending_confirmations:
            logger.warning(f"Invalid confirmation ID: {confirmation_id}")
            return False

        confirmation = self._pending_confirmations[confirmation_id]

        # Check timeout
        if (datetime.now() - confirmation["created_at"]).total_seconds() > self._confirmation_timeout:
            del self._pending_confirmations[confirmation_id]
            logger.warning(f"Confirmation timeout: {confirmation_id}")
            return False

        # Verify password
        if self.auth.verify_trade_password(confirmation["user_id"], password):
            confirmation["confirmed"] = True
            logger.info(f"2FA confirmed: {confirmation_id}")
            # Clean up confirmed operations
            del self._pending_confirmations[confirmation_id]
            return True
        else:
            logger.warning(f"2FA failed: invalid password for {confirmation_id}")
            return False

    def get_pending_confirmation(self, confirmation_id: str) -> dict | None:
        """Get pending confirmation details."""
        return self._pending_confirmations.get(confirmation_id)

    def cleanup_expired(self) -> None:
        """Clean up expired confirmations."""
        now = datetime.now()
        expired = [
            cid for cid, conf in self._pending_confirmations.items()
            if (now - conf["created_at"]).total_seconds() > self._confirmation_timeout
        ]
        for cid in expired:
            del self._pending_confirmations[cid]
