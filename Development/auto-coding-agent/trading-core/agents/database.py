"""
Message Persistence Database

This module handles persistent storage of agent messages using SQLite.
"""

import sqlite3
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
from loguru import logger
import asyncio

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

            # Create composite index for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_type_timestamp
                ON messages(msg_type, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sender_timestamp
                ON messages(sender, timestamp DESC)
            """)

            # Create archive table for old messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages_archive (
                    id TEXT PRIMARY KEY,
                    msg_type TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT,
                    content_json TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    correlation_id TEXT,
                    reply_to TEXT,
                    archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
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

    def save_messages_batch(self, messages: List[AgentMessage]) -> int:
        """
        Save multiple messages in a single transaction

        Args:
            messages: List of AgentMessage objects to save

        Returns:
            Number of messages successfully saved
        """
        if not messages:
            return 0

        saved_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Begin transaction
                cursor.execute("BEGIN TRANSACTION")

                for message in messages:
                    try:
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
                        saved_count += 1
                    except sqlite3.IntegrityError:
                        # Message already exists, skip
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to save message {message.id}: {e}")
                        continue

                # Commit transaction
                conn.commit()
                logger.info(f"Batch saved {saved_count}/{len(messages)} messages")

        except Exception as e:
            logger.error(f"Failed to save messages batch: {e}")
            return 0

        return saved_count

    def archive_old_messages(self, days: int = 30) -> int:
        """
        Archive messages older than specified days to archive table

        Args:
            days: Number of days after which messages are archived

        Returns:
            Number of messages archived
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cutoff = datetime.now() - timedelta(days=days)

                # Copy to archive table
                cursor.execute("""
                    INSERT INTO messages_archive
                    (id, msg_type, sender, recipient, content_json,
                     timestamp, correlation_id, reply_to)
                    SELECT id, msg_type, sender, recipient, content_json,
                           timestamp, correlation_id, reply_to
                    FROM messages
                    WHERE timestamp < ?
                """, (cutoff.isoformat(),))

                archived_count = cursor.rowcount

                # Delete from main table
                cursor.execute("""
                    DELETE FROM messages
                    WHERE timestamp < ?
                """, (cutoff.isoformat(),))

                conn.commit()

                logger.info(f"Archived {archived_count} messages (older than {days} days)")
                return archived_count

        except Exception as e:
            logger.error(f"Failed to archive messages: {e}")
            return 0

    def export_to_csv(
        self,
        output_path: str,
        msg_type: Optional[str] = None,
        sender: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000,
    ) -> bool:
        """
        Export messages to CSV file

        Args:
            output_path: Path to output CSV file
            msg_type: Filter by message type
            sender: Filter by sender
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of messages to export

        Returns:
            True if successful
        """
        try:
            messages = self.get_messages(
                msg_type=msg_type,
                sender=sender,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    'ID', 'Type', 'Sender', 'Recipient',
                    'Timestamp', 'Correlation ID', 'Content'
                ])

                # Write data
                for msg in messages:
                    content_str = json.dumps(msg.content, ensure_ascii=False)
                    writer.writerow([
                        msg.id,
                        msg.msg_type,
                        msg.sender,
                        msg.recipient or '',
                        msg.timestamp.isoformat(),
                        msg.correlation_id or '',
                        content_str,
                    ])

            logger.info(f"Exported {len(messages)} messages to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export messages to CSV: {e}")
            return False

    def export_to_json(
        self,
        output_path: str,
        msg_type: Optional[str] = None,
        sender: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10000,
    ) -> bool:
        """
        Export messages to JSON file

        Args:
            output_path: Path to output JSON file
            msg_type: Filter by message type
            sender: Filter by sender
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of messages to export

        Returns:
            True if successful
        """
        try:
            messages = self.get_messages(
                msg_type=msg_type,
                sender=sender,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dict format
            data = {
                'export_time': datetime.now().isoformat(),
                'total_messages': len(messages),
                'filters': {
                    'msg_type': msg_type,
                    'sender': sender,
                    'start_time': start_time.isoformat() if start_time else None,
                    'end_time': end_time.isoformat() if end_time else None,
                },
                'messages': [msg.to_dict() for msg in messages]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Exported {len(messages)} messages to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export messages to JSON: {e}")
            return False

    def get_database_size(self) -> Dict[str, Any]:
        """Get database file size statistics"""
        try:
            db_size = self.db_path.stat().st_size

            # Get table sizes
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM messages")
                main_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM messages_archive")
                archive_count = cursor.fetchone()[0]

            return {
                'file_size_bytes': db_size,
                'file_size_mb': round(db_size / (1024 * 1024), 2),
                'main_messages': main_count,
                'archived_messages': archive_count,
                'total_messages': main_count + archive_count,
            }

        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return {}

    def optimize_database(self) -> bool:
        """
        Optimize database (VACUUM and ANALYZE)

        Returns:
            True if successful
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                logger.info("Optimizing database...")

                # VACUUM to reclaim space
                cursor.execute("VACUUM")

                # ANALYZE to update statistics
                cursor.execute("ANALYZE")

                conn.commit()

                logger.info("Database optimization complete")
                return True

        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return False
