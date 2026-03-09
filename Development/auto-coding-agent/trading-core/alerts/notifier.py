"""
Alert Notifier

Sends alert notifications through various channels.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List
from loguru import logger

from .engine import Alert


class NotificationMethod(str, Enum):
    """Notification methods."""
    BROWSER = "browser"      # Browser push notification
    EMAIL = "email"          # Email notification
    SOUND = "sound"          # Sound alert
    SMS = "sms"              # SMS notification
    WEBHOOK = "webhook"      # Webhook callback


@dataclass
class NotificationConfig:
    """Configuration for notification methods."""
    enabled_methods: List[NotificationMethod]

    # Email config
    smtp_server: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""

    # Webhook config
    webhook_url: str = ""

    # Sound config
    sound_file: str = ""


class AlertNotifier:
    """
    Sends alert notifications through various channels.
    """

    def __init__(self, config: NotificationConfig):
        self.config = config

    async def notify(self, alert: Alert) -> bool:
        """
        Send notification through all enabled channels.

        Returns True if at least one notification succeeded.
        """
        success = False

        for method in self.config.enabled_methods:
            try:
                if method == NotificationMethod.BROWSER:
                    if await self._send_browser_notification(alert):
                        success = True
                elif method == NotificationMethod.EMAIL:
                    if await self._send_email_notification(alert):
                        success = True
                elif method == NotificationMethod.SOUND:
                    if await self._play_sound(alert):
                        success = True
                elif method == NotificationMethod.WEBHOOK:
                    if await self._send_webhook(alert):
                        success = True
            except Exception as e:
                logger.error(f"Failed to send {method} notification: {e}")

        return success

    async def _send_browser_notification(self, alert: Alert) -> bool:
        """Send browser notification (placeholder for WebSocket push)."""
        # In production, this would push through WebSocket
        logger.info(f"Browser notification: {alert.message}")
        return True

    async def _send_email_notification(self, alert: Alert) -> bool:
        """Send email notification."""
        if not self.config.smtp_server:
            logger.warning("SMTP server not configured")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔔 股票提醒 - {alert.symbol}"
            msg["From"] = self.config.from_email
            msg["To"] = alert.user_id  # In production, would fetch user email

            html = f"""
            <html>
              <body>
                <h2>股票价格提醒</h2>
                <p><strong>股票代码:</strong> {alert.symbol}</p>
                <p><strong>提醒类型:</strong> {alert.alert_type.value}</p>
                <p><strong>当前价格:</strong> ¥{alert.value:.2f}</p>
                <p><strong>阈值:</strong> ¥{alert.threshold:.2f}</p>
                <p><strong>触发时间:</strong> {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>{alert.message}</p>
              </body>
            </html>
            """

            part = MIMEText(html, "html")
            msg.attach(part)

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            logger.info(f"Email notification sent for {alert.symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def _play_sound(self, alert: Alert) -> bool:
        """Play sound notification."""
        if not self.config.sound_file:
            # Just log that sound would play
            logger.info(f"Sound notification: {alert.message}")
            return True

        try:
            import platform
            if platform.system() == "Darwin":  # macOS
                import os
                os.system(f"afplay {self.config.sound_file}")
            elif platform.system() == "Windows":
                import winsound
                winsound.PlaySound(self.config.sound_file, winsound.SND_FILENAME)
            else:  # Linux
                import os
                os.system(f"aplay {self.config.sound_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to play sound: {e}")
            return False

    async def _send_webhook(self, alert: Alert) -> bool:
        """Send webhook notification."""
        if not self.config.webhook_url:
            logger.warning("Webhook URL not configured")
            return False

        try:
            import aiohttp

            payload = {
                "alert_id": alert.id,
                "rule_id": alert.rule_id,
                "user_id": alert.user_id,
                "symbol": alert.symbol,
                "alert_type": alert.alert_type.value,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "triggered_at": alert.triggered_at.isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for {alert.symbol}")
                        return True
                    else:
                        logger.warning(f"Webhook returned status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    async def send_bulk_notifications(self, alerts: List[Alert]) -> int:
        """Send multiple notifications concurrently."""
        tasks = [self.notify(alert) for alert in alerts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return sum(1 for r in results if r is True)
