# SDMS File Structure Documentation

> **Secure Document Management System** — Complete project structure reference.
> Python 3.11+ | CustomTkinter | MongoDB | OpenCV | AES-256-CBC + RSA-2048

---

## Table of Contents

1. [Root Directory](#root-directory)
2. [config/](#config)
3. [database/](#database)
4. [models/](#models)
5. [crypto/](#crypto)
6. [services/](#services)
7. [controllers/](#controllers)
8. [gui/](#gui)
9. [cli/](#cli)
10. [utilities/](#utilities)
11. [exceptions/](#exceptions)
12. [logger/](#logger)
13. [storage/](#storage)
14. [tests/](#tests)
15. [Static Directories](#static-directories)
16. [Cross-Module Communication Diagram](#cross-module-communication-diagram)

---

## Root Directory

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `main.py` | 73 | Application entry point. Parses CLI args to launch either the GUI (`App`) or the CLI (`CLIApp`). Initializes logging, loads environment, and bootstraps all singletons before starting the chosen interface. | `main()`, `launch_gui()`, `launch_cli()` | `config.settings`, `gui.app`, `cli.main`, `logger.logging_config` | `argparse`, `sys`, `os` | Imports `App` from `gui.app`, `CLIApp` from `cli.main`, `Settings` from `config.settings`, and `setup_logging` from `logger.logging_config`. Calls `Settings.load()` first, then `setup_logging()`, then launches the appropriate interface. |
| `.env` | — | Stores environment variables loaded at startup. Contains `APP_NAME`, `MONGODB_URI`, `MONGODB_DB_NAME`, `SECRET_KEY`, `ENCRYPTION_KEY`, `LOG_LEVEL`, and optional `FACE_RECOGNITION_TOLERANCE`. | N/A | None | N/A | Read by `config/settings.py` via `python-dotenv`. |
| `requirements.txt` | — | Lists all pinned Python dependencies for `pip install -r`. | N/A | None | N/A | Referenced by `pyproject.toml` and CI pipelines. |
| `pyproject.toml` | — | Project metadata and `mypy` strict-mode configuration. Defines target Python version, exclude patterns, and plugin settings. | N/A | None | N/A | Consumed by `mypy`, `pytest`, and build tools. |

---

## config/

Configuration module. Loads `.env` and exposes a singleton `Settings` object used across the entire application.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `settings.py` | 78 | **Singleton settings class.** Loads `.env` via `python-dotenv`, validates required keys, and exposes typed properties. All modules import `Settings.instance()` to access config values. | `Settings` (singleton) | `python-dotenv`, `os` | `dotenv.load_dotenv`, `os` | Imported by virtually every module: `main.py`, `database.manager`, `services/*`, `crypto/*`, `logger.logging_config`, `storage.manager`. The singleton pattern means only one instance exists at runtime. `Settings.instance().mongodb_uri` is the canonical access pattern. |

### Settings Singleton Pattern

```
Settings.instance()  →  returns the single Settings object
Settings.load()      →  creates the singleton (called once in main.py)
```

---

## database/

MongoDB connection management and repository pattern for data access.

### database/\_\_init\_\_.py

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 30 | Package exports. Re-exports `DatabaseManager` and all repository classes so consumers can write `from database import UserRepository`. | N/A | `database.manager`, `database.repositories` | N/A | Re-exports: `DatabaseManager`, `BaseRepository`, `UserRepository`, `DocumentRepository`, `AuditRepository`, `CounterRepository`. |

### database/exceptions.py

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `exceptions.py` | 30 | Custom exception hierarchy for database operations. Separates connection errors, query errors, and not-found conditions. | `DatabaseError`, `ConnectionError`, `QueryError`, `DocumentNotFoundError`, `DuplicateKeyError` | None | None | Raised by all repository classes. Caught by `controllers/*` and `services/*` to produce user-facing error messages. |

### database/manager.py

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `manager.py` | 170 | **DatabaseManager singleton.** Manages the MongoDB connection pool, creates indexes (unique on `users.username`, `users.email`, compound on `documents.owner_id` + `documents.filename`), and exposes `db` and collection accessors. Handles reconnection logic and health checks. | `DatabaseManager` (singleton) | `pymongo`, `config.settings` | `pymongo.MongoClient`, `pymongo.errors`, `config.settings.Settings` | Called from `main.py` at startup (`DatabaseManager.instance().connect()`). Every repository receives the manager instance to access collections. `DatabaseManager.instance().get_collection("users")` is the standard pattern. |

### database/repositories/

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 20 | Package exports for all repositories. | N/A | `database.repositories.*` | N/A | Re-exports: `BaseRepository`, `UserRepository`, `DocumentRepository`, `AuditRepository`, `CounterRepository`. |
| `base.py` | 140 | **Abstract base repository.** Provides generic CRUD operations (`insert_one`, `find_one`, `find_many`, `update_one`, `delete_one`, `count`) that all concrete repositories inherit. Handles `ObjectId` conversion and common error wrapping. | `BaseRepository` (ABC) | `pymongo`, `database.exceptions`, `models.base` | `pymongo.results`, `bson.objectid.ObjectId`, `abc.ABC` | Parent class for all 4 concrete repositories. Receives a `collection` (PyMongo Collection) via constructor. Raises `DocumentNotFoundError`, `DuplicateKeyError` from `database.exceptions`. |
| `user_repository.py` | 180 | **User CRUD.** Extends `BaseRepository` with user-specific queries: `find_by_username`, `find_by_email`, `update_password`, `update_last_login`, `increment_failed_attempts`, `reset_failed_attempts`, `lock_account`, `update_face_encoding`. Ensures uniqueness via MongoDB unique indexes. | `UserRepository` | `BaseRepository`, `pymongo`, `models.user.User` | `bson.objectid.ObjectId`, `datetime.datetime` | Used by `auth_service.py` (login lookup), `registration_service.py` (create user), `face_recognition_service.py` (update face encoding). Calls `DatabaseManager.instance().get_collection("users")`. |
| `document_repository.py` | 160 | **Document CRUD.** Extends `BaseRepository` with document-specific queries: `find_by_owner`, `find_shared_with_user`, `find_by_doc_id`, `update_shared_users`, `find_by_type`, `search_by_name`. | `DocumentRepository` | `BaseRepository`, `pymongo`, `models.document.Document` | `re` (for regex search), `bson.objectid.ObjectId` | Used by all `document_*_service.py` files and `document_controller.py`. Calls `DatabaseManager.instance().get_collection("documents")`. |
| `audit_repository.py` | 150 | **Audit log queries.** Extends `BaseRepository` with: `find_by_user`, `find_by_action`, `find_by_date_range`, `find_by_document`, `get_recent_activity`, `export_audit_logs`. Supports filtering and pagination. | `AuditRepository` | `BaseRepository`, `pymongo`, `models.audit.AuditLog` | `datetime.datetime`, `bson.objectid.ObjectId` | Used by `audit_service.py` and `audit_controller.py`. Calls `DatabaseManager.instance().get_collection("audit_logs")`. |
| `counter_repository.py` | 60 | **Atomic counter for sequential document IDs.** Uses `find_one_and_update` with `upsert=True` and `$inc` to generate DOC-XXXX IDs atomically, preventing race conditions. | `CounterRepository` | `BaseRepository`, `pymongo` | `pymongo.ReturnDocument` | Used exclusively by `document_id_service.py`. Calls `DatabaseManager.instance().get_collection("counters")`. |

---

## models/

Data models using Python `dataclasses`. Pure data containers with serialization methods — no business logic.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 23 | Package exports for all models. | N/A | `models.user`, `models.document`, `models.audit` | N/A | Re-exports: `User`, `Document`, `SharedUser`, `AuditLog`, `AuditAction`. |
| `base.py` | 50 | **Abstract base model.** Defines the `BaseModel` ABC requiring `to_dict()` and `from_dict()` class methods. Provides a common interface for serialization to/from MongoDB documents. | `BaseModel` (ABC) | `abc.ABC` | `abc.ABC`, `abc.abstractmethod` | Parent class for `User`, `Document`, `AuditLog`. Used by all repositories for serialization/deserialization. |
| `user.py` | 95 | **User dataclass.** Fields: `id`, `username`, `full_name`, `email`, `password_hash`, `role` (admin/user), `created_at`, `last_login`, `is_active`, `failed_login_attempts`, `account_locked_until`, `face_encoding` (optional numpy array), `public_key`, `private_key`. Implements `to_dict()`/`from_dict()` with `ObjectId` handling. | `User` (dataclass) | `BaseModel` | `dataclasses.dataclass`, `datetime.datetime`, `typing.Optional`, `numpy.ndarray` | Created by `registration_service`, queried by `UserRepository`, passed to `auth_service` for verification. `face_encoding` is a numpy array stored as binary in MongoDB. |
| `document.py` | 130 | **Document dataclass** and **SharedUser dataclass.** Document fields: `id`, `doc_id` (DOC-XXXX), `filename`, `original_filename`, `owner_id`, `file_type`, `file_size`, `encrypted_path`, `iv`, `encrypted_key`, `sha256_hash`, `uploaded_at`, `description`, `tags`, `shared_users` (list of `SharedUser`). SharedUser fields: `user_id`, `permission` (view/download), `shared_at`. | `Document` (dataclass), `SharedUser` (dataclass) | `BaseModel` | `dataclasses.dataclass`, `datetime.datetime`, `typing.List`, `typing.Optional` | Created by `document_service` during upload, queried by `DocumentRepository`, passed through `document_controller` to all document-related services. `iv` and `encrypted_key` are base64 strings. |
| `audit.py` | 120 | **AuditLog dataclass** and **AuditAction enum.** Log fields: `id`, `user_id`, `username`, `action` (AuditAction enum), `document_id`, `document_name`, `details`, `ip_address`, `timestamp`, `status` (success/failure). AuditAction values: `LOGIN`, `LOGOUT`, `REGISTER`, `UPLOAD`, `DOWNLOAD`, `SHARE`, `REVOKE`, `SEARCH`, `FACE_ENROLL`, `FACE_VERIFY`, `PASSWORD_CHANGE`, `VIEW_DETAILS`, `EXPORT_AUDIT`. | `AuditLog` (dataclass), `AuditAction` (Enum) | `BaseModel` | `dataclasses.dataclass`, `enum.Enum`, `datetime.datetime` | Created by `audit_service` for every user action. Queried by `AuditRepository`. Displayed in `audit_page.py`. The enum is referenced across all services that create audit entries. |

---

## crypto/

Hybrid encryption engine: AES-256-CBC for file encryption, RSA-2048 OAEP for key encryption.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 60 | Package exports. Re-exports all crypto classes so consumers can write `from crypto import AESCipher`. | N/A | All crypto submodules | N/A | Re-exports: `BaseCipher`, `BaseHasher`, `AESCipher`, `RSACipher`, `Hasher`, `KeyGenerator`, `base64_encode`, `base64_decode`, `EncryptedPayload`, `EncryptedKeyPayload`, and all exception classes. |
| `interfaces.py` | 66 | **Abstract base classes** for ciphers and hashers. `BaseCipher` requires `encrypt(plaintext) → ciphertext` and `decrypt(ciphertext) → plaintext`. `BaseHasher` requires `hash(data) → hash_string` and `verify(data, hash_string) → bool`. | `BaseCipher` (ABC), `BaseHasher` (ABC) | `abc.ABC` | `abc.ABC`, `abc.abstractmethod` | Parent classes for `AESCipher`, `RSACipher`, and `Hasher`. Enforces interface contracts across all crypto implementations. |
| `aes_cipher.py` | 158 | **AES-256-CBC encryption/decryption.** Generates a random 32-byte key and 16-byte IV per encryption. Uses PKCS7 padding. Methods: `encrypt(plaintext) → EncryptedPayload`, `decrypt(payload) → plaintext`. Also `encrypt_bytes(data) → EncryptedPayload` for binary files. | `AESCipher` | `BaseCipher`, `cryptography.hazmat`, `crypto.payload`, `crypto.base64_utils`, `crypto.exceptions` | `cryptography.hazmat.primitives.ciphers.algorithms`, `cryptography.hazmat.primitives.ciphers.modes`, `cryptography.hazmat.primitives.ciphers.Cipher`, `cryptography.hazmat.primitives.padding`, `os` | Used by `document_service.py` (encrypt on upload) and `document_download_service.py` (decrypt on download). The AES key it generates is then encrypted by `RSACipher` for storage. Returns `EncryptedPayload` objects. |
| `rsa_cipher.py` | 260 | **RSA-2048 OAEP encryption/decryption and key pair generation.** `generate_keypair() → (public_key, private_key)` returns PEM strings. `encrypt(plaintext, public_key_pem) → EncryptedKeyPayload` encrypts the AES key with the recipient's public key. `decrypt(payload, private_key_pem) → plaintext` decrypts with owner's private key. Supports encrypting for multiple recipients during sharing. | `RSACipher` | `BaseCipher`, `cryptography.hazmat`, `crypto.payload`, `crypto.base64_utils`, `crypto.exceptions` | `cryptography.hazmat.primitives.asymmetric.rsa`, `cryptography.hazmat.primitives.asymmetric.padding`, `cryptography.hazmat.primitives.asymmetric.utils`, `cryptography.hazmat.primitives.serialization`, `cryptography.hazmat.primitives.hashes` | Called by `registration_service.py` to generate user key pairs. Called by `document_service.py` to encrypt the AES key with the uploader's public key. Called by `document_download_service.py` to decrypt the AES key with the owner's private key. Called by `document_sharing_service.py` to re-encrypt the AES key for recipients. |
| `hashing.py` | 135 | **SHA-256 hashing.** `hash(data: bytes) → str` produces a hex digest. `hash_file(file_path) → str` streams a file for memory-efficient hashing. `verify(data, expected_hash) → bool` compares hashes using constant-time comparison. | `Hasher` | `BaseHasher` | `hashlib`, `hmac` | Used by `document_service.py` to compute file hashes before upload. Used by `auth_service.py` for password hashing (via bcrypt, not here — this is for file integrity). Used by `document_download_service.py` to verify downloaded file integrity. |
| `key_generator.py` | 95 | **Cryptographically secure random key generation.** `generate_aes_key() → bytes` (32 bytes), `generate_iv() → bytes` (16 bytes), `generate_salt() → bytes` (16 bytes), `generate_session_token() → str` (UUID4). All use `os.urandom` or `secrets`. | `KeyGenerator` | None | `os`, `secrets`, `uuid` | Called by `AESCipher` for key/IV generation, by `auth_service.py` for session tokens, by `registration_service.py` for password salts. |
| `base64_utils.py` | 53 | **Base64 encode/decode utilities** for safely encoding binary crypto data to/from strings for MongoDB storage. `base64_encode(data: bytes) → str`, `base64_decode(data: str) → bytes`. | `base64_encode()`, `base64_decode()` | None | `base64` | Used by `AESCipher` and `RSACipher` to encode ciphertext and keys. Used by repositories when reading/writing encrypted fields to MongoDB. |
| `payload.py` | 50 | **Data containers for encrypted outputs.** `EncryptedPayload`: holds `ciphertext` (str), `iv` (str). `EncryptedKeyPayload`: holds `encrypted_key` (str). Both serialize cleanly for MongoDB storage. | `EncryptedPayload` (dataclass), `EncryptedKeyPayload` (dataclass) | None | `dataclasses.dataclass` | Returned by `AESCipher.encrypt()` and `RSACipher.encrypt()`. Consumed by `document_service.py` to store `iv` and `encrypted_key` in the Document model. |
| `exceptions.py` | 42 | **Crypto-specific exceptions.** `CryptoError` (base), `EncryptionError`, `DecryptionError`, `KeyGenerationError`, `InvalidKeyError`, `HashVerificationError`. | `CryptoError`, `EncryptionError`, `DecryptionError`, `KeyGenerationError`, `InvalidKeyError`, `HashVerificationError` | None | None | Raised by all crypto modules. Caught by `services/*` and `controllers/*` to handle encryption/decryption failures gracefully. |

---

## services/

Business logic layer. Each service encapsulates a single domain concern.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `auth_service.py` | 211 | **Authentication service.** Handles login (`authenticate(username, password) → User`), logout, password verification via bcrypt, account lockout after N failed attempts, session token generation, and "remember me" token persistence. Checks `account_locked_until` before allowing login attempts. | `AuthService` | `bcrypt`, `database.repositories.user_repository`, `services.session_manager`, `services.audit_service`, `crypto.key_generator` | `bcrypt`, `datetime.datetime`, `typing.Optional` | Called by `auth_controller.py`. Uses `UserRepository` for user lookup and update. Uses `SessionManager` to create/clear sessions. Uses `AuditService` to log LOGIN/LOGOUT events. `bcrypt.checkpw()` verifies password hashes. |
| `registration_service.py` | 221 | **User registration service.** Validates input (username uniqueness, email format, password strength), hashes password with `bcrypt.hashpw`, generates RSA-2048 key pair via `RSACipher.generate_keypair()`, creates `User` model, and inserts via `UserRepository`. Enforces username/email uniqueness at the service level before DB insert. | `RegistrationService` | `bcrypt`, `crypto.rsa_cipher.RSACipher`, `database.repositories.user_repository`, `models.user.User`, `services.audit_service` | `re` (email regex), `bcrypt`, `datetime.datetime` | Called by `auth_controller.py` with `register()` action. Uses `RSACipher` to generate public/private keys stored on the `User` model. Uses `UserRepository.insert()` to persist. Uses `AuditService` to log REGISTER event. |
| `session_manager.py` | 180 | **In-memory session singleton.** Tracks the currently logged-in user, session start time, "remember me" state, and session timeout. Methods: `create_session(user)`, `get_current_user() → Optional[User]`, `is_authenticated() → bool`, `clear_session()`, `is_expired() → bool`. Enforces configurable session timeout. | `SessionManager` (singleton) | `models.user.User`, `config.settings` | `datetime.datetime`, `typing.Optional`, `threading.Lock` | Used by `auth_service.py` to manage login/logout. Queried by `auth_controller.py`, `document_controller.py`, and every service that needs the current user. `SessionManager.instance().get_current_user()` is the canonical pattern. |
| `document_service.py` | 218 | **Document upload service.** `upload_file(file_path, description, tags, owner) → Document`: reads file, computes SHA-256 hash, generates AES key + IV, encrypts file with AES-256-CBC, encrypts AES key with owner's RSA public key, saves encrypted file to storage, generates sequential DOC-XXXX ID, inserts document metadata in MongoDB, logs audit event. | `DocumentUploadService` | `crypto.aes_cipher.AESCipher`, `crypto.rsa_cipher.RSACipher`, `crypto.hashing.Hasher`, `storage.manager.StorageManager`, `database.repositories.document_repository`, `services.document_id_service`, `services.audit_service`, `models.document.Document` | `os`, `pathlib.Path`, `datetime.datetime` | Called by `document_controller.py`. Orchestrates the entire upload pipeline: hash → encrypt AES → encrypt key RSA → store file → save metadata. Uses `StorageManager` for file I/O, `DocumentRepository` for DB, `DocumentIdService` for ID generation, `AuditService` for logging. |
| `document_download_service.py` | 222 | **Document download + decryption service.** `download_file(document_id, user) → file_path`: verifies user has access (owner or shared), decrypts AES key with user's RSA private key, decrypts file with AES, verifies SHA-256 integrity, saves to download directory. Supports optional post-download actions. | `DocumentDownloadService` | `crypto.aes_cipher.AESCipher`, `crypto.rsa_cipher.RSACipher`, `crypto.hashing.Hasher`, `storage.manager.StorageManager`, `database.repositories.document_repository`, `services.audit_service` | `os`, `pathlib.Path`, `datetime.datetime` | Called by `document_controller.py`. Reads encrypted file from `StorageManager`, uses `RSACipher` to decrypt the AES key, `AESCipher` to decrypt the file, `Hasher` to verify integrity. Uses `AuditService` to log DOWNLOAD event. |
| `document_listing_service.py` | 284 | **Document listing, search, and detail retrieval.** `list_user_documents(user) → List[Document]`, `list_shared_documents(user) → List[Document]`, `search_documents(query, mode) → List[Document]`, `get_document_detail(doc_id, user) → Document`, `get_documents_by_type(user) → dict`, `get_monthly_uploads(user) → dict`, `get_recent_activity(user) → List[AuditLog]`. | `DocumentListingService` | `database.repositories.document_repository`, `database.repositories.audit_repository`, `models.document.Document` | `re`, `datetime.datetime`, `typing.List`, `typing.Dict` | Called by `document_controller.py` and `audit_controller.py`. Queries `DocumentRepository` for listings/search. Queries `AuditRepository` for activity feed. Provides aggregation data for dashboard charts. |
| `document_sharing_service.py` | 180 | **Document sharing via key re-encryption.** `share_document(doc_id, owner, recipient_username, permission) → SharedUser`: looks up recipient, re-encrypts the AES key with recipient's public key, adds recipient to `shared_users` list. `revoke_access(doc_id, owner, recipient_username)`: removes recipient. Validates owner permissions and prevents self-sharing. | `DocumentSharingService` | `crypto.rsa_cipher.RSACipher`, `database.repositories.document_repository`, `database.repositories.user_repository`, `services.audit_service` | `datetime.datetime` | Called by `document_controller.py`. Uses `RSACipher` to re-encrypt the AES key for each recipient. Uses `UserRepository` to look up recipients. Uses `DocumentRepository` to update the shared_users array. Uses `AuditService` for SHARE/REVOKE events. |
| `document_id_service.py` | 57 | **Sequential document ID generator.** `generate_id() → str` returns "DOC-XXXX" where XXXX is a zero-padded sequential number. Uses `CounterRepository` for atomic incrementing. | `DocumentIdService` | `database.repositories.counter_repository` | `str` | Called by `DocumentUploadService` during upload. Delegates to `CounterRepository.increment("document_id")` which uses MongoDB's `find_one_and_update` with `$inc` for atomicity. |
| `audit_service.py` | 160 | **Audit event logging service.** `log_event(user, action, document_id, document_name, details, status)`: constructs an `AuditLog` model and inserts via `AuditRepository`. `get_user_activity(user) → List[AuditLog]`, `get_document_history(doc_id) → List[AuditLog]`, `export_logs(filters) → List[AuditLog]`. | `AuditService` | `database.repositories.audit_repository`, `models.audit.AuditLog`, `models.audit.AuditAction` | `datetime.datetime`, `typing.Optional` | Called by virtually every other service for logging events. `auth_service` logs LOGIN/LOGOUT. `document_service` logs UPLOAD. `document_download_service` logs DOWNLOAD. `document_sharing_service` logs SHARE/REVOKE. `face_recognition_service` logs FACE_ENROLL/FACE_VERIFY. |
| `face_recognition_service.py` | 485 | **LBP-based face recognition.** `enroll_face(username, video_frame) → bool`: detects face in frame, extracts LBP features, trains a recognizer, saves encoding to user profile. `verify_face(video_frame) → Optional[User]`: detects face, predicts identity against all enrolled encodings, returns matching user. Uses OpenCV's `face.LBPHFaceRecognizer_create()`, Haar cascade classifier, and custom LBP feature extraction. Handles face detection, alignment, preprocessing (grayscale, histogram equalization), and confidence thresholding. | `FaceRecognitionService` | `cv2` (OpenCV), `numpy`, `database.repositories.user_repository`, `services.audit_service`, `models.user.User` | `cv2`, `numpy`, `typing.Optional`, `typing.Tuple`, `os`, `pathlib.Path`, `pickle` | Called by `face_controller.py`. Uses `cv2.CascadeClassifier` for face detection, `cv2.LBPHFaceRecognizer` for recognition. Stores face models on disk and encoding blobs in MongoDB via `UserRepository.update_face_encoding()`. Uses `AuditService` for FACE_ENROLL/FACE_VERIFY events. Integrates with `SessionManager` for auto-login on successful verification. |

---

## controllers/

Orchestration layer. Controllers receive requests from GUI/CLI, coordinate services, handle errors, and return results.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `auth_controller.py` | 214 | **Authentication orchestration.** `handle_login(username, password) → Result`, `handle_register(data) → Result`, `handle_logout()`, `handle_face_login(video_frame) → Result`. Validates input at the controller level (non-empty fields, email format), delegates to `AuthService` or `RegistrationService`, returns success/failure with messages. | `AuthController` | `services.auth_service.AuthService`, `services.registration_service.RegistrationService`, `services.session_manager.SessionManager`, `services.face_recognition_service.FaceRecognitionService` | `typing.Dict`, `typing.Any`, `typing.Optional` | Called by `login_page.py`, `register_page.py`, `face_page.py`, and `sidebar.py` (logout). Returns dictionaries with `success: bool` and `message: str` keys that GUI pages render directly. |
| `document_controller.py` | 422 | **Document orchestration.** The largest controller. `handle_upload(file_path, description, tags) → Result`, `handle_download(doc_id) → Result`, `handle_share(doc_id, username, permission) → Result`, `handle_revoke(doc_id, username) → Result`, `handle_list_documents() → Result`, `handle_search(query, mode) → Result`, `handle_get_detail(doc_id) → Result`, `handle_get_stats() → Result`, `handle_get_activity() → Result`. Validates all inputs, checks authentication, delegates to appropriate services. | `DocumentController` | `services.document_service.DocumentUploadService`, `services.document_download_service.DocumentDownloadService`, `services.document_listing_service.DocumentListingService`, `services.document_sharing_service.DocumentSharingService`, `services.session_manager.SessionManager` | `typing.Dict`, `typing.Any`, `typing.List`, `typing.Optional` | Called by all document-related GUI pages: `upload_page.py`, `download_page.py`, `share_page.py`, `shared_page.py`, `search_page.py`, `documents_page.py`, `document_detail_page.py`, `dashboard_page.py`. Returns result dictionaries. |
| `audit_controller.py` | 84 | **Audit orchestration.** `handle_get_logs(filters) → Result`, `handle_export_csv(filters) → Result`, `handle_get_activity() → Result`. Validates filter parameters, delegates to `AuditService` and `DocumentListingService`. | `AuditController` | `services.audit_service.AuditService`, `services.document_listing_service.DocumentListingService` | `typing.Dict`, `typing.Any`, `typing.List` | Called by `audit_page.py`. Returns result dictionaries with log data. |
| `face_controller.py` | 135 | **Face recognition orchestration.** `handle_enroll(username, video_frame) → Result`, `handle_verify(video_frame) → Result`. Validates username existence before enrollment, handles OpenCV frame processing, delegates to `FaceRecognitionService`, triggers auto-login on successful verify via `SessionManager`. | `FaceController` | `services.face_recognition_service.FaceRecognitionService`, `services.session_manager.SessionManager`, `database.repositories.user_repository.UserRepository` | `numpy.ndarray`, `typing.Optional` | Called by `face_page.py`. On successful `handle_verify`, calls `SessionManager.instance().create_session(user)` to log the user in automatically. |

---

## gui/

CustomTkinter-based graphical user interface. Organized into core modules, reusable components, and page screens.

### gui/\_\_init\_\_.py and core

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 8 | Lazy export of `App` class. `from gui import App` triggers import of `gui.app`. | N/A | `gui.app` | N/A | Imported by `main.py`. |
| `app.py` | 491 | **Main application window and navigation controller.** `App(ctk.CTk)` subclass. Manages a frame stack for page navigation (`show_page(name)`), holds the sidebar and topbar, initializes all controllers as instance attributes, and routes page transitions. Contains the page registry mapping page names to constructor functions. Handles window close events for session cleanup. | `App` | `customtkinter`, `gui.theme.ThemeManager`, `gui.components.sidebar.Sidebar`, `gui.components.topbar.TopBar`, all page modules, all controller modules | `customtkinter`, `typing.Dict`, `typing.Callable` | The central hub. Creates `Sidebar` and `TopBar` in the layout. Passes `App` reference to all pages so they can call `app.show_page()`. Holds references to `AuthController`, `DocumentController`, `AuditController`, `FaceController` which pages use for backend calls. |
| `theme.py` | 277 | **ThemeManager singleton.** Manages color schemes, fonts, dimensions, and dark/light mode. `get_color(key) → str`, `get_font(name, size) → Font`, `get_dimension(key) → int`. Defines `COLORS` dict (primary, secondary, accent, bg, surface, text, error, success, warning), `FONTS` dict (heading, subheading, body, small, mono), `DIMENSIONS` dict (sidebar_width, topbar_height, card_radius, padding, etc.). Supports runtime theme switching. | `ThemeManager` (singleton) | `customtkinter`, `config.settings` | `customtkinter.CTkFont`, `typing.Dict`, `typing.Tuple` | Imported by every GUI file. `ThemeManager.instance().get_color("primary")` is the standard pattern. `app.py` calls `set_mode()` for theme switching. Pages use it for consistent styling. |
| `animations.py` | 175 | **Animation utilities.** `fade_in(widget, duration, steps)`, `slide_in(widget, direction, duration)`, `pulse(widget, scale_range, duration)`, `scale(widget, target_size, duration)`. All use `after()` scheduling for non-blocking frame-by-frame animation. Supports easing functions (ease_in, ease_out, ease_in_out). | `fade_in()`, `slide_in()`, `pulse()`, `scale()` | `customtkinter` | `typing.Tuple`, `math` | Used by `login_page.py` (card fade-in, orb animation), `dashboard_page.py` (stat card entrance), `loading.py` (spinner animation), `dialogs.py` (dialog entrance). |
| `smooth_scrolling.py` | 115 | **Cross-platform smooth scrolling.** `SmoothScrollFrame` — a `CTkScrollableFrame` subclass that intercepts mouse wheel events and applies smooth interpolation. Handles Windows (`MouseWheel`), Linux (`Button-4/5`), and macOS (`MouseWheel` with different delta) events. | `SmoothScrollFrame` | `customtkinter` | `platform`, `typing` | Used by pages with scrollable content: `register_page.py`, `documents_page.py`, `audit_page.py`, `settings_page.py`, `shared_page.py`. |
| `assets.py` | 116 | **Icon and emoji constants.** Defines 80+ Unicode icon constants used throughout the GUI. Examples: `ICON_HOME = "\uf015"`, `ICON_UPLOAD = "\uf093"`, `ICON_DOWNLOAD = "\uf019"`, `ICON_SHARE = "\uf1e0"`, `ICON_SEARCH = "\uf002"`, `ICON_SETTINGS = "\uf013"`, `ICON_USER = "\uf007"`, `ICON_LOCK = "\uf023"`, `ICON_FILE = "\uf15b"`, `ICON_FOLDER = "\uf07b"`, etc. Uses Font Awesome Unicode range. | N/A | None | Imported by all GUI components and pages for consistent iconography. Pages reference like `assets.ICON_UPLOAD` in button text and labels. |

### gui/components/

Reusable UI building blocks. Each component is self-contained and styled via `ThemeManager`.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 14 | Re-exports all components. | N/A | All component modules | N/A | Re-exports: `Sidebar`, `SidebarItem`, `TopBar`, `StatCard`, `InfoCard`, `ActionCard`, `PageHeader`, `DonutChart`, `BarChart`, `MiniSparkline`, `StyledEntry`, `PasswordEntry`, `StyledComboBox`, `StyledButton`, `StyledText`, `StyledTable`, `LoadingSpinner`, `StatusBadge`, `ToolTip`, `AnimatedProgressBar`, `BaseDialog`, `SuccessDialog`, `ErrorDialog`, `WarningDialog`, `ConfirmDialog`, `Toast`. |
| `sidebar.py` | 296 | **Navigation sidebar.** `Sidebar(CTkFrame)` with `SidebarItem` sub-widgets. Contains app logo/title, navigation items (Dashboard, Documents, Upload, Download, Share, Shared, Search, Face ID, Audit, Settings, Profile), and logout button. Each `SidebarItem` has icon + label, hover effect (color change + scale), and active state highlighting. Sidebar collapses to icon-only on narrow widths. | `Sidebar`, `SidebarItem` | `customtkinter`, `gui.theme.ThemeManager`, `gui.assets` | `customtkinter`, `typing.Callable`, `typing.List`, `typing.Dict` | Created by `App` in `app.py`. Receives `on_navigate` callback that calls `app.show_page(name)`. Highlights the active page. Communicates logout request to `App` which delegates to `AuthController`. |
| `topbar.py` | 131 | **Top bar.** Displays current page title, search shortcut, notification icon, and user avatar/username dropdown. Shows the logged-in user's name and role. Contains a profile dropdown menu with "Profile" and "Logout" options. | `TopBar` | `customtkinter`, `gui.theme.ThemeManager`, `gui.assets`, `services.session_manager.SessionManager` | `customtkinter`, `typing.Callable` | Created by `App` in `app.py`. Updates title on page change. Profile dropdown triggers navigation to profile page or logout. |
| `cards.py` | 189 | **Card widgets.** `StatCard`: displays a metric (number + label + icon + trend indicator) with colored accent strip. `InfoCard`: read-only key-value display card. `ActionCard`: clickable card with icon + title + description, used for quick actions. `PageHeader`: page title + subtitle + optional action button. All cards have rounded corners, hover effects, and shadow simulation. | `StatCard`, `InfoCard`, `ActionCard`, `PageHeader` | `customtkinter`, `gui.theme.ThemeManager` | `customtkinter`, `typing` | Used by `dashboard_page.py` (StatCard × 4, ActionCard × 4, PageHeader), `document_detail_page.py` (InfoCard with 10 rows), `documents_page.py` (PageHeader). |
| `charts.py` | 161 | **Canvas-based chart widgets.** `DonutChart`: draws a donut/pie chart on a `CTkCanvas` with labeled segments and center text. `BarChart`: draws vertical bars with labels and values. `MiniSparkline`: draws a small line chart for trend visualization. All use `CTkCanvas` for rendering with theme-aware colors. | `DonutChart`, `BarChart`, `MiniSparkline` | `customtkinter`, `gui.theme.ThemeManager` | `customtkinter.CTkCanvas`, `typing.List`, `typing.Dict`, `math` | Used by `dashboard_page.py` for document type distribution (donut) and monthly upload trends (bar). |
| `forms.py` | 243 | **Styled form input widgets.** `StyledEntry`: themed text entry with focus animation and validation. `PasswordEntry`: password field with show/hide toggle button. `StyledComboBox`: themed dropdown. `StyledButton`: themed button with hover/press animations, supports icon + text, loading state. `StyledText`: themed multiline text area. All enforce consistent styling via `ThemeManager`. | `StyledEntry`, `PasswordEntry`, `StyledComboBox`, `StyledButton`, `StyledText` | `customtkinter`, `gui.theme.ThemeManager` | `customtkinter`, `typing.Callable`, `typing.Optional` | Used by every form page: `login_page.py`, `register_page.py`, `upload_page.py`, `share_page.py`, `search_page.py`, `profile_page.py`, `settings_page.py`. The primary input mechanism across the entire GUI. |
| `tables.py` | 95 | **Styled table widget.** `StyledTable`: wraps `ttk.Treeview` with custom styling to match the theme. Supports column sorting (click header), row selection, right-click context menu, alternating row colors, and scroll integration. Configurable columns via `set_columns()` method. | `StyledTable` | `tkinter.ttk`, `gui.theme.ThemeManager` | `tkinter.ttk`, `typing.List`, `typing.Dict`, `typing.Callable` | Used by `documents_page.py` (table view), `download_page.py`, `share_page.py`, `shared_page.py`, `search_page.py`, `audit_page.py`. Receives data as list of dicts. |
| `loading.py` | 153 | **Loading and status indicators.** `LoadingSpinner`: animated rotating spinner using canvas arcs. `StatusBadge`: colored pill badge showing status text (success/pending/failed). `ToolTip`: hover tooltip that appears near the cursor. `AnimatedProgressBar`: progress bar with smooth animation and percentage label. | `LoadingSpinner`, `StatusBadge`, `ToolTip`, `AnimatedProgressBar` | `customtkinter`, `gui.theme.ThemeManager`, `gui.animations` | `customtkinter`, `typing` | Used by `upload_page.py` and `download_page.py` (progress bar + spinner), `face_page.py` (spinner during enrollment/verify), `documents_page.py` (loading state), all pages with async operations. |
| `dialogs.py` | 216 | **Modal dialog widgets.** `BaseDialog`: centered modal with overlay. `SuccessDialog`: green-accented success message with OK button. `ErrorDialog`: red-accented error message. `WarningDialog`: yellow-accented warning with confirm/cancel. `ConfirmDialog`: yes/no confirmation prompt. `Toast`: non-blocking notification that auto-dismisses after configurable seconds, appears at top-right. All extend `CTkToplevel`. | `BaseDialog`, `SuccessDialog`, `ErrorDialog`, `WarningDialog`, `ConfirmDialog`, `Toast` | `customtkinter`, `gui.theme.ThemeManager` | `customtkinter.CTkToplevel`, `typing.Callable`, `typing.Optional` | Used by all pages for user feedback. `auth_controller.py` results trigger Success/Error dialogs. Upload/download trigger Toast notifications. Share/revoke trigger Confirm dialogs. |

### gui/pages/

Full-screen page widgets. Each page is a `CTkFrame` subclass.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 14 | Re-exports all page classes. | N/A | All page modules | N/A | Re-exports all 14 page classes. |
| `login_page.py` | 216 | **Login screen.** Glassmorphism-style login card centered on screen. Animated background with 3 floating orbs (pastel colors, sine-wave motion via `after()`). Contains: username `StyledEntry`, password `PasswordEntry`, "Remember Me" checkbox, "Forgot Password" link (shows info toast), "Sign In" `StyledButton`, "Login with Face" button (navigates to face page), "Register" link (navigates to register page). Card has semi-transparent white background with blur simulation (layered frames). | `LoginPage` | `gui.components.forms.*`, `gui.animations`, `gui.theme.ThemeManager`, `gui.assets`, `controllers.auth_controller.AuthController`, `services.session_manager.SessionManager` | `customtkinter`, `typing` | **Navigation:** register link → `app.show_page("register")`, face button → `app.show_page("face")`, successful login → `app.show_page("dashboard")`. **Backend:** Calls `AuthController.handle_login()`, checks `result["success"]`. Shows `SuccessDialog`/`ErrorDialog` on result. **Visual:** 3 orbs animated with `after()` loop, each with different amplitude/frequency. Card uses `fg_color=("white", "gray85")` for light/dark mode glass effect. |
| `register_page.py` | 188 | **Registration form.** `SmoothScrollFrame` containing: username `StyledEntry`, full name `StyledEntry`, email `StyledEntry`, role `StyledComboBox` (admin/user), `PasswordEntry` with visual strength meter (4-segment colored bar: red/orange/yellow/green based on length + complexity), confirm password `StyledEntry`, terms checkbox, "Create Account" `StyledButton`, "Back to Login" link. Password strength updates in real-time via `<Key>` binding. | `RegisterPage` | `gui.components.forms.*`, `gui.smooth_scrolling.SmoothScrollFrame`, `gui.theme.ThemeManager`, `gui.assets`, `controllers.auth_controller.AuthController` | `customtkinter`, `re`, `typing` | **Navigation:** back link → `app.show_page("login")`, successful registration → `app.show_page("login")` with success toast. **Backend:** Calls `AuthController.handle_register()`. **Validation:** client-side: non-empty fields, email regex `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$`, password ≥ 8 chars with upper + lower + digit + special, passwords match, terms checked. **Visual:** Password strength meter uses 4 `CTkFrame` segments that change color progressively. |
| `dashboard_page.py` | 209 | **Main dashboard.** `SmoothScrollFrame` with: welcome header (username + greeting based on time of day), 4 `StatCard` widgets (Total Documents, Shared With Me, Storage Used, Account Status), `DonutChart` showing document type distribution, `BarChart` showing monthly upload counts, 4 `ActionCard` quick actions (Upload, Search, Share, Face ID), recent activity feed (last 5 `AuditLog` entries as styled rows), system status section (encryption status, database status as `StatusBadge`). | `DashboardPage` | `gui.components.cards.*`, `gui.components.charts.*`, `gui.components.loading.StatusBadge`, `gui.smooth_scrolling.SmoothScrollFrame`, `gui.animations`, `gui.theme.ThemeManager`, `gui.assets`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing`, `datetime` | **Navigation:** ActionCards navigate to respective pages via `app.show_page()`. **Backend:** Calls `DocumentController.handle_get_stats()` for chart data and stat cards, `DocumentController.handle_get_activity()` for recent feed. Data loaded in `on_show()` callback when page becomes visible. **Visual:** Stat cards animate in with `fade_in()`. Charts redraw on theme change. Time-based greeting: "Good Morning/Afternoon/Evening, {username}". |
| `documents_page.py` | 250 | **Document listing with view toggle.** Two view modes: **Grid** (cards with file type icon, filename, size, date, owner) and **Table** (`StyledTable` with 7 columns: ID, Filename, Type, Size, Owner, Shared, Date). Toggle button switches between modes. Top bar has: `PageHeader`, search `StyledEntry` with live filtering, view toggle button. Table supports column sorting, right-click context menu (Download, Share, View Details, Delete), hover highlight. Grid cards have file-type-specific icons (PDF=red, DOC=blue, IMG=green, etc.) and similar context menu on right-click. | `DocumentsPage` | `gui.components.tables.StyledTable`, `gui.components.cards.PageHeader`, `gui.components.forms.*`, `gui.smooth_scrolling.SmoothScrollFrame`, `gui.theme.ThemeManager`, `gui.assets`, `gui.components.dialogs.*`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing`, `typing.List`, `typing.Dict` | **Navigation:** Context menu "View Details" → `app.show_page("document_detail")`, "Download" → `app.show_page("download")`, "Share" → `app.show_page("share")`. **Backend:** Calls `DocumentController.handle_list_documents()` on show. Search filters locally with regex. **Validation:** Shows `Toast` if no documents found. **Visual:** Grid cards have 160px width, rounded corners, shadow. File type icons from `assets` mapped by extension. Table has alternating row colors. |
| `upload_page.py` | 272 | **Document upload screen.** Drag-and-drop zone (dashed border, icon + "Drop file here or click to browse"), file details form (description `StyledText`, tags `StyledEntry`), file info display (name, size, type), `AnimatedProgressBar` with percentage, "Upload" `StyledButton`, success frame (hidden by default, shown after upload with checkmark icon + "Upload Successful" + "View Documents" button + "Upload Another" button). File selection via `filedialog.askopenfilename()`. | `UploadPage` | `gui.components.forms.*`, `gui.components.loading.AnimatedProgressBar`, `gui.components.dialogs.*`, `gui.theme.ThemeManager`, `gui.assets`, `controllers.document_controller.DocumentController` | `customtkinter`, `tkinter.filedialog`, `os`, `typing` | **Navigation:** "View Documents" → `app.show_page("documents")`, "Upload Another" resets form. **Backend:** Calls `DocumentController.handle_upload(file_path, description, tags)`. Progress bar simulates stages (hashing → encrypting → uploading → done). **Validation:** File must be selected, description optional, max file size check (configurable). **Visual:** Drag zone highlights on drag-over (`<DragEnter>`/`<DragLeave>` bindings). Progress bar animates through phases. Success frame uses `fade_in()`. |
| `download_page.py` | 182 | **Document download screen.** `StyledTable` listing all documents available to the user (own + shared). Select a row, click "Download" button. `AnimatedProgressBar` shows download/decryption progress. Post-download buttons: "Open File" (opens file explorer), "Open Folder" (opens download directory), "Download Another". Table has columns: ID, Filename, Type, Size, Owner, Date. | `DownloadPage` | `gui.components.tables.StyledTable`, `gui.components.loading.AnimatedProgressBar`, `gui.components.forms.StyledButton`, `gui.theme.ThemeManager`, `controllers.document_controller.DocumentController` | `customtkinter`, `subprocess`, `os`, `typing` | **Navigation:** "Open File"/"Open Folder" uses `subprocess.Popen`/`os.startfile`. **Backend:** Calls `DocumentController.handle_list_documents()` to populate table, `DocumentController.handle_download(doc_id)` on button click. **Validation:** Row must be selected before download. Shows `ErrorDialog` if no selection. **Visual:** Progress bar shows decryption progress. Table row highlighted on selection. |
| `share_page.py` | 146 | **Document sharing screen.** Top section: `StyledTable` of user's own documents (select to share). Bottom section: share form with recipient username `StyledEntry`, permission `StyledComboBox` (View/Download), "Share" button. Shows currently shared users for selected document in an info section. "Revoke" button next to each shared user entry. | `SharePage` | `gui.components.tables.StyledTable`, `gui.components.forms.*`, `gui.components.cards.InfoCard`, `gui.theme.ThemeManager`, `gui.components.dialogs.*`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing`, `typing.List` | **Backend:** Calls `DocumentController.handle_list_documents()` for document table, `DocumentController.handle_share(doc_id, username, permission)` on share, `DocumentController.handle_revoke(doc_id, username)` on revoke. **Validation:** Must select a document, username must be non-empty, cannot share with self, permission must be selected. **Visual:** Selected document's shared users shown in `InfoCard` below the form. |
| `shared_page.py` | 116 | **Shared documents view.** Filter: `StyledComboBox` with "Shared With Me" / "Shared By Me" options. Search `StyledEntry` for filtering. `StyledTable` showing shared documents with columns: ID, Filename, Owner, Permission, Shared Date. "Revoke Access" button (only enabled for "Shared By Me" filter). | `SharedPage` | `gui.components.tables.StyledTable`, `gui.components.forms.*`, `gui.theme.ThemeManager`, `gui.assets`, `gui.smooth_scrolling.SmoothScrollFrame`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing` | **Backend:** Calls `DocumentController.handle_list_documents()` and filters based on mode. Revoke calls `DocumentController.handle_revoke()`. **Validation:** Must select a row and be in "Shared By Me" mode for revoke. **Visual:** Revoke button disabled when viewing "Shared With Me" documents. |
| `search_page.py` | 210 | **Advanced search screen.** Radio buttons for search mode: "Filename", "Type", "Owner", "All". Search `StyledEntry` with "Search" button. `StyledTable` for results with 7 columns. Search executes on Enter key or button click. Results update dynamically. | `SearchPage` | `gui.components.tables.StyledTable`, `gui.components.forms.*`, `gui.theme.ThemeManager`, `gui.assets`, `gui.components.dialogs.*`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing`, `typing.List` | **Backend:** Calls `DocumentController.handle_search(query, mode)` on submit. **Validation:** Query must be non-empty. Shows `Toast` for no results. **Visual:** Radio buttons styled with theme accent color. Results table fades in after search. |
| `face_page.py` | 261 | **Face enrollment and verification.** Two-column layout. **Left column (Enroll):** username `StyledEntry`, camera preview frame (displays `cv2.VideoCapture` feed as `CTkImage`), "Start Camera"/"Stop Camera" buttons, "Enroll Face" button, `LoadingSpinner` during enrollment. **Right column (Verify):** camera preview frame, "Start Camera"/"Stop Camera" buttons, "Verify Face" button, `LoadingSpinner` during verification, result display (success/fail icon + matched username). Camera feed updates via `after(30)` loop reading frames from `cv2.VideoCapture(0)`. | `FacePage` | `gui.components.forms.*`, `gui.components.loading.LoadingSpinner`, `gui.theme.ThemeManager`, `gui.assets`, `gui.components.dialogs.*`, `controllers.face_controller.FaceController` | `cv2`, `customtkinter`, `PIL.Image`, `PIL.ImageTk`, `numpy`, `typing` | **Backend:** Calls `FaceController.handle_enroll(username, frame)` and `FaceController.handle_verify(frame)`. **Validation:** Username required for enroll. Camera must be active. **Visual:** Camera preview uses `CTkImage` converted from OpenCV BGR → PIL RGB. Spinner shows during processing. Two-column layout uses `grid()` with `weight=1` for equal split. |
| `audit_page.py` | 140 | **Audit log viewer.** Filter row: action `StyledComboBox` (all LOGIN/UPLOAD/DOWNLOAD/etc.), user `StyledEntry` filter, search `StyledEntry`. `StyledTable` with 7 columns: Timestamp, User, Action, Document, Details, Status, IP. "Export CSV" button saves filtered logs to file via `filedialog.asksaveasfilename()`. | `AuditPage` | `gui.components.tables.StyledTable`, `gui.components.forms.*`, `gui.theme.ThemeManager`, `gui.assets`, `gui.smooth_scrolling.SmoothScrollFrame`, `gui.components.dialogs.*`, `controllers.audit_controller.AuditController` | `customtkinter`, `tkinter.filedialog`, `csv`, `typing` | **Backend:** Calls `AuditController.handle_get_logs(filters)` on show and filter change, `AuditController.handle_export_csv(filters)` on export. **Validation:** Shows `Toast` if no logs match filters. **Visual:** Table has color-coded status badges (green=success, red=failure). CSV export uses `csv.writer`. |
| `settings_page.py` | 151 | **Application settings.** Sections: **Appearance** — theme switcher (`StyledComboBox`: Dark/Light/System), accent color picker (8 color swatches as `StyledButton` toggles). **Security** — 2FA toggle (`StyledButton` on/off), session timeout `StyledComboBox` (15/30/60/120 min). **Backup** — "Create Backup" button (calls file dialog for destination), "Restore Backup" button. Each section is a `InfoCard` with title. Settings persist to `.env` and in-memory `Settings`. | `SettingsPage` | `gui.components.forms.*`, `gui.components.cards.InfoCard`, `gui.theme.ThemeManager`, `gui.assets`, `gui.components.dialogs.*` | `customtkinter`, `typing`, `config.settings.Settings` | **Navigation:** None (settings page). **Backend:** Theme change calls `ThemeManager.instance().set_mode()` and `customtkinter.set_appearance_mode()`. Accent color change updates `ThemeManager` colors. Backup/restore calls `storage.manager.StorageManager`. **Visual:** Accent color swatches are circular `StyledButton` widgets with colored backgrounds. Active swatch has a border highlight. |
| `profile_page.py` | 187 | **User profile and password change.** Two sections. **Profile:** circular avatar with user initial (first letter of username, colored background), `StyledEntry` fields for full name and email (editable), "Save Changes" button. **Change Password:** current password `PasswordEntry`, new password `PasswordEntry` with strength meter, confirm password `PasswordEntry`, "Update Password" button. Profile data loaded from `SessionManager.instance().get_current_user()`. | `ProfilePage` | `gui.components.forms.*`, `gui.theme.ThemeManager`, `gui.assets`, `gui.components.dialogs.*`, `controllers.auth_controller.AuthController`, `services.session_manager.SessionManager` | `customtkinter`, `typing` | **Backend:** Save profile calls update endpoint. Change password calls `AuthController.handle_password_change()`. **Validation:** Email format, new password strength requirements, passwords match. **Visual:** Avatar is 80px circle with centered initial letter in white on a theme-colored background. |
| `document_detail_page.py` | 162 | **Document metadata detail view.** Back arrow button (navigates to documents page). `PageHeader` with document filename. `InfoCard` with 10 metadata rows: Document ID, Filename, Original Filename, Type, Size (formatted), Owner, Upload Date, SHA-256 Hash (truncated with copy button), Description, Tags. Action buttons at bottom: "Download", "Share", "Delete" (with confirmation dialog). | `DocumentDetailPage` | `gui.components.cards.*`, `gui.components.forms.StyledButton`, `gui.components.dialogs.*`, `gui.theme.ThemeManager`, `gui.assets`, `controllers.document_controller.DocumentController` | `customtkinter`, `typing` | **Navigation:** Back button → `app.show_page("documents")`. Download → `app.show_page("download")`. Share → `app.show_page("share")`. **Backend:** Receives `doc_id` as parameter, calls `DocumentController.handle_get_detail(doc_id)` on show. Delete calls `DocumentController` with confirm dialog. **Visual:** Hash field shows first 32 chars + "..." with clipboard copy on click. |

---

## cli/

Command-line interface. Full-featured CLI alternative to the GUI.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `main.py` | 767 | **Complete CLI application.** `CLIApp` class with 13 menu options: 1) Login, 2) Register, 3) Upload Document, 4) Download Document, 5) List Documents, 6) Share Document, 7) View Shared Documents, 8) Search Documents, 9) Face Enrollment, 10) Face Verification, 11) View Audit Logs, 12) User Profile, 13) Logout. Uses `getpass` for hidden password input, `colorama` for colored terminal output, `rich` tables for formatted display. Each option delegates to the same controllers used by the GUI. | `CLIApp` | `controllers.auth_controller.AuthController`, `controllers.document_controller.DocumentController`, `controllers.audit_controller.AuditController`, `controllers.face_controller.FaceController`, `services.session_manager.SessionManager` | `getpass`, `colorama`, `rich.console.Console`, `rich.table.Table`, `os`, `typing`, `sys` | Uses the exact same controller and service layer as the GUI. The only difference is the presentation layer. This proves the MVC separation works — controllers are interface-agnostic. Calls `AuthController.handle_login()`, `DocumentController.handle_upload()`, etc. directly. |

---

## utilities/

Cross-cutting utility functions.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `helpers.py` | 100 | **Shared utility functions.** `get_timestamp() → str` (ISO format), `get_formatted_timestamp() → str` (human-readable), `sanitize_filename(name) → str` (removes special chars, limits length), `validate_email(email) → bool` (regex check), `validate_password_strength(password) → tuple[bool, str]` (min 8, upper, lower, digit, special), `format_file_size(bytes) → str` (human-readable: KB/MB/GB), `truncate_string(s, max_len) → str`. | `get_timestamp()`, `get_formatted_timestamp()`, `sanitize_filename()`, `validate_email()`, `validate_password_strength()`, `format_file_size()`, `truncate_string()` | None | `re`, `datetime.datetime`, `typing.Tuple` | Imported by `services/registration_service.py` (email/password validation), `services/document_service.py` (filename sanitization), `gui/pages/document_detail_page.py` (file size formatting, string truncation), `cli/main.py` (input validation). |

---

## exceptions/

Application-level exception hierarchy.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `custom_exceptions.py` | 55 | **8 custom exception classes.** `SDMSError` (base), `AuthenticationError`, `AuthorizationError`, `DocumentNotFoundError`, `DocumentAccessDenied`, `EncryptionError`, `DecryptionError`, `ValidationError`, `SessionExpiredError`. Each carries a `message` and optional `code`. | `SDMSError`, `AuthenticationError`, `AuthorizationError`, `DocumentNotFoundError`, `DocumentAccessDenied`, `EncryptionError`, `DecryptionError`, `ValidationError`, `SessionExpiredError` | None | None | Base class for all SDMS exceptions. Raised by services when business logic fails. Caught by controllers to produce result dictionaries. Caught by GUI pages to show error dialogs. Caught by CLI to print colored error messages. The hierarchy allows `except SDMSError` to catch all application errors. |

---

## logger/

Application logging configuration.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `logging_config.py` | 80 | **Rotating file + stream logging setup.** `setup_logging()`: configures Python `logging` with two handlers — `RotatingFileHandler` (writes to `logs/sdms.log`, 5MB max, 5 backups) and `StreamHandler` (stdout for console). Log format: `[%(asctime)s] %(levelname)s %(name)s: %(message)s`. Reads log level from `Settings`. Configures separate loggers for `uvicorn`, `pymongo`, and application code with different levels. | `setup_logging()` | `config.settings.Settings`, `logging` | `logging`, `logging.handlers.RotatingFileHandler`, `os` | Called by `main.py` at startup before any other initialization. Sets the root logger config. All modules using `logging.getLogger(__name__)` inherit this configuration. The `logs/` directory is created if it doesn't exist. |

---

## storage/

File system operations for encrypted and temp files.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `manager.py` | 80 | **StorageManager singleton.** Handles all file I/O for encrypted documents and temporary files. `save_encrypted(doc_id, data) → str` (saves to `storage/encrypted_documents/{doc_id}.enc`, returns path). `load_encrypted(path) → bytes`. `save_temp(filename, data) → str` (saves to `storage/temp/`). `cleanup_temp()` (deletes all temp files). `get_storage_path(doc_id) → Path`. `ensure_directories()` (creates required dirs if missing). | `StorageManager` (singleton) | `pathlib.Path`, `config.settings` | `pathlib.Path`, `os`, `shutil`, `typing` | Used by `document_service.py` (save encrypted file after upload), `document_download_service.py` (load encrypted file for decryption), `upload_page.py` and `download_page.py` (via controller). Directory structure: `storage/encrypted_documents/` for permanent encrypted files, `storage/temp/` for temporary decrypted files. `ensure_directories()` called at startup. |

---

## tests/

Pytest test suite. 7 test files with 207-line conftest providing shared fixtures.

| File | Lines | Purpose | Key Classes/Functions | Dependencies | Imported Modules | Communication |
|------|-------|---------|----------------------|--------------|-----------------|---------------|
| `__init__.py` | 0 | Package marker. Empty. | N/A | None | None | N/A |
| `conftest.py` | 207 | **Shared pytest fixtures.** `mock_db`: mocked MongoDB with `mongomock`. `mock_settings`: patched `Settings`. `sample_user`: creates a `User` with test data. `sample_document`: creates a `Document`. `sample_audit_log`: creates an `AuditLog`. `mock_session_manager`: mocked singleton. `mock_repositories`: mocked repository instances. `temp_dir`: temporary directory cleaned after test. `mock_aes_cipher`: mocked AES cipher. `mock_rsa_cipher`: mocked RSA cipher. `authenticated_session`: pre-authenticated session. `mock_file_upload`: mock file bytes. | Multiple fixtures | `pytest`, `mongomock`, `unittest.mock`, `models.*`, `config.settings` | `pytest.fixture`, `mongomock.MongoClient`, `unittest.mock.patch`, `unittest.mock.MagicMock`, `tempfile`, `os` | Used by all test files. Provides isolated, mocked dependencies so tests don't require a live MongoDB instance or filesystem. |
| `test_authentication.py` | 246 | **Auth service tests.** Tests: successful login, wrong password, non-existent user, account lockout after N failures, session creation/clearance, password hashing verification, login audit logging, logout audit logging, session expiry. | Multiple test functions | `conftest.py` fixtures, `services.auth_service.AuthService` | `pytest`, `unittest.mock` | Uses `conftest.mock_db`, `conftest.sample_user`, `conftest.mock_session_manager`. Mocks `bcrypt.checkpw` for password verification. |
| `test_document_upload.py` | 291 | **Upload service tests.** Tests: successful upload (encryption + storage + DB), file hashing, AES key generation, RSA key encryption, sequential ID generation, upload audit logging, empty file handling, large file handling, duplicate filename handling, storage directory creation. | Multiple test functions | `conftest.py` fixtures, `services.document_service.DocumentUploadService` | `pytest`, `unittest.mock`, `tempfile` | Uses `conftest.mock_aes_cipher`, `conftest.mock_rsa_cipher`, `conftest.temp_dir`. Mocks `StorageManager` for file operations. |
| `test_document_download.py` | 431 | **Download service tests.** Tests: successful download (decrypt + verify), owner access, shared user access, unauthorized access denial, AES key decryption with private key, file decryption, SHA-256 integrity verification, download audit logging, file not found handling, corrupted file detection, permission checks. | Multiple test functions | `conftest.py` fixtures, `services.document_download_service.DocumentDownloadService` | `pytest`, `unittest.mock` | Uses `conftest.sample_document`, `conftest.sample_user`, `conftest.mock_rsa_cipher`. Mocks file read operations. |
| `test_document_listing.py` | 528 | **Listing service tests.** Tests: list user documents, list shared documents, search by filename, search by type, search by owner, search all, document detail retrieval, document type aggregation, monthly upload stats, recent activity feed, empty results, pagination, access control (only own + shared). | Multiple test functions | `conftest.py` fixtures, `services.document_listing_service.DocumentListingService` | `pytest`, `unittest.mock` | Uses `conftest.sample_document`, `conftest.sample_audit_log`. Mocks repository queries with various filter combinations. |
| `test_document_sharing.py` | 411 | **Sharing service tests.** Tests: successful share (key re-encryption + DB update), recipient lookup, permission assignment, share audit logging, revoke access, revoke audit logging, self-sharing prevention, double-share prevention, owner-only revoke, non-existent recipient, non-existent document. | Multiple test functions | `conftest.py` fixtures, `services.document_sharing_service.DocumentSharingService` | `pytest`, `unittest.mock` | Uses `conftest.sample_document`, `conftest.sample_user`, `conftest.mock_rsa_cipher`. Mocks `RSACipher.encrypt` for key re-encryption. |
| `test_models.py` | 163 | **Model serialization tests.** Tests: `User.to_dict()` / `User.from_dict()` round-trip, `Document.to_dict()` / `Document.from_dict()` round-trip, `SharedUser` serialization, `AuditLog` serialization, `AuditAction` enum values, `ObjectId` handling in serialization, optional field handling, default value behavior. | Multiple test functions | `models.user.User`, `models.document.Document`, `models.audit.AuditLog` | `pytest`, `bson.objectid.ObjectId`, `datetime.datetime` | Direct model testing — no mocks needed. Verifies data integrity through serialization cycles. |
| `test_registration.py` | 233 | **Registration service tests.** Tests: successful registration, duplicate username rejection, duplicate email rejection, invalid email format, weak password rejection, RSA key pair generation, password hashing, user model creation, registration audit logging, username uniqueness validation. | Multiple test functions | `conftest.py` fixtures, `services.registration_service.RegistrationService` | `pytest`, `unittest.mock` | Uses `conftest.mock_db`, `conftest.mock_rsa_cipher`. Mocks `bcrypt.hashpw` for password hashing. |
| `test_repositories.py` | 287 | **Repository CRUD tests.** Tests: `UserRepository` insert/find/update/delete, `DocumentRepository` CRUD + search + shared queries, `AuditRepository` insert + date range queries + action filter, `CounterRepository` atomic increment, `BaseRepository` generic operations, duplicate key error handling, not-found error handling, empty collection handling. | Multiple test functions | `conftest.py` fixtures, `database.repositories.*` | `pytest`, `mongomock` | Uses `conftest.mock_db` (mongomock) for in-memory MongoDB. Tests run against a real MongoDB wire protocol via mongomock. |

---

## Static Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `assets/animations/` | Animation data files (Lottie JSON, keyframe definitions) | Empty — reserved for future use |
| `assets/fonts/` | Custom font files (TTF/OTF) | Empty — uses system fonts via ThemeManager |
| `assets/icons/` | Application icon files (ICO, PNG) | Empty — uses Unicode icons from `assets.py` |
| `assets/images/` | Image assets (logos, backgrounds) | Empty — uses canvas-drawn graphics |
| `assets/themes/` | Theme JSON files for CustomTkinter | Empty — themes defined in `theme.py` |
| `download/` | Decrypted files are saved here after download | Runtime-created, user-facing |
| `logs/` | Rotating log file `sdms.log` (5MB × 5 backups) | Runtime-created, contains application logs |
| `storage/encrypted_documents/` | Encrypted document files (`.enc` extension) | Runtime-created, permanent |
| `storage/temp/` | Temporary decrypted files (cleaned after use) | Runtime-created, transient |

---

## Cross-Module Communication Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     main.py                             │
│  Loads .env → Settings.load() → setup_logging()        │
│  Parses args → App() or CLIApp()                        │
└──────────────┬────────────────────┬─────────────────────┘
               │                    │
        ┌──────▼──────┐     ┌──────▼──────┐
        │   GUI Layer │     │   CLI Layer  │
        │  (gui/app)  │     │  (cli/main)  │
        └──────┬──────┘     └──────┬──────┘
               │                    │
               └────────┬───────────┘
                        │
        ┌───────────────▼───────────────┐
        │     Controller Layer          │
        │  auth_controller              │
        │  document_controller          │
        │  audit_controller             │
        │  face_controller              │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │      Service Layer            │
        │  auth_service                 │
        │  registration_service         │
        │  session_manager (singleton)  │
        │  document_service             │
        │  document_download_service    │
        │  document_listing_service     │
        │  document_sharing_service     │
        │  document_id_service          │
        │  audit_service                │
        │  face_recognition_service     │
        └──┬──────────┬───────────┬─────┘
           │          │           │
    ┌──────▼──┐ ┌─────▼─────┐ ┌──▼──────────┐
    │  Crypto │ │ Database  │ │  Storage    │
    │  Layer  │ │  Layer    │ │  Layer      │
    │ AES     │ │ Manager   │ │ Manager     │
    │ RSA     │ │ Repos     │ │ (singleton) │
    │ Hash    │ │ (×4)      │ │             │
    │ Keys    │ │           │ │             │
    └────┬────┘ └─────┬─────┘ └─────────────┘
         │            │
    ┌────▼────┐ ┌─────▼─────┐
    │ Models  │ │  MongoDB  │
    │ User    │ │ (remote)  │
    │ Document│ │           │
    │ AuditLog│ │           │
    └─────────┘ └───────────┘
```

### Key Communication Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Singleton Access** | Config, DB manager, session, and storage use singleton pattern | `Settings.instance()`, `DatabaseManager.instance()`, `SessionManager.instance()` |
| **Dependency Injection** | Controllers receive services via constructor or method params | `DocumentController` uses `DocumentUploadService` |
| **Result Dictionaries** | Controllers return `{"success": bool, "message": str, "data": Any}` | GUI pages read `result["success"]` to decide dialog type |
| **Event Logging** | Every significant action creates an `AuditLog` via `AuditService` | Login, upload, download, share, revoke, face events |
| **Encryption Pipeline** | Upload: generate AES key → encrypt file → encrypt key with RSA → store both | `AESCipher` → `RSACipher` → `StorageManager` |
| **Decryption Pipeline** | Download: decrypt RSA key → decrypt AES → verify hash → save file | `RSACipher` → `AESCipher` → `Hasher` → `StorageManager` |
| **GUI Callback Chain** | Widget event → Controller method → Service method → Repository → MongoDB | Button click → `document_controller.handle_upload()` → `document_service.upload()` → `document_repository.insert()` |
