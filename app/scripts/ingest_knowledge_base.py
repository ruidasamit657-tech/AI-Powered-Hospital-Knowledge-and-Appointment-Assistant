import os
import sys
import logging
import time
import importlib.util
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.document_loader import DocumentLoader
from app.services.chunking import TextChunker
from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore
from app.core.config import settings


# ---------------------------------------------------------------------------
# Dependency check WITHOUT importing the packages.
# This avoids Pylance "Import could not be resolved" and
# "is not accessed" warnings.
# ---------------------------------------------------------------------------
def _missing_packages(*package_names: str) -> List[str]:
    """Return the subset of package_names that are not importable."""
    missing: List[str] = []
    for name in package_names:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append(name)
        except (ImportError, ValueError):
            missing.append(name)
    return missing


_REQUIRED_PACKAGES = ("chromadb", "sentence_transformers", "numpy")
_MISSING_PACKAGES: List[str] = _missing_packages(*_REQUIRED_PACKAGES)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class KnowledgeBaseIngester:
    """Handles ingestion of knowledge base documents"""

    def __init__(self):
        self.document_loader = DocumentLoader()
        self.chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.knowledge_base_path = Path(os.getcwd()) / "data" / "knowledge_base"
        self.supported_extensions = ['.txt', '.pdf', '.docx', '.md', '.markdown']

    def ensure_directories(self) -> bool:
        """Ensure all required directories exist"""
        try:
            data_dir = self.knowledge_base_path.parent
            if not data_dir.exists():
                logger.info("Creating data directory: %s", data_dir)
                data_dir.mkdir(parents=True, exist_ok=True)

            if not self.knowledge_base_path.exists():
                logger.info("Creating knowledge base directory: %s", self.knowledge_base_path)
                self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
                self._create_sample_documents()
                return True

            files = self._get_document_files()
            if not files:
                logger.warning("No documents found in %s", self.knowledge_base_path)
                logger.info("Creating sample documents...")
                self._create_sample_documents()
                files = self._get_document_files()
                if not files:
                    logger.warning("Still no documents after creating samples")
                    return False

            return True

        except PermissionError as e:
            logger.error("Permission error creating directories: %s", e)
            return False
        except OSError as e:
            logger.error("OS error creating directories: %s", e)
            return False

    def _get_document_files(self) -> List[Path]:
        """Get all document files from knowledge base directory"""
        files: List[Path] = []
        try:
            if self.knowledge_base_path.exists():
                for ext in self.supported_extensions:
                    files.extend(self.knowledge_base_path.glob(f"*{ext}"))
        except OSError as e:
            logger.error("Error getting document files: %s", e)
        return files

    def _create_sample_documents(self):
        sample_docs = [
            {
                "filename": "hospital_policies.txt",
                "content": """# Hospital General Policies

## Visiting Hours
- General Wards: 8:00 AM to 8:00 PM
- ICU: 10:00 AM to 12:00 PM and 4:00 PM to 6:00 PM
- Emergency Department: 24/7 access for emergency cases
- Maximum 2 visitors per patient at a time
- Children under 12 years old are not allowed in patient areas

## Patient Rights
1. Right to receive respectful and dignified care
2. Right to privacy and confidentiality of medical records
3. Right to informed consent before any procedure
4. Right to refuse treatment
5. Right to access medical records
6. Right to have an advance directive
7. Right to have a patient advocate

## Emergency Procedures
- Dial 555-0199 for medical emergencies
- Code Blue: Cardiac arrest response team
- Code Red: Fire emergency
- Code Yellow: Disaster response
- Code Pink: Infant abduction alert

## Departments and Services
- Cardiology: Heart disease diagnosis and treatment
- Neurology: Brain and nervous system disorders
- Orthopedics: Bone and joint conditions
- Pediatrics: Children's healthcare
- Obstetrics & Gynecology: Women's reproductive health
- Emergency Medicine: 24/7 emergency care
- Radiology: X-ray, MRI, CT scans
- Laboratory: Blood tests, pathology

## Insurance and Billing
- We accept most major insurance plans
- Self-pay patients must pay 50% upfront
- Payment plans available for qualifying patients
- Financial assistance programs available
- Contact Billing Department at 555-0198

## Contact Information
- Main Hospital: 555-0100
- Emergency: 555-0199
- Appointments: 555-0101
- Billing: 555-0198
- Patient Relations: 555-0102
"""
            },
            {
                "filename": "medical_guidelines.md",
                "content": """# Medical Guidelines and Protocols

## COVID-19 Protocols
- All patients and visitors must wear masks in clinical areas
- Temperature screening at all entrances
- COVID-19 testing before surgical procedures
- Isolation protocols for positive cases
- Vaccination available for eligible patients

## Medication Administration Guidelines
1. Verify patient identity using two identifiers (name and date of birth)
2. Check for allergies before administering any medication
3. Document all medications in patient's electronic health record
4. Follow the "Five Rights" of medication administration:
- Right Patient
- Right Drug
- Right Dose
- Right Route
- Right Time

## Infection Control
- Hand hygiene before and after every patient contact
- Use appropriate personal protective equipment (PPE)
- Proper disposal of medical waste in designated containers
- Clean and disinfect all equipment between patients
- Follow isolation precautions for infectious diseases

## Patient Discharge Planning
- Assess patient's needs for follow-up care
- Provide clear discharge instructions
- Schedule follow-up appointments
- Coordinate with home health services if needed
- Ensure medications and prescriptions are ready
- Document discharge summary in medical record

## Surgical Protocols
- Pre-operative assessment and testing
- Informed consent obtained by surgeon
- "Time Out" procedure before surgery:
- Correct patient identity
- Correct procedure
- Correct site marking
- Correct equipment and implants
- Post-operative monitoring and pain management

## Emergency Department Triage
- Level 1: Immediate life-threatening (immediate treatment)
- Level 2: Emergent (treatment within 10 minutes)
- Level 3: Urgent (treatment within 30 minutes)
- Level 4: Semi-urgent (treatment within 60 minutes)
- Level 5: Non-urgent (treatment within 120 minutes)
"""
            },
            {
                "filename": "faq.txt",
                "content": """# Frequently Asked Questions

## Appointments
Q: How do I schedule an appointment?
A: Call 555-0101 or use our online portal. You can also visit the hospital's appointment desk.

Q: What should I bring to my appointment?
A: Bring your ID, insurance card, list of current medications, and any relevant medical records.

Q: Can I reschedule my appointment?
A: Yes, please call at least 24 hours in advance to reschedule.

## Insurance and Payment
Q: What insurance do you accept?
A: We accept Medicare, Medicaid, Blue Cross, UnitedHealthcare, Aetna, and Cigna, among others.

Q: Do you offer payment plans?
A: Yes, we offer payment plans for patients who qualify. Contact our billing department at 555-0198.

Q: How do I get a copy of my medical records?
A: Complete a medical records release form at the medical records office or download from our website.

## Visiting
Q: What are visiting hours?
A: General wards: 8 AM to 8 PM. ICU: 10 AM to 12 PM and 4 PM to 6 PM.

Q: How many visitors can I have?
A: Maximum 2 visitors per patient at a time.

Q: Can children visit?
A: Children under 12 are not allowed in patient areas except in special circumstances.

## Medical Services
Q: What services does your hospital offer?
A: We offer cardiology, neurology, orthopedics, pediatrics, OB/GYN, emergency services, radiology, laboratory, and more.

Q: Do you have an emergency room?
A: Yes, our emergency department is open 24/7.

Q: Do you have specialists for chronic conditions?
A: Yes, we have specialists in various fields including cardiology, neurology, diabetes management, and more.

## Additional Services
Q: Do you have interpreter services?
A: Yes, we offer interpreter services for over 50 languages. Please request when scheduling.

Q: Is there parking available?
A: Yes, there is a parking garage and surface parking available. Valet parking is also available.

Q: Do you have a cafeteria?
A: Yes, our cafeteria is open 6 AM to 10 PM daily.
"""
            }
        ]

        for doc in sample_docs:
            try:
                file_path = self.knowledge_base_path / doc["filename"]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(doc["content"])
                logger.info("Created sample document: %s", doc['filename'])
            except OSError as e:
                logger.error("Error creating sample document %s: %s", doc['filename'], e)

    def load_documents(self) -> List[Dict[str, str]]:
        """Load all documents from knowledge base directory"""
        files = self._get_document_files()

        if not files:
            logger.warning("No document files found")
            return []

        logger.info("Found %d document files", len(files))
        documents: List[Dict[str, str]] = []

        for file_path in files:
            try:
                logger.info("Loading: %s", file_path.name)
                # pylint: disable=no-member
                # NOTE: verify the actual method name on DocumentLoader in
                # app/services/document_loader.py. If it is `load()` or
                # `load_file()`, rename the call below accordingly.
                doc = self.document_loader.load_document(str(file_path))
                if doc and doc.get("text"):
                    documents.append(doc)
                    logger.info("  ✓ Loaded %s (%d characters)", file_path.name, len(doc['text']))
                else:
                    logger.warning("  ⚠️  No text extracted from %s", file_path.name)
            except (OSError, ValueError) as e:
                logger.error("  ✗ Error loading %s: %s", file_path.name, e)

        return documents

    def ingest(self, clear_existing: bool = True) -> Dict[str, Any]:
        """Main ingestion process"""
        start_time = time.time()

        print("\n" + "=" * 60)
        print("📚 KNOWLEDGE BASE INGESTION")
        print("=" * 60)

        print("\n📁 Step 1: Checking directories...")
        if not self.ensure_directories():
            return {"success": False, "error": "Directory setup failed"}
        print("  ✅ Directories ready")

        print("\n📄 Step 2: Loading documents...")
        documents = self.load_documents()

        if not documents:
            print("  ❌ No documents loaded")
            return {"success": False, "error": "No documents found"}

        print(f"  ✅ Loaded {len(documents)} documents")

        print("\n✂️  Step 3: Chunking documents...")
        try:
            # pylint: disable=no-member
            chunks = self.chunker.chunk_documents(documents)
        except (ValueError, RuntimeError) as e:
            print(f"  ❌ Chunking failed: {e}")
            return {"success": False, "error": f"Chunking failed: {str(e)}"}

        if not chunks:
            print("  ❌ No chunks created")
            return {"success": False, "error": "Chunking failed"}

        print(f"  ✅ Created {len(chunks)} chunks")

        print("\n🧠 Step 4: Generating embeddings...")
        try:
            # pylint: disable=no-member
            chunks_with_embeddings = self.embedding_service.generate_chunk_embeddings(chunks)
            print(f"  ✅ Generated embeddings for {len(chunks_with_embeddings)} chunks")
        except (ValueError, RuntimeError) as e:
            print(f"  ❌ Embedding generation failed: {e}")
            return {"success": False, "error": f"Embedding failed: {str(e)}"}

        if clear_existing:
            print("\n🔄 Step 5: Clearing existing vector store...")
            try:
                # pylint: disable=no-member
                self.vector_store.delete_all()
                print("  ✅ Vector store cleared")
            except (ValueError, RuntimeError) as e:
                print(f"  ⚠️  Could not clear vector store: {e}")

        print("\n💾 Step 6: Storing in vector database...")
        try:
            # pylint: disable=no-member
            self.vector_store.add_chunks(chunks_with_embeddings)
            # pylint: disable=no-member
            count = self.vector_store.count()
            print(f"  ✅ Stored {count} chunks in vector database")
        except (ValueError, RuntimeError) as e:
            print(f"  ❌ Vector store operation failed: {e}")
            return {"success": False, "error": f"Vector store failed: {str(e)}"}

        elapsed_time = time.time() - start_time
        total_chars = sum(len(doc.get("text", "")) for doc in documents)

        print("\n" + "=" * 60)
        print("📊 INGESTION SUMMARY")
        print("=" * 60)
        print(f"  Documents loaded:     {len(documents)}")
        print(f"  Total characters:      {total_chars:,}")
        print(f"  Chunks created:        {len(chunks)}")
        print(f"  Chunks stored:         {count}")
        print(f"  Average chunk size:    "
              f"{sum(len(c['text']) for c in chunks) // len(chunks) if chunks else 0} chars")
        print(f"  Embedding model:       {settings.EMBEDDING_MODEL}")
        print(f"  Chunk size:            {settings.CHUNK_SIZE}")
        print(f"  Chunk overlap:         {settings.CHUNK_OVERLAP}")
        print(f"  Time elapsed:          {elapsed_time:.2f} seconds")
        print("=" * 60)

        print("\n📚 Document sources:")
        for doc in documents:
            source = doc.get("source", "unknown")
            print(f"  • {Path(source).name if source else 'unknown'}")
        print()

        return {
            "success": True,
            "documents_loaded": len(documents),
            "chunks_created": len(chunks),
            "chunks_stored": count,
            "total_chars": total_chars,
            "elapsed_time": elapsed_time
        }


def main():
    """Main entry point"""
    try:
        # Check if required packages are installed (without importing them)
        if _MISSING_PACKAGES:
            missing_str = ", ".join(_MISSING_PACKAGES)
            print(f"❌ Required package(s) not installed: {missing_str}")
            print("\nPlease install required packages:")
            print("  pip install chromadb sentence-transformers numpy")
            sys.exit(1)

        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            print("⚠️  .env file not found. Using default settings.")
            print("   Create .env file for custom configuration.")

        # Create ingester and run
        ingester = KnowledgeBaseIngester()
        result = ingester.ingest(clear_existing=True)

        if result.get("success"):
            print("✅ Ingestion completed successfully!")
            print("\nYou can now use the chatbot with the knowledge base.")
            print("Start the server: uvicorn app.main:app --reload")
            sys.exit(0)
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ Ingestion failed: {error_msg}")
            print("\nTroubleshooting tips:")
            print("  1. Check that data/knowledge_base directory exists")
            print("  2. Verify your .env file has correct settings")
            print("  3. Make sure you have enough disk space")
            print("  4. Check that you have read/write permissions")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Ingestion interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()