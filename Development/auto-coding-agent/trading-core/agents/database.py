"""
Message Persistence Database

This module handles persistent storage of agent messages using SQLite.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
from loguru import logger

from .messages import AgentMessage


class MessageDatabase:
    """
    SQLite database for storing agent messages

    Provides persistent storage for all messages sent between agents,
    enabling message history tracking and debugging.
    """

    def __init__(self, db_path: str = "data/messages.db"):
        """
        Initialize message database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_db()

        logger.info(f"MessageDatabase initialized: {self.db_path}")

    def _init_db(self) -> None:
        """Create database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    msg_type TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT,
                    content_json TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    correlation_id TEXT,
                    reply_to TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_msg_type
                ON messages(msg_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sender
                ON messages(sender)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON messages(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_recipient
                ON messages(recipient)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def save_message(self, message: AgentMessage) -> bool:
        """
        Save a message to the database

        Args:
            message: AgentMessage to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO messages
                    (id, msg_type, sender, recipient, content_json,
                     timestamp, correlation_id, reply_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.id,
                    message.msg_type,
                    message.sender,
                    message.recipient,
                    json.dumps(message.content, ensure_ascii=False),
                    message.timestamp.isoformat(),
                    message.correlation_id,
                    message.reply_to,
                ))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Failed to save message to database: {e}")
            return False

    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """
        Get a message by ID

        Args:
            message_id: Message ID

        Returns:
            AgentMessage or None if not found
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM messages WHERE id = ?
                """, (message_id,))

                row = cursor.fetchone()
                if row:
                    return self._row_to_message(row)

                return None

        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            return None

    def get_messages(
        self,
        msg_type: Optional[str] = None,
        sender: Optional[str] = None,
        recipient: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[AgentMessage]:
        """
        Get messages with optional filters

        Args:
            msg_type: Filter by message type
            sender: Filter by sender
            recipient: Filter by recipient
            start_time: Filter by start time
            end_time: Filter by end time
            correlation_id: Filter by correlation ID
            limit: Maximum number of messages to return

        Returns:
            List of AgentMessage objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build query
                query = "SELECT * FROM messages WHERE 1=1"
                params = []

                if msg_type:
                    query += " AND msg_type = ?"
                    params.append(msg_type)

                if sender:
                    query += " AND sender = ?"
                    params.append(sender)

                if recipient:
                    query += " AND recipient = ?"
                    params.append(recipient)

                if start_time:
                    query += " AND timestamp >= ?"
                    params.append(start_time.isoformat())

                if end_time:
                    query += " AND timestamp <= ?"
                    params.append(end_time.isoformat())

                if correlation_id:
                    query += " AND correlation_id = ?"
                    params.append(correlation_id)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [self._row_to_message(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []

    def get_conversation(
        self,
        correlation_id: str,
    ) -> List[AgentMessage]:
        """
        Get all messages in a conversation (by correlation ID)

        Args:
            correlation_id: Correlation ID

        Returns:
            List of AgentMessage objects in chronological order
        """
        messages = self.get_messages(correlation_id=correlation_id, limit=1000)
        return sorted(messages, key=lambda m: m.timestamp)

    def get_message_history(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AgentMessage]:
        """
        Get recent message history

        Args:
            limit: Number of messages to return
            offset: Number of messages to skip

        Returns:
            List of AgentMessage objects
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM messages
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))

                rows = cursor.fetchall()
                return [self._row_to_message(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []

    def clear_old_messages(self, days: int = 30) -> int:
        """
        Delete messages older than specified days

        Args:
            days: Number of days to retain

        Returns:
            Number of messages deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff = datetime.now() - timedelta(days=days)

                cursor.execute("""
                    DELETE FROM messages
                    WHERE timestamp < ?
                """, (cutoff.isoformat(),))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"Cleared {deleted_count} old messages (older than {days} days)")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear old messages: {e}")
            return 0

    def get_message_count(self) -> int:
        """Get total number of messages in database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM messages")
                count = cursor.fetchone()[0]

                return count

        except Exception as e:
            logger.error(f"Failed to get message count: {e}")
            return 0

    def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about stored messages"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total count
                cursor.execute("SELECT COUNT(*) FROM messages")
                total = cursor.fetchone()[0]

                # Count by type
                cursor.execute("""
                    SELECT msg_type, COUNT(*) as count
                    FROM messages
                    GROUP BY msg_type
                    ORDER BY count DESC
                """)
                by_type = {row[0]: row[1] for row in cursor.fetchall()}

                # Count by sender
                cursor.execute("""
                    SELECT sender, COUNT(*) as count
                    FROM messages
                    GROUP BY sender
                    ORDER BY count DESC
                """)
                by_sender = {row[0]: row[1] for row in cursor.fetchall()}

                # Date range
                cursor.execute("""
                    SELECT MIN(timestamp) as min_time,
                           MAX(timestamp) as max_time
                    FROM messages
                """)
                row = cursor.fetchone()
                date_range = {
                    "oldest": row[0],
                    "newest": row[1],
                }

                return {
                    "total_messages": total,
                    "by_type": by_type,
                    "by_sender": by_sender,
                    "date_range": date_range,
                }

        except Exception as e:
            logger.error(f"Failed to get message stats: {e}")
            return {}

    def _row_to_message(self, row: sqlite3.Row) -> AgentMessage:
        """Convert database row to AgentMessage"""
        return AgentMessage.from_dict({
            "id": row["id"],
            "msg_type": row["msg_type"],
            "sender": row["sender"],
            "recipient": row["recipient"],
            "content": json.loads(row["content_json"]),
            "timestamp": row["timestamp"],
            "correlation_id": row["correlation_id"],
            "reply_to": row["reply_to"],
        })

    def close(self) -> None:
        """Close database connection and cleanup"""
        # SQLite connections are closed automatically by context manager
        logger.info("MessageDatabase closed")
