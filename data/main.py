"""
Command-line interface for data management.
"""

import argparse
from pathlib import Path

# pylint: disable=wrong-import-position, import-error, no-name-in-module
from app.data.data_manager import DataManager  # type: ignore
from app.data.data_cleanup import DataCleanup  # type: ignore

# Define missing directory paths using Path objects
PROJECT_ROOT = Path(__file__).parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / "data" / "storage"
VECTOR_INDEX_DIR = PROJECT_ROOT / "data" / "vector_index"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "data" / "knowledge_base"


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Data management for Hospital AI Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List documents in knowledge base")
    list_parser.add_argument("--detailed", action="store_true", help="Show detailed information")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up data directories")
    cleanup_parser.add_argument("--storage-days", type=int, default=7, help="Days to keep storage files")
    cleanup_parser.add_argument("--full", action="store_true", help="Perform full cleanup")
    
    # Stats command
    subparsers.add_parser("stats", help="Show data statistics")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear data directories")
    clear_parser.add_argument("--storage", action="store_true", help="Clear storage directory")
    clear_parser.add_argument("--vector-index", action="store_true", help="Clear vector index")
    clear_parser.add_argument("--knowledge-base", action="store_true", help="Clear knowledge base")
    clear_parser.add_argument("--all", action="store_true", help="Clear all directories")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_documents(args.detailed)
    elif args.command == "cleanup":
        cleanup_data(args.storage_days, args.full)
    elif args.command == "stats":
        show_stats()
    elif args.command == "clear":
        clear_data(args)
    else:
        parser.print_help()


def list_documents(detailed: bool):
    """List documents in knowledge base."""
    data_manager = DataManager()
    documents = data_manager.list_documents()
    
    if not documents:
        print("No documents found in knowledge base.")
        return
    
    print(f"\n📄 Documents in Knowledge Base ({len(documents)} total):")
    print("-" * 80)
    
    for doc in documents:
        print(f"📄 {doc['filename']}")
        print(f"   ID: {doc['id']}")
        print(f"   Size: {doc['file_size'] / 1024:.1f} KB")
        print(f"   Created: {doc['created_at']}")
        if detailed:
            print(f"   Path: {doc['file_path']}")
        print("-" * 40)


def cleanup_data(storage_days: int, full: bool):
    """Clean up data directories."""
    cleaner = DataCleanup()
    
    print("\n🧹 Cleaning up data directories...")
    
    if full:
        results = cleaner.perform_full_cleanup()
        print(f"✅ Storage cleaned: {results['storage_cleaned']} files")
        print(f"✅ Vector orphans cleaned: {results['vector_orphans']} files")
        print(f"✅ Compression: {'Successful' if results['compressed'] else 'Failed'}")
    else:
        deleted = cleaner.cleanup_old_storage_files(storage_days)
        print(f"✅ Cleaned {deleted} storage files older than {storage_days} days")
        
        orphans = cleaner.cleanup_orphaned_vector_index()
        print(f"✅ Cleaned {orphans} orphaned vector files")
    
    print("✅ Cleanup complete!")


def show_stats():
    """Show data statistics."""
    cleaner = DataCleanup()
    stats = cleaner.get_data_statistics()
    
    print("\n📊 Data Statistics:")
    print("=" * 60)
    
    for category, data in stats.items():
        if category == "total":
            print("\n📊 TOTAL:")
        else:
            print(f"\n📁 {category.upper()}:")
        
        print(f"   Files: {data.get('file_count', 0)}")
        print(f"   Size: {data.get('total_size_mb', 0):.2f} MB")
        
        if data.get('oldest_file'):
            print(f"   Oldest: {data['oldest_file']}")
        if data.get('newest_file'):
            print(f"   Newest: {data['newest_file']}")


def clear_data(args):
    """Clear specified data directories."""
    print("\n⚠️  WARNING: This will permanently delete data!")
    response = input("Are you sure? (yes/no): ")
    
    if response.lower() != "yes":
        print("Operation cancelled.")
        return
    
    deleted = 0
    
    if (args.all or args.storage) and STORAGE_DIR.exists():
        for file_path in STORAGE_DIR.iterdir():
            if file_path.is_file():
                file_path.unlink()
                deleted += 1
        print(f"✅ Cleared {deleted} files from storage")
    
    if (args.all or args.vector_index) and VECTOR_INDEX_DIR.exists():
        deleted = 0
        for file_path in VECTOR_INDEX_DIR.iterdir():
            if file_path.is_file():
                file_path.unlink()
                deleted += 1
        print(f"✅ Cleared {deleted} files from vector index")
    
    if (args.all or args.knowledge_base) and KNOWLEDGE_BASE_DIR.exists():
        deleted = 0
        for file_path in KNOWLEDGE_BASE_DIR.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                file_path.unlink()
                deleted += 1
        print(f"✅ Cleared {deleted} files from knowledge base")
    
    print("✅ Clear operation complete!")


if __name__ == "__main__":
    main()
