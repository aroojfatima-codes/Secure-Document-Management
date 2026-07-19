# PROJECT_ARCHITECTURE.md — Secure Document Management System (SDMS)

> Comprehensive architecture documentation covering layered design,
> data flows, cryptosystem design, and design patterns.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Layered Architecture](#2-layered-architecture)
3. [Component Inventory](#3-component-inventory)
4. [Cryptosystem Architecture](#4-cryptosystem-architecture)
5. [Authentication Flow](#5-authentication-flow)
6. [Document Upload Flow](#6-document-upload-flow)
7. [Document Download Flow](#7-document-download-flow)
8. [Document Sharing Flow](#8-document-sharing-flow)
9. [Face Recognition Flow](#9-face-recognition-flow)
10. [GUI Navigation Flow](#10-gui-navigation-flow)
11. [Data Model Schema](#11-data-model-schema)
12. [Design Patterns](#12-design-patterns)
13. [Database Schema & Indexes](#13-database-schema--indexes)
14. [Error Handling Strategy](#14-error-handling-strategy)
15. [Security Considerations](#15-security-considerations)

---

## 1. Architecture Overview

SDMS follows a **5-layer, MVC-inspired, service-oriented architecture** that
separates concerns cleanly between presentation, business logic, data access,
and infrastructure. The system is designed around these principles:

- **Separation of Concerns** — each layer has a single responsibility.
- **Dependency Inversion** — upper layers depend on abstractions (ABCs),
  not concrete implementations.
- **Singleton Infrastructure** — configuration, database connections, session
  state, and theme management are shared singletons.
- **Repository Pattern** — all MongoDB access is encapsulated behind typed
  repository classes.
- **Facade Pattern** — controllers act as thin facades that delegate to
  service-layer methods.
- **Factory Pattern** — the GUI app creates pages lazily through a factory
  dictionary.

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                              │
│                                                                     │
│   ┌─────────────────────┐          ┌──────────────────────┐        │
│   │   GUI (CustomTkinter)│          │   CLI (argparse)     │        │
│   │                      │          │                      │        │
│   │  14 Pages            │          │  main.py --cli       │        │
│   │  8 Components        │          │  Command dispatch    │        │
│   │  ThemeManager        │          │                      │        │
│   │  Animations          │          │                      │        │
│   └──────────┬───────────┘          └──────────┬───────────┘        │
├──────────────┼─────────────────────────────────┼───────────────────┤
│              │        CONTROLLER LAYER         │                    │
│              │                                 │                    │
│   ┌──────────▼───────────┐          ┌──────────▼───────────┐        │
│   │  AuthController      │          │  DocumentController  │        │
│   │  FaceController      │          │  AuditController     │        │
│   └──────────┬───────────┘          └──────────┬───────────┘        │
├──────────────┼─────────────────────────────────┼───────────────────┤
│              │          SERVICE LAYER          │                    │
│              │                                 │                    │
│   ┌──────────▼──────────────────────────────────────────────┐      │
│   │  AuthService          DocumentService                   │      │
│   │  RegistrationService  DocumentUploadService             │      │
│   │  SessionManager       DocumentDownloadService           │      │
│   │  AuditService         DocumentListingService            │      │
│   │  FaceRecognitionService  DocumentSharingService         │      │
│   │                       DocumentIdService                 │      │
│   └──────────┬──────────────────────────────────────────────┘      │
├──────────────┼──────────────────────────────────────────────────────┤
│              │       DATA ACCESS LAYER (Repository)                 │
│              │                                                     │
│   ┌──────────▼──────────────────────────────────────────────┐      │
│   │  BaseRepository<T>                                      │      │
│   │    ├── UserRepository                                   │      │
│   │    ├── DocumentRepository                               │      │
│   │    ├── AuditRepository                                  │      │
│   │    └── CounterRepository                                │      │
│   └──────────┬──────────────────────────────────────────────┘      │
├──────────────┼──────────────────────────────────────────────────────┤
│              │        INFRASTRUCTURE LAYER                          │
│              │                                                     │
│   ┌──────────▼──────────────────────────────────────────────┐      │
│   │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │      │
│   │  │   Crypto     │  │   Storage    │  │   Database    │  │      │
│   │  │              │  │              │  │               │  │      │
│   │  │ AES Cipher   │  │ StorageMgr   │  │ DatabaseMgr   │  │      │
│   │  │ RSA Cipher   │  │ File I/O     │  │ MongoDB       │  │      │
│   │  │ KeyGenerator │  │ Temp staging │  │ Indexes       │  │      │
│   │  │ Hashing      │  │              │  │               │  │      │
│   │  │ Base64Utils  │  │              │  │               │  │      │
│   │  │ Payload DTOs │  │              │  │               │  │      │
│   │  └─────────────┘  └──────────────┘  └───────────────┘  │      │
│   │                                                         │      │
│   │  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │      │
│   │  │   Config     │  │   Logger     │  │  Exceptions   │  │      │
│   │  │ Settings ◉  │  │ logging_conf │  │  custom_exc   │  │      │
│   │  └─────────────┘  └──────────────┘  └───────────────┘  │      │
│   └─────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Components | Responsibility |
|-------|-----------|----------------|
| **Presentation** | 14 GUI pages, 8 UI components, CLI module | User interaction, input validation display, navigation |
| **Controller** | Auth, Document, Audit, Face controllers | Thin facade — translates UI requests into service calls |
| **Service** | 10 service modules + SessionManager | Business logic, orchestration, validation, encryption workflow |
| **Data Access** | 4 repository classes + BaseRepository | MongoDB CRUD operations, query building, index management |
| **Infrastructure** | Crypto modules, StorageManager, DatabaseManager, Settings, Logger, Exceptions | Low-level I/O, cryptography, database connectivity, configuration |

---

## 3. Component Inventory

### 3.1 Presentation Layer (14 pages + 8 components)

| Page File | Purpose |
|-----------|---------|
| `login_page.py` | Username/password form + face-login button |
| `register_page.py` | New user registration form |
| `dashboard_page.py` | Overview cards, quick actions, recent documents |
| `documents_page.py` | Paginated document grid with actions |
| `document_detail_page.py` | Single document metadata, share, download |
| `upload_page.py` | File picker, progress, upload trigger |
| `download_page.py` | File picker from user's docs, download trigger |
| `share_page.py` | Recipient selector, permission level, share trigger |
| `shared_page.py` | Read-only list of documents shared with current user |
| `search_page.py` | Search bar with filter results |
| `face_page.py` | Camera capture for enrollment and verification |
| `audit_page.py` | Scrollable audit log table with filters |
| `settings_page.py` | Theme toggle, app preferences |
| `profile_page.py` | Current user info display |

| Component File | Purpose |
|----------------|---------|
| `sidebar.py` | Collapsible left navigation with role-aware menus |
| `topbar.py` | Breadcrumb, theme toggle, user avatar, logout |
| `cards.py` | Dashboard stat cards (total docs, shared, storage used) |
| `charts.py` | Chart widgets for dashboard analytics |
| `dialogs.py` | Toast notifications, confirmation modals |
| `forms.py` | Reusable labeled input fields with validation |
| `loading.py` | Spinner and progress indicators |
| `tables.py` | Generic sortable table widget |

### 3.2 Controller Layer (4 controllers)

| Controller | Methods | Delegates To |
|------------|---------|-------------|
| `AuthController` | `login()`, `register()`, `logout()` | AuthService, RegistrationService, SessionManager |
| `DocumentController` | `upload()`, `download()`, `share()`, `list_my_documents()`, `list_shared_with_me()`, `search()`, `get_detail()` | DocumentService, DocumentUploadService, DocumentDownloadService, DocumentListingService, DocumentSharingService |
| `AuditController` | `view_audit_logs()`, `search_logs()` | AuditService |
| `FaceController` | `enroll()`, `login_face()`, `remove_enrollment()` | FaceRecognitionService |

### 3.3 Service Layer (10 services + 1 singleton)

| Service | Responsibility |
|---------|---------------|
| `AuthService` | Credential verification, password hashing comparison |
| `RegistrationService` | User creation, RSA key generation, password hashing |
| `SessionManager` | Singleton — stores `current_user`, `session_id`, role |
| `DocumentService` | CRUD orchestration, validation, ID assignment |
| `DocumentUploadService` | Read file → AES encrypt → RSA wrap → SHA-256 hash → store |
| `DocumentDownloadService` | Load metadata → RSA unwrap → AES decrypt → SHA-256 verify → save |
| `DocumentListingService` | Paginated queries, search, shared-with-me filtering |
| `DocumentSharingService` | Fetch recipient's RSA public key → re-encrypt AES key → update |
| `DocumentIdService` | Auto-incrementing document IDs via CounterRepository |
| `AuditService` | Create audit entries, query audit logs |
| `FaceRecognitionService` | LBPH training, camera capture, face matching |

### 3.4 Data Access Layer (4 repositories)

| Repository | MongoDB Collection | Key Operations |
|------------|-------------------|----------------|
| `BaseRepository<T>` | *(abstract)* | `insert()`, `find_by_id()`, `update()`, `delete()`, `find_many()` |
| `UserRepository` | `users` | `find_by_username()`, `update_face_encoding()`, `update_rsa_keys()` |
| `DocumentRepository` | `documents` | `find_by_owner()`, `find_shared_with()`, `search()` |
| `AuditRepository` | `audit_logs` | `find_by_user()`, `find_by_action()`, `filter_by_date_range()` |
| `CounterRepository` | `counters` | `next_value(collection)` — atomic increment |

### 3.5 Infrastructure Layer

| Module | Responsibility |
|--------|---------------|
| `AESCipher` | AES-256-CBC encrypt/decrypt with PKCS7 padding |
| `RSACipher` | RSA-2048-OAEP-SHA256 encrypt/decrypt key wrapping |
| `KeyGenerator` | RSA-2048 key-pair generation (PEM format) |
| `Hasher` | SHA-256 hash computation and verification |
| `Base64Utils` | Base64 encode/decode for safe storage |
| `EncryptedPayload` | Immutable DTO — AES ciphertext + IV + algorithm |
| `EncryptedKeyPayload` | Immutable DTO — RSA-wrapped key + IV + algorithms |
| `StorageManager` | Creates/verifies storage directories on startup |
| `DatabaseManager` | MongoDB connection, index creation, disconnect |
| `Settings` | Singleton — loads `.env`, exposes typed attributes |
| `setup_logging` | Configures root logger with file + console handlers |

---

## 4. Cryptosystem Architecture

### 4.1 Hybrid Encryption Scheme

SDMS uses a **hybrid encryption** approach where:

1. A random **AES-256 key** (32 bytes) and **IV** (16 bytes) are generated.
2. The document plaintext is encrypted with **AES-256-CBC**.
3. The AES key is wrapped (encrypted) with the owner's **RSA-2048-OAEP-SHA-256
   public key**.
4. Both the wrapped AES key and the AES ciphertext are stored.

This allows fast symmetric encryption of large files while protecting the AES
key with asymmetric cryptography so only the key holder can decrypt.

```
┌────────────────────────────────────────────────────────────────┐
│                    HYBRID ENCRYPTION                           │
│                                                                │
│  ┌──────────┐     ┌───────────┐     ┌──────────────────────┐  │
│  │ Plaintext │────▶│ AES-256   │────▶│ Ciphertext (bytes)   │  │
│  │  (file)   │     │ CBC + IV  │     │                      │  │
│  └──────────┘     └─────┬─────┘     └──────────────────────┘  │
│                         │                                      │
│                    ┌────▼────┐                                  │
│                    │ AES Key │                                  │
│                    │ (32 B)  │                                  │
│                    └────┬────┘                                  │
│                         │                                      │
│                    ┌────▼──────────────┐                       │
│                    │ RSA-2048-OAEP     │                       │
│                    │ (owner's pub key) │                       │
│                    └────┬──────────────┘                       │
│                         │                                      │
│                    ┌────▼──────────────┐                       │
│                    │ Wrapped AES Key   │                       │
│                    │ (Base64 in DB)    │                       │
│                    └───────────────────┘                       │
│                                                                │
│  ┌──────────┐     ┌───────────┐                                │
│  │ Plaintext │────▶│ SHA-256   │────▶ Hash (hex in DB)         │
│  └──────────┘     └───────────┘                                │
└────────────────────────────────────────────────────────────────┘
```

### 4.2 Module Breakdown

```
crypto/
├── interfaces.py      # BaseCipher[PayloadT]  (ABC)
│                      # BaseHasher             (ABC)
│
├── payload.py         # EncryptedPayload       (frozen dataclass)
│                      # EncryptedKeyPayload    (frozen dataclass)
│
├── aes_cipher.py      # AESCipher(BaseCipher[EncryptedPayload])
│                      #   - encrypt(bytes) → EncryptedPayload
│                      #   - decrypt(EncryptedPayload) → bytes
│                      #   - PKCS7 padding, random IV per call
│
├── rsa_cipher.py      # RSACipher(BaseCipher[bytes])
│                      #   - encrypt(bytes, public_key) → bytes
│                      #   - decrypt(bytes, private_key) → bytes
│                      #   - OAEP SHA-256 padding
│
├── key_generator.py   # KeyGenerator
│                      #   - generate_rsa_keypair() → (pub_pem, priv_pem)
│                      #   - 2048-bit modulus, e=65537
│
├── hashing.py         # SHA256Hasher(BaseHasher)
│                      #   - hash(bytes) → hex str
│                      #   - verify(bytes, hex) → bool
│
├── base64_utils.py    # encode(bytes) → Base64 str
│                      #   decode(Base64 str) → bytes
│
└── exceptions.py      # EncryptionError
                       # DecryptionError
                       # HashVerificationError
                       # KeyGenerationError
```

### 4.3 Per-User Key Architecture

Each user has their own RSA-2048 key pair generated at registration time:

```
┌──────────────────────────────────────────────────────────────┐
│                    USER RSA KEY PAIR                          │
│                                                              │
│  Registration:                                               │
│    KeyGenerator.generate_rsa_keypair()                       │
│    → rsa_public_key  (PEM, stored in users collection)       │
│    → rsa_private_key (PEM, encrypted with password, stored)  │
│                                                              │
│  Upload:                                                     │
│    random AES key → encrypt file → wrap with OWNER's pubkey  │
│                                                              │
│  Share:                                                      │
│    same AES key → wrap with RECIPIENT's pubkey               │
│    → stored in document.shared_with[].encrypted_aes_key      │
│                                                              │
│  Download:                                                   │
│    unwrap AES key with USER's private key → decrypt file     │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Authentication Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant GUI as LoginPage
    participant AuthCtrl as AuthController
    participant AuthSvc as AuthService
    participant UserRepo as UserRepository
    participant AuditSvc as AuditService
    participant SessionMgr as SessionManager
    participant DB as MongoDB

    User->>GUI: Enter username + password, click Login
    GUI->>AuthCtrl: login(username, password)
    AuthCtrl->>AuthSvc: authenticate(username, password)
    AuthSvc->>UserRepo: find_by_username(username)
    UserRepo->>DB: db.users.findOne({username})
    DB-->>UserRepo: User document (or null)
    UserRepo-->>AuthSvc: User object (or None)

    alt User not found
        AuthSvc-->>AuthCtrl: {"success": False, "error": "Invalid credentials"}
        AuthCtrl-->>GUI: Toast error message
    else User found
        AuthSvc->>AuthSvc: Compare SHA-256(password) with stored hash
        alt Password mismatch
            AuthSvc->>AuditSvc: log(ACTION=USER_LOGIN_FAILED, SEVERITY=WARNING)
            AuditSvc->>DB: db.audit_logs.insertOne(...)
            AuthSvc-->>AuthCtrl: {"success": False, "error": "Invalid credentials"}
            AuthCtrl-->>GUI: Toast error message
        else Password matches
            AuthSvc->>AuditSvc: log(ACTION=USER_LOGIN, SEVERITY=INFO)
            AuditSvc->>DB: db.audit_logs.insertOne(...)
            AuthSvc-->>AuthCtrl: {"success": True, user_id, username, role}
            AuthCtrl-->>GUI: Login success
            GUI->>SessionMgr: set_current_user(user_data)
            SessionMgr-->>GUI: Session active
            GUI->>GUI: Navigate to Dashboard
        end
    end
```

---

## 6. Document Upload Flow

```mermaid
flowchart TD
    A[User selects file in UploadPage] --> B[DocumentController.upload]
    B --> C[DocumentUploadService.upload]
    C --> D[Read file bytes from disk]
    D --> E[Generate random AES-256 key + IV]
    E --> F[AES-256-CBC encrypt file bytes]
    F --> G[Compute SHA-256 hash of plaintext]
    G --> H[RSA-2048-OAEP wrap AES key<br>with owner's public key]
    H --> I[Base64-encode wrapped key, IV,<br>and ciphertext]
    I --> J[Write ciphertext to<br>storage/encrypted_documents/]
    J --> K[DocumentIdService.next_id]
    K --> L[Build Document model]
    L --> M[DocumentRepository.insert into MongoDB]
    M --> N[AuditService.log DOCUMENT_UPLOAD]
    N --> O[Return success + document metadata]
    O --> P[GUI shows toast + navigates to Documents]

    style A fill:#e1f5fe
    style F fill:#fff3e0
    style H fill:#fff3e0
    style G fill:#f3e5f5
    style P fill:#e8f5e9
```

### Step-by-Step Detail

| Step | Layer | What Happens |
|------|-------|-------------|
| 1 | Presentation | `UploadPage` opens a file dialog, validates file size against `STORAGE_MAX_FILE_SIZE_MB` |
| 2 | Controller | `DocumentController.upload()` delegates to `DocumentUploadService` |
| 3 | Service | File bytes are read into memory |
| 4 | Crypto | `KeyGenerator` creates a fresh 32-byte AES key and 16-byte IV |
| 5 | Crypto | `AESCipher.encrypt()` produces `EncryptedPayload(ciphertext, iv, "AES-256-CBC")` |
| 6 | Crypto | `SHA256Hasher.hash()` computes the plaintext digest |
| 7 | Crypto | `RSACipher.encrypt(aes_key, owner_public_key)` wraps the AES key |
| 8 | Crypto | `Base64Utils` encodes the wrapped key and IV for MongoDB storage |
| 9 | Storage | Ciphertext bytes are written to `storage/encrypted_documents/{doc_id}.enc` |
| 10 | Data Access | `DocumentRepository.insert()` saves the `Document` document to MongoDB |
| 11 | Service | `AuditService.log()` records the upload action |
| 12 | Presentation | Toast notification + navigation to documents page |

---

## 7. Document Download Flow

```mermaid
flowchart TD
    A[User selects document in DownloadPage] --> B[DocumentController.download]
    B --> C[DocumentDownloadService.download]
    C --> D[DocumentRepository.find_by_id]
    D --> E{Document exists?}
    E -->|No| F[Return error: Document not found]
    E -->|Yes| G{User is owner or<br>has shared access?}
    G -->|No| H[AuditService.log PERMISSION_DENIED]
    G -->|Yes| I[Read user's RSA private key]
    I --> J[RSA-2048-OAEP unwrap AES key<br>with user's private key]
    J --> K[Read ciphertext from<br>storage/encrypted_documents/]
    K --> L[AES-256-CBC decrypt<br>with unwrapped key + IV]
    L --> M[Compute SHA-256 of decrypted bytes]
    M --> N{Hash matches<br>stored sha256_hash?}
    N -->|No| O[AuditService.log INTEGRITY_FAILURE]
    N -->|Yes| P[Write plaintext to user-selected path]
    P --> Q[AuditService.log DOCUMENT_DOWNLOAD]
    Q --> R[Return success]
    R --> S[GUI shows toast]

    style A fill:#e1f5fe
    style J fill:#fff3e0
    style L fill:#fff3e0
    style M fill:#f3e5f5
    style O fill:#ffebee
    style S fill:#e8f5e9
```

### Step-by-Step Detail

| Step | Layer | What Happens |
|------|-------|-------------|
| 1 | Presentation | `DownloadPage` loads user's document list, user selects one |
| 2 | Controller | `DocumentController.download(doc_id, save_path)` |
| 3 | Data Access | `DocumentRepository.find_by_id()` retrieves document metadata |
| 4 | Service | Ownership / share-access check against current user |
| 5 | Crypto | `RSACipher.decrypt(wrapped_aes_key, user_private_key)` → raw AES key |
| 6 | Storage | Read encrypted file bytes from disk |
| 7 | Crypto | `AESCipher.decrypt(EncryptedPayload(ciphertext, iv))` → plaintext |
| 8 | Crypto | `SHA256Hasher.verify(plaintext, stored_hash)` — integrity check |
| 9 | Storage | Write plaintext to user-selected path |
| 10 | Service | `AuditService.log(DOCUMENT_DOWNLOAD)` |
| 11 | Presentation | Toast: "Document downloaded successfully" |

---

## 8. Document Sharing Flow

```mermaid
flowchart TD
    A[Owner selects document + recipient<br>in SharePage] --> B[DocumentController.share]
    B --> C[DocumentSharingService.share]
    C --> D[DocumentRepository.find_by_id]
    D --> E[UserRepository.find_by_username<br>recipient]
    E --> F{Recipient exists?}
    F -->|No| G[Return error]
    F -->|Yes| H[Decrypt owner's wrapped AES key<br>with owner's private key]
    H --> I[Re-encrypt AES key with<br>recipient's RSA public key]
    I --> J[Base64-encode re-encrypted key]
    J --> K[Document.add_share<br>user_id, permission, re_encrypted_key]
    K --> L[DocumentRepository.update<br>shared_with array]
    L --> M[AuditService.log DOCUMENT_SHARE]
    M --> N[Return success]
    N --> O[GUI toast: "Document shared!"]

    style A fill:#e1f5fe
    style H fill:#fff3e0
    style I fill:#fff3e0
    style K fill:#f3e5f5
    style O fill:#e8f5e9
```

### Key Insight: Per-Recipient Key Re-Encryption

When a document is shared:

1. The **original AES key** (used to encrypt the file) is **never re-generated**.
2. The same AES key is **re-encrypted** with the recipient's RSA public key.
3. The re-encrypted key is stored in `document.shared_with[].encrypted_aes_key`.
4. When the recipient downloads, they decrypt **their copy** of the AES key
   using **their own RSA private key**.

This means the encrypted file on disk is the same for all users — only the
key-wrapping differs per user.

```
Owner's AES Key ──┬── RSA(owner_pubkey) ──▶ owner's encrypted_aes_key
                  │
                  └── RSA(recipient_pubkey) ──▶ recipient's encrypted_aes_key
```

---

## 9. Face Recognition Flow

### 9.1 Enrollment Flow

```mermaid
flowchart TD
    A[User clicks Enroll Face<br>in FacePage] --> B[OpenCV VideoCapture<br>camera.open 0]
    B --> C[Capture frame from webcam]
    C --> D[Convert to grayscale]
    D --> E[Haar Cascade face detection]
    E --> F{Face detected?}
    F -->|No| G[Show error: No face found]
    F -->|Yes| H[LBPH face recognizer<br>.train on captured face]
    H --> I[Extract LBP feature vector]
    I --> J[FaceController.enroll]
    J --> K[FaceRecognitionService.enroll]
    K --> L[UserRepository.update_face_encoding<br>face_encoding, face_enrolled=true]
    L --> M[AuditService.log FACE_ENROLLMENT]
    M --> N[GUI toast: Face enrolled!]

    style A fill:#e1f5fe
    style E fill:#fff3e0
    style H fill:#fff3e0
    style I fill:#f3e5f5
    style N fill:#e8f5e9
```

### 9.2 Login (Verification) Flow

```mermaid
flowchart TD
    A[User clicks Login with Face<br>in LoginPage] --> B[OpenCV VideoCapture<br>camera.open 0]
    B --> C[Capture frame from webcam]
    C --> D[Convert to grayscale]
    D --> E[Haar Cascade face detection]
    E --> F{Face detected?}
    F -->|No| G[Return error: No face]
    F -->|Yes| H[Load all enrolled<br>face encodings from DB]
    H --> I[LBPH .predict on captured frame]
    I --> J{Match confidence<br>below threshold?}
    J -->|No match| K[AuditService.log FACE_LOGIN_FAILED]
    K --> L[Return error: No match]
    J -->|Match found| M[Fetch matched user from DB]
    M --> N[AuditService.log FACE_LOGIN]
    N --> O[SessionManager.set_current_user]
    O --> P[GUI navigates to Dashboard]

    style A fill:#e1f5fe
    style E fill:#fff3e0
    style I fill:#fff3e0
    style K fill:#ffebee
    style P fill:#e8f5e9
```

### 9.3 Technology Stack

| Component | Technology |
|-----------|-----------|
| Face Detection | Haar Cascade Classifier (`haarcascade_frontalface_default.xml`) |
| Feature Extraction | Local Binary Patterns Histograms (LBPH) |
| Classifier | `cv2.face.LBPHFaceRecognizer_create()` |
| Camera Capture | `cv2.VideoCapture(0)` |
| Image Processing | NumPy array operations, grayscale conversion |

---

## 10. GUI Navigation Flow

```mermaid
flowchart TD
    START([Application Start]) --> MAIN[SDMSApp.__init__]
    MAIN --> LOGIN[LoginPage]
    MAIN --> SIDEBAR_UNAUTH[Sidebar: unauthenticated menu]
    MAIN --> TOPBAR_UNAUTH[TopBar: no user info]

    LOGIN -->|Login success| DASH[DashboardPage]
    LOGIN -->|Register click| REG[RegisterPage]
    LOGIN -->|Face login| FACE_VERIFY[Face Login Flow]

    REG -->|Register success| LOGIN

    DASH --> SIDEBAR_AUTH[Sidebar: authenticated menu]
    DASH --> TOPBAR_AUTH[TopBar: user name + role]

    SIDEBAR_AUTH -->|Documents| DOCS[DocumentsPage]
    SIDEBAR_AUTH -->|Upload| UPLOAD[UploadPage]
    SIDEBAR_AUTH -->|Download| DOWNLOAD[DownloadPage]
    SIDEBAR_AUTH -->|Share| SHARE[SharePage]
    SIDEBAR_AUTH -->|Shared With Me| SHARED[SharedPage]
    SIDEBAR_AUTH -->|Search| SEARCH[SearchPage]
    SIDEBAR_AUTH -->|Face Recognition| FACE_PAGE[FacePage]
    SIDEBAR_AUTH -->|Audit Logs| AUDIT[AuditPage]
    SIDEBAR_AUTH -->|Settings| SETTINGS[SettingsPage]
    SIDEBAR_AUTH -->|Profile| PROFILE[ProfilePage]
    SIDEBAR_AUTH -->|Logout| LOGIN

    DOCS -->|Click document| DETAIL[DocumentDetailPage]
    UPLOAD -->|Upload success| DOCS
    DOWNLOAD -->|Download success| DOCS
    SHARE -->|Share success| DOCS

    style START fill:#e1f5fe
    style LOGIN fill:#fff3e0
    style DASH fill:#e8f5e9
```

### Page Factory (Lazy Creation)

Pages are created on-demand through a factory dictionary in `App._create_page()`:

```python
pages = {
    "dashboard":       _make_dashboard,
    "documents":       _make_documents,
    "document_detail": _make_document_detail,
    "upload":          _make_upload,
    "download":        _make_download,
    "share":           _make_share,
    "shared":          _make_shared,
    "search":          _make_search,
    "face":            _make_face,
    "audit":           _make_audit,
    "settings":        _make_settings,
    "profile":         _make_profile,
}
```

Once created, pages are cached in `_page_cache` and shown/hidden via
`grid()` / `grid_forget()` rather than destroyed and recreated.

---

## 11. Data Model Schema

### 11.1 User Document (`users` collection)

```json
{
  "user_id": "a1b2c3d4e5f6...",
  "username": "john_doe",
  "password_hash": "5e884898da280471...",
  "role": "admin",
  "rsa_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBI...",
  "rsa_private_key": "-----BEGIN ENCRYPTED PRIVATE KEY-----\nMIIF...",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "is_active": true,
  "face_encoding": [0.12, 0.45, ...],
  "face_enrolled": true
}
```

### 11.2 Document Document (`documents` collection)

```json
{
  "document_id": "DOC001",
  "original_filename": "report.pdf",
  "encrypted_filename": "DOC001.enc",
  "owner_id": "a1b2c3d4e5f6...",
  "encrypted_aes_key": "Base64(RSA-wrapped AES key)",
  "iv": "Base64(16-byte IV)",
  "sha256_hash": "e3b0c44298fc1c14...",
  "file_size": 1048576,
  "mime_type": "application/pdf",
  "algorithm": "AES-256-CBC",
  "created_at": "2025-01-15T11:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "is_deleted": false,
  "shared_with": [
    {
      "user_id": "b2c3d4e5f6a1...",
      "permission": "view",
      "encrypted_aes_key": "Base64(RSA-wrapped for recipient)",
      "shared_at": "2025-01-15T12:00:00Z"
    }
  ]
}
```

### 11.3 Audit Log Document (`audit_logs` collection)

```json
{
  "audit_id": "AUD001",
  "timestamp": "2025-01-15T11:00:05Z",
  "user_id": "a1b2c3d4e5f6...",
  "username": "john_doe",
  "role": "admin",
  "action": "DOCUMENT_UPLOAD",
  "resource_type": "DOCUMENT",
  "resource_id": "DOC001",
  "resource_name": "report.pdf",
  "status": "SUCCESS",
  "message": "Document uploaded and encrypted successfully",
  "severity": "INFO",
  "session_id": "sess_xyz...",
  "client_ip": "192.168.1.100",
  "device_info": "Windows-10-Python3.11",
  "metadata": {"file_size": 1048576, "algorithm": "AES-256-CBC"},
  "created_at": "2025-01-15T11:00:05Z"
}
```

---

## 12. Design Patterns

### 12.1 Singleton Pattern

Used for shared infrastructure that must exist as exactly one instance:

| Singleton | Module | Purpose |
|-----------|--------|---------|
| `Settings` | `config/settings.py` | Load `.env` once, share config across all modules |
| `DatabaseManager` | `database/manager.py` | One MongoDB connection pool for the entire app |
| `SessionManager` | `services/session_manager.py` | Track current user/session across GUI pages |
| `ThemeManager` | `gui/theme.py` | Centralize color palette and font definitions |

**Implementation pattern:**

```python
class Settings:
    _instance: ClassVar[Settings | None] = None

    def __new__(cls) -> Settings:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance
```

### 12.2 Repository Pattern

All MongoDB operations are abstracted behind typed repository classes:

```python
class BaseRepository(Generic[T]):
    """Generic CRUD operations for any MongoDB collection."""

    def __init__(self, collection_name: str, model_class: type[T]):
        self._collection = db[collection_name]
        self._model = model_class

    def insert(self, entity: T) -> str: ...
    def find_by_id(self, entity_id: str) -> T | None: ...
    def update(self, entity: T) -> bool: ...
    def delete(self, entity_id: str) -> bool: ...
    def find_many(self, filter: dict) -> list[T]: ...
```

Benefits:
- Services never import `pymongo` directly.
- Collection schema changes only affect one file.
- Easy to swap MongoDB for another backend.

### 12.3 Facade Pattern

Controllers are thin facades that translate UI events into service calls:

```python
class DocumentController:
    def __init__(self):
        self._upload_svc = DocumentUploadService()
        self._download_svc = DocumentDownloadService()
        self._sharing_svc = DocumentSharingService()
        self._listing_svc = DocumentListingService()

    def upload(self, file_path, user_id, ...):
        return self._upload_svc.upload(file_path, user_id, ...)

    def download(self, doc_id, save_path, user_id, ...):
        return self._download_svc.download(doc_id, save_path, user_id, ...)
```

### 12.4 Factory Pattern

Page creation uses a factory dictionary to map route names to builder
functions, enabling lazy instantiation and easy extension:

```python
def _create_page(self, name: str):
    factory = {
        "dashboard": _make_dashboard,
        "documents": _make_documents,
        # ...
    }.get(name)
    return factory() if factory else None
```

### 12.5 Strategy Pattern (Polymorphic Crypto)

`BaseCipher` and `BaseHasher` ABCs allow different implementations to be
swapped without changing callers:

```python
class BaseCipher(ABC, Generic[_PayloadT]):
    @abstractmethod
    def encrypt(self, data: bytes) -> _PayloadT: ...
    @abstractmethod
    def decrypt(self, ciphertext: _PayloadT) -> bytes: ...
```

`AESCipher` returns `EncryptedPayload`, while `RSACipher` returns `bytes` —
both satisfy `BaseCipher` through different type parameters.

### 12.6 Template Method Pattern

`BaseRepository` defines the skeleton of CRUD operations; concrete
repositories override query-specific methods while inheriting generic ones.

### 12.7 Observer-like Pattern (Theme Changes)

The `TopBar` theme toggle triggers a cascade:

```
TopBar callback → App._change_theme(mode) → ThemeManager.set_mode()
    → App._apply_theme_recursive(widget) → widget.apply_theme()
```

Every widget that implements `apply_theme()` is notified, enabling instant
global theme switching.

---

## 13. Database Schema & Indexes

### Collections

| Collection | Purpose | Key Indexes |
|------------|---------|-------------|
| `users` | User accounts & keys | `user_id` (unique), `username` (unique) |
| `documents` | Document metadata & shares | `document_id` (unique), `owner_id`, `shared_with.user_id` |
| `audit_logs` | Immutable audit trail | `audit_id` (unique), `timestamp`, `user_id`, `action` |
| `counters` | Auto-increment ID generation | `_id` (collection name) |

### Index Creation (in `DatabaseManager.create_indexes()`)

```python
# Users
db.users.create_index("user_id", unique=True)
db.users.create_index("username", unique=True)

# Documents
db.documents.create_index("document_id", unique=True)
db.documents.create_index("owner_id")
db.documents.create_index("shared_with.user_id")

# Audit Logs
db.audit_logs.create_index("audit_id", unique=True)
db.audit_logs.create_index("timestamp")
db.audit_logs.create_index("user_id")
db.audit_logs.create_index("action")
```

---

## 14. Error Handling Strategy

SDMS uses a layered exception hierarchy:

```
exceptions/custom_exceptions.py
├── SDMSError              (base for all app errors)
│   ├── DatabaseError      (connection, query failures)
│   ├── AuthenticationError (invalid credentials, lockout)
│   ├── AuthorizationError (RBAC violations)
│   ├── DocumentError      (upload, download, sharing failures)
│   ├── ValidationError    (model validation failures)
│   └── StorageError       (filesystem I/O failures)

crypto/exceptions.py
├── CryptoError            (base for crypto errors)
│   ├── EncryptionError
│   ├── DecryptionError
│   ├── HashVerificationError
│   └── KeyGenerationError
```

**Propagation rules:**
- Services catch infrastructure exceptions and re-raise as domain exceptions.
- Controllers catch service exceptions and return `{"success": False, "error": ...}` dicts.
- GUI pages catch controller errors and display `Toast` notifications.
- The CLI catches controller errors and prints formatted error messages.
- Audit logging captures failures with `SeverityLevel.WARNING` or `SECURITY_ALERT`.

---

## 15. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Plaintext passwords | SHA-256 hashed before storage; never logged |
| File confidentiality | AES-256-CBC encryption; files stored encrypted on disk |
| Key management | RSA-2048-OAEP wrapping; each user has unique key pair |
| Access control | RBAC enforced at service layer before any operation |
| Audit trail | Immutable audit logs with timestamp, user, action, severity |
| Tamper detection | SHA-256 hash verified on every download |
| Secure sharing | AES key re-encrypted per-recipient; no shared keys in plaintext |
| Session security | SessionManager tracks active user; logout clears state |
| Input validation | Model `validate()` methods reject malformed data |
| Error masking | Stack traces logged to file; user sees friendly messages |

### Known Limitations

1. **Password hashing** uses SHA-256 without salting — production systems should
   use bcrypt/argon2. This is acceptable for the academic scope.
2. **RSA private keys** are stored encrypted but the passphrase management is
   simplified for demo purposes.
3. **No network encryption** — MongoDB runs locally without TLS (appropriate
   for single-user desktop deployment).
4. **Face recognition** accuracy depends on lighting and camera quality;
   not suitable as sole authentication factor in production.
