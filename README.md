# Secure Document Management System (SDMS)

A production-grade **Secure Document Management System** developed as part of an Information Security course. The system implements **Hybrid Cryptography** (AES-256 + RSA), **SHA-256 integrity verification**, **Role-Based Access Control (RBAC)**, and secure document sharing on top of **MongoDB**.

> **Current Milestone — User Authentication & Session Management**  
> This milestone implements secure login, logout, and session management: SHA-256 password verification via the crypto module, credential validation against stored user records, singleton SessionManager with create/validate/destroy lifecycle, role-based authorization checks, and a CLI menu that adapts based on authentication state. Only authenticated users can access protected operations in future milestones.

---

## Objectives

| Objective | Description |
| --------- | ----------- |
| **Hybrid Cryptography** | Encrypt documents with AES-256 symmetric keys and wrap those keys with RSA-4096 public-key encryption. |
| **Integrity Verification** | Compute and verify SHA-256 hashes for every stored document. |
| **Secure Sharing** | Share encrypted documents between authenticated users via granular permissions. |
| **RBAC** | Role-based access control with Admin, Editor, and Viewer roles. |
| **MongoDB** | Persist users, documents, metadata, and access logs in a document database. |

---

## Directory Structure

```
secure-document-management/
├── config/                  # Centralised configuration (Settings singleton)
│   ├── __init__.py
│   └── settings.py
├── controllers/             # Request-handling layer (Auth, Document)
│   ├── __init__.py
│   ├── auth_controller.py
│   └── document_controller.py
├── crypto/                  # Cryptographic library (standalone, reusable)
│   ├── __init__.py           # Public API exports
│   ├── interfaces.py         # BaseCipher[_PayloadT], BaseHasher ABCs
│   ├── exceptions.py         # AESError, RSAError, HashingError, etc.
│   ├── base64_utils.py       # b64_encode / b64_decode helpers
│   ├── key_generator.py      # Secure random: keys, IVs, salts, tokens
│   ├── hashing.py            # SHA256Hasher (strings, files, streams)
│   ├── payload.py            # EncryptedPayload, EncryptedKeyPayload
│   ├── aes_cipher.py         # AESCipher (AES-256-CBC, PKCS7 padding)
│   └── rsa_cipher.py         # RSACipher (RSA-2048-OAEP-SHA-256)
├── database/                # Database layer (connection, repositories)
│   ├── __init__.py           # Public API exports
│   ├── manager.py            # DatabaseManager (singleton, pool, indexes)
│   ├── exceptions.py         # DuplicateKeyError, UserNotFoundError, etc.
│   └── repositories/         # Repository pattern
│       ├── __init__.py
│       ├── base.py           # BaseRepository (generic CRUD, pagination)
│       ├── user_repository.py      # UserRepository
│       └── document_repository.py  # DocumentRepository
├── exceptions/              # Custom exception hierarchy
│   ├── __init__.py
│   └── custom_exceptions.py
├── logger/                  # Reusable logging configuration
│   ├── __init__.py
│   └── logging_config.py
├── models/                  # ORM-style data models (User, Document)
│   ├── __init__.py
│   ├── document.py
│   └── user.py
├── services/                # Business-logic layer (Auth, Document)
│   ├── __init__.py
│   ├── auth_service.py
│   └── document_service.py
├── storage/                 # On-disk encrypted-document management
│   ├── __init__.py
│   └── manager.py
├── utilities/               # Stateless helper functions
│   ├── __init__.py
│   └── helpers.py
├── cli/                     # Command-line interface
│   ├── __init__.py
│   └── main.py
├── tests/                   # Test suite (empty scaffolding)
│   └── __init__.py
├── logs/                    # Application log files (auto-created)
│   └── .gitkeep
├── .env                     # Environment variables (not tracked)
├── .gitignore
├── main.py                  # Application entry point
├── README.md
└── requirements.txt
```

### Module Responsibilities

| Module | Responsibility |
| ------ | -------------- |
| `config/`   | Load `.env` file, provide a singleton `Settings` object. |
| `database/` | Singleton `DatabaseManager` with connection pooling, `BaseRepository` with generic CRUD, `UserRepository` and `DocumentRepository` with domain-specific queries. |
| `crypto/`   | Standalone security library: AES-256-CBC, RSA-2048-OAEP, SHA-256 hashing, key generation, Base64, payload DTOs. |
| `controllers/` | Thin layer that receives input and delegates to services. |
| `models/`   | Pydantic-inspired data classes for User, Document, etc. |
| `services/` | Encapsulate business logic and orchestrate crypto+storage+database. |
| `storage/`  | Manage encrypted document files on disk. |
| `utilities/`| Pure helper functions (timestamp, ID generation, sanitisation). |
| `exceptions/` | Typed exception hierarchy for fine-grained error handling. |
| `logger/`   | Rotating-file + console logging with a single factory function. |
| `cli/`      | Welcome banner and menu system (future). |
| `tests/`    | Unit & integration tests (future). |

---

## Prerequisites

- **Python 3.13+**
- **MongoDB 7.0+** (running locally or on a reachable host)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/secure-document-management.git
cd secure-document-management

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
#    Windows (PowerShell):
.\venv\Scripts\Activate.ps1
#    Linux / macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## MongoDB Setup

Ensure MongoDB is installed and running:

```bash
# Start MongoDB (default port 27017)
mongod --dbpath /path/to/data
```

No collections need to be created manually — the application will initialise them in a later milestone.

---

## Environment Configuration

Copy the example environment file and adjust values as needed:

```bash
# The .env file is already present in the repository root.
# Edit it to match your local setup:
```

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | `secure_document_db` | Database name |
| `MONGODB_CONNECT_TIMEOUT_MS` | `5000` | Connection timeout (ms) |
| `MONGODB_SERVER_SELECTION_TIMEOUT_MS` | `5000` | Server selection timeout (ms) |
| `STORAGE_ENCRYPTED_DIR` | `storage/encrypted_documents` | Encrypted file storage path |
| `STORAGE_TEMP_DIR` | `storage/temp` | Temporary file path |
| `STORAGE_MAX_FILE_SIZE_MB` | `50` | Maximum upload size (MB) |
| `APP_ENVIRONMENT` | `development` | `development`, `staging`, or `production` |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `LOG_DIR` | `logs` | Directory for log files |

> **Security note:** The `.env` file is listed in `.gitignore` and must **never** be committed to version control.

---

## Running the Application

```bash
python main.py
```

The application will:
1. Load configuration from `.env`.
2. Initialise the rotating-file logger.
3. Connect to MongoDB (verifies connectivity with a `ping` command).
4. Create storage directories (`storage/encrypted_documents/`, `storage/temp/`).
5. Display a welcome banner.
6. Disconnect from MongoDB and exit cleanly.

Expected output:

```
   ╔══════════════════════════════════════════════════════╗
   ║     Secure Document Management System  v1.0.0       ║
   ║              Information Security                    ║
   ╚══════════════════════════════════════════════════════╝

  Environment  :  development
  Log Level    :  DEBUG
  Log File     :  ...\logs\sdms.log
  MongoDB URI  :  mongodb://localhost:27017
  Database     :  secure_document_db
  Storage      :  ...\storage\encrypted_documents
```

---

## Code Quality

This project follows **PEP-8** conventions and uses modern Python features:

- **Type hints** on all public functions and methods.
- **Docstrings** on all public classes, methods, and functions (reStructuredText style).
- **Modular architecture** with single-responsibility packages.
- **Abstract base classes** in the crypto module for polymorphic cipher implementations.
- **Singleton pattern** for Settings and DatabaseManager.
- **Rotating file handler** prevents unbounded log growth.

Development tools (install via `requirements.txt`):

```bash
# Lint
ruff check .

# Type-check
mypy .

# Test
pytest
```

---

## License

This project is developed for educational purposes as part of an Information Security course. All rights reserved.

---

## Future Milestones

| Milestone | Features |
| --------- | -------- |
| **1** | Project scaffolding, configuration, logging, DB connection, storage setup |
| **1** | Project scaffolding, configuration, logging, DB connection, storage setup |
| **2** | Cryptography module: AES-256-CBC, RSA-2048-OAEP, SHA-256, key generation, Base64, payload DTOs |
| **1** | Project scaffolding, configuration, logging, DB connection, storage setup |
| **2** | Cryptography module: AES-256-CBC, RSA-2048-OAEP, SHA-256, key generation, Base64, payload DTOs |
| **3** | Database layer: models, repositories, indexes, connection pooling, typed exceptions |
| **1** | Project scaffolding, configuration, logging, DB connection, storage setup |
| **2** | Cryptography module: AES-256-CBC, RSA-2048-OAEP, SHA-256, key generation, Base64, payload DTOs |
| **3** | Database layer: models, repositories, indexes, connection pooling, typed exceptions |
| **4** | User registration: validation, password hashing, RSA key generation, CLI registration menu |
| **5** (current) | User authentication & session management: login, logout, session lifecycle, role checks |
| **6** | Document upload, encrypt, download, decrypt |
| **7** | Secure document sharing with hybrid encryption |
| **8** | Audit logging, input sanitisation, security hardening |
