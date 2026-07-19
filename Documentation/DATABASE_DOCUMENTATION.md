# SDMS Database Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Connection Configuration](#2-connection-configuration)
3. [Collections](#3-collections)
4. [Indexes](#4-indexes)
5. [Entity Relationship Diagram](#5-entity-relationship-diagram)
6. [Document Schemas with Examples](#6-document-schemas-with-examples)
7. [Design Patterns](#7-design-patterns)
8. [Connection Management](#8-connection-management)
9. [Query Patterns](#9-query-patterns)

---

## 1. Overview

The Secure Document Management System (SDMS) uses **MongoDB 7.0+** as its primary data store, accessed through the **PyMongo 4.10+** Python driver.

| Property       | Value                    |
|----------------|--------------------------|
| Database Engine| MongoDB 7.0+             |
| Python Driver  | PyMongo 4.10+            |
| Database Name  | `secure_document_db`     |
| Data Model     | Document-oriented (BSON) |
| Consistency    | Strong (single node)     |

MongoDB was chosen for its flexible schema, native JSON/BSON support, and ease of integration with Python. The document-oriented model allows embedded arrays (e.g., `shared_with` in documents) without joins.

---

## 2. Connection Configuration

### Connection URI

```
mongodb://localhost:27017
```

### Connection Parameters

| Parameter          | Value   | Description                                  |
|--------------------|---------|----------------------------------------------|
| Host               | localhost | MongoDB server hostname                   |
| Port               | 27017   | Default MongoDB port                         |
| Connect Timeout    | 5000 ms | Maximum time to establish connection         |
| Min Pool Size      | 1       | Minimum connections in the connection pool   |
| Max Pool Size      | 10      | Maximum connections in the connection pool   |
| Server Selection   | 5000 ms | Timeout for server availability check        |

### Connection String (PyMongo)

```python
client = pymongo.MongoClient(
    "mongodb://localhost:27017",
    serverSelectionTimeoutMS=5000,
    minPoolSize=1,
    maxPoolSize=10
)
```

---

## 3. Collections

### 3.1 `users`

Stores user accounts, credentials, RSA keys, and face recognition data.

| Field            | Type       | Constraints       | Description                                  |
|------------------|------------|-------------------|----------------------------------------------|
| `user_id`        | string     | unique, indexed   | Auto-generated unique user identifier        |
| `username`       | string     | unique, indexed   | User-chosen login name                       |
| `password_hash`  | string     | required          | SHA-256 hash of the user's password          |
| `role`           | string     | indexed           | One of: `admin`, `editor`, `viewer`          |
| `rsa_public_key` | string     | required          | PEM-encoded RSA-2048 public key              |
| `rsa_private_key`| string     | required          | PEM-encoded RSA-2048 private key             |
| `face_encoding`  | list       | optional          | Averaged LBP histogram (944 floats)          |
| `face_enrolled`  | boolean    | indexed           | `true` if face enrollment is complete        |
| `is_active`      | boolean    | indexed           | `false` if account is deactivated            |
| `created_at`     | datetime   | required          | Account creation timestamp                   |
| `updated_at`     | datetime   | required          | Last modification timestamp                  |

### 3.2 `documents`

Stores metadata and encryption information for uploaded files. The actual encrypted file is stored on disk; this collection holds the metadata.

| Field               | Type       | Constraints     | Description                                  |
|---------------------|------------|-----------------|----------------------------------------------|
| `document_id`       | string     | unique, indexed | Auto-generated unique document identifier    |
| `original_filename` | string     | indexed, TEXT   | Original filename before encryption          |
| `encrypted_filename`| string     | required        | Filename on disk (UUID-based)                |
| `owner_id`          | string     | indexed         | `user_id` of the uploading user              |
| `encrypted_aes_key` | string     | required        | RSA-encrypted AES-256 key (owner's)          |
| `iv`                | string     | required        | Initialization vector for AES-CBC            |
| `sha256_hash`       | string     | required        | SHA-256 hash of original file for integrity  |
| `file_size`         | integer    | required        | File size in bytes                           |
| `mime_type`         | string     | required        | MIME type of the original file               |
| `algorithm`         | string     | required        | Encryption algorithm identifier              |
| `is_deleted`        | boolean    | indexed         | Soft-delete flag                             |
| `shared_with`       | array      | indexed         | Embedded array of sharing records            |
| `created_at`        | datetime   | indexed         | Upload timestamp                             |
| `updated_at`        | datetime   | required        | Last modification timestamp                  |

**`shared_with` Embedded Document:**

| Sub-field          | Type     | Description                            |
|--------------------|----------|----------------------------------------|
| `user_id`          | string   | Recipient user identifier              |
| `permission`       | string   | `read` or `write`                      |
| `encrypted_aes_key`| string   | AES key re-encrypted with recipient's RSA public key |
| `shared_at`        | datetime | Timestamp of the share action          |

### 3.3 `audit_logs`

Immutable log of all system actions for accountability and forensics.

| Field            | Type       | Constraints     | Description                                  |
|------------------|------------|-----------------|----------------------------------------------|
| `audit_id`       | string     | unique, indexed | Auto-generated unique audit identifier       |
| `timestamp`      | datetime   | indexed         | When the action occurred                     |
| `user_id`        | string     | indexed         | Identifier of the acting user               |
| `username`       | string     | indexed         | Username of the acting user (denormalized)  |
| `role`           | string     | required        | Role of the acting user at time of action    |
| `action`         | string     | indexed         | Action performed (e.g., `LOGIN`, `UPLOAD`)  |
| `resource_type`  | string     | indexed         | Type of resource (e.g., `document`, `user`) |
| `resource_id`    | string     | indexed         | Identifier of the affected resource         |
| `resource_name`  | string     | required        | Human-readable resource name                |
| `status`         | string     | indexed         | `success` or `failure`                       |
| `message`        | string     | required        | Descriptive message                          |
| `severity`       | string     | indexed         | `INFO`, `WARNING`, or `ERROR`                |
| `session_id`     | string     | optional        | Associated session identifier               |
| `client_ip`      | string     | optional        | Client IP address (if available)             |
| `device_info`    | string     | optional        | Device/OS information                       |
| `metadata`       | object     | optional        | Arbitrary additional key-value data         |
| `created_at`     | datetime   | required        | Record creation timestamp                   |

### 3.4 `counters`

Atomic counter collection for generating sequential unique IDs.

| Field | Type    | Constraints | Description                       |
|-------|---------|-------------|-----------------------------------|
| `_id` | string  | primary key | Counter name (e.g., `user_id`)    |
| `seq` | integer | required    | Current sequence value            |

---

## 4. Indexes

### 4.1 `users` Collection

| Index Name          | Field           | Type    | Description                        |
|---------------------|-----------------|---------|------------------------------------|
| `idx_user_id`       | `user_id`       | Unique  | Fast lookup by user ID             |
| `idx_username`      | `username`      | Unique  | Fast lookup by username, login     |
| `idx_user_role`     | `role`          | Standard| Filter users by role               |
| `idx_user_is_active`| `is_active`     | Standard| Filter active/inactive users       |
| `idx_user_face_enrolled` | `face_enrolled` | Standard | Filter enrolled users          |

### 4.2 `documents` Collection

| Index Name              | Field               | Type    | Description                        |
|-------------------------|---------------------|---------|------------------------------------|
| `idx_document_id`       | `document_id`       | Unique  | Fast lookup by document ID         |
| `idx_doc_owner`         | `owner_id`          | Standard| Filter documents by owner          |
| `idx_doc_created_at`    | `created_at`        | Standard| Sort/filter by upload date         |
| `idx_doc_filename_text` | `original_filename` | TEXT    | Full-text search on filenames      |
| `idx_doc_shared_with`   | `shared_with`       | Standard| Query shared documents by user     |
| `idx_doc_is_deleted`    | `is_deleted`        | Standard| Exclude soft-deleted documents     |

### 4.3 `audit_logs` Collection

| Index Name               | Field            | Type    | Description                         |
|--------------------------|------------------|---------|-------------------------------------|
| `idx_audit_id`           | `audit_id`       | Unique  | Fast lookup by audit entry ID       |
| `idx_audit_timestamp`    | `timestamp`      | Standard| Time-range queries                  |
| `idx_audit_username`     | `username`       | Standard| Filter by username                  |
| `idx_audit_action`       | `action`         | Standard| Filter by action type               |
| `idx_audit_severity`     | `severity`       | Standard| Filter by severity level            |
| `idx_audit_resource_type`| `resource_type`  | Standard| Filter by resource type             |
| `idx_audit_resource_id`  | `resource_id`    | Standard| Look up audit entries for resource  |
| `idx_audit_status`       | `status`         | Standard| Filter success/failure              |
| `idx_audit_user_id`      | `user_id`        | Standard| All actions by a specific user      |

---

## 5. Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    USERS ||--o{ AUDIT_LOGS : performs
    USERS ||--o{ USERS : shares_with
    DOCUMENTS ||--o{ AUDIT_LOGS : referenced_in

    USERS {
        string user_id PK "Auto-generated"
        string username UK "Unique login name"
        string password_hash "SHA-256 hash"
        string role "admin | editor | viewer"
        string rsa_public_key "PEM format"
        string rsa_private_key "PEM format"
        array face_encoding "LBP histogram (944 floats)"
        boolean face_enrolled
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    DOCUMENTS {
        string document_id PK "Auto-generated"
        string original_filename "Original name"
        string encrypted_filename "UUID on disk"
        string owner_id FK "Refers to users.user_id"
        string encrypted_aes_key "RSA-encrypted AES key"
        string iv "AES-CBC initialization vector"
        string sha256_hash "File integrity hash"
        integer file_size "Bytes"
        string mime_type "MIME type"
        string algorithm "Encryption algorithm"
        boolean is_deleted "Soft-delete flag"
        array shared_with "Embedded sharing records"
        datetime created_at
        datetime updated_at
    }

    DOCUMENTS {
        array shared_with_entry "Embedded"
        string shared_with_entry.user_id FK
        string shared_with_entry.permission "read | write"
        string shared_with_entry.encrypted_aes_key
        datetime shared_with_entry.shared_at
    }

    AUDIT_LOGS {
        string audit_id PK "Auto-generated"
        datetime timestamp
        string user_id FK
        string username "Denormalized"
        string role "Role at time of action"
        string action "LOGIN | UPLOAD | ..."
        string resource_type "document | user | ..."
        string resource_id FK
        string resource_name "Human-readable"
        string status "success | failure"
        string message "Description"
        string severity "INFO | WARNING | ERROR"
        string session_id "Optional"
        string client_ip "Optional"
        string device_info "Optional"
        object metadata "Additional data"
        datetime created_at
    }

    COUNTERS {
        string _id PK "Counter name"
        integer seq "Current value"
    }
```

---

## 6. Document Schemas with Examples

### 6.1 `users` Example Document

```json
{
  "user_id": "USR-000001",
  "username": "john_doe",
  "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "role": "editor",
  "rsa_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
  "rsa_private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
  "face_encoding": [12.45, 23.67, 34.89, 45.12, 56.34, 67.56, 78.78, 89.01, ...],
  "face_enrolled": true,
  "is_active": true,
  "created_at": { "$date": "2025-07-15T10:30:00Z" },
  "updated_at": { "$date": "2025-07-15T10:30:00Z" }
}
```

### 6.2 `documents` Example Document

```json
{
  "document_id": "DOC-000001",
  "original_filename": "project_proposal.pdf",
  "encrypted_filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.enc",
  "owner_id": "USR-000001",
  "encrypted_aes_key": "Base64-encoded RSA-encrypted AES key...",
  "iv": "Base64-encoded initialization vector...",
  "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "file_size": 1048576,
  "mime_type": "application/pdf",
  "algorithm": "AES-256-CBC + RSA-2048",
  "is_deleted": false,
  "shared_with": [
    {
      "user_id": "USR-000002",
      "permission": "read",
      "encrypted_aes_key": "Base64-encoded AES key re-encrypted for USR-000002...",
      "shared_at": { "$date": "2025-07-16T14:20:00Z" }
    },
    {
      "user_id": "USR-000003",
      "permission": "write",
      "encrypted_aes_key": "Base64-encoded AES key re-encrypted for USR-000003...",
      "shared_at": { "$date": "2025-07-16T15:45:00Z" }
    }
  ],
  "created_at": { "$date": "2025-07-15T11:00:00Z" },
  "updated_at": { "$date": "2025-07-16T15:45:00Z" }
}
```

### 6.3 `audit_logs` Example Document

```json
{
  "audit_id": "AUD-000001",
  "timestamp": { "$date": "2025-07-15T11:05:23Z" },
  "user_id": "USR-000001",
  "username": "john_doe",
  "role": "editor",
  "action": "UPLOAD",
  "resource_type": "document",
  "resource_id": "DOC-000001",
  "resource_name": "project_proposal.pdf",
  "status": "success",
  "message": "Document uploaded and encrypted successfully",
  "severity": "INFO",
  "session_id": "SESS-abc123",
  "client_ip": "192.168.1.100",
  "device_info": "Windows 11 / Python 3.11",
  "metadata": {
    "file_size": 1048576,
    "mime_type": "application/pdf"
  },
  "created_at": { "$date": "2025-07-15T11:05:23Z" }
}
```

### 6.4 `counters` Example Document

```json
{
  "_id": "user_id",
  "seq": 42
}

{
  "_id": "document_id",
  "seq": 127
}

{
  "_id": "audit_id",
  "seq": 1024
}
```

---

## 7. Design Patterns

### 7.1 Embedded Document Pattern (`shared_with` Array)

The `documents` collection uses the **embedded document pattern** for sharing records. Rather than maintaining a separate `shares` collection with references, each document contains a `shared_with` array with embedded sub-documents:

```json
"shared_with": [
  {
    "user_id": "USR-000002",
    "permission": "read",
    "encrypted_aes_key": "...",
    "shared_at": { "$date": "2025-07-16T14:20:00Z" }
  }
]
```

**Advantages:**
- Single read retrieves document metadata and all sharing information
- No joins or secondary queries required
- Atomic updates to sharing records via positional operator (`$`)

**Considerations:**
- 16 MB document size limit (rarely a concern for sharing metadata)
- Querying "which documents are shared with user X" requires an index on `shared_with.user_id`

**MongoDB Query:**
```python
db.documents.find({"shared_with.user_id": "USR-000002"})
```

---

### 7.2 Atomic Counter Pattern

Unique sequential IDs (`USR-000001`, `DOC-000001`, `AUD-000001`) are generated using the **atomic counter pattern** via the `counters` collection.

**Mechanism:**

```python
def generate_id(collection, prefix):
    result = collection.find_one_and_update(
        {"_id": f"{prefix}_id"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER
    )
    return f"{prefix}-{result['seq']:06d}"
```

**How It Works:**
1. `find_one_and_update` is **atomic** at the MongoDB server level
2. `$inc` increments the `seq` field by 1 in a single operation
3. `upsert=True` creates the counter document if it does not exist
4. The sequence number is zero-padded to 6 digits and prefixed

**Generated IDs:**
| Counter   | Example Output |
|-----------|---------------|
| `user_id` | `USR-000001`  |
| `document_id` | `DOC-000001` |
| `audit_id` | `AUD-000001` |

---

## 8. Connection Management

The application uses a **singleton pattern** for database connection management through the `DatabaseManager` class.

### Architecture

```
Application Code
       |
       v
  DatabaseManager (singleton)
       |
       v
  pymongo.MongoClient
       |
       v
  MongoDB (localhost:27017)
```

### Implementation Pattern

```python
import pymongo

class DatabaseManager:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._client = pymongo.MongoClient(
                "mongodb://localhost:27017",
                serverSelectionTimeoutMS=5000,
                minPoolSize=1,
                maxPoolSize=10
            )
            cls._db = cls._client["secure_document_db"]
        return cls._instance

    def get_database(self):
        return self._db

    def get_collection(self, name):
        return self._db[name]

    def close(self):
        if self._client:
            self._client.close()
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Singleton pattern | Single connection pool shared across all repositories |
| Connection pooling (1-10) | Balances resource usage with concurrent request handling |
| 5s connection timeout | Fails fast if MongoDB is unavailable |
| Lazy initialization | Database connection established on first use |

---

## 9. Query Patterns

### 9.1 User Repository

| Operation | Query | Index Used |
|-----------|-------|------------|
| Find by ID | `db.users.find_one({"user_id": uid})` | `idx_user_id` |
| Find by username | `db.users.find_one({"username": name})` | `idx_username` |
| List active users | `db.users.find({"is_active": True})` | `idx_user_is_active` |
| List enrolled users | `db.users.find({"face_enrolled": True})` | `idx_user_face_enrolled` |
| Filter by role | `db.users.find({"role": "editor"})` | `idx_user_role` |
| Update user | `db.users.update_one({"user_id": uid}, {"$set": {...}})` | `idx_user_id` |
| Deactivate user | `db.users.update_one({"user_id": uid}, {"$set": {"is_active": False}})` | `idx_user_id` |

### 9.2 Document Repository

| Operation | Query | Index Used |
|-----------|-------|------------|
| Find by ID | `db.documents.find_one({"document_id": did})` | `idx_document_id` |
| List owner's docs | `db.documents.find({"owner_id": uid, "is_deleted": False})` | `idx_doc_owner` + `idx_doc_is_deleted` |
| Search by name | `db.documents.find({"$text": {"$search": term}})` | `idx_doc_filename_text` |
| Shared with user | `db.documents.find({"shared_with.user_id": uid})` | `idx_doc_shared_with` |
| Recent documents | `db.documents.find(...).sort("created_at", -1)` | `idx_doc_created_at` |
| Soft delete | `db.documents.update_one({"document_id": did}, {"$set": {"is_deleted": True}})` | `idx_document_id` |
| Add sharing | `db.documents.update_one({"document_id": did}, {"$push": {"shared_with": {...}}})` | `idx_document_id` |
| Remove sharing | `db.documents.update_one({"document_id": did}, {"$pull": {"shared_with": {"user_id": uid}}})` | `idx_document_id` |

### 9.3 Audit Log Repository

| Operation | Query | Index Used |
|-----------|-------|------------|
| Log action | `db.audit_logs.insert_one({...})` | N/A (insert) |
| Get by ID | `db.audit_logs.find_one({"audit_id": aid})` | `idx_audit_id` |
| Time range | `db.audit_logs.find({"timestamp": {"$gte": start, "$lte": end}})` | `idx_audit_timestamp` |
| By user | `db.audit_logs.find({"username": name})` | `idx_audit_username` |
| By action | `db.audit_logs.find({"action": "LOGIN"})` | `idx_audit_action` |
| By severity | `db.audit_logs.find({"severity": "ERROR"})` | `idx_audit_severity` |
| By status | `db.audit_logs.find({"status": "failure"})` | `idx_audit_status` |
| By resource | `db.audit_logs.find({"resource_id": rid})` | `idx_audit_resource_id` |
| Paginated | `db.audit_logs.find(...).skip(offset).limit(page_size).sort("timestamp", -1)` | `idx_audit_timestamp` |

### 9.4 Counter Repository

| Operation | Query | Index Used |
|-----------|-------|------------|
| Increment & get | `db.counters.find_one_and_update({"_id": name}, {"$inc": {"seq": 1}}, upsert=True, return_document=AFTER)` | `_id` (primary) |

---

## Appendix: Database Name Reference

| Alias | Actual Name |
|-------|-------------|
| `secure_document_db` | `secure_document_db` |

All collection names, index names, and field names are exact and should be used as-is when implementing repository classes.
