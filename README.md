# AI-Powered Hospital Knowledge and Appointment Assistant

A FastAPI backend where users can register/login, manage hospital departments/doctors/patients/appointments, upload approved hospital knowledge documents, index them into a vector store, and ask a medical/hospital chatbot grounded in those documents.

---

## Features

### Minimum Features
1. User registration and login.
2. JWT-based protected routes.
3. Department CRUD.
4. Doctor CRUD.
5. Patient CRUD.
6. Appointment CRUD.
7. Staff/admin document upload.
8. Knowledge-base indexing.
9. Chatbot answer from indexed documents.
10. Source references in answer.
11. Emergency/safety response.
12. Swagger documentation.
13. Tests for main workflows.

### Extra Features
1. Chat history page.
2. Admin dashboard.
3. Search/filter doctors by department.
4. Appointment status update.
5. Document list/delete.
6. Better UI for upload and chat.
7. Docker Compose setup.
8. GitHub Actions CI.

---

## Tech Stack

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy ORM
- PostgreSQL
- Alembic
- JWT Authentication
- Passlib / Bcrypt
- ChromaDB (Vector Store)
- Sentence Transformers (Embeddings)
- Groq / OpenAI LLM Integration
- WebSockets
- Docker & Docker Compose
- Pytest

---

## Project Structure
  
hospital-ai-assistant/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── alembic/
│ ├── env.py
│ └── versions/
├── app/
│ ├── main.py
│ ├── api/
│ │ ├── deps.py
│ │ └── v1/
│ │ ├── router.py
│ │ └── endpoints/
│ │ ├── auth.py
│ │ ├── users.py
│ │ ├── departments.py
│ │ ├── doctors.py
│ │ ├── patients.py
│ │ ├── appointments.py
│ │ ├── documents.py
│ │ ├── chat.py
│ │ └── health.py
│ ├── core/
│ │ ├── config.py
│ │ ├── logging.py
│ │ └── security.py
│ ├── db/
│ │ ├── base.py
│ │ ├── session.py
│ │ └── models/
│ │ ├── user.py
│ │ ├── department.py
│ │ ├── doctor.py
│ │ ├── patient.py
│ │ ├── appointment.py
│ │ ├── knowledge_document.py
│ │ ├── knowledge_chunk.py
│ │ ├── chat_session.py
│ │ └── chat_message.py
│ ├── schemas/
│ │ ├── auth.py
│ │ ├── user.py
│ │ ├── department.py
│ │ ├── doctor.py
│ │ ├── patient.py
│ │ ├── appointment.py
│ │ ├── document.py
│ │ └── chat.py
│ ├── crud/
│ │ ├── user.py
│ │ ├── department.py
│ │ ├── doctor.py
│ │ ├── patient.py
│ │ ├── appointment.py
│ │ ├── knowledge_document.py
│ │ └── chat.py
│ ├── services/
│ │ ├── document_loader.py
│ │ ├── chunking.py
│ │ ├── embedding.py
│ │ ├── vector_store.py
│ │ ├── retriever.py
│ │ ├── prompt_builder.py
│ │ ├── rag_service.py
│ │ ├── chat_service.py
│ │ ├── medical_guard.py
│ │ └── emergency_guard.py
│ ├── llm/
│ │ ├── base.py
│ │ ├── factory.py
│ │ ├── retrieval_only.py
│ │ └── groq_provider.py
│ ├── websocket/
│ │ ├── manager.py
│ │ └── chat_handler.py
│ ├── static/
│ │ ├── chat.html
│ │ ├── chat.js
│ │ └── styles.css
│ └── scripts/
│ ├── ingest_knowledge_base.py
│ ├── create_admin.py
│ └── check_local_setup.py
├── tests/
│ ├── conftest.py
│ ├── unit/
│ └── integration/
└── data/
├── knowledge_base/
├── storage/
├── vector_index/
└── .gitkeep

text

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (optional)
- Git

---

## Environment Variables

Copy `.env.example` to `.env` and update values:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db
DATABASE_URL_TEST=postgresql://user:password@localhost:5432/hospital_db_test
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
APP_NAME=Hospital AI Assistant
DEBUG=True
LOG_LEVEL=INFO
.env is not committed. Only .env.example is committed.

Local Setup
1. Clone Repository
bash
git clone <repo-url>
cd hospital-ai-assistant
2. Create Virtual Environment
bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
3. Install Dependencies
bash
pip install -r requirements.txt
4. Configure Environment
bash
cp .env.example .env
# Edit .env with your database and API keys
5. Create Database
bash
createdb hospital_db
6. Run Migrations
bash
alembic revision --autogenerate -m "init"
alembic upgrade head
7. Create Admin User
bash
python -m app.scripts.create_admin \
  --email admin@example.com \
  --username admin \
  --full-name "Admin User" \
  --password admin123
8. Ingest Knowledge Base
Place PDF/DOCX/TXT/MD files in data/knowledge_base/, then run:

bash
python -m app.scripts.ingest_knowledge_base --dir data/knowledge_base
9. Run Server
bash
uvicorn app.main:app --reload
Open:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Chat UI: http://localhost:8000/

10. Verify Setup
bash
python -m app.scripts.check_local_setup
Docker Setup
Build and Run
bash
docker-compose up --build
Run Migrations Inside Container
bash
docker-compose exec api alembic upgrade head
Create Admin Inside Container
bash
docker-compose exec api python -m app.scripts.create_admin \
  --email admin@example.com \
  --username admin \
  --full-name "Admin User" \
  --password admin123
API Endpoints
Health
Method	Endpoint	Auth	Description
GET	/api/v1/health/	Public	Health check
Authentication
Method	Endpoint	Auth	Description
POST	/api/v1/auth/register	Public	Register new user
POST	/api/v1/auth/login	Public	Login and get JWT
GET	/api/v1/auth/me	User	Get current user info
User Management (Admin Only)
Method	Endpoint	Auth	Description
GET	/api/v1/auth/users	Admin	Get all users
GET	/api/v1/auth/users/{user_id}	Admin	Get user by ID
PUT	/api/v1/auth/users/{user_id}	Admin	Update user
PATCH	/api/v1/auth/users/{user_id}/role	Admin	Update user role
DELETE	/api/v1/auth/users/{user_id}	Admin	Delete user
Departments
Method	Endpoint	Auth	Description
GET	/api/v1/departments/	User	Get all departments
GET	/api/v1/departments/{id}	User	Get department by ID
POST	/api/v1/departments/	Admin	Create department
PUT	/api/v1/departments/{id}	Admin	Update department
DELETE	/api/v1/departments/{id}	Admin	Delete department
Doctors
Method	Endpoint	Auth	Description
GET	/api/v1/doctors/	User	Get all doctors (filter by department/specialization)
GET	/api/v1/doctors/{id}	User	Get doctor by ID
POST	/api/v1/doctors/	Admin	Create doctor
PUT	/api/v1/doctors/{id}	Admin	Update doctor
DELETE	/api/v1/doctors/{id}	Admin	Delete doctor
Patients
Method	Endpoint	Auth	Description
GET	/api/v1/patients/	User	Get all patients
GET	/api/v1/patients/{id}	User	Get patient by ID
POST	/api/v1/patients/	Admin	Create patient
PUT	/api/v1/patients/{id}	Admin	Update patient
DELETE	/api/v1/patients/{id}	Admin	Delete patient
Appointments
Method	Endpoint	Auth	Description
GET	/api/v1/appointments/	User	Get all appointments (filter by patient/doctor/date)
GET	/api/v1/appointments/{id}	User	Get appointment by ID
POST	/api/v1/appointments/	User	Create appointment
PUT	/api/v1/appointments/{id}	User	Update appointment
PATCH	/api/v1/appointments/{id}/status	User	Update appointment status
DELETE	/api/v1/appointments/{id}	Admin	Delete appointment
Documents
Method	Endpoint	Auth	Description
POST	/api/v1/documents/upload	Admin	Upload and index document
GET	/api/v1/documents/	Admin	List documents
DELETE	/api/v1/documents/{id}	Admin	Delete document
Chat
Method	Endpoint	Auth	Description
POST	/api/v1/chat/	User	Send chat message
GET	/api/v1/chat/sessions	User	Get chat sessions
WebSocket
Protocol	Endpoint	Auth	Description
WS	/ws/chat?token={jwt_token}	User	Real-time chat
Testing
Run all tests:

bash
pytest -q
Run unit tests only:

bash
pytest tests/unit -q
Run integration tests only:

bash
pytest tests/integration -q
RAG Pipeline
Upload – Admin uploads PDF/DOCX/TXT/MD.

Extract – Text is extracted from document.

Chunk – Text is split into overlapping chunks.

Embed – Each chunk is converted into a vector embedding.

Store – Vectors are stored in ChromaDB.

Query – User question is embedded.

Retrieve – Top-k similar chunks are retrieved.

Prompt – Context + question is sent to LLM.

Answer – LLM returns grounded answer with sources.

Chat Modes
Retrieval Only – Returns most relevant context without LLM.

Groq – Uses Groq LLM for generated answers.

Emergency Handling
If a query contains emergency keywords (e.g., “chest pain”, “stroke”, “bleeding”), the system returns an emergency alert directing the user to call emergency services immediately.

Git Commands
Clone:

bash
git clone <repo-url>
cd <repo-folder>
Check status:

bash
git status
Create branch:

bash
git switch -c feature/my-work
Add and commit:

bash
git add .
git commit -m "Add hospital RAG chatbot setup"
Push:

bash
git push -u origin feature/my-work
Pull latest:

bash
git pull
Show history:

bash
git log --oneline
Classroom Demo Order
Show folder structure.

Open .env.example.

Explain why .env is not committed.

Start server.

Open /docs.

Call health endpoint.

Register/login.

Create department.

Create patient.

Create doctor.

Create appointment.

Ingest knowledge base.

Ask chatbot a hospital question.

Ask chatbot an unrelated question.

Ask an emergency-style question.

Show tests.

Run pytest -q.

Explain Docker only after students understand local run.

Final Capstone Submission
Students should submit:

GitHub repository link.

README with setup commands.

.env.example, not .env.

Database migration files.

Source code.

Sample knowledge documents.

Test files.

Screenshots or short demo video:

Swagger health endpoint.

Login response.

CRUD endpoint.

Document upload/indexing.

Chatbot answer with sources.

Short explanation:

What is RAG?

What is chunking?

What is embedding?

What is vector search?

Why JWT is used?

Why FastAPI is used?

Concept Explanations
What is RAG?
Retrieval-Augmented Generation (RAG) combines document retrieval with LLM generation. It retrieves relevant chunks from a knowledge base and uses them as context for the LLM to produce grounded answers.

What is Chunking?
Chunking is splitting large documents into smaller overlapping pieces so they can be embedded and retrieved efficiently.

What is Embedding?
An embedding is a numerical vector representation of text that captures its semantic meaning. Similar texts have similar vectors.

What is Vector Search?
Vector search finds the most similar vectors (and therefore text chunks) to a query vector using distance metrics like cosine similarity.

Why JWT?
JWT (JSON Web Token) is used for stateless authentication. The server issues a signed token; the client sends it with each request, and the server verifies it without storing session state.

Why FastAPI?
FastAPI is modern, fast, supports async, automatic OpenAPI docs, Pydantic validation, dependency injection, and is ideal for building REST APIs and WebSocket services.

License
This project is for educational purposes.  
