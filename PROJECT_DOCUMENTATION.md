# Secure Document Management System (SDMS)

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Directory Structure](#3-directory-structure)
4. [Technology Stack](#4-technology-stack)
5. [Setup & Installation](#5-setup--installation)
6. [Configuration](#6-configuration)
7. [Application Entry Points](#7-application-entry-points)
8. [Core Modules Reference](#8-core-modules-reference)
   - 8.1 [Models](#81-models)
   - 8.2 [Cryptography](#82-cryptography)
   - 8.3 [Database Layer](#83-database-layer)
   - 8.4 [Services](#84-services)
   - 8.5 [Controllers](#85-controllers)
   - 8.6 [Utilities](#86-utilities)
   - 8.7 [Exceptions](#87-exceptions)
   - 8.8 [Logging](#88-logging)
9. [GUI Reference](#9-gui-reference)
   - 9.1 [Theme Engine](#91-theme-engine)
   - 9.2 [Components](#92-components)
   - 9.3 [Pages](#93-pages)
   - 9.4 [Animations](#94-animations)
   - 9.5 [Assets](#95-assets)
10. [CLI Reference](#10-cli-reference)
11. [Testing](#11-testing)
12. [Security Model](#12-security-model)
13. [Data Flow](#13-data-flow)

---

## 1. Project Overview

SDMS is a full-stack document management system implementing **hybrid encryption** (AES-256-CBC + RSA-2048) for at-rest document protection, **face recognition** for biometric authentication, **role-based access control** (RBAC), and a complete **audit trail**. The system provides both a GUI (CustomTkinter) and an interactive CLI.

**Key Features:**

- Hybrid encryption: AES-256-CBC for file encryption, RSA-2048 for key wrapping
- SHA-256 integrity verification for all stored documents
- LBPH face recognition (OpenCV) for passwordless login
- Role-based access control (admin/user/viewer)
- MongoDB persistence with repository pattern
- Dark/light theme GUI with 14 page screens
- Interactive menu-driven CLI
- Comprehensive audit logging

---

## 2. Architecture

The project follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                  Entry Points                    │
│            main.py  │  cli/main.py              │
├─────────────────────────────────────────────────┤
│            Presentation Layer                    │
│     gui/ (CustomTkinter)  │  cli/ (menus)       │
├─────────────────────────────────────────────────┤
│           Coordination Layer                     │
│         controllers/ (thin wrappers)            │
├─────────────────────────────────────────────────┤
│             Business Logic Layer                 │
│            services/ (orchestration)            │
├─────────────────────────────────────────────────┤
│              Infrastructure Layer                │
│  crypto/  │  database/  │  models/  │  logger/  │
└─────────────────────────────────────────────────┘
```

**Dependency Flow:** Entry points → Controllers → Services → (Crypto + Database + Models)

Controllers are thin coordinators that delegate business logic to services and log audit events. Services orchestrate multi-step workflows. The crypto and database layers are low-level infrastructure with no upward dependencies.

---

## 3. Directory Structure

```
Secure-Document-Management/
├── main.py                          # Application entry point (56 lines)
├── cli/
│   └── main.py                      # Interactive CLI (632 lines)
├── config/
│   └── settings.py                  # Environment-based config (60 lines)
├── controllers/                     # Presentation coordination
│   ├── auth_controller.py           # Registration, login, logout
│   ├── document_controller.py       # Upload, list, detail, search, download, share
│   ├── face_controller.py           # Face enrollment, login, removal
│   └── audit_controller.py          # Audit log queries
├── crypto/                          # Cryptographic primitives
│   ├── aes_cipher.py                # AES-256-CBC encryption/decryption
│   ├── rsa_cipher.py                # RSA-2048 OAEP-SHA-256 encryption
│   ├── hashing.py                   # SHA-256 hashing
│   ├── key_generator.py             # Secure random key/IV/token generation
│   ├── interfaces.py                # Abstract crypto interfaces
│   ├── base64_utils.py             # Base64 encode/decode utilities
│   ├── payload.py                   # Encrypted payload dataclass
│   └── exceptions.py                # Crypto-specific exceptions
├── database/                        # Persistence layer
│   ├── manager.py                   # MongoDB connection manager
│   ├── exceptions.py                # Database exceptions
│   └── repositories/
│       ├── base.py                  # Abstract base repository (CRUD)
│       ├── user_repository.py       # User CRUD + biometric data
│       ├── document_repository.py   # Document CRUD + ACL queries
│       └── audit_repository.py      # Audit log queries + filters
├── models/                          # Data models
│   ├── base.py                      # Abstract BaseModel
│   ├── user.py                      # User model (credentials, RSA keys, role, face encoding)
│   ├── document.py                  # Document model (encrypted file metadata, ACL)
│   └── audit.py                     # AuditLog model (actions, severity, status enums)
├── services/                        # Business logic
│   ├── auth_service.py              # Credential validation, session lifecycle
│   ├── registration_service.py      # User registration orchestration
│   ├── document_service.py          # Secure upload (AES + RSA + hash)
│   ├── document_listing_service.py  # Paginated queries, search, detail
│   ├── document_download_service.py # Secure download (RSA unwrap + AES decrypt)
│   ├── document_sharing_service.py  # RSA key re-encryption + ACL update
│   ├── face_recognition_service.py  # LBPH face enrollment + verification
│   ├── session_manager.py           # Active session singleton
│   └── audit_service.py             # Audit entry creation + queries
├── utilities/
│   └── helpers.py                   # Timestamp, ID, path, validation helpers
├── logger/
│   └── logging_config.py            # Rotating file + stderr logging
├── exceptions/
│   └── custom_exceptions.py         # SDMS exception hierarchy
├── gui/                             # CustomTkinter GUI
│   ├── app.py                       # Main application controller
│   ├── theme.py                     # Theme engine (dark/light, colors, fonts)
│   ├── animations.py                # Fade, slide, pulse animations
│   ├── assets.py                    # Unicode icon mappings
│   ├── components/                  # Reusable widgets
│   │   ├── cards.py                 # StatCard, InfoCard, ActionCard, PageHeader
│   │   ├── charts.py               # DonutChart, BarChart, MiniSparkline
│   │   ├── dialogs.py              # Toast, ConfirmDialog, SuccessDialog, etc.
│   │   ├── forms.py                # StyledEntry, PasswordEntry, StyledButton, etc.
│   │   ├── loading.py              # LoadingSpinner, StatusBadge, ToolTip
│   │   ├── sidebar.py              # Animated sidebar with nav items
│   │   ├── tables.py               # StyledTreeview table
│   │   └── topbar.py               # Top bar with breadcrumb + theme toggle
│   └── pages/                       # 14 page screens
│       ├── login_page.py            # Login (password + face recognition)
│       ├── register_page.py         # User registration
│       ├── dashboard_page.py        # Stats, charts, activity, system status
│       ├── documents_page.py        # Document library (grid + table views)
│       ├── document_detail_page.py  # Single document metadata view
│       ├── upload_page.py           # Secure file upload
│       ├── download_page.py         # Secure file download + decryption
│       ├── share_page.py            # Document sharing (RSA key re-encryption)
│       ├── shared_page.py           # Documents shared with current user
│       ├── search_page.py           # Document search with filters
│       ├── face_page.py             # Face enrollment + verification
│       ├── audit_page.py            # Audit log viewer
│       ├── settings_page.py         # Theme, session, system settings
│       └── profile_page.py          # User profile view
├── tests/                           # pytest test suite
│   ├── conftest.py                  # Shared fixtures
│   ├── test_repositories.py         # Repository CRUD integration tests
│   ├── test_registration.py         # Registration flow tests
│   ├── test_models.py               # Model validation unit tests
│   ├── test_document_upload.py      # Upload + encryption tests
│   ├── test_document_sharing.py     # Sharing + re-encryption tests
│   ├── test_document_listing.py     # Listing, detail, search tests
│   ├── test_document_download.py    # Download + decryption tests
│   └── test_authentication.py       # Auth service + controller tests
├── storage/encrypted_documents/     # Runtime encrypted file storage
├── download/                        # Decrypted output files
├── logs/                            # Application log files
└── assets/                          # Placeholder asset directories
    ├── animations/
    ├── fonts/
    ├── icons/
    ├── images/
    └── themes/
```

**Total:** 93 Python files | ~11,500 lines of code

---

## 4. Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| GUI Framework | CustomTkinter (tkinter-based) |
| Database | MongoDB (via pymongo) |
| Face Recognition | OpenCV (Haar Cascade + LBPH) |
| Symmetric Crypto | AES-256-CBC (pycryptodome) |
| Asymmetric Crypto | RSA-2048 OAEP-SHA-256 (pycryptodome) |
| Hashing | SHA-256 (hashlib) |
| Config | python-dotenv (.env files) |
| Testing | pytest |
| Logging | Python logging (rotating file handler) |

---

## 5. Setup & Installation

### Prerequisites

- Python 3.10+
- MongoDB running locally (default: `mongodb://localhost:27017`)
- Webcam (optional, for face recognition)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Secure-Document-Management

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux
```

### Running

```bash
# Launch GUI (default)
python main.py

# Launch CLI
python main.py --cli

# Run tests
pytest tests/ -v
```

---

## 6. Configuration

Configuration is loaded from environment variables via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_MODE` | `gui` | Entry mode: `gui` or `cli` |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | `sdms_db` | Database name |
| `STORAGE_DIR` | `storage/encrypted_documents` | Encrypted file storage |
| `DOWNLOAD_DIR` | `download` | Decrypted file output |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_DIR` | `logs` | Log file directory |

---

## 7. Application Entry Points

### `main.py` (56 lines)

The root entry point that:
1. Initializes logging via `logger.logging_config`
2. Loads settings from `.env` via `config.settings`
3. Connects to MongoDB via `database.manager`
4. Creates storage directories
5. Parses CLI arguments (`--cli` flag)
6. Launches either `gui.app.App` or `cli.main` interactive menu

### `cli/main.py` (632 lines)

An interactive menu-driven CLI providing:
- User registration and login (password or face)
- Document upload with automatic encryption
- Document listing and search
- Secure document download and decryption
- Document sharing
- Admin audit log viewing

---

## 8. Core Modules Reference

### 8.1 Models

Located in `models/`. All models extend `BaseModel` and implement `to_dict()`, `validate()`, `from_dict()`, and `update()`.

**User** (`models/user.py`):
- Fields: `user_id`, `username`, `password_hash`, `role` (admin/user/viewer), `rsa_public_key`, `rsa_private_key`, `face_encoding`, `status` (active/inactive/locked), `created_at`, `updated_at`
- Role validation: must be one of the RBAC roles

**Document** (`models/document.py`):
- Fields: `document_id`, `owner_id`, `original_filename`, `stored_filename`, `mime_type`, `file_size`, `sha256_hash`, `aes_key` (base64), `aes_iv` (base64), `rsa_encrypted_aes_key`, `status` (active/archived/deleted), `shared_with` (list of `SharedUser`), `created_at`, `updated_at`
- `SharedUser`: `user_id`, `rsa_encrypted_key`, `shared_at`

**AuditLog** (`models/audit.py`):
- Fields: `log_id`, `user_id`, `username`, `action` (enum), `resource_type`, `resource_id`, `severity` (info/warning/error/critical), `status` (success/failure/pending), `details`, `ip_address`, `timestamp`
- Enums: `AuditAction`, `Severity`, `ResourceType`, `AuditStatus`

### 8.2 Cryptography

Located in `crypto/`. Implements a hybrid encryption scheme.

**AES-256-CBC** (`crypto/aes_cipher.py`):
- `encrypt(plaintext: bytes, key: bytes, iv: bytes) -> EncryptedPayload`
- `decrypt(payload: EncryptedPayload, key: bytes) -> bytes`
- PKCS7 padding, base64-encoded output

**RSA-2048** (`crypto/rsa_cipher.py`):
- `generate_keypair() -> (public_key, private_key)` (PEM format)
- `encrypt(data: bytes, public_key) -> bytes` (OAEP-SHA-256)
- `decrypt(data: bytes, private_key) -> bytes`
- Supports PEM import/export and file loading

**SHA-256 Hashing** (`crypto/hashing.py`):
- `hash_data(data: bytes) -> str`
- `hash_string(text: str) -> str`
- `hash_file(filepath: str) -> str`
- `verify_hash(data: bytes, expected_hash: str) -> bool`

**Key Generation** (`crypto/key_generator.py`):
- `generate_aes_key() -> bytes` (32 bytes)
- `generate_iv() -> bytes` (16 bytes)
- `generate_salt() -> bytes`
- `generate_token(length: int) -> str`
- `generate_uuid() -> str`

### 8.3 Database Layer

Located in `database/`. Uses MongoDB via pymongo with a repository pattern.

**Manager** (`database/manager.py`):
- Singleton MongoDB connection manager
- Connection pooling, connectivity validation
- Idempotent index creation for all collections
- Collections: `users`, `documents`, `audit_logs`

**BaseRepository** (`database/repositories/base.py`):
- Generic CRUD: `create()`, `find_by_id()`, `find_one()`, `find_many()`, `update()`, `delete()`
- Pagination: `find_many()` with `skip`/`limit`
- `count()`, `exists()`

**UserRepository** (`database/repositories/user_repository.py`):
- `find_by_username()`, `create_user()`, `update_face_encoding()`
- `search_users()`, `check_username_exists()`
- Supports soft delete via status field

**DocumentRepository** (`database/repositories/document_repository.py`):
- `find_by_owner()`, `find_shared_with_user()`, `get_document_detail()`
- `search_documents()`, `find_by_mime_type()`
- ACL-aware queries for shared document access

**AuditRepository** (`database/repositories/audit_repository.py`):
- `query_logs()` with filters: username, action, severity, resource_type, status, date range
- Sorted by timestamp descending

### 8.4 Services

Located in `services/`. Orchestrate multi-step business workflows.

**AuthService** (`services/auth_service.py`):
- `login(username, password) -> dict`
- `logout()`
- `get_current_user() -> dict`
- Password verification via SHA-256 hash comparison

**RegistrationService** (`services/registration_service.py`):
- `register(username, password, role) -> dict`
- Input validation, username normalization
- RSA-2048 key pair generation for each user
- Password hashing and storage

**DocumentService** (`services/document_service.py`):
- `upload_document(file_path, owner_id) -> dict`
- Full hybrid encryption workflow:
  1. Read file → SHA-256 hash
  2. Generate AES key + IV → AES-256-CBC encrypt
  3. RSA-wrap the AES key with owner's public key
  4. Store encrypted file + metadata

**DocumentListingService** (`services/document_listing_service.py`):
- `list_my_documents(user_id, page, per_page) -> dict`
- `list_shared_with_me(user_id, page, per_page) -> dict`
- `get_document_detail(document_id) -> dict`
- `search_documents(query, filters) -> dict`
- Exposes only safe metadata (no crypto keys leaked)

**DocumentDownloadService** (`services/document_download_service.py`):
- `download_document(document_id, user_id) -> dict`
- RSA-unwraps AES key → AES decrypts file → SHA-256 integrity check → writes plaintext

**DocumentSharingService** (`services/document_sharing_service.py`):
- `share_document(document_id, owner_id, target_user_id) -> dict`
- Re-encrypts AES key with recipient's RSA public key
- Updates document's access-control list
- Prevents duplicate and self-sharing

**FaceRecognitionService** (`services/face_recognition_service.py`):
- `enroll(user_id, username) -> dict` — Multi-sample face enrollment via webcam
- `login_face() -> dict` — Live camera capture → LBPH matching → user identification
- `remove_enrollment(user_id) -> dict`
- Uses OpenCV Haar Cascade for detection, LBPH for recognition

**SessionManager** (`services/session_manager.py`):
- Singleton maintaining single active user session
- `create_session(user_data)`, `logout()`, `get_current_user()`
- `is_authenticated()`, `require_role(role)`

**AuditService** (`services/audit_service.py`):
- `log_action(action, resource_type, resource_id, details, status) -> dict`
- `query_logs(filters) -> dict`
- Automatically enriches entries with session user data

### 8.5 Controllers

Located in `controllers/`. Thin coordinators that delegate to services and log audit events.

**AuthController** (`controllers/auth_controller.py`):
- `register(username, password, role) -> dict`
- `login(username, password) -> dict`
- `logout()`
- Delegates to `RegistrationService` and `AuthService`

**DocumentController** (`controllers/document_controller.py`):
- `upload_document(file_path) -> dict`
- `list_my_documents(page, per_page) -> dict`
- `list_shared_with_me(page, per_page) -> dict`
- `get_document_detail(document_id) -> dict`
- `search_documents(query) -> dict`
- `download_document(document_id) -> dict`
- `share_document(document_id, target_username) -> dict`
- Delegates to respective services, logs each action

**FaceController** (`controllers/face_controller.py`):
- `enroll(user_id, username) -> dict`
- `login_face() -> dict`
- `remove_enrollment(user_id) -> dict`
- Delegates to `FaceRecognitionService`

**AuditController** (`controllers/audit_controller.py`):
- `view_audit_logs(filters) -> dict`
- Delegates to `AuditService`

### 8.6 Utilities

**Helpers** (`utilities/helpers.py`):
- `get_timestamp() -> str` — ISO 8601 timestamp
- `generate_document_id() -> str` — Unique document identifier
- `sanitize_filename(filename: str) -> str` — Safe filename normalization
- `validate_file_path(path: str) -> bool`
- `ensure_directory(path: str)`
- `is_valid_object_id(oid: str) -> bool`

### 8.7 Exceptions

**Custom Exceptions** (`exceptions/custom_exceptions.py`):

```
SDMSException
├── AuthenticationError
├── AuthorizationError
├── CryptographyError
├── DatabaseError
├── FileError
└── ValidationError
```

### 8.8 Logging

**Configuration** (`logger/logging_config.py`):
- RotatingFileHandler: 5 MB max size, 3 backup files
- StreamHandler: stderr output
- Module-level logger factory: `get_logger(name)`

---

## 9. GUI Reference

Built with CustomTkinter. The GUI follows a single-window, multi-page pattern with an animated sidebar, top bar with breadcrumbs, and page caching.

### 9.1 Theme Engine

**`gui/theme.py`** provides:

- **ThemeManager** — Singleton managing dark/light mode switching
- **_ThemeColors** — Proxy singleton that dynamically resolves colors at access time, ensuring module-level `C = tm.C` references always return current-theme values
- **Fonts** — Named font tuples (TITLE, BODY, SMALL, TINY, MONO, ICON variants)
- **Dim** — Layout constants (sidebar width, padding, radii, animation speeds)

Color palettes define 40+ semantic tokens per mode (bg_main, bg_card, primary, danger, text_primary, border, etc.)

### 9.2 Components

| Component | File | Description |
|-----------|------|-------------|
| **StatCard** | `cards.py` | Dashboard stat card with icon, value, title |
| **InfoCard** | `cards.py` | Card with title header and key-value rows |
| **ActionCard** | `cards.py` | Clickable card for dashboard quick actions |
| **PageHeader** | `cards.py` | Page title with optional subtitle and action buttons |
| **StyledButton** | `forms.py` | Themed button with variants (primary/success/danger/warning/outline) |
| **StyledEntry** | `forms.py` | Themed text input with optional label |
| **PasswordEntry** | `forms.py` | Password input with show/hide toggle |
| **StyledComboBox** | `forms.py` | Themed dropdown selector |
| **StyledText** | `forms.py` | Themed multiline text area |
| **StyledTable** | `tables.py` | Themed Treeview table with selection and scroll |
| **DonutChart** | `charts.py` | Canvas-drawn donut/pie chart with legend |
| **BarChart** | `charts.py` | Canvas-drawn horizontal bar chart |
| **MiniSparkline** | `charts.py` | Canvas-drawn sparkline for trend display |
| **Toast** | `dialogs.py` | Animated slide-in notification (success/error/warning/info) |
| **ConfirmDialog** | `dialogs.py` | Modal yes/no confirmation dialog |
| **SuccessDialog** | `dialogs.py` | Modal success notification |
| **ErrorDialog** | `dialogs.py` | Modal error notification |
| **WarningDialog** | `dialogs.py` | Modal warning notification |
| **LoadingSpinner** | `loading.py` | Animated circular loading indicator |
| **StatusBadge** | `loading.py` | Colored status label badge |
| **ToolTip** | `loading.py` | Hover tooltip for widgets |
| **AnimatedProgressBar** | `loading.py` | Animated horizontal progress bar |
| **Sidebar** | `sidebar.py` | Animated collapsible sidebar with navigation |
| **TopBar** | `topbar.py` | Top bar with breadcrumb, user info, theme toggle |

### 9.3 Pages

All 14 page screens in `gui/pages/`:

| Page | Route | Description |
|------|-------|-------------|
| LoginPage | `login` | Username/password login + face recognition button |
| RegisterPage | `register` | New user registration form |
| DashboardPage | `dashboard` | Welcome header, 4 stat cards, donut/bar charts, activity feed, system status |
| DocumentsPage | `documents` | Document library with grid/table toggle, search, right-click context menu |
| DocumentDetailPage | `document_detail` | Full metadata view for a single document with download/share actions |
| UploadPage | `upload` | File picker with automatic encryption and upload |
| DownloadPage | `download` | Document list with secure download + decryption |
| SharePage | `share` | Share document with another user (RSA key re-encryption) |
| SharedPage | `shared` | Documents shared with the current user |
| SearchPage | `search` | Full-text document search with MIME type filtering |
| FacePage | `face` | Face enrollment and verification via webcam |
| AuditPage | `audit` | Audit log viewer with date/severity filters |
| SettingsPage | `settings` | Theme toggle, session info, system status |
| ProfilePage | `profile` | Current user profile display |

**Navigation:** Sidebar items trigger `_navigate(page_name)` in `app.py`, which creates pages on-demand and caches them. The top bar shows a breadcrumb trail.

### 9.4 Animations

**`gui/animations.py`**:
- `fade_in(widget, duration, steps)` — Opacity fade-in via color interpolation
- `fade_out(widget, duration, steps)` — Opacity fade-out
- `slide_in(widget, direction, distance, duration)` — Horizontal slide with cubic easing
- `pulse_color(widget, color_a, color_b, duration, cycles)` — Color cycling pulse

### 9.5 Assets

**`gui/assets.py`** — Static dictionaries mapping semantic names to Unicode characters:
- `ICONS`: navigation, action, and status icons
- `FILE_ICONS`: file extension to icon mapping

No external font or image dependencies required.

---

## 10. CLI Reference

**`cli/main.py`** provides an interactive text-based menu:

```
=== Secure Document Management System ===
1.  Register
2.  Login (Password)
3.  Login (Face Recognition)
4.  Upload Document
5.  List My Documents
6.  Search Documents
7.  Download Document
8.  Share Document
9.  View Shared Documents
10. View Audit Logs (Admin)
0.  Logout / Exit
```

Each option delegates to the appropriate controller, displaying results in formatted text output.

---

## 11. Testing

**Framework:** pytest

**Test Files:**

| File | Coverage |
|------|----------|
| `test_models.py` | User and Document model validation, serialization, field enforcement |
| `test_repositories.py` | UserRepository and DocumentRepository CRUD, search, existence checks |
| `test_registration.py` | Registration flow, input validation, RSA key generation, persistence |
| `test_authentication.py` | SessionManager lifecycle, AuthService login/logout, AuthController responses |
| `test_document_upload.py` | Upload flow, file validation, encryption, storage, error handling |
| `test_document_download.py` | Download flow, RSA/AES decryption, integrity check, filename preservation |
| `test_document_listing.py` | Listing, detail, search, pagination, safe-field exposure |
| `test_document_sharing.py` | Sharing flow, key re-encryption, ACL updates, duplicate prevention |

**Shared Fixtures** (`conftest.py`):
- Database setup/teardown per test
- Pre-created repository and service instances
- Sample model objects
- Pre-registered test users with active sessions
- Uploaded test documents

**Running Tests:**
```bash
pytest tests/ -v                    # All tests
pytest tests/test_models.py -v      # Single file
pytest -k "test_upload" -v          # By name pattern
```

---

## 12. Security Model

### Encryption Scheme

```
Upload:
  plaintext_file → SHA-256 hash
  plaintext_file → AES-256-CBC(key, iv) → ciphertext
  AES key → RSA-2048-OAEP(owner_public_key) → wrapped_key
  Store: ciphertext + wrapped_key + iv + hash + metadata

Download:
  wrapped_key → RSA-2048-OAEP(owner_private_key) → AES key
  ciphertext → AES-256-CBC-decrypt(key, iv) → plaintext
  SHA-256(plaintext) == stored_hash → integrity verified
```

### Face Recognition

- Multi-sample enrollment (captures multiple frames for accuracy)
- OpenCV Haar Cascade for face detection
- LBPH (Local Binary Pattern Histograms) for face recognition
- Chi-Square distance metric for matching
- Configurable confidence threshold

### Role-Based Access Control

| Role | Permissions |
|------|------------|
| `admin` | Full access: upload, download, share, view all audit logs, manage users |
| `user` | Upload, download own + shared documents, share documents |
| `viewer` | Read-only access to shared documents |

### Session Management

- Singleton session: only one user active at a time
- Session stored in-memory (not persisted to database)
- All actions logged to audit trail with user context

### Audit Trail

Every significant action is logged:
- User registration, login, logout
- Document upload, download, share, search
- Face enrollment, verification
- Includes: user_id, username, action, resource, severity, status, timestamp

---

## 13. Data Flow

### Document Upload Flow

```
User selects file
  → DocumentController.upload_document()
    → AuthService.get_current_user() [session check]
    → DocumentService.upload_document()
      → Read file bytes
      → SHA-256 hash file content
      → Generate AES key + IV
      → AES-256-CBC encrypt file
      → RSA-OAES wrap AES key with owner's public key
      → Write ciphertext to storage/
      → DocumentRepository.create() [metadata to MongoDB]
    → AuditService.log_action("upload", ...)
    → Return success with document_id
```

### Document Download Flow

```
User selects document
  → DocumentController.download_document()
    → AuthService.get_current_user() [session check]
    → DocumentService → get document metadata from DB
    → Check ownership or shared access
    → DocumentDownloadService.download_document()
      → Read ciphertext from storage/
      → RSA-OAES unwrap AES key with owner's private key
      → AES-256-CBC decrypt ciphertext
      → SHA-256 verify integrity
      → Write plaintext to download/
    → AuditService.log_action("download", ...)
    → Return file path
```

### Face Login Flow

```
User clicks "Login with Face"
  → FaceController.login_face()
    → Session check (new session for face login)
    → FaceRecognitionService.login_face()
      → Open camera
      → Detect face via Haar Cascade
      → Extract LBPH features
      → Compare against all enrolled users
      → If match found within threshold → return user_id
    → AuthController.login() with identified user
    → AuditService.log_action("face_login", ...)
```

---

*Generated for Secure Document Management System v1.0.0*
*93 Python files | ~11,500 lines of code*
