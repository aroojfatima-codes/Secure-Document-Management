# Secure Document Management System (SDMS)

A production-grade **Secure Document Management System** with hybrid cryptography (AES-256-CBC + RSA-2048-OAEP), SHA-256 integrity verification, face recognition authentication, TOTP 2FA, Role-Based Access Control (RBAC), and a full audit trail. Features both a **CustomTkinter desktop GUI** (14 screens) and a **FastAPI REST API**.

---

## Features

| Feature | Description |
|---------|-------------|
| **Hybrid Cryptography** | AES-256-CBC encrypts documents; RSA-2048-OAEP wraps the AES key |
| **Integrity Verification** | SHA-256 hashing on upload; verified on download |
| **Secure Sharing** | Re-encrypt AES key with recipient's RSA public key; encrypted file untouched |
| **Face Recognition** | OpenCV Haar Cascade detection + LBPH recognition + Chi-Square matching |
| **TOTP 2FA** | RFC 6238 time-based one-time passwords via HMAC-SHA256 |
| **RBAC** | Admin, Editor, Viewer roles with 15 granular permissions |
| **Audit Trail** | Every action logged with 32 action types, 4 severity levels, IP, timestamp |
| **Desktop GUI** | 14-screen CustomTkinter app with dark/light theme, animations, charts |
| **REST API** | Full CRUD via FastAPI with JWT auth, auto-generated Swagger docs |
| **MongoDB** | Document persistence with repository pattern, indexing, pagination |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Desktop GUI** | CustomTkinter 5.2+ |
| **REST API** | FastAPI 0.115+ / Uvicorn |
| **Database** | MongoDB 7.0+ (PyMongo 4.10+) |
| **Symmetric Crypto** | PyCryptodome (AES-256-CBC) |
| **Asymmetric Crypto** | PyCryptodome (RSA-2048 OAEP-SHA-256) |
| **Face Recognition** | OpenCV contrib (Haar Cascade + LBPH) |
| **JWT** | PyJWT (HS256) |
| **Testing** | pytest 8.3+ |
| **Linting** | Ruff 0.8+ |
| **Type Checking** | mypy 1.13+ |

---

## Project Structure

```
secure-document-management/
├── main.py                  # GUI entry point
├── api/                     # FastAPI REST API (routes, auth, schemas)
├── config/                  # Singleton Settings from .env
├── controllers/             # Thin facade layer (auth, document, face, audit)
├── crypto/                  # AES, RSA, SHA-256, key generation, Base64
├── database/                # MongoDB manager + repositories (CRUD, pagination)
├── exceptions/              # Typed exception hierarchy
├── gui/                     # CustomTkinter app (14 pages, 25+ components)
│   ├── app.py               # Main App class (navigation, theming)
│   ├── theme.py             # Dark/light theme engine
│   ├── components/          # Cards, charts, dialogs, forms, tables, sidebar, topbar
│   └── pages/               # Login, register, dashboard, documents, upload, etc.
├── logger/                  # Rotating-file + stderr logging
├── models/                  # User, Document, AuditLog data models
├── services/                # Business logic (auth, registration, document, face, audit)
├── storage/                 # On-disk encrypted document storage
├── utilities/               # Permissions (RBAC), TOTP (2FA), helpers
├── tests/                   # pytest suite (9 test files)
├── Documentation/           # Detailed architecture, security, GUI docs
├── .env                     # Environment configuration
├── pyproject.toml           # mypy config
├── requirements.txt         # Python dependencies
└── nginx.conf               # Nginx reverse proxy config
```

---

## Prerequisites

- **Python 3.10+**
- **MongoDB 7.0+** (running locally or reachable host)

---

## Installation

```bash
git clone https://github.com/your-org/secure-document-management.git
cd secure-document-management

python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Linux:   source venv/bin/activate

pip install -r requirements.txt
```

## Environment Configuration

Edit `.env` to match your setup:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `secure_document_db` | Database name |
| `STORAGE_ENCRYPTED_DIR` | `storage/encrypted_documents` | Encrypted file path |
| `STORAGE_MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `APP_ENVIRONMENT` | `development` | `development`, `staging`, `production` |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |

---

## Running the Application

### Desktop GUI

```bash
python main.py
```

### REST API

```bash
uvicorn api.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for Swagger UI or `http://localhost:8000/redoc` for ReDoc.

---

## Code Quality

```bash
ruff check .          # Lint
mypy .                # Type-check
pytest                # Run tests (9 test suites, ~90 tests)
pytest --cov=.        # With coverage
```

---

## Architecture

```
┌──────────────────────────────────────┐
│     Presentation Layer               │
│   gui/ (CustomTkinter, 14 pages)    │
│   api/ (FastAPI, REST endpoints)     │
├──────────────────────────────────────┤
│     Controller Layer (Facade)        │
│   controllers/ (thin coordinators)   │
├──────────────────────────────────────┤
│     Business Logic Layer             │
│   services/ (orchestration)          │
├──────────────────────────────────────┤
│     Infrastructure Layer             │
│   crypto/ │ database/ │ models/      │
└──────────────────────────────────────┘
```

---

## License

Educational project — Information Security course. All rights reserved.
