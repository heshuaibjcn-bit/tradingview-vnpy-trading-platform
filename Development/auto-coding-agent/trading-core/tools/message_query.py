#!/usr/bin/env python
"""
Message Database Query Tool

Command-line tool for querying and managing the agent message database.
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.database import MessageDatabase
from loguru import logger


def query_messages(args):
    """Query and display messages"""
    db = MessageDatabase(args.db)

    # Parse filters
    start_time = None
    if args.hours:
        start_time = datetime.now() - timedelta(hours=args.hours)

    # Get messages
    messages = db.get_messages(
        msg_type=args.type,
        sender=args.sender,
        start_time=start_time,
        limit=args.limit,
    )

    # Display results
    print(f"\nFound {len(messages)} messages:")
    print("-" * 80)

    for msg in messages:
        print(f"\n[{msg.timestamp}] {msg.msg_type}")
        print(f"  From: {msg.sender}")
        if msg.recipient:
            print(f"  To: {msg.recipient}")
        print(f"  Content: {json.dumps(msg.content, ensure_ascii=False)[:200]}")

    # db.close() is not needed


def show_stats(args):
    """Show message statistics"""
    db = MessageDatabase(args.db)

    stats = db.get_message_stats()
    size = db.get_database_size()

    print("\n=== Message Database Statistics ===\n")

    print(f"Total Messages: {stats.get('total_messages', 0)}")
    print(f"Database Size: {size.get('file_size_mb', 0):.2f} MB")
    print(f"Main Messages: {size.get('main_messages', 0)}")
    print(f"Archived Messages: {size.get('archived_messages', 0)}")

    if stats.get('date_range'):
        print(f"\nDate Range:")
        print(f"  Oldest: {stats['date_range'].get('oldest', 'N/A')}")
        print(f"  Newest: {stats['date_range'].get('newest', 'N/A')}")

    if stats.get('by_type'):
        print(f"\nMessages by Type:")
        for msg_type, count in list(stats['by_type'].items())[:10]:
            print(f"  {msg_type}: {count}")

    if stats.get('by_sender'):
        print(f"\nMessages by Sender:")
        for sender, count in list(stats['by_sender'].items())[:10]:
            print(f"  {sender}: {count}")

    # db.close() is not needed, connections are managed automatically


def export_messages(args):
    """Export messages to file"""
    db = MessageDatabase(args.db)

    start_time = None
    if args.hours:
        start_time = datetime.now() - timedelta(hours=args.hours)

    success = False
    if args.format == 'csv':
        success = db.export_to_csv(
            args.output,
            msg_type=args.type,
            sender=args.sender,
            start_time=start_time,
            limit=args.limit,
        )
    else:  # json
        success = db.export_to_json(
            args.output,
            msg_type=args.type,
            sender=args.sender,
            start_time=start_time,
            limit=args.limit,
        )

    if success:
        print(f"\n✅ Messages exported to {args.output}")
    else:
        print(f"\n❌ Export failed")

    # db.close() is not needed


def clean_messages(args):
    """Clean old messages"""
    db = MessageDatabase(args.db)

    if args.archive:
        count = db.archive_old_messages(days=args.days)
        print(f"\n✅ Archived {count} messages (older than {args.days} days)")
    else:
        count = db.clear_old_messages(days=args.days)
        print(f"\n✅ Deleted {count} messages (older than {args.days} days)")

    # db.close() is not needed


def optimize_database(args):
    """Optimize database"""
    db = MessageDatabase(args.db)

    size_before = db.get_database_size()

    if db.optimize_database():
        size_after = db.get_database_size()
        print(f"\n✅ Database optimized")
        print(f"   Size before: {size_before.get('file_size_mb', 0):.2f} MB")
        print(f"   Size after: {size_after.get('file_size_mb', 0):.2f} MB")
        print(f"   Saved: {size_before.get('file_size_mb', 0) - size_after.get('file_size_mb', 0):.2f} MB")
    else:
        print("\n❌ Optimization failed")

    # db.close() is not needed


def main():
    parser = argparse.ArgumentParser(
        description="Agent Message Database Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show recent messages
  %(prog)s query --limit 20

  # Show messages from market_fetcher
  %(prog)s query --sender market_fetcher --limit 10

  # Show statistics
  %(prog)s stats

  # Export last 24 hours to JSON
  %(prog)s export --hours 24 --format json --output messages.json

  # Clean messages older than 30 days
  %(prog)s clean --days 30

  # Optimize database
  %(prog)s optimize
        """
    )

    parser.add_argument(
        '--db',
        default='data/messages.db',
        help='Path to message database (default: data/messages.db)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query messages')
    query_parser.add_argument('--type', help='Filter by message type')
    query_parser.add_argument('--sender', help='Filter by sender')
    query_parser.add_argument('--hours', type=int, help='Last N hours')
    query_parser.add_argument('--limit', type=int, default=50, help='Max messages to show')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export messages')
    export_parser.add_argument('--output', '-o', required=True, help='Output file path')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='json', help='Export format')
    export_parser.add_argument('--type', help='Filter by message type')
    export_parser.add_argument('--sender', help='Filter by sender')
    export_parser.add_argument('--hours', type=int, help='Last N hours')
    export_parser.add_argument('--limit', type=int, default=10000, help='Max messages to export')

    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean old messages')
    clean_parser.add_argument('--days', type=int, default=30, help='Messages older than N days')
    clean_parser.add_argument('--archive', action='store_true', help='Archive instead of delete')

    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize database')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'query':
        query_messages(args)
    elif args.command == 'stats':
        show_stats(args)
    elif args.command == 'export':
        export_messages(args)
    elif args.command == 'clean':
        clean_messages(args)
    elif args.command == 'optimize':
        optimize_database(args)


if __name__ == '__main__':
    main()
