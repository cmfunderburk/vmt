"""
CLI Debugging Tools for Delta Files

Usage:
    python -m econsim.delta debug deltas.msgpack
    python -m econsim.delta export deltas.msgpack output.json
    python -m econsim.delta summary deltas.msgpack
    python -m econsim.delta validate deltas.msgpack
"""

import argparse
import sys
from pathlib import Path

from .serializer import DeltaDebugger, DeltaSerializer


def debug_command(args):
    """Debug a delta file - print summary and optionally export to JSON."""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    DeltaDebugger.print_delta_summary(args.file, args.step)
    
    if args.export:
        DeltaDebugger.export_to_json(args.file, args.export, pretty=not args.no_pretty)
        print(f"Exported to JSON: {args.export}")
    
    return 0


def export_command(args):
    """Export delta file to JSON."""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    DeltaDebugger.export_to_json(args.file, args.output, pretty=not args.no_pretty)
    print(f"Exported {args.file} to {args.output}")
    return 0


def summary_command(args):
    """Print summary of delta file."""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    DeltaDebugger.print_delta_summary(args.file, args.step)
    return 0


def validate_command(args):
    """Validate delta file."""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    result = DeltaDebugger.validate_file(args.file)
    if result['valid']:
        print("✅ File is valid")
        print(f"  Delta count: {result['delta_count']}")
        print(f"  Steps: {result['steps'][:5]}{'...' if len(result['steps']) > 5 else ''}")
        print(f"  Schema version: {result['schema_version']}")
        return 0
    else:
        print(f"❌ File is invalid: {result['error']}")
        return 1


def find_command(args):
    """Find specific events in delta file."""
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1
    
    events = DeltaDebugger.find_events(args.file, args.event_type, args.agent_id)
    print(f"Found {len(events)} {args.event_type} events")
    
    for i, event in enumerate(events[:args.limit]):
        print(f"  {i+1}: {event}")
    
    if len(events) > args.limit:
        print(f"  ... and {len(events) - args.limit} more")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Delta file debugging and analysis tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s debug deltas.msgpack
  %(prog)s debug deltas.msgpack --step 100 --export debug.json
  %(prog)s export deltas.msgpack output.json
  %(prog)s summary deltas.msgpack --step 50
  %(prog)s validate deltas.msgpack
  %(prog)s find trade_events deltas.msgpack --agent-id 5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug delta file')
    debug_parser.add_argument('file', help='Delta file path')
    debug_parser.add_argument('--step', type=int, help='Specific step to debug')
    debug_parser.add_argument('--export', help='Export to JSON file')
    debug_parser.add_argument('--no-pretty', action='store_true', help='No pretty printing')
    debug_parser.set_defaults(func=debug_command)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export to JSON')
    export_parser.add_argument('file', help='Delta file path')
    export_parser.add_argument('output', help='Output JSON file path')
    export_parser.add_argument('--no-pretty', action='store_true', help='No pretty printing')
    export_parser.set_defaults(func=export_command)
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Print summary')
    summary_parser.add_argument('file', help='Delta file path')
    summary_parser.add_argument('--step', type=int, help='Specific step to summarize')
    summary_parser.set_defaults(func=summary_command)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate file')
    validate_parser.add_argument('file', help='Delta file path')
    validate_parser.set_defaults(func=validate_command)
    
    # Find command
    find_parser = subparsers.add_parser('find', help='Find specific events')
    find_parser.add_argument('event_type', help='Event type to find')
    find_parser.add_argument('file', help='Delta file path')
    find_parser.add_argument('--agent-id', type=int, help='Filter by agent ID')
    find_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    find_parser.set_defaults(func=find_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
