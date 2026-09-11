# 🏥 AI-Powered Hospital Knowledge and Appointment Assistant

A comprehensive FastAPI backend system that combines hospital management with an AI-powered chatbot using RAG (Retrieval-Augmented Generation) technology.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Docker Setup](#docker-setup)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project is a complete hospital management system that integrates:
- **Hospital Operations**: Manage departments, doctors, patients, and appointments
- **Knowledge Management**: Upload and index hospital documents
- **AI Chatbot**: RAG-powered assistant that answers questions based on hospital knowledge
- **Security**: JWT-based authentication with role-based access control

## ✨ Features

### Core Features
- ✅ User registration and login with JWT authentication
- ✅ Department CRUD operations
- ✅ Doctor CRUD operations
- ✅ Patient CRUD operations
- ✅ Appointment CRUD operations
- ✅ Document upload (PDF, DOCX, TXT, MD)
- ✅ Knowledge-base indexing with embeddings
- ✅ RAG-powered chatbot with source references
- ✅ Emergency response detection
- ✅ Swagger API documentation
- ✅ Comprehensive test suite

### Advanced Features
- 🔍 Search/filter doctors by department
- 📊 Admin dashboard
- 💬 Chat history
- 📄 Document management (list/delete)
- 🎨 Modern web UI for chat
- 🐳 Docker Compose setup
- 🔄 GitHub Actions CI/CD

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication
- **ChromaDB** - Vector database
- **Sentence Transformers** - Embeddings

### AI/ML
- **LangChain** - RAG framework
- **Groq** - LLM provider
- **Sentence-BERT** - Embedding model

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container setup
- **GitHub Actions** - CI/CD

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- Docker and Docker Compose (optional)
- Git
- Groq API key (or OpenAI API key)

## 🚀 Installation

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd hospital-ai-assistant

# Create and activate virtual environment 

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate

# Install dependencies

pip install --upgrade pip
pip install -r requirements.txt

#Configure Environment

cp .env.example .env

#Setup Database

# Create database
createdb hospital_ai

# Run migrations
alembic upgrade head

# Create Admin User

python scripts/create_admin.py

# Run server

python -m uvicorn main:app --reload

