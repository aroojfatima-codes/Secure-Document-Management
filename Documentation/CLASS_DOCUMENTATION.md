# SDMS Class Documentation

> **Secure Document Management System — Complete Class Reference**
> Version 1.0.0 | Generated from source code

---

## Table of Contents

1. [Models Module](#1-models-module)
2. [Crypto Module](#2-crypto-module)
3. [Database Module](#3-database-module)
4. [Services Module](#4-services-module)
5. [Controllers Module](#5-controllers-module)
6. [Storage Module](#6-storage-module)
7. [Config Module](#7-config-module)
8. [Exceptions Module](#8-exceptions-module)
9. [GUI Classes](#9-gui-classes)

---

## 1. Models Module

**Path:** `models/`

### 1.1 BaseModel (ABC)

**File:** `models/base.py:14`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Abstract base class providing a consistent interface for all SDMS data models. Ensures every model can serialise to MongoDB documents, validate its fields, and deserialise from stored data. |
| **Parent Class** | `abc.ABC` |
| **Used By** | `User`, `Document`, `AuditLog` |

#### Constructor

No `__init__`; relies on subclass dataclass fields.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | **Abstract.** Serialize this model to a MongoDB document dict (excludes `_id`). |
| `validate` | `(self) -> None` | **Abstract.** Validate model fields; raises `ValidationError` on failure. |
| `from_dict` | `@classmethod (cls, data: dict[str, Any]) -> BaseModel` | **Abstract.** Construct a model instance from a MongoDB document dict. |
| `update` | `(self, updates: dict[str, Any]) -> None` | Apply field updates from a dict, skipping unknown attributes. |

#### Usage Example

```python
class MyModel(BaseModel):
    def to_dict(self): return {"field": self.field}
    def validate(self): pass
    @classmethod
    def from_dict(cls, data): return cls(**data)
```

---

### 1.2 User

**File:** `models/user.py:21`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Represents an authenticated system user with credentials, RSA key material, role-based access, and optional face biometric data. |
| **Parent Class** | `BaseModel` (via `@dataclass`) |
| **Used By** | `UserRepository`, `AuthService`, `RegistrationService`, `FaceRecognitionService`, `SessionManager` |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `str` | `""` | Unique identifier (UUID4 hex) |
| `username` | `str` | `""` | Unique login name |
| `password_hash` | `str` | `""` | SHA-256 hex digest of the user's password |
| `role` | `str` | `"viewer"` | RBAC role: `"admin"`, `"editor"`, or `"viewer"` |
| `rsa_public_key` | `str` | `""` | PEM-encoded RSA-2048 public key |
| `rsa_private_key` | `str` | `""` | PEM-encoded encrypted RSA-2048 private key |
| `created_at` | `datetime` | `datetime.now(UTC)` | Account creation timestamp |
| `updated_at` | `datetime` | `datetime.now(UTC)` | Last modification timestamp |
| `is_active` | `bool` | `True` | Whether the account is enabled |
| `face_encoding` | `list[float]` | `[]` | Facial recognition encoding (LBPH histogram) |
| `face_enrolled` | `bool` | `False` | Whether face biometrics are enrolled |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | Serialize to a MongoDB document dict (without `_id`). |
| `validate` | `(self) -> None` | Validate `user_id`, `username`, `password_hash`, `role`, and `created_at`. Raises `ValidationError`. |
| `from_dict` | `@classmethod (cls, data: dict) -> User` | Construct from a MongoDB document dict. Handles `_id` presence. |
| `touch` | `(self) -> None` | Set `updated_at` to the current UTC time. |

#### Usage Example

```python
from models.user import User

user = User(
    user_id="a1b2c3...",
    username="alice",
    password_hash="5e884898da2...",
    role="editor",
)
user.validate()
user_dict = user.to_dict()
restored = User.from_dict(user_dict)
user.touch()  # updates updated_at
```

---

### 1.3 SharedUser

**File:** `models/document.py:19`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Represents a user with whom a document has been shared. Embedded as a sub-document in the `Document.shared_with` list. |
| **Parent Class** | `@dataclass` (standalone) |
| **Used By** | `Document.add_share()`, `DocumentRepository`, `DocumentSharingService` |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `user_id` | `str` | *(required)* | The target user's unique identifier |
| `permission` | `str` | `"view"` | Access level: `"view"` or `"edit"` |
| `encrypted_aes_key` | `str` | `""` | AES key encrypted with the recipient's RSA public key (Base64) |
| `shared_at` | `datetime` | `datetime.now(UTC)` | Timestamp when the share was created |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | Serialize for MongoDB embedding. |
| `from_dict` | `@classmethod (cls, data: dict) -> SharedUser` | Construct from a MongoDB sub-document. |

---

### 1.4 Document

**File:** `models/document.py:58`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Represents an encrypted document with integrity and sharing metadata. Stores everything needed to locate, decrypt, and verify a document. |
| **Parent Class** | `BaseModel` (via `@dataclass`) |
| **Used By** | `DocumentRepository`, `DocumentUploadService`, `DocumentDownloadService`, `DocumentSharingService` |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_id` | `str` | `""` | Unique identifier (UUID4 hex or sequential `DOC-XXXX`) |
| `original_filename` | `str` | `""` | User-visible filename before encryption |
| `encrypted_filename` | `str` | `""` | Filename used on disk after encryption |
| `owner_id` | `str` | `""` | `user_id` of the document owner |
| `encrypted_aes_key` | `str` | `""` | RSA-wrapped AES-256 key (Base64) |
| `iv` | `str` | `""` | AES-CBC initialisation vector (Base64) |
| `sha256_hash` | `str` | `""` | SHA-256 hex digest of the plaintext |
| `file_size` | `int` | `0` | Original plaintext size in bytes |
| `mime_type` | `str` | `"application/octet-stream"` | MIME type of the original file |
| `algorithm` | `str` | `"AES-256-CBC"` | Encryption algorithm identifier |
| `created_at` | `datetime` | `datetime.now(UTC)` | Upload timestamp |
| `updated_at` | `datetime` | `datetime.now(UTC)` | Last modification timestamp |
| `is_deleted` | `bool` | `False` | Soft-delete flag |
| `shared_with` | `list[SharedUser]` | `[]` | List of sharing entries |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | Serialize to a MongoDB document dict. Recursively serialises `shared_with`. |
| `validate` | `(self) -> None` | Validate required fields: `document_id`, `original_filename`, `encrypted_filename`, `owner_id`, `encrypted_aes_key`, `iv`, `sha256_hash`. |
| `from_dict` | `@classmethod (cls, data: dict) -> Document` | Construct from a MongoDB document dict, including nested `SharedUser` entries. |
| `touch` | `(self) -> None` | Set `updated_at` to the current UTC time. |
| `add_share` | `(self, user_id: str, permission: str = "view", encrypted_aes_key: str = "") -> None` | Append a `SharedUser` entry and call `touch()`. No duplicate check. |

#### Usage Example

```python
doc = Document(document_id="DOC-0001", original_filename="report.pdf", owner_id="u1")
doc.add_share(user_id="u2", permission="view", encrypted_aes_key="base64...")
print(doc.shared_with)  # [SharedUser(user_id='u2', ...)]
```

---

### 1.5 AuditLog

**File:** `models/audit.py:57`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Immutable audit trail record for every significant system event. Tracks who did what, when, with what outcome. |
| **Parent Class** | `BaseModel` (via `@dataclass`) |
| **Used By** | `AuditRepository`, `AuditService`, all controllers |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `audit_id` | `str` | `""` | Unique identifier (UUID4 hex) |
| `timestamp` | `datetime` | `datetime.now(UTC)` | When the event occurred |
| `user_id` | `str` | `""` | Acting user's ID |
| `username` | `str` | `""` | Acting user's name |
| `role` | `str` | `""` | Acting user's role |
| `action` | `str` | `""` | Action performed (from `AuditAction` enum values) |
| `resource_type` | `str` | `""` | Resource affected (from `ResourceType` enum values) |
| `resource_id` | `str` | `""` | ID of the affected resource |
| `resource_name` | `str` | `""` | Human-readable resource name |
| `status` | `str` | `""` | Outcome: `"SUCCESS"`, `"FAILURE"`, `"DENIED"`, `"ERROR"` |
| `message` | `str` | `""` | Descriptive message |
| `severity` | `str` | `"INFO"` | `"INFO"`, `"WARNING"`, `"SECURITY_ALERT"`, `"CRITICAL"` |
| `session_id` | `str` | `""` | Session in which the event occurred |
| `client_ip` | `str` | `""` | Client IP address |
| `device_info` | `str` | `""` | Client device information |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary additional data |
| `created_at` | `datetime | None` | `None` (set to `timestamp` in `__post_init__`) | Creation timestamp |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | Serialize to a MongoDB document dict. |
| `validate` | `(self) -> None` | Validate `audit_id`, `action`, `resource_type`, `status`, and `severity`. |
| `from_dict` | `@classmethod (cls, data: dict) -> AuditLog` | Construct from a MongoDB document dict. |

---

### 1.6 Enumerations

**File:** `models/audit.py`

#### AuditAction

| Value | Description |
|-------|-------------|
| `USER_REGISTRATION` | New user registered |
| `USER_LOGIN` | Successful login |
| `USER_LOGIN_FAILED` | Failed login attempt |
| `USER_LOGOUT` | User logged out |
| `DOCUMENT_UPLOAD` | Document uploaded |
| `DOCUMENT_DOWNLOAD` | Document downloaded |
| `DOCUMENT_SHARE` | Document shared with another user |
| `DOCUMENT_ACCESS_REQUEST` | Access to document was requested |
| `UNAUTHORIZED_ACCESS` | Unauthorized access attempt |
| `PERMISSION_DENIED` | Permission check failed |
| `INTEGRITY_FAILURE` | Document integrity verification failed |
| `AUDIT_LOG_VIEW` | Audit logs viewed |
| `AUDIT_LOG_SEARCH` | Audit logs searched |
| `FACE_ENROLLMENT` | Face biometrics enrolled |
| `FACE_ENROLLMENT_FAILED` | Face enrollment failed |
| `FACE_LOGIN` | Login via face recognition |
| `FACE_LOGIN_FAILED` | Face recognition login failed |
| `FACE_ENROLLMENT_REMOVED` | Face enrollment removed |

#### SeverityLevel

| Value | Description |
|-------|-------------|
| `INFO` | Normal operation |
| `WARNING` | Non-critical issue |
| `SECURITY_ALERT` | Security-related concern |
| `CRITICAL` | Severe issue requiring immediate attention |

#### ResourceType

| Value | Description |
|-------|-------------|
| `USER` | User account resource |
| `DOCUMENT` | Encrypted document resource |
| `SESSION` | User session resource |
| `SHARING` | Document sharing ACL |
| `SYSTEM` | System-level resource |
| `AUDIT_LOG` | Audit log resource |

#### OperationStatus

| Value | Description |
|-------|-------------|
| `SUCCESS` | Operation completed successfully |
| `FAILURE` | Operation failed |
| `DENIED` | Access denied |
| `ERROR` | Unexpected error occurred |

---

## 2. Crypto Module

**Path:** `crypto/`

### 2.1 BaseCipher (ABC, Generic)

**File:** `crypto/interfaces.py:18`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Abstract generic interface for all cipher implementations. Defines the contract for encrypt/decrypt operations. |
| **Parent Class** | `abc.ABC`, `Generic[_PayloadT]` |
| **Used By** | `AESCipher`, `RSACipher` |
| **Type Parameter** | `_PayloadT` — `EncryptedPayload` for AES, `bytes` for RSA |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `encrypt` | `@abstractmethod (self, data: bytes) -> _PayloadT` | Encrypt plaintext bytes. |
| `decrypt` | `@abstractmethod (self, ciphertext: _PayloadT) -> bytes` | Decrypt ciphertext back to plaintext. |

---

### 2.2 BaseHasher (ABC)

**File:** `crypto/interfaces.py:51`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Abstract interface for hashing implementations. |
| **Parent Class** | `abc.ABC` |
| **Used By** | `SHA256Hasher` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `hash` | `@abstractmethod (self, data: bytes) -> str` | Return a hex-encoded digest of `data`. |
| `verify` | `@abstractmethod (self, data: bytes, digest: str) -> bool` | Check whether `data` hashes to the given `digest`. |

---

### 2.3 AESCipher

**File:** `crypto/aes_cipher.py:23`

| Aspect | Detail |
|--------|--------|
| **Purpose** | AES-256-CBC symmetric encryption with PKCS7 padding. Provides both `EncryptedPayload` and raw bytes interfaces. |
| **Parent Class** | `BaseCipher[EncryptedPayload]` |
| **Used By** | `DocumentUploadService`, `DocumentDownloadService` |
| **Key Size** | 32 bytes (256 bits) |
| **Block Size** | 16 bytes (128 bits) |
| **Algorithm** | `"AES-256-CBC"` |

#### Constructor

```python
AESCipher(key: bytes)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `bytes` | 32-byte AES-256 key |

**Raises:** `AESError` if key is not exactly 32 bytes.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `encrypt` | `(self, data: bytes) -> EncryptedPayload` | Encrypt data with a fresh random IV. Returns `EncryptedPayload(ciphertext, iv, algorithm)`. |
| `decrypt` | `(self, payload: EncryptedPayload) -> bytes` | Decrypt an `EncryptedPayload` to plaintext. |
| `encrypt_bytes` | `(self, data: bytes, iv: bytes | None = None) -> tuple[bytes, bytes]` | Encrypt with a caller-supplied or fresh IV. Returns `(ciphertext, iv)`. |
| `decrypt_bytes` | `(self, ciphertext: bytes, iv: bytes) -> bytes` | Decrypt raw ciphertext with a given IV. |

#### Usage Example

```python
from crypto.aes_cipher import AESCipher
from crypto.key_generator import generate_aes_key

key = generate_aes_key()
cipher = AESCipher(key)
payload = cipher.encrypt(b"Hello, World!")
plaintext = cipher.decrypt(payload)
assert plaintext == b"Hello, World!"
```

---

### 2.4 RSACipher

**File:** `crypto/rsa_cipher.py:23`

| Aspect | Detail |
|--------|--------|
| **Purpose** | RSA-2048 asymmetric encryption using OAEP with SHA-256. Used for wrapping AES keys in the hybrid encryption scheme. |
| **Parent Class** | `BaseCipher[bytes]` |
| **Used By** | `RegistrationService` (key generation), `DocumentUploadService`, `DocumentDownloadService`, `DocumentSharingService` |
| **Key Size** | 2048 bits |
| **Algorithm** | `"RSA-2048-OAEP-SHA-256"` |
| **Max Encrypt Size** | ~190 bytes |

#### Constructor

```python
RSACipher(key_pair: RSA.RsaKey | None = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key_pair` | `RSA.RsaKey | None` | Optional existing key pair. If `None`, call `generate_keypair()` before use. |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate_keypair` | `(self) -> None` | Generate a new 2048-bit RSA key pair. |
| `export_private_key` | `(self, password: str | None = None) -> bytes` | Export private key as PEM bytes. Optional password encryption with AES-256-CBC. |
| `export_public_key` | `(self) -> bytes` | Export public key as PEM bytes. |
| `load_private_key` | `(self, pem_data: bytes, password: str | None = None) -> None` | Load a private key from PEM bytes. |
| `load_public_key` | `(self, pem_data: bytes) -> None` | Load a public key from PEM bytes. |
| `load_private_key_from_file` | `(self, file_path: str | Path, password: str | None = None) -> None` | Load a private key from a PEM file on disk. |
| `load_public_key_from_file` | `(self, file_path: str | Path) -> None` | Load a public key from a PEM file on disk. |
| `encrypt` | `(self, data: bytes) -> bytes` | Encrypt data using the public key. Max ~190 bytes. |
| `decrypt` | `(self, ciphertext: bytes) -> bytes` | Decrypt ciphertext using the private key. |
| `has_private_key` | `@property -> bool` | Whether the loaded key contains a private component. |
| `has_public_key` | `@property -> bool` | Whether any key is currently loaded. |

#### Usage Example

```python
from crypto.rsa_cipher import RSACipher

cipher = RSACipher()
cipher.generate_keypair()
encrypted = cipher.encrypt(b"secret-aes-key")
decrypted = cipher.decrypt(encrypted)
assert decrypted == b"secret-aes-key"
```

---

### 2.5 SHA256Hasher

**File:** `crypto/hashing.py:18`

| Aspect | Detail |
|--------|--------|
| **Purpose** | SHA-256 hashing for passwords, document integrity checks, and file verification. |
| **Parent Class** | `BaseHasher` |
| **Used By** | `AuthService`, `RegistrationService`, `DocumentUploadService`, `DocumentDownloadService` |

#### Constructor

No parameters. Stateless hasher.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `hash` | `(self, data: bytes) -> str` | Return a 64-character hex-encoded SHA-256 digest. |
| `verify` | `(self, data: bytes, digest: str) -> bool` | Check if `data` hashes to the given `digest`. |
| `hash_string` | `(self, value: str) -> str` | Hash a Unicode string (UTF-8 encoded). |
| `hash_file` | `(self, file_path: str | Path, chunk_size: int = 65536) -> str` | Compute SHA-256 of a file using streaming (64 KB chunks). |
| `hash_stream` | `(self, stream: BinaryIO, chunk_size: int = 65536) -> str` | Compute SHA-256 of a binary stream. |
| `verify_file` | `(self, file_path: str | Path, expected_digest: str) -> bool` | Verify file integrity against an expected hash. |

#### Usage Example

```python
from crypto.hashing import SHA256Hasher

hasher = SHA256Hasher()
digest = hasher.hash_string("password123")
assert hasher.verify(b"password123", digest)
assert hasher.hash_file("/path/to/document.pdf")
```

---

### 2.6 EncryptedPayload

**File:** `crypto/payload.py:18`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Immutable data structure representing the result of an AES encryption operation. |
| **Parent Class** | `@dataclass(frozen=True)` |
| **Used By** | `AESCipher`, `DocumentUploadService` |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `ciphertext` | `bytes` | *(required)* | The encrypted bytes |
| `iv` | `bytes` | *(required)* | 16-byte initialisation vector |
| `algorithm` | `str` | `"AES-256-CBC"` | Algorithm identifier |

---

### 2.7 EncryptedKeyPayload

**File:** `crypto/payload.py:33`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Immutable data structure representing an RSA-encrypted AES key (used in hybrid encryption scenarios). |
| **Parent Class** | `@dataclass(frozen=True)` |
| **Used By** | Hybrid encryption workflows |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `encrypted_key` | `bytes` | *(required)* | RSA-encrypted AES key bytes |
| `iv` | `bytes` | *(required)* | The AES IV stored alongside the wrapped key |
| `wrapped_algorithm` | `str` | `"RSA-2048-OAEP-SHA-256"` | Algorithm used to encrypt the AES key |
| `data_algorithm` | `str` | `"AES-256-CBC"` | Algorithm used for the actual data encryption |

---

## 3. Database Module

**Path:** `database/`

### 3.1 DatabaseManager (Singleton)

**File:** `database/manager.py:29`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Singleton managing the MongoDB connection pool, database access, and index creation. All repository classes obtain collections through this manager. |
| **Parent Class** | None (uses `__new__` singleton pattern) |
| **Used By** | All repository classes, `main.py` |

#### Constructor

No parameters. Singleton — returns the same instance on every call.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `connect` | `(self) -> None` | Establish MongoDB connection with connection pool (max 10, min 1). Pings server to validate. Raises `DatabaseError`. |
| `disconnect` | `(self) -> None` | Close the MongoDB connection pool gracefully. |
| `get_database` | `(self) -> Database` | Return the active `pymongo.database.Database` instance. Raises `DatabaseError` if not connected. |
| `get_collection` | `(self, name: str) -> Collection` | Return a `pymongo.collection.Collection` by name. |
| `is_connected` | `@property -> bool` | Check whether the MongoDB client is currently connected (pings server). |
| `create_indexes` | `(self) -> None` | Create all required indexes for users, documents, and audit_logs collections. Idempotent. |

#### Indexes Created

- **users:** `user_id` (unique), `username` (unique), `role`, `is_active`, `face_enrolled`
- **documents:** `document_id` (unique), `owner_id`, `created_at`, `original_filename` (text), `shared_with.user_id`, `is_deleted`
- **audit_logs:** `audit_id` (unique), `timestamp`, `username`, `action`, `severity`, `resource_type`, `resource_id`, `status`, `user_id`

---

### 3.2 BaseRepository

**File:** `database/repositories/base.py:24`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Abstract generic repository providing reusable MongoDB CRUD operations. Concrete repositories subclass this and supply the collection name and ID field. |
| **Parent Class** | None |
| **Used By** | `UserRepository`, `DocumentRepository`, `AuditRepository` |

#### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `_collection_name` | `str` | MongoDB collection name (set by subclass) |
| `_id_field` | `str` | Document identifier field name (set by subclass) |

#### Constructor

```python
BaseRepository()
```

Raises `NotImplementedError` if `_collection_name` is empty. Obtains a `DatabaseManager` instance.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `_collection` | `@property -> Collection` | Return the PyMongo collection handle. |
| `create` | `(self, document: dict) -> str` | Insert a new document. Returns the `_id_field` value. Raises `DuplicateKeyError`, `ValidationError`. |
| `get_by_id` | `(self, doc_id: str) -> dict | None` | Retrieve a document by its identifier. Returns `None` if not found. |
| `update` | `(self, doc_id: str, updates: dict) -> dict | None` | Update a document using `$set`. Returns the updated document or `None`. |
| `delete` | `(self, doc_id: str) -> bool` | Permanently delete a document. Returns `True` if deleted. |
| `exists` | `(self, filters: dict) -> bool` | Check whether at least one document matches the filters. |
| `count` | `(self, filters: dict | None = None) -> int` | Count documents matching the filters. `None` counts all. |
| `find` | `(self, filters, skip=0, limit=20, sort=None, projection=None) -> list[dict]` | Search with pagination and sorting. Defaults to descending `_id` order. |
| `find_one` | `(self, filters: dict) -> dict | None` | Find a single document matching the filters. |

---

### 3.3 UserRepository

**File:** `database/repositories/user_repository.py:23`

| Aspect | Detail |
|--------|--------|
| **Purpose** | CRUD operations for the `users` collection. Translates between `User` objects and MongoDB documents. |
| **Parent Class** | `BaseRepository` |
| **Collection** | `"users"` |
| **ID Field** | `"user_id"` |
| **Used By** | `AuthService`, `RegistrationService`, `FaceRecognitionService`, `DocumentSharingService` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_user` | `(self, user: User) -> str` | Validate and persist a new `User`. Returns `user_id`. |
| `get_by_username` | `(self, username: str) -> User | None` | Look up a user by username. |
| `get_by_user_id` | `(self, user_id: str) -> User | None` | Look up a user by their unique identifier. |
| `update_user` | `(self, user_id: str, updates: dict) -> User` | Update fields on an existing user. Raises `UserNotFoundError`. |
| `delete_user` | `(self, user_id: str) -> None` | Permanently remove a user. Raises `UserNotFoundError`. |
| `soft_delete_user` | `(self, user_id: str) -> User` | Mark a user as inactive (`is_active=False`). |
| `username_exists` | `(self, username: str) -> bool` | Check whether a username is already taken. |
| `user_id_exists` | `(self, user_id: str) -> bool` | Check whether a user_id already exists. |
| `search_users` | `(self, query="", role=None, is_active=None, skip=0, limit=20) -> list[User]` | Search with optional regex on username, role filter, and active filter. |
| `get_all_users` | `(self, skip=0, limit=50) -> list[User]` | Retrieve all users (paginated). |
| `get_enrolled_users` | `(self) -> list[User]` | Retrieve all users with `face_enrolled=True`. |
| `update_face_encoding` | `(self, user_id: str, encoding: list[float]) -> User` | Store a facial encoding and mark as enrolled. |
| `remove_face_encoding` | `(self, user_id: str) -> User` | Clear the facial encoding and mark as not enrolled. |

---

### 3.4 DocumentRepository

**File:** `database/repositories/document_repository.py:23`

| Aspect | Detail |
|--------|--------|
| **Purpose** | CRUD operations for the `documents` collection. No encryption logic — only metadata persistence. |
| **Parent Class** | `BaseRepository` |
| **Collection** | `"documents"` |
| **ID Field** | `"document_id"` |
| **Used By** | `DocumentUploadService`, `DocumentDownloadService`, `DocumentListingService`, `DocumentSharingService` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_document` | `(self, document: Document) -> str` | Validate and persist a new `Document`. Returns `document_id`. |
| `get_by_document_id` | `(self, document_id: str) -> Document | None` | Look up a document by its unique identifier. |
| `get_documents_by_owner` | `(self, owner_id: str, include_deleted=False, skip=0, limit=20) -> list[Document]` | Retrieve documents owned by a user. |
| `get_shared_with_user` | `(self, user_id: str, include_deleted=False, skip=0, limit=20) -> list[Document]` | Retrieve documents shared with a user (via `shared_with.user_id`). |
| `update_document` | `(self, document_id: str, updates: dict) -> Document` | Update fields on an existing document. Raises `DocumentNotFoundError`. |
| `delete_document` | `(self, document_id: str) -> None` | Permanently remove a document. |
| `soft_delete_document` | `(self, document_id: str) -> Document` | Mark a document as deleted (`is_deleted=True`). |
| `document_id_exists` | `(self, document_id: str) -> bool` | Check whether a document identifier already exists. |
| `search_documents` | `(self, query="", owner_id=None, mime_type=None, include_deleted=False, skip=0, limit=20) -> list[Document]` | Search with text index, owner filter, and MIME type filter. |

---

### 3.5 AuditRepository

**File:** `database/repositories/audit_repository.py:16`

| Aspect | Detail |
|--------|--------|
| **Purpose** | CRUD operations for the `audit_logs` collection. Stores and queries audit trail entries. |
| **Parent Class** | `BaseRepository` |
| **Collection** | `"audit_logs"` |
| **ID Field** | `"audit_id"` |
| **Used By** | `AuditService` |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_audit_log` | `(self, audit_log: AuditLog) -> str` | Validate and persist a new `AuditLog`. |
| `get_by_audit_id` | `(self, audit_id: str) -> AuditLog | None` | Look up an audit log by ID. |
| `find_logs` | `(self, username=None, action=None, severity=None, resource_type=None, status=None, date_from=None, date_to=None, user_id=None, resource_id=None, skip=0, limit=50) -> list[AuditLog]` | Search with multiple optional filters and date range. |
| `count_logs` | `(self, username=None, action=None, severity=None, resource_type=None, status=None, date_from=None, date_to=None) -> int` | Count logs matching the given filters. |
| `get_logs_by_user` | `(self, user_id: str, skip=0, limit=50) -> list[AuditLog]` | Get logs for a specific user. |
| `get_logs_by_action` | `(self, action: str, skip=0, limit=50) -> list[AuditLog]` | Get logs for a specific action. |
| `get_logs_by_date_range` | `(self, date_from: datetime, date_to: datetime, skip=0, limit=50) -> list[AuditLog]` | Get logs within a date range. |
| `get_logs_by_severity` | `(self, severity: str, skip=0, limit=50) -> list[AuditLog]` | Get logs of a specific severity. |

---

### 3.6 CounterRepository

**File:** `database/repositories/counter_repository.py:25`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Atomic sequential counter operations. Manages the `counters` collection for generating sequential IDs (e.g., Document IDs). Uses MongoDB's `find_one_and_update` with `$inc` for concurrency safety. |
| **Parent Class** | None (standalone) |
| **Collection** | `"counters"` |
| **Used By** | `DocumentIDGeneratorService` |

#### Constructor

```python
CounterRepository()
```

Obtains a `DatabaseManager` instance.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_next_sequence` | `(self, counter_name: str) -> int` | Atomically increment and return the next sequence value. Creates counter at 1 if it doesn't exist. |
| `get_current_value` | `(self, counter_name: str) -> int` | Return the current value without incrementing. Returns 0 if counter doesn't exist. |
| `reset_counter` | `(self, counter_name: str, value: int = 0) -> None` | Reset a counter to a specific value. Uses `upsert=True`. |

---

## 4. Services Module

**Path:** `services/`

### 4.1 SessionManager (Singleton)

**File:** `services/session_manager.py:56`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Singleton maintaining the currently authenticated user's session. Only one active session exists at a time. |
| **Parent Class** | None (singleton via `__new__`) |
| **Used By** | `AuthService`, `AuditService`, all document services, all controllers, `FaceRecognitionService` |

#### Constructor

No parameters. Singleton.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `create_session` | `(self, user_id, username, role, rsa_public_key, rsa_private_key) -> Session` | Create a new authenticated session. Replaces any existing session. Raises `AuthenticationError` if required fields are missing. |
| `logout` | `(self) -> None` | Destroy the current session, clearing all sensitive data. |
| `is_authenticated` | `@property -> bool` | Whether a valid session currently exists. |
| `get_current_session` | `(self) -> Session` | Return the active session. Raises `AuthenticationError` if none. |
| `get_current_user_id` | `(self) -> str` | Return the currently authenticated user's ID. |
| `require_role` | `(self, *roles: str) -> None` | Check that the current user has one of the given roles. Raises `AuthorizationError`. |

---

### 4.2 Session

**File:** `services/session_manager.py:22`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Immutable record of an authenticated user's session data. |
| **Parent Class** | `@dataclass` |
| **Used By** | `SessionManager`, `AuthService` |

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_id` | `str` | `""` | Unique session identifier |
| `user_id` | `str` | `""` | User's unique identifier |
| `username` | `str` | `""` | Login name |
| `role` | `str` | `""` | RBAC role |
| `rsa_public_key` | `str` | `""` | PEM-encoded RSA public key |
| `rsa_private_key` | `str` | `""` | PEM-encoded RSA private key |
| `login_timestamp` | `datetime` | `datetime.now(UTC)` | When the session was created |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict` | `(self) -> dict[str, Any]` | Return session data as a plain dict (safe for logging; excludes RSA keys). |

---

### 4.3 AuthService

**File:** `services/auth_service.py:29`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Coordinates login and logout workflows. Validates credentials, verifies password hashes, and manages session lifecycle. |
| **Parent Class** | None |
| **Used By** | `AuthController`, `FaceController` |

#### Constructor

```python
AuthService()
```

Initialises `SHA256Hasher`, `UserRepository`, and `SessionManager`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `login` | `(self, username: str, password: str) -> dict[str, Any]` | Authenticate a user and create a session. Returns `{user_id, username, role}`. Raises `ValidationError`, `AuthenticationError`, `DatabaseError`. |
| `logout` | `(self) -> dict[str, Any]` | Terminate the current session. Returns `{success, message}`. |
| `is_authenticated` | `(self) -> bool` | Check whether a session is currently active. |
| `get_current_user` | `(self) -> dict[str, Any] | None` | Return current session info (without RSA keys) or `None`. |
| `_validate_input` | `@staticmethod (username: str, password: str) -> None` | Check that both fields are non-empty. Raises `ValidationError`. |
| `_verify_password` | `@staticmethod (plaintext: str, stored_hash: str) -> bool` | Hash plaintext with SHA-256 and compare to stored hash. |

#### Login Flow

1. Validate both fields are non-empty.
2. Normalize username (spaces → underscores).
3. Retrieve user from database.
4. Verify the account is active.
5. Hash supplied password and compare with stored hash.
6. Create session with user identity and RSA keys.
7. Return success summary (without secrets).

---

### 4.4 RegistrationService

**File:** `services/registration_service.py:31`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Coordinates the full user-registration workflow: validation, password hashing, RSA key generation, and persistence. |
| **Parent Class** | None |
| **Used By** | `AuthController` |

#### Constructor

```python
RegistrationService()
```

Initialises `SHA256Hasher` and `UserRepository`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `(self, username: str, password: str, role: str) -> dict[str, Any]` | Full registration flow. Returns `{user_id, username, role, created_at}`. |
| `_normalize_username` | `@staticmethod (username: str) -> str` | Replace whitespace sequences with underscores. |
| `_validate_username` | `@staticmethod (username: str) -> None` | Check pattern `^[a-zA-Z0-9_]{3,30}$`. Raises `ValidationError`. |
| `_validate_password` | `@staticmethod (password: str) -> None` | Enforce: 8+ chars, uppercase, lowercase, digit, special char. Shows ALL missing rules. |
| `_validate_role` | `@staticmethod (role: str) -> None` | Check role is in `{"admin", "editor", "viewer"}`. |
| `_ensure_username_unique` | `(self, username: str) -> None` | Raise if username is already taken. |
| `_hash_password` | `@staticmethod (password: str) -> str` | Return SHA-256 hex digest of password. |
| `_generate_rsa_keys` | `@staticmethod () -> tuple[str, str]` | Generate RSA-2048 key pair. Returns `(public_pem, private_pem)`. |

---

### 4.5 DocumentUploadService

**File:** `services/document_service.py:43`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Orchestrates the secure hybrid-encryption upload workflow. |
| **Parent Class** | None |
| **Used By** | `DocumentController` |
| **Max File Size** | 50 MB |

#### Constructor

```python
DocumentUploadService()
```

Initialises `SessionManager`, `StorageManager`, `DocumentRepository`, `SHA256Hasher`, `DocumentIDGeneratorService`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `upload` | `(self, file_path: str) -> dict[str, Any]` | Full upload flow. Returns `{document_id, original_filename, file_size, sha256_hash, ...}`. |
| `_validate_file` | `@staticmethod (file_path: str) -> Path` | Validate file exists, is readable, not empty, within size limits. |

#### Upload Flow

1. Verify authenticated session.
2. Validate file (exists, readable, ≤ 50 MB).
3. Read file bytes.
4. Generate SHA-256 hash of plaintext.
5. Generate AES-256 key and IV.
6. AES-256-CBC encrypt the file contents.
7. RSA-wrap the AES key with the user's public key.
8. Save encrypted file to storage.
9. Persist document metadata in MongoDB.
10. Return success summary.

---

### 4.6 DocumentDownloadService

**File:** `services/document_download_service.py:32`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Reverses the upload process: RSA unwrap, AES decrypt, SHA-256 verify, and write to disk. |
| **Parent Class** | None |
| **Used By** | `DocumentController` |

#### Constructor

```python
DocumentDownloadService()
```

Initialises `SessionManager`, `StorageManager`, `DocumentRepository`, `SHA256Hasher`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `download` | `(self, document_id: str, output_dir: str) -> dict[str, Any]` | Full download/decrypt/verify flow. Returns `{document_id, original_filename, output_path, integrity_verified, ...}`. |
| `_resolve_output_path` | `@staticmethod (target: Path) -> Path` | If target exists, append numeric suffix (`_1`, `_2`, ...). |

#### Download Flow

1. Verify authenticated session.
2. Retrieve document metadata from MongoDB.
3. Confirm user is owner or has sharing access.
4. Load encrypted file from storage.
5. RSA-decrypt the AES key using the session's private key.
6. AES-256-CBC decrypt the ciphertext.
7. SHA-256 integrity verification against the stored hash.
8. Write decrypted file to output directory.

---

### 4.7 DocumentListingService

**File:** `services/document_listing_service.py:100`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Retrieves document metadata for display. Provides paginated listings, detail view, and search. No decryption or file I/O. |
| **Parent Class** | None |
| **Used By** | `DocumentController` |
| **Max Per Page** | 100 |
| **Default Per Page** | 20 |

#### Constructor

```python
DocumentListingService()
```

Initialises `SessionManager` and `DocumentRepository`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `list_my_documents` | `(self, page=1, per_page=20) -> dict[str, Any]` | Paginated list of documents owned by the current user. |
| `list_shared_with_me` | `(self, page=1, per_page=20) -> dict[str, Any]` | Paginated list of documents shared with the current user. |
| `get_document_detail` | `(self, document_id: str) -> dict[str, Any]` | Return safe metadata for a single document. Checks owner or shared access. |
| `search_my_documents` | `(self, query="", mime_type=None, page=1, per_page=20) -> dict[str, Any]` | Search and filter documents owned by the current user. |
| `_validate_pagination` | `@staticmethod (page: int, per_page: int) -> tuple[int, int]` | Validate and clamp pagination parameters to safe ranges. |

#### Module-Level Helper Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `_format_file_size` | `(size_bytes: int) -> str` | Return human-readable string (e.g., `"12.3 KB"`). |
| `_get_file_extension` | `(filename: str) -> str` | Return lowercase extension with dot (e.g., `".pdf"`). |
| `_safe_document_info` | `(doc: dict) -> dict` | Extract only safe metadata fields, excluding crypto fields. |
| `_build_pagination_meta` | `(total: int, page: int, per_page: int) -> dict` | Build pagination metadata dict. |

---

### 4.8 DocumentSharingService

**File:** `services/document_sharing_service.py:28`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Securely shares encrypted documents via key re-encryption. The AES key is unwrapped with the owner's private key, then re-wrapped with the recipient's public key. |
| **Parent Class** | None |
| **Used By** | `DocumentController` |

#### Constructor

```python
DocumentSharingService()
```

Initialises `SessionManager`, `DocumentRepository`, `UserRepository`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `share_document` | `(self, document_id: str, recipient_username: str) -> dict[str, Any]` | Full sharing flow. Returns `{document_id, recipient_user_id, recipient_username, permission}`. |

#### Sharing Flow

1. Verify authenticated session.
2. Retrieve document; confirm caller is owner.
3. Look up recipient by username.
4. Validate recipient is not the owner and doesn't already have access.
5. RSA-decrypt the AES key with owner's private key.
6. RSA-encrypt the AES key with recipient's public key.
7. Append `SharedUser` entry to the document's ACL.
8. Persist updated ACL to MongoDB.

---

### 4.9 DocumentIDGeneratorService

**File:** `services/document_id_service.py:24`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generates human-readable sequential document IDs in the format `DOC-XXXX`. |
| **Parent Class** | None |
| **Used By** | `DocumentUploadService` |
| **Prefix** | `"DOC"` |
| **Width** | 4 digits (zero-padded) |

#### Constructor

```python
DocumentIDGeneratorService()
```

Initialises `CounterRepository`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate_document_id` | `(self) -> str` | Generate the next sequential ID (e.g., `"DOC-0001"`, `"DOC-0042"`). |
| `get_current_count` | `(self) -> int` | Return how many IDs have been generated (0 if none). |

---

### 4.10 AuditService

**File:** `services/audit_service.py:19`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Centralised audit event logging and querying. Enriches events with session data when available. |
| **Parent Class** | None |
| **Used By** | All controllers |

#### Constructor

```python
AuditService()
```

Initialises `AuditRepository` and `SessionManager`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `log_event` | `(self, action: str, resource_type: str, resource_id: str = "", resource_name: str = "", status: str = "SUCCESS", message: str = "", severity: str = "INFO", metadata: dict | None = None) -> bool` | Create and persist an audit log entry. Returns `True` on success, `False` on failure (never raises). |
| `query_logs` | `(self, username=None, action=None, severity=None, resource_type=None, status=None, date_from=None, date_to=None, user_id=None, resource_id=None, page=1, per_page=50) -> dict[str, Any]` | Paginated query with multiple optional filters. Returns `{success, logs, total, page, per_page, total_pages, has_next, has_previous}`. |

---

### 4.11 FaceRecognitionService

**File:** `services/face_recognition_service.py:67`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Face recognition using OpenCV's LBPH face recogniser. Provides enrollment, recognition, and management. Uses LBP histograms and Chi-Square distance matching. |
| **Parent Class** | None |
| **Used By** | `FaceController` |
| **Match Threshold** | 55.0 (LBPH confidence — lower = better match) |
| **Enrollment Samples** | 5 |
| **Camera Index** | 0 |
| **Face Image Size** | 200×200 |
| **Feature Vector** | 944-dimensional (16 blocks × 59 bins) |

#### Constructor

```python
FaceRecognitionService()
```

Initialises `UserRepository` and `SessionManager`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_available` | `(self) -> bool` | Whether face recognition is available (Haar cascade loaded). |
| `is_enrolled` | `(self, user_id: str) -> bool` | Whether a specific user has enrolled face biometrics. |
| `enroll_face` | `(self, user_id: str, username: str) -> dict[str, Any]` | Capture 5 face samples, train LBPH model, store average histogram. Returns `{success, message, samples_captured}`. |
| `recognize_user` | `(self) -> dict[str, Any]` | Capture a live frame, extract LBP histogram, compare against enrolled users via Chi-Square distance. Returns `{success, user_id, username, role, distance, message}`. Creates session on match. |
| `remove_enrollment` | `(self, user_id: str) -> dict[str, Any]` | Clear facial encoding data for a user. |
| `_compute_lbp_histogram` | `@staticmethod (face_gray: np.ndarray) -> np.ndarray` | Compute 944-dimensional LBP histogram (16 blocks × 59 bins). |
| `_local_binary_pattern` | `@staticmethod (image: np.ndarray) -> np.ndarray` | Compute basic LBP (radius=1, 8 neighbours) on a grayscale image. |
| `_chi_square_distance` | `@staticmethod (hist_a: np.ndarray, hist_b: np.ndarray) -> float` | Chi-Square distance between two histograms (normalized by bin count). |
| `_detect_face` | `@staticmethod (frame: np.ndarray) -> tuple[np.ndarray, tuple]` | Detect exactly one face in frame using Haar cascade. Returns `(cropped_gray_200x200, (x, y, w, h))`. |
| `_capture_frame` | `@staticmethod (cap, instruction: str, delay_ms: int = 2000) -> np.ndarray` | Capture a single frame with live preview and instruction overlay. |
| `_capture_with_preview` | `@staticmethod (instruction: str, duration_ms: int = 2000) -> np.ndarray` | Open camera, show preview, and return captured frame. |
| `_check_camera` | `@staticmethod () -> None` | Raise if the camera cannot be opened. |

---

## 5. Controllers Module

**Path:** `controllers/`

### 5.1 AuthController

**File:** `controllers/auth_controller.py:28`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Thin presentation-coordination layer for authentication. Delegates to services, handles errors, and logs audit events. |
| **Parent Class** | None |
| **Used By** | `App` (GUI), CLI |

#### Constructor

```python
AuthController()
```

Initialises `RegistrationService`, `AuthService`, `AuditService`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `register` | `(self, username: str, password: str, role: str) -> dict[str, Any]` | Register a new user. Returns `{success, user_id, username, role, message}`. Logs audit event. |
| `login` | `(self, username: str, password: str) -> dict[str, Any]` | Authenticate a user. Returns `{success, user_id, username, role, message}`. Logs audit events for both success and failure. |
| `logout` | `(self) -> dict[str, Any]` | Terminate the current session. Logs audit event. |
| `is_authenticated` | `(self) -> bool` | Check whether a session is active. |
| `get_current_user` | `(self) -> dict[str, Any] | None` | Return current session info (without RSA keys). |

---

### 5.2 DocumentController

**File:** `controllers/document_controller.py:31`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Thin presentation-coordination layer for document operations. Delegates to services, handles errors, and logs audit events. |
| **Parent Class** | None |
| **Used By** | `App` (GUI), CLI |

#### Constructor

```python
DocumentController()
```

Initialises `DocumentUploadService`, `DocumentListingService`, `DocumentDownloadService`, `DocumentSharingService`, `AuditService`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `upload` | `(self, file_path: str) -> dict[str, Any]` | Upload, encrypt, and persist a document. Logs audit event on success. |
| `list_my_documents` | `(self, page=1, per_page=20) -> dict[str, Any]` | List documents owned by the current user. |
| `list_shared_with_me` | `(self, page=1, per_page=20) -> dict[str, Any]` | List documents shared with the current user. |
| `get_document_detail` | `(self, document_id: str) -> dict[str, Any]` | View safe metadata for a single document. |
| `search_my_documents` | `(self, query="", mime_type=None, page=1, per_page=20) -> dict[str, Any]` | Search and filter documents. |
| `download` | `(self, document_id: str, output_dir: str) -> dict[str, Any]` | Download, decrypt, verify, and save a document. Logs audit event. On integrity failure, logs a `CRITICAL` severity event. |
| `share_document` | `(self, document_id: str, recipient_username: str) -> dict[str, Any]` | Share a document with another registered user. Logs audit event. |

---

### 5.3 AuditController

**File:** `controllers/audit_controller.py:14`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Thin presentation-coordination layer for viewing audit logs. Parses date strings and delegates to `AuditService`. |
| **Parent Class** | None |
| **Used By** | `App` (GUI), CLI |

#### Constructor

```python
AuditController()
```

Initialises `AuditService`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `view_audit_logs` | `(self, username=None, action=None, severity=None, resource_type=None, status=None, date_from=None, date_to=None, page=1, per_page=50) -> dict[str, Any]` | Query audit logs with filters. Parses ISO date strings for `date_from` and `date_to`. Logs an `AUDIT_LOG_VIEW` event on success. |

---

### 5.4 FaceController

**File:** `controllers/face_controller.py:18`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Thin presentation-coordination layer for face recognition operations. Logs audit events for enrollment and login. |
| **Parent Class** | None |
| **Used By** | `App` (GUI), CLI |

#### Constructor

```python
FaceController()
```

Initialises `FaceRecognitionService`, `AuthService`, `AuditService`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_available` | `(self) -> bool` | Check whether face recognition is available. |
| `enroll` | `(self, user_id: str, username: str) -> dict[str, Any]` | Enroll face biometrics. Logs `FACE_ENROLLMENT` or `FACE_ENROLLMENT_FAILED`. |
| `login_face` | `(self) -> dict[str, Any]` | Authenticate via face recognition. Logs `FACE_LOGIN` or `FACE_LOGIN_FAILED`. |
| `remove_enrollment` | `(self, user_id: str, username: str) -> dict[str, Any]` | Remove face enrollment. Logs `FACE_ENROLLMENT_REMOVED`. |
| `is_enrolled` | `(self, user_id: str) -> bool` | Check whether a user has enrolled face biometrics. |

---

## 6. Storage Module

**Path:** `storage/`

### 6.1 StorageManager

**File:** `storage/manager.py:21`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Manages on-disk encrypted document storage. All file operations use encrypted filenames (never original) to prevent information leakage. |
| **Parent Class** | None |
| **Used By** | `DocumentUploadService`, `DocumentDownloadService`, `main.py` |
| **Directories** | Encrypted: `storage/encrypted_documents/` ; Temp: `storage/temp/` |

#### Constructor

```python
StorageManager()
```

Reads paths from `settings.STORAGE_ENCRYPTED_PATH` and `settings.STORAGE_TEMP_PATH`.

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `initialise` | `(self) -> None` | Create storage directories if they do not exist. |
| `encrypted_dir` | `@property -> Path` | Resolved path to the encrypted-document directory. |
| `temp_dir` | `@property -> Path` | Resolved path to the temporary-storage directory. |
| `save_encrypted_file` | `(self, encrypted_filename: str, data: bytes) -> Path` | Write encrypted bytes to disk. Returns the full path. Raises `FileHandlingError`. |
| `read_encrypted_file` | `(self, encrypted_filename: str) -> bytes` | Read encrypted bytes from disk. Raises `FileHandlingError` if not found. |
| `delete_encrypted_file` | `(self, encrypted_filename: str) -> None` | Remove an encrypted file from disk. Logs warning if not found (no error). |
| `encrypted_file_exists` | `(self, encrypted_filename: str) -> bool` | Check whether an encrypted file exists on disk. |

---

## 7. Config Module

**Path:** `config/`

### 7.1 Settings (Singleton)

**File:** `config/settings.py:17`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Centralised configuration management. Loads environment variables from `.env` and provides a singleton object consumed by all modules. |
| **Parent Class** | None (singleton via `__new__`) |
| **Used By** | All modules in the system |

#### Configuration Variables

| Attribute | Default | Description |
|-----------|---------|-------------|
| `APP_NAME` | `"Secure Document Management System"` | Application name |
| `APP_VERSION` | `"1.0.0"` | Application version |
| `APP_ENVIRONMENT` | `"development"` | Runtime environment |
| `LOG_LEVEL` | `"DEBUG"` | Logging level |
| `LOG_DIR` | `"logs"` | Log file directory |
| `MONGODB_URI` | `"mongodb://localhost:27017"` | MongoDB connection string |
| `MONGODB_DATABASE` | `"secure_document_db"` | Database name |
| `MONGODB_CONNECT_TIMEOUT_MS` | `5000` | Connection timeout (ms) |
| `MONGODB_SERVER_SELECTION_TIMEOUT_MS` | `5000` | Server selection timeout (ms) |
| `STORAGE_ENCRYPTED_DIR` | `"storage/encrypted_documents"` | Encrypted file storage path |
| `STORAGE_TEMP_DIR` | `"storage/temp"` | Temporary file storage path |
| `STORAGE_MAX_FILE_SIZE_MB` | `50` | Maximum file upload size |

#### Properties

| Property | Returns | Description |
|----------|---------|-------------|
| `STORAGE_ENCRYPTED_PATH` | `Path` | Absolute path for encrypted document storage |
| `STORAGE_TEMP_PATH` | `Path` | Absolute path for temporary storage |
| `LOG_PATH` | `Path` | Absolute path for log files |

---

## 8. Exceptions Module

**Path:** `exceptions/`, `crypto/`, `database/`

### 8.1 Application Exception Hierarchy

```
SDMSException
├── AuthenticationError        — login, token validation failures
├── AuthorizationError         — permission check failures
├── CryptographicError         — encryption/decryption failures
│   ├── AESError               — AES encrypt/decrypt failures
│   ├── RSAError               — RSA key/encrypt/decrypt failures
│   ├── HashingError           — hash computation failures
│   ├── KeyGenerationError     — secure random generation failures
│   ├── Base64Error            — Base64 encode/decode failures
│   ├── PaddingError           — PKCS7 padding failures
│   ├── KeySerializationError  — PEM import/export failures
│   └── IntegrityCheckError    — hash verification failures
├── DatabaseError              — database operation failures
│   ├── DuplicateKeyError      — unique index violations
│   ├── DocumentNotFoundError  — document not found
│   ├── UserNotFoundError      — user not found
│   ├── CollectionNotInitialisedError — collection not ready
│   └── IndexCreationError     — index creation failures
├── FileHandlingError          — file I/O failures
├── ValidationError            — input validation failures
├── DocumentIDGenerationError  — sequential ID generation failures
└── CounterNotFoundError       — counter not found in database
```

---

## 9. GUI Classes

**Path:** `gui/`

### 9.1 App (alias `SDMSApp`)

**File:** `gui/app.py:30`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Main application window. Manages navigation, page routing, authentication state, theme switching, sidebar toggle, and user session. |
| **Parent Class** | `ctk.CTk` |
| **Used By** | `main.py` |

#### Constructor

```python
App(controller: dict = None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `controller` | `dict` | Dictionary of controllers: `{"auth": AuthController, "document": DocumentController, "audit": AuditController, "face": FaceController}` |

#### Key Methods

| Method | Description |
|--------|-------------|
| `_show_login()` | Clear pages, build unauth sidebar, show login page. |
| `_show_register()` | Clear pages, show register page. |
| `_handle_login(username, password)` | Delegate to `auth` controller, update user state, navigate to dashboard. |
| `_handle_face_login()` | Delegate to `face` controller for face recognition login. |
| `_handle_register(...)` | Delegate to `auth` controller for registration. |
| `_on_auth_success()` | Build auth sidebar, update topbar, navigate to dashboard. |
| `_logout()` | Call `auth.logout()`, clear state, show login. |
| `_navigate(page_name)` | Route to the specified page (cached or created on demand). |
| `_create_page(name)` | Factory method creating the appropriate page widget. |
| `_toggle_sidebar()` | Animate sidebar between expanded (220px) and collapsed (60px) width. |
| `_change_theme(mode)` | Switch theme, recursively apply to all widgets. |
| `_clear_pages(destroy=False)` | Hide or destroy all page widgets. |
| `_on_close()` | Logout and destroy the window. |

#### Supported Pages

`login`, `register`, `dashboard`, `documents`, `document_detail`, `upload`, `download`, `share`, `shared`, `search`, `face`, `audit`, `settings`, `profile`

---

### 9.2 ThemeManager (Singleton)

**File:** `gui/theme.py:225`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Singleton managing the active theme mode (dark/light). Notifies observer callbacks on change. |
| **Parent Class** | None (singleton via `__new__`) |

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `mode` | `@property -> str` | Current mode: `"dark"` or `"light"`. |
| `C` | `@property -> _ThemeColors` | Shorthand for the current colour palette proxy. |
| `toggle` | `(self) -> str` | Toggle between dark and light modes. Returns new mode. |
| `set_mode` | `(self, mode: str) -> None` | Set mode directly. Notifies observers. |
| `on_change` | `(self, callback) -> None` | Register a theme change observer. |
| `get_color` | `(self, name: str) -> str` | Look up a colour name from the active palette. |

---

### 9.3 _ThemeColors (Singleton)

**File:** `gui/theme.py:13`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Dynamic colour proxy that resolves colour values at access time from the current theme mode. Prevents stale references after theme switches. |
| **Parent Class** | None (singleton via `__new__`) |

#### Usage

```python
C = ThemeManager().C
C.bg_main       # resolves to current mode's bg_main
C.text_primary  # resolves to current mode's text_primary
```

#### Available Colour Names

`bg_root`, `bg_main`, `bg_sidebar`, `bg_sidebar_hover`, `bg_card`, `bg_card_hover`, `bg_input`, `bg_input_focus`, `bg_topbar`, `bg_modal`, `bg_tooltip`, `bg_code`, `bg_selected`, `bg_card_translucent`, `accent_blue`, `accent_purple`, `primary`, `primary_hover`, `primary_light`, `primary_dark`, `primary_subtle`, `success`, `success_hover`, `success_subtle`, `warning`, `warning_hover`, `warning_subtle`, `danger`, `danger_hover`, `danger_subtle`, `info`, `info_hover`, `text_primary`, `text_secondary`, `text_dim`, `text_on_primary`, `text_link`, `border`, `border_light`, `border_focus`, `divider`, `scrollbar`, `scrollbar_hover`, `sidebar_active`, `sidebar_active_text`, `sidebar_text`, `shadow`, `overlay`, `chart_1` – `chart_6`, `glass_bg`, `glass_border`

---

### 9.4 Sidebar

**File:** `gui/components/sidebar.py:104`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Animated expandable sidebar with branding, navigation items, hover effects, and active state glow. Supports authenticated and unauthenticated menus. |
| **Parent Class** | `ctk.CTkFrame` |

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `master` | widget | Parent widget |
| `width` | `int` | Initial width (default: `Dim.SIDEBAR_W` = 220) |
| `on_navigate` | `Callable` | Navigation callback |
| `on_toggle` | `Callable` | Toggle callback |
| `on_logout` | `Callable` | Logout callback |
| `on_login` | `Callable` | Login page callback |
| `on_register` | `Callable` | Register page callback |

#### Key Methods

| Method | Description |
|--------|-------------|
| `add_item(icon, label, command)` | Add a navigation item. |
| `add_separator()` | Add a visual separator line. |
| `add_label(text)` | Add a section label. |
| `clear()` | Remove all items and bottom widgets. |
| `set_active(idx)` | Highlight the item at index `idx`. |
| `animate_width(target)` | Animate sidebar width to target pixels. |
| `build_auth_menu(user)` | Build the authenticated navigation menu (Dashboard, Upload, Documents, Search, Shared, Audit, Face, Settings, Profile, Logout). |
| `build_unauth_menu()` | Build the unauthenticated menu (Login, Register). |

---

### 9.5 SidebarItem

**File:** `gui/components/sidebar.py:13`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Single clickable sidebar navigation item with icon, label, hover effects, and active/danger states. |
| **Parent Class** | `ctk.CTkFrame` |

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `master` | widget | Parent widget |
| `icon_text` | `str` | Unicode icon character |
| `label` | `str` | Display label |
| `command` | `Callable | None` | Click callback |
| `height` | `int` | Item height (default: 40) |

#### Key Methods

| Method | Description |
|--------|-------------|
| `set_active(active)` | Toggle active state (changes colours to `sidebar_active`). |
| `set_expanded(expanded)` | Show/hide the text label. |
| `set_danger_style()` | Apply danger colour scheme (red text). |

---

### 9.6 TopBar

**File:** `gui/components/topbar.py:12`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Horizontal top bar with breadcrumb, search, theme toggle, user avatar/info, and logout button. |
| **Parent Class** | `ctk.CTkFrame` |

#### Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `master` | widget | Parent widget |
| `height` | `int` | Bar height (default: `Dim.TOPBAR_H` = 48) |

#### Key Methods

| Method | Description |
|--------|-------------|
| `set_breadcrumb(text)` | Update the breadcrumb text. |
| `set_user(username, role)` | Update the user display. |
| `set_theme_change_callback(cb)` | Register theme change callback. |
| `set_logout_callback(cb)` | Register logout callback. |
| `set_logged_in(logged_in)` | Show/hide the logout button. |
| `apply_theme()` | Re-apply colours after theme switch. |

---

### 9.7 Page Classes (Brief)

All pages inherit from `ctk.CTkFrame` and live in `gui/pages/`.

| Class | File | Purpose |
|-------|------|---------|
| `LoginPage` | `login_page.py` | Username/password login form with face login option |
| `RegisterPage` | `register_page.py` | New user registration form |
| `DashboardPage` | `dashboard_page.py` | Overview with stat cards, charts, quick actions |
| `DocumentsPage` | `documents_page.py` | Table listing of owned documents with actions |
| `DocumentDetailPage` | `document_detail_page.py` | Single document metadata detail view |
| `UploadPage` | `upload_page.py` | File picker and upload form |
| `DownloadPage` | `download_page.py` | Document selection and download form |
| `SharePage` | `share_page.py` | Document selection and recipient username entry for sharing |
| `SharedPage` | `shared_page.py` | Table listing of documents shared with the user |
| `SearchPage` | `search_page.py` | Search form with results table |
| `FacePage` | `face_page.py` | Face enrollment and verification interface |
| `AuditPage` | `audit_page.py` | Audit log table with filters (admin only) |
| `SettingsPage` | `settings_page.py` | Theme toggle and application settings |
| `ProfilePage` | `profile_page.py` | User profile display |

---

### 9.8 Component Classes (Brief)

All components inherit from `ctk.CTkFrame` (or `ctk.CTkButton`/`ctk.CTkToplevel`) and live in `gui/components/`.

#### Cards (`gui/components/cards.py`)

| Class | Purpose |
|-------|---------|
| `StatCard` | Dashboard stat card with icon, large value, subtitle, and accent colour |
| `InfoCard` | Card with title header and key-value row content |
| `ActionCard` | Clickable card for dashboard quick actions with hover effects |
| `PageHeader` | Page title bar with optional subtitle and action buttons |

#### Charts (`gui/components/charts.py`)

| Class | Purpose |
|-------|---------|
| `DonutChart` | Canvas-drawn donut/pie chart with legend |
| `BarChart` | Horizontal bar chart with labels |
| `MiniSparkline` | Tiny sparkline for stat cards |

#### Forms (`gui/components/forms.py`)

| Class | Purpose |
|-------|---------|
| `StyledEntry` | Themed text input with label, placeholder, `get_value()`/`set_value()`/`clear()`/`focus()` |
| `PasswordEntry` | Password input with show/hide toggle button |
| `StyledComboBox` | Themed dropdown combo box with `get_value()`/`set_value()` |
| `StyledButton` | Themed button with variant support: `"primary"`, `"success"`, `"danger"`, `"warning"`, `"outline"` |
| `StyledText` | Multi-line text area with `get_value()`/`set_value()`/`clear()` |

#### Tables (`gui/components/tables.py`)

| Class | Purpose |
|-------|---------|
| `StyledTable` | Styled Treeview table with sortable columns, selection, and scrollbar. Methods: `clear()`, `insert_rows()`, `get_selected()`, `bind_select()`, `get_row_count()` |

#### Loading & Status (`gui/components/loading.py`)

| Class | Purpose |
|-------|---------|
| `LoadingSpinner` | Animated spinner with message. Methods: `start()`, `stop()` |
| `StatusBadge` | Coloured pill badge with text. Methods: `set_text()`, `set_color()` |
| `ToolTip` | Hover tooltip for any widget. Created per-widget instance. |
| `AnimatedProgressBar` | Horizontal progress bar with smooth animation. Method: `set_progress(value, animate=True)` |

#### Dialogs (`gui/components/dialogs.py`)

| Class | Parent | Purpose |
|-------|--------|---------|
| `BaseDialog` | `ctk.CTkToplevel` | Modal dialog with icon, title, message, and OK button. Centre-screen positioned. |
| `SuccessDialog` | `BaseDialog` | Green success modal. |
| `ErrorDialog` | `BaseDialog` | Red error modal. |
| `WarningDialog` | `BaseDialog` | Yellow/amber warning modal. |
| `ConfirmDialog` | `ctk.CTkToplevel` | Confirmation dialog with Cancel and Confirm buttons. Callbacks: `on_yes`, `on_no`. |
| `Toast` | `ctk.CTkToplevel` | Non-blocking toast notification with slide-in/out animation. Auto-dismisses after `duration` ms. Types: `"success"`, `"error"`, `"warning"`, `"info"`. |

---

### 9.9 Utility Classes

#### Fonts (`gui/theme.py:181`)

Named font tuples used across all widgets. All use `"Segoe UI"` except `MONO`/`MONO_SM` which use `"Consolas"`.

| Attribute | Tuple |
|-----------|-------|
| `TITLE_XL` | `("Segoe UI", 28, "bold")` |
| `TITLE_LG` | `("Segoe UI", 22, "bold")` |
| `TITLE` | `("Segoe UI", 20, "bold")` |
| `BODY` | `("Segoe UI", 12)` |
| `SMALL` | `("Segoe UI", 11)` |
| `TINY` | `("Segoe UI", 10)` |
| `ICON` | `("Segoe UI", 16)` |
| `MONO` | `("Consolas", 11)` |

#### Dim (`gui/theme.py:203`)

Layout dimension constants.

| Constant | Value |
|----------|-------|
| `SIDEBAR_W` | 220 |
| `SIDEBAR_COLLAPSED_W` | 60 |
| `TOPBAR_H` | 48 |
| `RADIUS_SM` | 6 |
| `RADIUS` | 8 |
| `RADIUS_LG` | 12 |
| `RADIUS_XL` | 16 |
| `MIN_W` | 1080 |
| `MIN_H` | 640 |
| `ANIM_FAST` | 80 |
| `ANIM_NORMAL` | 150 |
| `ANIM_SLOW` | 300 |

---

*End of Class Documentation*
