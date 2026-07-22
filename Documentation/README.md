# Secure Document Management System (SDMS)

> A production-grade, cryptographically secured document management platform
> built with Python, CustomTkinter, MongoDB, and OpenCV — designed as a
> university Final Year Project.

---

## Table of Contents

1. [Project Description](#project-description)
2. [Problem Statement](#problem-statement)
3. [Objectives](#objectives)
4. [Motivation](#motivation)
5. [Key Features](#key-features)
6. [Technologies Used](#technologies-used)
7. [Project Structure](#project-structure)
8. [Installation Guide](#installation-guide)
9. [Login & Registration](#login--registration)
10. [Screenshots](#screenshots)
11. [Testing](#testing)
12. [Future Enhancements](#future-enhancements)
13. [Contributors](#contributors)
14. [License](#license)

---

## Project Description

The **Secure Document Management System (SDMS)** is a desktop application that
allows users to upload, store, retrieve, and share documents with end-to-end
encryption. Files are encrypted using a **hybrid cryptosystem** (AES-256-CBC +
RSA-2048-OAEP) before being written to disk, and all metadata is persisted in
**MongoDB**. Access is governed by **Role-Based Access Control (RBAC)** with
three roles — *admin*, *editor*, and *viewer* — and every user action is
recorded in a tamper-evident **audit log**. An additional **face-recognition
module** based on OpenCV's LBPH algorithm provides biometric login and
enrollment capabilities.

---

## Problem Statement

Traditional document management systems store files in plaintext or with weak
encryption, making them vulnerable to unauthorized access, data breaches, and
insider threats. Many lack granular access control, comprehensive audit trails,
or any form of biometric verification. SDMS addresses these gaps by combining
military-grade cryptography, role-based authorization, and facial biometrics
into a single, user-friendly desktop application.

---

## Objectives

| # | Objective |
|---|-----------|
| 1 | Implement hybrid encryption (AES-256-CBC + RSA-2048) for all stored documents |
| 2 | Provide RBAC with admin, editor, and viewer roles |
| 3 | Integrate OpenCV LBPH face recognition for biometric login |
| 4 | Maintain a complete, immutable audit log of all user actions |
| 5 | Support secure document sharing with per-user key re-encryption |
| 6 | Deliver a modern, intuitive GUI using CustomTkinter |
| 7 | Offer a secondary CLI interface for headless/legacy use |
| 8 | Verify document integrity using SHA-256 checksums |
| 9 | Store encrypted files on the local filesystem with metadata in MongoDB |

---

## Motivation

With the exponential growth of digital documents in both corporate and academic
environments, the need for a secure, auditable, and user-friendly document
management solution has never been greater. SDMS was motivated by the desire to
demonstrate that strong cryptographic principles, biometric authentication, and
modern UX design can coexist in a single open-source project — and that
security does not have to come at the expense of usability.

---

## Key Features

### Cryptography

- **Hybrid Encryption** — AES-256-CBC encrypts document contents; RSA-2048-OAEP
  wraps the AES keys so only authorized recipients can decrypt.
- **SHA-256 Integrity Checks** — every document's plaintext hash is computed at
  upload time and re-verified at download time to detect tampering.
- **Base64 Payload Encoding** — encrypted blobs are Base64-encoded for safe
  storage in MongoDB and filesystem paths.

### Access Control & Authentication

- **Role-Based Access Control (RBAC)** — three roles (`admin`, `editor`,
  `viewer`) with distinct permission sets for upload, download, share, and
  audit-view operations.
- **Password Authentication** — passwords are hashed with SHA-256 and compared
  server-side.
- **Face Recognition Login** — users can enroll their face and subsequently log
  in biometrically via OpenCV's LBPH face recognizer.
- **Session Management** — the `SessionManager` singleton tracks the current
  user, role, and session metadata across the application lifetime.

### Document Management

- **Upload & Encrypt** — files are read, AES-encrypted, RSA-wrapped, hashed,
  and stored to disk with metadata saved to MongoDB.
- **Download & Decrypt** — the stored AES key is decrypted with the user's RSA
  private key, the file is AES-decrypted, the SHA-256 hash is verified, and
  the plaintext is saved to a user-selected location.
- **Secure Sharing** — documents can be shared with other users; the AES key is
  re-encrypted with the recipient's RSA public key.
- **Search** — full-text search across document names, owners, and metadata.
- **Soft Delete** — documents are flagged as deleted rather than removed, preserving
  audit trail integrity.

### Audit & Compliance

- **Comprehensive Audit Logging** — every action (login, upload, download,
  share, face enrollment, etc.) is recorded with timestamp, user, role,
  severity, and resource details.
- **Audit Log Viewer** — admins can browse and search audit logs from the GUI.

### User Interface

- **14 GUI Pages** — Login, Register, Dashboard, Documents, Document Detail,
  Upload, Download, Share, Shared With Me, Search, Face Recognition, Audit
  Logs, Settings, and Profile.
- **Sidebar Navigation** with collapsible menu and role-aware menu items.
- **TopBar** with breadcrumb trail, theme switcher (light/dark), and user info.
- **Smooth Animations** — fade-in page transitions and animated sidebar toggle.
- **Dark / Light Theme** — instant theme switching via `ThemeManager`.
- **Responsive Layout** — pages adapt to window resize with grid-based layouts.
- **Toast Notifications** — non-intrusive success/error/info messages.

---

## Technologies Used

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| Language | Python | 3.11+ | Core runtime |
| GUI | CustomTkinter | 5.2+ | Modern tkinter widgets, theming |
| Database | MongoDB | 7.0+ | Metadata & audit log storage |
| Database Driver | PyMongo | 4.10+ | Python MongoDB driver |
| Symmetric Crypto | PyCryptodome | 3.23+ | AES-256-CBC encryption |
| Asymmetric Crypto | PyCryptodome | 3.23+ | RSA-2048-OAEP key wrapping |
| Hashing | PyCryptodome | 3.23+ | SHA-256 integrity verification |
| Face Recognition | OpenCV | 4.10+ | LBPH face recognizer, camera capture |
| Numerical | NumPy | 1.26+ | Array operations for face encodings |
| Env Management | python-dotenv | 1.0+ | `.env` file loading |
| Testing | pytest | 8.3+ | Unit & integration tests |
| Coverage | pytest-cov | 6.0+ | Code coverage reporting |
| Linting | Ruff | 0.8+ | Fast Python linter & formatter |
| Type Checking | mypy | 1.13+ | Static type analysis |

---

## Project Structure

```
Secure-Document-Management/
│
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # mypy / tool configuration
├── .env                             # Environment variables (not committed)
├── .gitignore                       # Git ignore rules
│
├── config/
│   ├── __init__.py
│   └── settings.py                  # Singleton Settings (loads .env)
│
├── models/
│   ├── __init__.py
│   ├── base.py                      # BaseModel (to_dict / from_dict ABC)
│   ├── user.py                      # User dataclass
│   ├── document.py                  # Document + SharedUser dataclasses
│   └── audit.py                     # AuditLog dataclass + enums
│
├── crypto/
│   ├── __init__.py
│   ├── interfaces.py                # BaseCipher / BaseHasher ABCs
│   ├── payload.py                   # EncryptedPayload / EncryptedKeyPayload
│   ├── aes_cipher.py                # AES-256-CBC implementation
│   ├── rsa_cipher.py                # RSA-2048-OAEP implementation
│   ├── key_generator.py             # RSA key-pair generation
│   ├── hashing.py                   # SHA-256 hash / verify
│   ├── base64_utils.py              # Base64 encode / decode helpers
│   └── exceptions.py                # Crypto-specific exceptions
│
├── database/
│   ├── __init__.py
│   ├── manager.py                   # DatabaseManager (MongoDB connection)
│   ├── exceptions.py                # Database-specific exceptions
│   └── repositories/
│       ├── __init__.py
│       ├── base.py                  # BaseRepository (CRUD template)
│       ├── user_repository.py       # User CRUD operations
│       ├── document_repository.py   # Document CRUD operations
│       ├── audit_repository.py      # Audit log CRUD operations
│       └── counter_repository.py    # Auto-increment ID counters
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py              # Login / password verification
│   ├── registration_service.py      # New user registration
│   ├── session_manager.py           # Singleton session state
│   ├── document_service.py          # Core document CRUD orchestration
│   ├── document_upload_service.py   # Upload pipeline (encrypt + store)
│   ├── document_download_service.py # Download pipeline (decrypt + verify)
│   ├── document_listing_service.py  # List / search documents
│   ├── document_sharing_service.py  # Share with re-encryption
│   ├── document_id_service.py       # ID generation / resolution
│   ├── audit_service.py             # Audit log creation & retrieval
│   └── face_recognition_service.py  # LBPH enroll / recognize
│
├── controllers/
│   ├── __init__.py
│   ├── auth_controller.py           # Login / register / logout facade
│   ├── document_controller.py       # Document operations facade
│   ├── audit_controller.py          # Audit log facade
│   └── face_controller.py           # Face recognition facade
│
├── gui/
│   ├── __init__.py
│   ├── app.py                       # SDMSApp (main window, routing)
│   ├── theme.py                     # ThemeManager singleton, colors, fonts
│   ├── animations.py                # Fade-in / slide transitions
│   ├── assets.py                    # Icon & image loaders
│   ├── smooth_scrolling.py          # Smooth scroll implementation
│   │
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── login_page.py            # Login form + face-login button
│   │   ├── register_page.py         # Registration form
│   │   ├── dashboard_page.py        # Overview cards & stats
│   │   ├── documents_page.py        # Document list grid
│   │   ├── document_detail_page.py  # Single document detail view
│   │   ├── upload_page.py           # File picker + upload form
│   │   ├── download_page.py         # File picker + download form
│   │   ├── share_page.py            # Share form with user selector
│   │   ├── shared_page.py           # Documents shared with me
│   │   ├── search_page.py           # Search bar + results
│   │   ├── face_page.py             # Face enrollment / verification
│   │   ├── audit_page.py            # Audit log table
│   │   ├── settings_page.py         # Theme & preferences
│   │   └── profile_page.py          # User profile view
│   │
│   └── components/
│       ├── __init__.py
│       ├── sidebar.py               # Collapsible sidebar navigation
│       ├── topbar.py                # Top bar (breadcrumb, theme, user)
│       ├── cards.py                 # Stat cards for dashboard
│       ├── charts.py                # Chart widgets
│       ├── dialogs.py               # Toast notifications & modals
│       ├── forms.py                 # Reusable form field components
│       ├── loading.py               # Loading spinner / progress
│       └── tables.py                # Reusable table widget
│
├── storage/
│   ├── __init__.py
│   ├── manager.py                   # StorageManager (dir init)
│   ├── encrypted_documents/         # Encrypted file storage
│   └── temp/                        # Temporary file staging
│
├── logger/
│   ├── __init__.py
│   └── logging_config.py            # Logging setup (file + console)
│
├── exceptions/
│   ├── __init__.py
│   └── custom_exceptions.py         # All custom exception classes
│
├── utilities/
│   ├── __init__.py
│   └── helpers.py                   # Misc helper functions
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_authentication.py       # Auth service tests
│   ├── test_registration.py         # Registration tests
│   ├── test_document_upload.py      # Upload pipeline tests
│   ├── test_document_download.py    # Download pipeline tests
│   ├── test_document_listing.py     # Listing / search tests
│   ├── test_document_sharing.py     # Sharing tests
│   ├── test_models.py               # Model serialization tests
│   └── test_repositories.py         # Repository CRUD tests
│
├── logs/                            # Runtime log files
└── Documentation/
    ├── README.md                    # This file
    ├── PROJECT_ARCHITECTURE.md      # Architecture documentation
    └── PROJECT_WORKFLOW.md          # Workflow documentation
```

---

## Installation Guide

### Prerequisites

| Requirement | Minimum Version | Notes |
|------------|----------------|-------|
| Python | 3.11 | Must be on `PATH` |
| MongoDB | 7.0 | Local or remote instance |
| pip | 23.0+ | Bundled with Python |
| Webcam | Any | Required for face recognition |
| OS | Windows 10+, macOS, Linux | Tested primarily on Windows |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-org/Secure-Document-Management.git
cd Secure-Document-Management
```

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set Up MongoDB

Ensure MongoDB is running on the default port (`27017`). You can start it with:

```bash
# Windows (if installed as a service)
net start MongoDB

# macOS (Homebrew)
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

Verify the connection:

```bash
mongosh --eval "db.runCommand({ ping: 1 })"
```

### Step 5 — Configure Environment Variables

Copy the example `.env` or edit the existing one:

```ini
APP_NAME=Secure Document Management System
APP_VERSION=1.0.0
APP_ENVIRONMENT=development
LOG_LEVEL=DEBUG
LOG_DIR=logs

MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=secure_document_db
MONGODB_CONNECT_TIMEOUT_MS=5000
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000

STORAGE_ENCRYPTED_DIR=storage/encrypted_documents
STORAGE_TEMP_DIR=storage/temp
STORAGE_MAX_FILE_SIZE_MB=50
```

### Step 6 — Run the Application

```bash
python main.py
```

---

## Login & Registration

SDMS does **not** ship with pre-seeded demo accounts. On first launch you must
create an account:

1. Click **Register** on the login screen.
2. Enter a username, full name, email, password, and select a role.
3. On successful registration you are redirected to the login screen.
4. Log in with your credentials — or click **Login with Face** if you have
   previously enrolled your face biometrics.

> **Note:** Face enrollment is performed from the *Face Recognition* page after
> logging in for the first time.

---

## Screenshots

> Screenshots will be added after the final UI polish pass.

| Page | Preview |
|------|---------|
| Login | *Coming soon* |
| Dashboard | *Coming soon* |
| Documents | *Coming soon* |
| Upload | *Coming soon* |
| Share | *Coming soon* |
| Face Recognition | *Coming soon* |
| Audit Logs | *Coming soon* |

---

## Testing

Run the full test suite:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

Lint the codebase:

```bash
ruff check .
ruff format --check .
```

Type-check:

```bash
mypy .
```

---

## Future Enhancements

| Area | Enhancement |
|------|------------|
| Cloud Storage | Migrate file storage to AWS S3 / MinIO with server-side encryption |
| Zero-Knowledge Proofs | Add ZKP-based document verification without revealing content |
| Database Encryption | Enable MongoDB field-level encryption for at-rest metadata protection |

| Versioning | Document version history with diff comparison |
| Real-Time Sync | WebSocket-based live collaboration on shared documents |
| Mobile Client | React Native companion app with on-device face enrollment |
| Docker | Containerized deployment with `docker-compose` (app + MongoDB) |
| CI/CD | GitHub Actions pipeline for automated test, lint, and release |
| Localization | i18n support for English, Urdu, and Arabic |
| Document Preview | In-app PDF/image preview without full decryption to disk |
| Admin Dashboard | System-wide analytics, user management, and storage monitoring |

---

## Contributors

| Name | Role | Contact |
|------|------|---------|
| *[Your Name]* | Lead Developer & Researcher | *[email]* |
| *[Supervisor Name]* | Project Supervisor | *[email]* |
| *[Team Member 2]* | Backend & Crypto | *[email]* |
| *[Team Member 3]* | GUI & Testing | *[email]* |

---

## License

This project is released for academic purposes as a university Final Year
Project. For questions about usage or contribution, please open an issue on
the repository.
