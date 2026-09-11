#!/usr/bin/env python
"""
Script to check if the local setup is configured correctly.
Run: python -m app.scripts.check_local_setup
"""

import importlib
import logging
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# pylint: disable=wrong-import-position, import-error, no-name-in-module
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check environment variables"""
    print("\n📋 Checking Environment Variables...")
    
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES"
    ]
    
    optional_vars = [
        "GROQ_API_KEY",
        "OPENAI_API_KEY",
        "EMBEDDING_MODEL",
        "CHUNK_SIZE",
        "CHUNK_OVERLAP",
        "APP_NAME",
        "DEBUG",
        "LOG_LEVEL"
    ]
    
    all_present = True
    
    for var in required_vars:
        val = os.getenv(var)
        if val:
            print(f"  ✅ {var}: {val[:20]}...")
        else:
            print(f"  ❌ {var}: Not set")
            all_present = False
    
    for var in optional_vars:
        val = os.getenv(var)
        if val:
            print(f"  ✅ {var}: {val[:20]}...")
        else:
            print(f"  ⚠️  {var}: Not set (optional)")
    
    return all_present

def check_database():
    """Check database connection"""
    print("\n📋 Checking Database...")
    
    try:
        from app.db.session import engine # type: ignore
        
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print("  ✅ Database connection successful")
            return True
    except SQLAlchemyError as e:
        print(f"  ❌ Database connection failed: {e}")
        return False

def check_vector_store():
    """Check vector store"""
    print("\n📋 Checking Vector Store...")
    
    try:
        from app.services.vector_store import VectorStore # type: ignore
        store = VectorStore()
        
        # pylint: disable=no-member
        count = store.count() if hasattr(store, 'count') else "N/A"
        print(f"  ✅ Vector store initialized (Document Count: {count})")
        return True
    except (ImportError, AttributeError, ValueError) as e:
        print(f"  ❌ Vector store initialization failed: {e}")
        return False

def check_models():
    """Check if models can be imported"""
    print("\n📋 Checking Models...")
    
    models = [
        "app.db.models.user",
        "app.db.models.department",
        "app.db.models.doctor",
        "app.db.models.patient",
        "app.db.models.appointment",
        "app.db.models.knowledge_document",
        "app.db.models.knowledge_chunk",
        "app.db.models.chat_session",
        "app.db.models.chat_message"
    ]
    
    all_loaded = True
    
    for model in models:
        try:
            importlib.import_module(model)
            print(f"  ✅ {model}")
        except ImportError as e:
            print(f"  ❌ {model}: {e}")
            all_loaded = False
    
    return all_loaded

def check_services():
    """Check if services can be imported"""
    print("\n📋 Checking Services...")
    
    services = [
        "app.services.document_loader",
        "app.services.chunking",
        "app.services.embedding",
        "app.services.vector_store",
        "app.services.retriever",
        "app.services.prompt_builder",
        "app.services.rag_service",
        "app.services.emergency_guard"
    ]
    
    all_loaded = True
    
    for service in services:
        try:
            importlib.import_module(service)
            print(f"  ✅ {service}")
        except ImportError as e:
            print(f"  ❌ {service}: {e}")
            all_loaded = False
    
    return all_loaded

def check_folders():
    """Check required folders exist"""
    print("\n📋 Checking Folders...")
    
    folders = [
        "data",
        "data/knowledge_base",
        "data/storage",
        "data/vector_index",
        "alembic/versions"
    ]
    
    all_exist = True
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"  ✅ {folder}")
        else:
            print(f"  ❌ {folder}: Does not exist")
            all_exist = False
    
    return all_exist

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("🔍 HOSPITAL AI ASSISTANT - SETUP CHECK")
    print("="*60)
    
    # Load .env file
    load_dotenv()
    
    # Run checks
    checks = {
        "Environment": check_environment(),
        "Database": check_database(),
        "Vector Store": check_vector_store(),
        "Models": check_models(),
        "Services": check_services(),
        "Folders": check_folders()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in checks.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✅ All checks passed! You're ready to run the application.")
        print("\nTo start the server:")
        print("  uvicorn app.main:app --reload")
        print("\nTo create an admin user:")
        print("  python -m app.scripts.create_admin")
        print("\nTo ingest knowledge base:")
        print("  python -m app.scripts.ingest_knowledge_base")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nTroubleshooting tips:")
        print("1. Make sure .env file exists with all required variables")
        print("2. Check that PostgreSQL is running")
        print("3. Run database migrations: alembic upgrade head")
        print("4. Install required packages: pip install -r requirements.txt")
        print("5. Create required folders manually if they don't exist")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
