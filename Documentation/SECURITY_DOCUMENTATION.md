# SDMS Security Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication](#2-authentication)
3. [Authorization](#3-authorization)
4. [Password Security](#4-password-security)
5. [File Encryption](#5-file-encryption)
6. [Key Management](#6-key-management)
7. [Data Integrity](#7-data-integrity)
8. [Face Recognition Security](#8-face-recognition-security)
9. [Session Management](#9-session-management)
10. [Input Validation](#10-input-validation)
11. [Audit Logging](#11-audit-logging)
12. [Security Best Practices Implemented](#12-security-best-practices-implemented)
13. [Security Weaknesses and Improvements](#13-security-weaknesses-and-improvements)

---

## 1. Overview

The Secure Document Management System (SDMS) implements a multi-layered security architecture combining **password-based authentication**, **face recognition**, **role-based access control (RBAC)**, **hybrid encryption (AES + RSA)**, and **comprehensive audit logging**.

### Security Layers

```
┌─────────────────────────────────────────────┐
│              INPUT VALIDATION               │
├─────────────────────────────────────────────┤
│           AUTHENTICATION LAYER              │
│    ┌──────────────┬───────────────────┐     │
│    │  Password    │  Face Recognition  │     │
│    │  (SHA-256)   │  (LBPH + OpenCV)  │     │
│    └──────────────┴───────────────────┘     │
├─────────────────────────────────────────────┤
│          SESSION MANAGEMENT                 │
│     (In-memory singleton, RSA keys)         │
├─────────────────────────────────────────────┤
│        AUTHORIZATION (RBAC)                 │
│     admin → editor → viewer                │
├─────────────────────────────────────────────┤
│         FILE ENCRYPTION                     │
│    AES-256-CBC + RSA-2048 Hybrid           │
├─────────────────────────────────────────────┤
│         INTEGRITY VERIFICATION              │
│          SHA-256 Hashing                    │
├─────────────────────────────────────────────┤
│           AUDIT LOGGING                     │
│     Every action recorded immutably         │
└─────────────────────────────────────────────┘
```

---

## 2. Authentication

SDMS supports **two authentication methods**:

### 2.1 Password-Based Authentication

| Property | Details |
|----------|---------|
| Hash Function | SHA-256 (via Python `hashlib`) |
| Storage | Only the hash is stored; plaintext is never persisted |
| Verification | Hash the provided password and compare to stored hash |
| Enrollment | Password set during user registration |

**Flow:**
```
User enters password
        │
        v
hashlib.sha256(password.encode()).hexdigest()
        │
        v
Compare to stored password_hash
        │
        ├── Match → Authentication success
        └── No match → Authentication failure
```

### 2.2 Face Recognition Authentication

| Property | Details |
|----------|---------|
| Detection Algorithm | Haar Cascade (Haar cascade frontal face classifier) |
| Feature Extraction | Local Binary Pattern (LBP) Histogram |
| Matching Method | Chi-Square distance |
| Match Threshold | 55.0 (distance must be ≤ threshold) |
| Camera | Default system camera (`cv2.VideoCapture(0)`) |

**Flow:**
```
User requests face login
        │
        v
Open camera → Capture frame
        │
        v
Haar cascade detects face region
        │
        v
Convert to grayscale → Resize to 200×200
        │
        v
Compute LBP histogram (944-dim vector)
        │
        v
Compare against all enrolled users (Chi-Square)
        │
        ├── Best distance ≤ 55.0 → Create session
        └── Best distance > 55.0 → Reject
```

---

## 3. Authorization

### Role-Based Access Control (RBAC)

SDMS enforces authorization through three hierarchical roles:

| Role | Permissions |
|------|-------------|
| **admin** | Full access: manage users, upload/download/delete/share documents, view audit logs, manage system |
| **editor** | Upload, download, delete own documents, share own documents, view own audit logs |
| **viewer** | Download documents shared with them, view own profile |

### Permission Matrix

| Action | admin | editor | viewer |
|--------|-------|--------|--------|
| Create user | Yes | No | No |
| Deactivate user | Yes | No | No |
| Change roles | Yes | No | No |
| Upload document | Yes | Yes | No |
| Download own document | Yes | Yes | No |
| Download shared document | Yes | Yes | Yes |
| Delete own document | Yes | Yes | No |
| Delete any document | Yes | No | No |
| Share own document | Yes | Yes | No |
| View all audit logs | Yes | No | No |
| View own audit logs | Yes | Yes | Yes |
| View user list | Yes | No | No |

### Enforcement Mechanism

Roles are enforced via `SessionManager.require_role()` which is called at the start of each protected operation:

```python
# Pseudocode for role enforcement
def require_role(self, allowed_roles):
    session = self.get_current_session()
    if session is None:
        raise AuthenticationError("Not logged in")
    if session.role not in allowed_roles:
        raise AuthorizationError("Insufficient permissions")
    return session
```

**Usage in controllers:**
```python
# Only admins can create users
session = session_manager.require_role(["admin"])

# Admins and editors can upload
session = session_manager.require_role(["admin", "editor"])

# Anyone logged in can download shared docs
session = session_manager.require_role(["admin", "editor", "viewer"])
```

---

## 4. Password Security

### 4.1 Hashing

Passwords are hashed using **SHA-256**:

```python
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
```

**Output:** 64-character hexadecimal string (256 bits)

### 4.2 Password Policy

| Rule | Requirement |
|------|-------------|
| Minimum length | 8 characters |
| Maximum length | 128 characters |
| Uppercase letters | At least 1 required |
| Lowercase letters | At least 1 required |
| Digits | At least 1 required |
| Special characters | At least 1 required (`!@#$%^&*()_+-=[]{}|;:'",.<>?/`) |

**Validation regex:**
```python
import re

def validate_password(password: str) -> bool:
    if len(password) < 8 or len(password) > 128:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/`~]', password):
        return False
    return True
```

### 4.3 Username Validation

| Rule | Requirement |
|------|-------------|
| Length | 3-30 characters |
| Allowed characters | Alphanumeric, underscore, hyphen |
| Must start with | Letter or underscore |
| Uniqueness | Checked against database |

**Validation regex:**
```python
USERNAME_REGEX = r'^[a-zA-Z_][a-zA-Z0-9_-]{2,29}$'
```

---

## 5. File Encryption

SDMS implements **hybrid encryption** combining AES-256-CBC for file encryption with RSA-2048 for key encryption.

### 5.1 Upload (Encryption) Flow

```
┌─────────────────────────────────────────────────────────┐
│                    ENCRYPTION FLOW                       │
│                                                         │
│  Original File                                          │
│       │                                                 │
│       ├──► Compute SHA-256 hash (integrity check)       │
│       │                                                 │
│       ├──► Generate random AES-256 key (32 bytes)       │
│       │                                                 │
│       ├──► Generate random IV (16 bytes)                │
│       │                                                 │
│       ├──► Encrypt file with AES-256-CBC                │
│       │    using key + IV                               │
│       │         │                                       │
│       │         v                                       │
│       │    Encrypted file (.enc)                        │
│       │                                                 │
│       └──► RSA-encrypt AES key with owner's             │
│            RSA-2048 public key                          │
│                 │                                       │
│                 v                                       │
│            encrypted_aes_key (stored in MongoDB)        │
└─────────────────────────────────────────────────────────┘
```

**Encryption details:**

| Parameter | Value |
|-----------|-------|
| Symmetric algorithm | AES-256-CBC |
| AES key size | 256 bits (32 bytes) |
| IV size | 128 bits (16 bytes) |
| RSA algorithm | RSA-2048-OAEP |
| Key derivation | Random (no KDF) |
| Padding | OAEP for RSA |

### 5.2 Download (Decryption) Flow

```
┌─────────────────────────────────────────────────────────┐
│                    DECRYPTION FLOW                       │
│                                                         │
│  Encrypted file (.enc)                                  │
│       │                                                 │
│       ├──► Retrieve encrypted_aes_key + IV from DB      │
│       │                                                 │
│       ├──► RSA-decrypt AES key using owner's            │
│            RSA-2048 private key                         │
│                 │                                       │
│                 v                                       │
│            Decrypted AES key                            │
│                 │                                       │
│       ├──► Decrypt file with AES-256-CBC                │
│       │    using key + IV                               │
│       │         │                                       │
│       │         v                                       │
│       │    Decrypted file                               │
│       │                                                 │
│       └──► Compute SHA-256 hash of decrypted file       │
│                 │                                       │
│                 ├── Match stored hash → Return file     │
│                 └── Mismatch → Error (tampering!)       │
└─────────────────────────────────────────────────────────┘
```

### 5.3 File Sharing (Re-Encryption) Flow

```
┌─────────────────────────────────────────────────────────┐
│                  SHARING FLOW                            │
│                                                         │
│  Owner's encrypted_aes_key                              │
│       │                                                 │
│       ├──► RSA-decrypt with owner's private key         │
│       │         │                                       │
│       │         v                                       │
│       │    Plaintext AES key                            │
│       │         │                                       │
│       └──► RSA-encrypt with recipient's public key      │
│                 │                                       │
│                 v                                       │
│       Recipient's encrypted_aes_key                     │
│       (stored in shared_with array)                     │
└─────────────────────────────────────────────────────────┘
```

**Key insight:** The actual AES key is never stored in plaintext. Each user has their own RSA key pair. Sharing works by re-encrypting the same AES key with each recipient's RSA public key.

---

## 6. Key Management

### 6.1 RSA Key Generation

Each user receives a unique RSA-2048 key pair during registration:

```python
from Crypto.PublicKey import RSA

def generate_rsa_keypair():
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return public_key, private_key
```

### 6.2 Key Storage

| Key | Storage Location | Format |
|-----|-----------------|--------|
| RSA public key | MongoDB `users.rsa_public_key` | PEM string |
| RSA private key | MongoDB `users.rsa_private_key` | PEM string |
| AES keys | MongoDB `documents.encrypted_aes_key` | RSA-encrypted Base64 |
| AES IVs | MongoDB `documents.iv` | Base64 string |

### 6.3 Key Lifecycle

```
Registration → Generate RSA key pair → Store in DB
     │
     v
Upload file → Generate random AES key → RSA-encrypt with public key → Store
     │
     v
Share file → RSA-decrypt (owner's private key) → RSA-encrypt (recipient's public key)
     │
     v
Download file → RSA-decrypt AES key (private key) → Decrypt file
```

---

## 7. Data Integrity

### SHA-256 Hash Verification

| Stage | Action |
|-------|--------|
| Upload | Compute SHA-256 hash of original plaintext file, store in `documents.sha256_hash` |
| Download | After decryption, compute SHA-256 hash and compare to stored hash |
| Mismatch | Raise an error — file has been tampered with or corrupted |

```python
import hashlib

def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# At upload
original_hash = compute_hash(original_file_data)
# Store original_hash in documents.sha256_hash

# At download
decrypted_hash = compute_hash(decrypted_file_data)
if decrypted_hash != stored_hash:
    raise IntegrityError("File integrity check failed")
```

---

## 8. Face Recognition Security

### 8.1 Technology Stack

| Component | Technology |
|-----------|-----------|
| Face Detection | Haar Cascade Classifier (`haarcascade_frontalface_default.xml`) |
| Feature Extraction | Local Binary Patterns (LBP) |
| Histogram Computation | 4×4 spatial blocks, 59-bin histogram per block |
| Feature Vector | 4×4×59 = 944 dimensions |
| Matching Metric | Chi-Square distance |
| Decision Threshold | 55.0 (match if distance ≤ threshold) |
| Library | OpenCV (`cv2.face.LBPHFaceRecognizer`) |

### 8.2 Enrollment Process

| Step | Action |
|------|--------|
| 1 | Open camera |
| 2 | Capture 5 face samples (straight, left, right, up, final) |
| 3 | For each sample: detect face → grayscale → resize 200×200 → compute LBP histogram |
| 4 | Average all 5 histograms element-wise |
| 5 | Store averaged histogram in `users.face_encoding` |
| 6 | Set `users.face_enrolled = True` |

### 8.3 Authentication Process

| Step | Action |
|------|--------|
| 1 | Get all enrolled users from database |
| 2 | Open camera, capture single face frame |
| 3 | Compute LBP histogram of captured face |
| 4 | Calculate Chi-Square distance to each enrolled user |
| 5 | Find minimum distance |
| 6 | If min distance ≤ 55.0 → authenticate; else → reject |

### 8.4 Chi-Square Distance

```
χ²(A, B) = Σ [(Aᵢ - Bᵢ)² / (Aᵢ + Bᵢ)]
```

| Distance Range | Interpretation |
|----------------|---------------|
| 0.0 | Perfect match (identical histograms) |
| 0.0 – 55.0 | **Accepted** — same person |
| > 55.0 | **Rejected** — different person or poor quality |

---

## 9. Session Management

### 9.1 Session Store

Sessions are stored in an **in-memory singleton** (Python dictionary), not persisted to disk.

```python
class SessionManager:
    _instance = None
    _sessions = {}  # {session_id: session_data}

    # Singleton pattern ensures one session store across the application
```

### 9.2 Session Data

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | string | Authenticated user's ID |
| `username` | string | Authenticated user's name |
| `role` | string | User's role (admin/editor/viewer) |
| `rsa_public_key` | string | User's RSA public key (PEM) |
| `rsa_private_key` | string | User's RSA private key (PEM) |
| `created_at` | datetime | Session start time |

### 9.3 Session Lifecycle

```
Login (password or face)
    │
    ├── Create session → Store in memory
    │
    v
Active session
    │
    ├── Required for all authenticated operations
    │
    v
Logout
    │
    └── Remove session from memory
```

### 9.4 Properties

| Property | Value |
|----------|-------|
| Storage | In-memory (Python dict) |
| Persistence | None (lost on application restart) |
| Concurrency | Single session at a time (singleton) |
| Timeout | None (cleared only on logout or restart) |
| Encryption | RSA keys stored in plaintext in memory |

---

## 10. Input Validation

### 10.1 Username Validation

| Rule | Implementation |
|------|---------------|
| Length | 3-30 characters |
| Pattern | `^[a-zA-Z_][a-zA-Z0-9_-]{2,29}$` |
| Uniqueness | Checked against `users.username` index |
| Empty check | Rejected if empty or whitespace-only |

### 10.2 Password Validation

| Rule | Implementation |
|------|---------------|
| Minimum length | 8 characters |
| Maximum length | 128 characters |
| Uppercase | At least 1 `[A-Z]` |
| Lowercase | At least 1 `[a-z]` |
| Digit | At least 1 `\d` |
| Special character | At least 1 `[!@#$%^&*()_+\-=...]` |

### 10.3 File Upload Validation

| Rule | Implementation |
|------|---------------|
| File not empty | Reject zero-byte files |
| File size limit | Configurable maximum (prevents DoS) |
| MIME type | Logged for audit; basic type checking |
| Filename sanitization | Original filename stored separately from encrypted filename |

### 10.4 General Validation

| Rule | Implementation |
|------|---------------|
| Null checks | All required fields validated before processing |
| Type checking | Ensure correct types before operations |
| SQL injection | N/A — NoSQL database |
| NoSQL injection | PyMongo parameterized queries (no string interpolation in queries) |

---

## 11. Audit Logging

### 11.1 Scope

Every significant action in SDMS is recorded in the `audit_logs` collection.

### 11.2 Logged Actions

| Action | Severity | Description |
|--------|----------|-------------|
| `LOGIN` | INFO | Successful or failed login attempt |
| `LOGOUT` | INFO | User logout |
| `REGISTER` | INFO | New user account created |
| `FACE_LOGIN` | INFO | Face recognition authentication attempt |
| `UPLOAD` | INFO | Document uploaded and encrypted |
| `DOWNLOAD` | INFO | Document downloaded and decrypted |
| `DELETE` | WARNING | Document soft-deleted |
| `SHARE` | INFO | Document shared with another user |
| `UNSHE_REVOKE` | INFO | Sharing revoked |
| `USER_CREATE` | INFO | Admin created new user |
| `USER_DEACTIVATE` | WARNING | Admin deactivated user |
| `ROLE_CHANGE` | WARNING | User role changed |
| `HASH_GENERATE` | INFO | File hash computed |
| `INTEGRITY_CHECK` | INFO/ERROR | File integrity verification result |

### 11.3 Audit Record Fields

| Field | Description |
|-------|-------------|
| `audit_id` | Unique identifier (atomic counter) |
| `timestamp` | UTC timestamp of the action |
| `user_id` | Acting user's ID |
| `username` | Acting user's name (denormalized for readability) |
| `role` | User's role at time of action |
| `action` | Action type string |
| `resource_type` | Type of affected resource |
| `resource_id` | ID of affected resource |
| `resource_name` | Human-readable resource name |
| `status` | `success` or `failure` |
| `message` | Descriptive message |
| `severity` | `INFO`, `WARNING`, or `ERROR` |
| `client_ip` | Client IP address (if available) |
| `device_info` | Device/OS information (if available) |
| `metadata` | Additional context data |

### 11.4 Example Audit Entries

**Successful login:**
```json
{
  "audit_id": "AUD-000001",
  "timestamp": "2025-07-15T10:30:00Z",
  "user_id": "USR-000001",
  "username": "john_doe",
  "role": "editor",
  "action": "LOGIN",
  "resource_type": "user",
  "resource_id": "USR-000001",
  "resource_name": "john_doe",
  "status": "success",
  "message": "Password authentication successful",
  "severity": "INFO",
  "session_id": "SESS-abc123",
  "client_ip": "192.168.1.100",
  "device_info": "Windows 11 / Python 3.11",
  "metadata": {}
}
```

**Failed login:**
```json
{
  "audit_id": "AUD-000002",
  "timestamp": "2025-07-15T10:30:05Z",
  "user_id": null,
  "username": "john_doe",
  "role": null,
  "action": "LOGIN",
  "resource_type": "user",
  "resource_id": null,
  "resource_name": "john_doe",
  "status": "failure",
  "message": "Invalid password",
  "severity": "WARNING",
  "session_id": null,
  "client_ip": "192.168.1.100",
  "device_info": "Windows 11 / Python 3.11",
  "metadata": {}
}
```

---

## 12. Security Best Practices Implemented

| # | Practice | Implementation |
|---|----------|---------------|
| 1 | Password hashing | SHA-256 (plaintext never stored) |
| 2 | Encryption at rest | AES-256-CBC for all stored files |
| 3 | Key encapsulation | RSA-2048 protects AES keys |
| 4 | Integrity verification | SHA-256 hash checked on every download |
| 5 | RBAC | Three-tier role system with enforcement |
| 6 | Audit logging | All actions recorded immutably |
| 7 | Input validation | Username, password, and file validation |
| 8 | Separate key per user | Each user has unique RSA key pair |
| 9 | No plaintext secrets | Passwords hashed, AES keys RSA-encrypted |
| 10 | Soft deletion | Documents soft-deleted (recoverable) |
| 11 | Unique constraints | Enforced at database level for user/document IDs |
| 12 | Connection pooling | Limits concurrent database connections |

---

## 13. Security Weaknesses and Improvements

### 13.1 Password Hashing Without Salt

**Weakness:** SHA-256 is used without a per-user salt. This makes the system vulnerable to **rainbow table attacks** — precomputed hash lookup tables.

**Impact:** If an attacker gains access to the `password_hash` field, they can use precomputed tables to reverse common passwords instantly.

**Improvement:**
```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
```

**Recommended alternatives:**
- **bcrypt** (with salt + work factor)
- **Argon2id** (memory-hard, GPU-resistant)
- **scrypt** (memory-hard)

---

### 13.2 Unencrypted RSA Private Keys in MongoDB

**Weakness:** RSA private keys are stored as plaintext PEM strings in the `users` collection.

**Impact:** If an attacker gains read access to MongoDB, they can decrypt all files owned by any user. The entire file encryption scheme collapses.

**Improvement:**
- Encrypt private keys with a key derived from the user's password (e.g., PBKDF2)
- Use a Hardware Security Module (HSM) for key storage
- Encrypt private keys with a master key managed outside the database

---

### 13.3 No HTTPS/TLS for MongoDB Connection

**Weakness:** The MongoDB connection URI is `mongodb://localhost:27017` (plaintext TCP).

**Impact:** If MongoDB is accessed over a network (not just localhost), credentials and data are transmitted in cleartext.

**Improvement:**
```
mongodb+srv://user:password@cluster.example.com/db?tls=true
```
- Enable TLS for all MongoDB connections in production
- Use x.509 certificate authentication

---

### 13.4 In-Memory Session Storage

**Weakness:** Sessions are stored only in Python memory (singleton dictionary). They are lost on application restart and cannot be shared across processes.

**Impact:**
- All users are logged out on restart
- No horizontal scaling possible
- No session persistence

**Improvement:**
- Use Redis or MongoDB for session storage
- Implement session expiration/TTL
- Add session invalidation on logout

---

### 13.5 No Rate Limiting on Login

**Weakness:** There is no rate limiting on authentication attempts (password or face recognition).

**Impact:** Brute-force attacks are possible — an attacker can attempt unlimited password guesses or face recognition attempts.

**Improvement:**
- Implement exponential backoff after failed attempts
- Lock accounts after N consecutive failures
- Add CAPTCHA after repeated failures
- Log and alert on suspicious login patterns

---

### 13.6 No CSRF Protection

**Weakness:** No Cross-Site Request Forgery tokens are implemented.

**Impact:** Lower risk since SDMS is a **desktop application** (Tkinter), not a web application. However, if a web interface is added in the future, CSRF becomes a real threat.

**Improvement:**
- Add CSRF tokens if a web interface is introduced
- Validate Origin/Referer headers in web endpoints

---

### 13.7 Face Recognition Threshold Tuning

**Weakness:** The Chi-Square distance threshold of 55.0 is a fixed constant. It has not been validated against a standardized face recognition benchmark.

**Impact:**
- Too low → False rejects (legitimate users rejected)
- Too high → False accepts (impostors accepted)

**Improvement:**
- Test against a labeled dataset to calibrate the threshold
- Implement adaptive thresholding based on user feedback
- Add a confidence score display for the user
- Consider adding liveness detection (blink detection, head movement)

---

### 13.8 Additional Recommendations

| Issue | Recommendation |
|-------|----------------|
| No HTTPS | If a web interface is added, enforce HTTPS with Let's Encrypt |
| No 2FA | Add TOTP or SMS-based second factor |
| No password rotation | Enforce periodic password changes |
| No account lockout | Lock accounts after N failed attempts |
| No session timeout | Add automatic session expiration |
| No IP allowlisting | Restrict database access to known IPs |
| No encryption key rotation | Implement periodic RSA key pair rotation |
| No backup encryption | Encrypt database backups |
| Hardcoded constants | Move thresholds to configuration files |
| No security headers | Add security headers if web interface is added |

---

## Summary

| Layer | Current State | Risk Level |
|-------|--------------|------------|
| Authentication | Password + Face (functional but weak hash) | Medium |
| Authorization | RBAC (well-implemented) | Low |
| Encryption | AES-256 + RSA-2048 (strong) | Low |
| Key Management | Keys in DB unencrypted | High |
| Integrity | SHA-256 (effective) | Low |
| Sessions | In-memory only | Medium |
| Audit Logging | Comprehensive | Low |
| Input Validation | Basic validation present | Low-Medium |
| Rate Limiting | Not implemented | Medium |
| Transport Security | No TLS | High (in production) |
