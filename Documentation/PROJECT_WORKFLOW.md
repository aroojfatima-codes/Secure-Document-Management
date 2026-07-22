# PROJECT_WORKFLOW.md — Secure Document Management System (SDMS)

> End-to-end workflow documentation covering every major user journey from
> application startup through shutdown, with layer-by-layer detail.

---

## Table of Contents

1. [Application Startup Sequence](#1-application-startup-sequence)
2. [Login Workflow](#2-login-workflow)
3. [Registration Workflow](#3-registration-workflow)
4. [Dashboard Loading](#4-dashboard-loading)
5. [Document Upload Workflow](#5-document-upload-workflow)
6. [Document Listing & Search](#6-document-listing--search)
7. [Document Download Workflow](#7-document-download-workflow)
8. [Document Sharing Workflow](#8-document-sharing-workflow)
9. [Face Enrollment Workflow](#9-face-enrollment-workflow)
10. [Face Login Workflow](#10-face-login-workflow)
11. [Audit Logging Throughout](#11-audit-logging-throughout)
12. [Logout Workflow](#12-logout-workflow)
13. [Complete End-to-End Workflow](#13-complete-end-to-end-workflow)

---

## 1. Application Startup Sequence

```mermaid
flowchart TD
    A([python main.py]) --> B[setup_logging]
    B --> C[Log startup banner<br>app name, version, environment]
    C --> D[DatabaseManager.__init__]
    D --> E[DatabaseManager.connect]
    E --> F{MongoDB reachable?}

    F -->|No| G[Raise DatabaseError]
    G --> H[Log error + sys.exit 1]

    F -->|Yes| I[DatabaseManager.create_indexes]
    I --> J[Ensure users, documents,<br>audit_logs, counters indexes]

    J --> K[StorageManager.__init__]
    K --> L[StorageManager.initialise]
    L --> M{Create directories<br>if missing}
    M --> N[storage/encrypted_documents/]
    M --> O[storage/temp/]
    M --> P[logs/]

    N --> Q[Instantiate 4 controllers]
    O --> Q
    P --> Q

    Q --> R[AuthController]
    Q --> S[DocumentController]
    Q --> T[AuditController]
    Q --> U[FaceController]

    R --> V[SDMSApp.__init__]
    S --> V
    T --> V
    U --> V

    V --> W[Create Sidebar - unauth menu]
    W --> X[Create TopBar]
    X --> Y[Show LoginPage]
    Y --> Z[app.mainloop]

    style A fill:#e1f5fe
    style G fill:#ffebee
    style H fill:#ffebee
    style Z fill:#e8f5e9
```

### Layer-by-Layer Detail

| Step | Layer | Component | What Happens |
|------|-------|-----------|-------------|
| 1 | Infrastructure | `main.py` | Entry point; imports are deferred to avoid circular deps |
| 2 | Infrastructure | `logging_config.py` | Root logger configured with file handler (`logs/sdms.log`) and console handler; log level from `.env` |
| 3 | Infrastructure | `DatabaseManager` | Singleton creates `pymongo.MongoClient` with configured URI and timeouts |
| 4 | Infrastructure | `DatabaseManager.create_indexes()` | Creates unique indexes on `user_id`, `username`, `document_id`, `audit_id`; compound indexes on `owner_id`, `timestamp` |
| 5 | Infrastructure | `StorageManager` | Verifies/creates `storage/encrypted_documents/`, `storage/temp/`, `logs/` directories |
| 6 | Infrastructure | `Settings` singleton | Already loaded during import; `.env` values available to all modules |
| 7 | Presentation | `SDMSApp` (CustomTkinter `CTk`) | Main window created; geometry set to screen size; sidebar + topbar + page container laid out in grid |
| 8 | Presentation | `Sidebar` | Builds unauthenticated menu: Login, Register items only |
| 9 | Presentation | `TopBar` | Theme toggle set to light; breadcrumb shows "Login"; user section hidden |
| 10 | Presentation | `LoginPage` | Rendered in page container; username/password fields + Login button + Face Login button + Register link |

---

## 2. Login Workflow

```mermaid
flowchart TD
    A[LoginPage displayed] --> B[User enters username + password]
    B --> C[User clicks Login]
    C --> D[GUI calls AuthController.login]

    D --> E[AuthController delegates<br>to AuthService.authenticate]
    E --> F[AuthService calls<br>UserRepository.find_by_username]
    F --> G[MongoDB: db.users.findOne]

    G --> H{User found?}
    H -->|No| I[AuthSvc returns failure]
    I --> J[AuthCtrl returns<br>success=False, error=msg]
    J --> K[LoginPage shows Toast error]

    H -->|Yes| L[AuthService: SHA-256 password<br>compare with stored hash]
    L --> M{Hash matches?}

    M -->|No| N[AuthService calls<br>AuditService.log]
    N --> O[AuditRepo.insert<br>action=USER_LOGIN_FAILED<br>severity=WARNING]
    O --> P[Return failure to GUI]
    P --> K

    M -->|Yes| Q[AuthService calls<br>AuditService.log]
    Q --> R[AuditRepo.insert<br>action=USER_LOGIN<br>severity=INFO]
    R --> S[Return success + user data]
    S --> T[AuthCtrl returns<br>success, user_id, username, role]
    T --> U[SDMSApp._handle_login]
    U --> V[Set _current_user dict]
    V --> W[SessionManager.set_current_user]
    W --> X[SDMSApp._on_auth_success]
    X --> Y[Toast: Welcome message]
    Y --> Z[Sidebar rebuilds<br>authenticated menu]
    Z --> AA[TopBar shows user info]
    AA --> AB[Navigate to DashboardPage]

    style A fill:#e1f5fe
    style K fill:#ffebee
    style AB fill:#e8f5e9
```

### Password Verification Detail

```python
# AuthService.authenticate() simplified
def authenticate(self, username: str, password: str) -> dict:
    user = self._user_repo.find_by_username(username)
    if user is None:
        return {"success": False, "error": "Invalid credentials"}

    computed_hash = SHA256Hasher.hash(password.encode())
    if computed_hash != user.password_hash:
        self._audit_svc.log(
            action=AuditAction.USER_LOGIN_FAILED,
            user_id=user.user_id,
            severity=SeverityLevel.WARNING,
        )
        return {"success": False, "error": "Invalid credentials"}

    self._audit_svc.log(
        action=AuditAction.USER_LOGIN,
        user_id=user.user_id,
        severity=SeverityLevel.INFO,
    )
    return {
        "success": True,
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
    }
```

---

## 3. Registration Workflow

```mermaid
flowchart TD
    A[RegisterPage displayed] --> B[User fills form:<br>username, fullname, email,<br>role, password]
    B --> C[User clicks Register]
    C --> D[GUI validates inputs<br>non-empty, valid email format]
    D --> E{Validation passes?}

    E -->|No| F[Show inline error messages]
    E -->|Yes| G[GUI calls<br>AuthController.register]

    G --> H[AuthController delegates<br>to RegistrationService.register]
    H --> I[Check username uniqueness<br>UserRepository.find_by_username]
    I --> J{Username available?}

    J -->|No| K[Return error:<br>Username already exists]
    K --> L[Toast error message]

    J -->|Yes| M[SHA-256 hash password]
    M --> N[KeyGenerator.generate_rsa_keypair]
    N --> O[RSA-2048 key pair:<br>public_key + private_key]

    O --> P[Build User model<br>user_id = uuid4 hex]
    P --> Q[UserRepository.insert<br>into MongoDB]
    Q --> R[AuditService.log<br>action=USER_REGISTRATION]
    R --> S[Return success]
    S --> T[Toast: Account created]
    T --> U[Navigate to LoginPage]

    style A fill:#e1f5fe
    style F fill:#ffebee
    style K fill:#ffebee
    style U fill:#e8f5e9
```

### RSA Key Generation at Registration

```
RegistrationService.register(username, password, role):
    1. password_hash = SHA-256(password)
    2. (public_pem, private_pem) = KeyGenerator.generate_rsa_keypair()
       - Uses PyCryptodome: RSA.generate(2048, e=65537)
       - Exports public key in PEM format
       - Exports private key in PEM format
    3. user = User(
           user_id = uuid4().hex,
           username = username,
           password_hash = password_hash,
           role = role,
           rsa_public_key = public_pem,
           rsa_private_key = private_pem,
           created_at = datetime.now(UTC),
           is_active = True,
       )
    4. user_repo.insert(user)
    5. audit_svc.log(USER_REGISTRATION)
```

---

## 4. Dashboard Loading

```mermaid
flowchart TD
    A[Auth success triggers<br>_on_auth_success] --> B[Navigate to dashboard]
    B --> C[App._create_page'dashboard']
    C --> D[DashboardPage.__init__]
    D --> E[Load user info from<br>_current_user dict]
    E --> F[Render stat cards:<br>Total Documents, Shared,<br>Storage Used]
    F --> G[Render quick action buttons:<br>Upload, Download, Share]
    G --> H[Render recent documents list]
    H --> I[Page displayed with fade-in animation]

    style A fill:#e1f5fe
    style I fill:#e8f5e9
```

### Dashboard Data Sources

| Widget | Data Source |
|--------|-----------|
| "Welcome, {name}" | `_current_user["full_name"]` |
| Role badge | `_current_user["role"]` |
| Total documents | `DocumentController.list_my_documents()` → count |
| Shared documents | `DocumentController.list_shared_with_me()` → count |
| Recent documents | First 5 from `list_my_documents()` |
| Quick actions | Static buttons linking to upload/download/share pages |

---

## 5. Document Upload Workflow

```mermaid
flowchart TD
    A[UploadPage displayed] --> B[User clicks Browse]
    B --> C[tkinter filedialog<br>opens file picker]
    C --> D[User selects file]
    D --> E[Display file info:<br>name, size, type]
    E --> F[User clicks Upload]
    F --> G[GUI validates:<br>file exists, size < 50MB]

    G --> H{Valid?}
    H -->|No| I[Show error message]
    H -->|Yes| J[Show loading spinner]
    J --> K[DocumentController.upload<br>file_path, user_id]

    K --> L[DocumentUploadService.upload]

    L --> M[Step 1: Read file bytes]
    M --> N[Step 2: Generate AES-256 key<br>random 32 bytes]
    N --> O[Step 3: Generate IV<br>random 16 bytes]
    O --> P[Step 4: AES-256-CBC encrypt<br>plaintext → ciphertext]
    P --> Q[Step 5: SHA-256 hash<br>of plaintext bytes]

    Q --> R[Step 6: Fetch owner's<br>RSA public key from DB]
    R --> S[Step 7: RSA-2048-OAEP encrypt<br>AES key with public key]

    S --> T[Step 8: Base64-encode<br>wrapped key + IV]
    T --> U[Step 9: Generate doc_id<br>CounterRepository.next_value]

    U --> V[Step 10: Write ciphertext to<br>storage/encrypted_documents/DOCxxx.enc]
    V --> W[Step 11: Build Document model]
    W --> X[Step 12: DocumentRepository.insert<br>metadata into MongoDB]

    X --> Y[Step 13: AuditService.log<br>DOCUMENT_UPLOAD, INFO]
    Y --> Z[Return success + doc metadata]

    Z --> AA[Hide loading spinner]
    AA --> AB[Toast: Document uploaded!]
    AB --> AC[Navigate to DocumentsPage]

    style A fill:#e1f5fe
    style I fill:#ffebee
    style P fill:#fff3e0
    style S fill:#fff3e0
    style AB fill:#e8f5e9
```

### Encryption Pipeline (Step 4-7 Detail)

```python
# DocumentUploadService.upload() core logic
def upload(self, file_path: str, user_id: str) -> dict:
    # 1. Read plaintext
    with open(file_path, "rb") as f:
        plaintext = f.read()

    # 2-3. Generate AES key and IV
    aes_key = get_random_bytes(32)   # AES-256
    iv = get_random_bytes(16)        # CBC IV

    # 4. Encrypt
    cipher = AESCipher(key=aes_key)
    payload = cipher.encrypt(plaintext)  # EncryptedPayload

    # 5. Hash
    hasher = SHA256Hasher()
    file_hash = hasher.hash(plaintext)

    # 6-7. Wrap AES key
    owner = self._user_repo.find_by_id(user_id)
    rsa = RSACipher()
    wrapped_key = rsa.encrypt(aes_key, owner.rsa_public_key)

    # 8. Encode for storage
    b64_key = Base64Utils.encode(wrapped_key)
    b64_iv = Base64Utils.encode(payload.iv)

    # 9-12. Store
    doc_id = self._id_svc.next_id()
    encrypted_filename = f"{doc_id}.enc"
    storage_path = settings.STORAGE_ENCRYPTED_PATH / encrypted_filename
    storage_path.write_bytes(payload.ciphertext)

    document = Document(
        document_id=doc_id,
        original_filename=os.path.basename(file_path),
        encrypted_filename=encrypted_filename,
        owner_id=user_id,
        encrypted_aes_key=b64_key,
        iv=b64_iv,
        sha256_hash=file_hash,
        file_size=len(plaintext),
        algorithm="AES-256-CBC",
    )
    self._doc_repo.insert(document)
    return {"success": True, "document_id": doc_id}
```

---

## 6. Document Listing & Search

```mermaid
flowchart TD
    A[DocumentsPage displayed] --> B[App._create_page'documents']
    B --> C[DocumentController.list_my_documents]
    C --> D[DocumentListingService.list_user_documents]
    D --> E[DocumentRepository.find_many<br>{owner_id: user_id, is_deleted: false}]
    E --> F[MongoDB: db.documents.find]
    F --> G[Return list of Document models]
    G --> H[Convert to display dicts]
    H --> I[DocumentsPage.load_documents]
    I --> J[Render document cards<br>with name, date, size, actions]

    J --> K{User clicks Search tab}
    K --> L[SearchPage displayed]
    L --> M[User enters search query]
    M --> N[DocumentController.search]
    N --> O[DocumentListingService.search]
    O --> P[DocumentRepository.search<br>regex on filename, owner]
    P --> Q[Return matching documents]
    Q --> R[SearchPage displays results]

    style A fill:#e1f5fe
    style J fill:#e8f5e9
    style R fill:#e8f5e9
```

### Listing Filters

| Filter | MongoDB Query |
|--------|--------------|
| My documents | `{owner_id: user_id, is_deleted: false}` |
| Shared with me | `{shared_with.user_id: user_id, is_deleted: false}` |
| Search by name | `{original_filename: {$regex: query, $options: "i"}}` |
| Search by owner | `{owner_id: {$in: [matching_user_ids]}}` |
| Date range | `{created_at: {$gte: start, $lte: end}}` |

---

## 7. Document Download Workflow

```mermaid
flowchart TD
    A[DownloadPage displayed] --> B[Load user's document list]
    B --> C[User selects document]
    C --> D[User clicks Download]
    D --> E[tkinter filedialog<br>asks save location]
    E --> F[User selects save path]
    F --> G[Show loading spinner]
    G --> H[DocumentController.download<br>doc_id, save_path, user_id]

    H --> I[DocumentDownloadService.download]

    I --> J[Step 1: Fetch document<br>metadata from MongoDB]
    J --> K{Document exists?}
    K -->|No| L[Return error]
    L --> M[Toast: Document not found]

    K -->|Yes| N[Step 2: Access check<br>owner or shared_with user?]
    N --> O{Authorized?}
    O -->|No| P[Audit: PERMISSION_DENIED]
    P --> Q[Toast: Access denied]

    O -->|Yes| R[Step 3: Fetch user's<br>RSA private key]
    R --> S[Step 4: Base64-decode<br>wrapped AES key + IV]
    S --> T[Step 5: RSA-2048-OAEP decrypt<br>wrapped key → raw AES key]

    T --> U[Step 6: Read ciphertext<br>from encrypted_documents/]
    U --> V[Step 7: AES-256-CBC decrypt<br>ciphertext → plaintext]

    V --> W[Step 8: SHA-256 verify<br>computed hash vs stored hash]
    W --> X{Hash matches?}

    X -->|No| Y[Audit: INTEGRITY_FAILURE<br>severity=CRITICAL]
    Y --> Z[Return error:<br>Integrity check failed]
    Z --> AA[Toast: Document may be<br>corrupted or tampered]

    X -->|Yes| AB[Step 9: Write plaintext<br>to user-selected path]
    AB --> AC[Step 10: AuditService.log<br>DOCUMENT_DOWNLOAD, INFO]
    AC --> AD[Return success]

    AD --> AE[Hide loading spinner]
    AE --> AF[Toast: Downloaded!]

    style A fill:#e1f5fe
    style M fill:#ffebee
    style Q fill:#ffebee
    style Y fill:#ffebee
    style AA fill:#ffebee
    style AF fill:#e8f5e9
```

### Integrity Verification Detail

```python
# DocumentDownloadService.download() core logic
def download(self, doc_id: str, save_path: str, user_id: str) -> dict:
    # 1. Fetch document
    document = self._doc_repo.find_by_id(doc_id)
    if document is None:
        return {"success": False, "error": "Document not found"}

    # 2. Access check
    if document.owner_id != user_id:
        shared_entry = next(
            (s for s in document.shared_with if s.user_id == user_id),
            None,
        )
        if shared_entry is None:
            self._audit_svc.log(PERMISSION_DENIED)
            return {"success": False, "error": "Access denied"}
        wrapped_key_b64 = shared_entry.encrypted_aes_key
    else:
        wrapped_key_b64 = document.encrypted_aes_key

    # 3-5. Unwrap AES key
    user = self._user_repo.find_by_id(user_id)
    wrapped_key = Base64Utils.decode(wrapped_key_b64)
    rsa = RSACipher()
    aes_key = rsa.decrypt(wrapped_key, user.rsa_private_key)

    # 6-7. Decrypt file
    encrypted_path = settings.STORAGE_ENCRYPTED_PATH / document.encrypted_filename
    ciphertext = encrypted_path.read_bytes()
    iv = Base64Utils.decode(document.iv)
    aes = AESCipher(key=aes_key)
    payload = EncryptedPayload(ciphertext=ciphertext, iv=iv)
    plaintext = aes.decrypt(payload)

    # 8. Verify integrity
    hasher = SHA256Hasher()
    if not hasher.verify(plaintext, document.sha256_hash):
        self._audit_svc.log(INTEGRITY_FAILURE, severity=CRITICAL)
        return {"success": False, "error": "Integrity check failed"}

    # 9. Write to disk
    with open(save_path, "wb") as f:
        f.write(plaintext)

    # 10. Audit
    self._audit_svc.log(DOCUMENT_DOWNLOAD)
    return {"success": True, "path": save_path}
```

---

## 8. Document Sharing Workflow

```mermaid
flowchart TD
    A[SharePage displayed] --> B[Load user's document list]
    B --> C[User selects document to share]
    C --> D[User enters recipient username]
    D --> E[User selects permission:<br>view or edit]
    E --> F[User clicks Share]

    F --> G[DocumentController.share<br>doc_id, recipient_name, permission]
    G --> H[DocumentSharingService.share]

    H --> I[Step 1: Fetch document<br>from MongoDB]
    I --> J{Document exists?}
    J -->|No| K[Return error]

    J -->|Yes| L[Step 2: Verify sender<br>is document owner]
    L --> M{Is owner?}
    M -->|No| N[Return error:<br>Not authorized]

    M -->|Yes| O[Step 3: Find recipient<br>UserRepository.find_by_username]
    O --> P{Recipient exists?}
    P -->|No| Q[Return error:<br>User not found]

    P -->|Yes| R[Step 4: Fetch recipient's<br>RSA public key]
    R --> S[Step 5: Fetch owner's<br>RSA private key]

    S --> T[Step 6: Decrypt owner's<br>wrapped AES key<br>→ raw AES key]

    T --> U[Step 7: Re-encrypt AES key<br>with RECIPIENT's<br>RSA public key]

    U --> V[Step 8: Base64-encode<br>re-encrypted key]

    V --> W[Step 9: Document.add_share<br>user_id, permission,<br>encrypted_aes_key]

    W --> X[Step 10: DocumentRepository.update<br>shared_with array in MongoDB]

    X --> Y[Step 11: AuditService.log<br>DOCUMENT_SHARE, INFO]
    Y --> Z[Return success]

    Z --> AA[Toast: Document shared<br>successfully!]

    style A fill:#e1f5fe
    style K fill:#ffebee
    style N fill:#ffebee
    style Q fill:#ffebee
    style T fill:#fff3e0
    style U fill:#fff3e0
    style AA fill:#e8f5e9
```

### Key Re-Encryption Flow

```
Original state:
  document.encrypted_aes_key = RSA_owner_pubkey(AES_key)

After sharing with User B:
  document.shared_with[0] = {
    user_id: "B",
    permission: "view",
    encrypted_aes_key: RSA_B_pubkey(AES_key)    ← NEW
  }

After sharing with User C:
  document.shared_with[1] = {
    user_id: "C",
    permission: "edit",
    encrypted_aes_key: RSA_C_pubkey(AES_key)    ← NEW
  }

The file on disk (DOCxxx.enc) is NOT re-encrypted.
Only the key wrapping changes per recipient.
```

---

## 9. Face Enrollment Workflow

```mermaid
flowchart TD
    A[FacePage displayed] --> B[User clicks Start Camera]
    B --> C[OpenCV VideoCapture opens<br>webcam device 0]
    C --> D[Live video feed displayed<br>in GUI frame]

    D --> E[User clicks Capture Face]
    E --> F[Single frame captured<br>from video stream]
    F --> G[Convert frame to grayscale]
    G --> H[Haar Cascade classifier<br>detect face regions]

    H --> I{Face detected?}
    I -->|No| J[Show message:<br>No face detected]
    J --> K[User repositions and<br>tries again]
    K --> E

    I -->|Yes| L[Draw rectangle around<br>detected face]
    L --> M[FaceRecognitionService.enroll]

    M --> N[Step 1: Extract face ROI<br>Region of Interest]
    N --> O[Step 2: Resize to standard<br>dimensions]
    O --> P[Step 3: LBPH feature<br>extraction]
    P --> Q[Step 4: Train LBPH recognizer<br>on captured sample]
    Q --> R[Step 5: Get label/prediction<br>confidence]

    R --> S[UserRepository.update_face_encoding<br>face_encoding = feature_vector<br>face_enrolled = True]

    S --> T[AuditService.log<br>FACE_ENROLLMENT, INFO]
    T --> U[Return success]
    U --> V[Toast: Face enrolled<br>successfully!]
    V --> W[Display enrollment<br>confirmation in GUI]

    style A fill:#e1f5fe
    style J fill:#ffebee
    style L fill:#fff3e0
    style P fill:#fff3e0
    style W fill:#e8f5e9
```

### LBPH Processing Detail

```python
# FaceRecognitionService.enroll() core logic
def enroll(self, user_id: str, username: str) -> dict:
    # 1. Open camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return {"success": False, "error": "Camera error"}

    # 2. Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 3. Detect face
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return {"success": False, "error": "No face detected"}

    # 4. Extract face ROI
    x, y, w, h = faces[0]
    face_roi = gray[y:y+h, x:x+w]

    # 5. Train LBPH recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    labels = [0]
    recognizer.train([face_roi], np.array(labels))

    # 6. Get feature vector (LBP histogram)
    # The trained model internally computes LBP features
    # which are stored as the face encoding

    # 7. Store in database
    face_encoding = recognizer.getLabels()  # or computed histogram
    self._user_repo.update_face_encoding(
        user_id=user_id,
        face_encoding=face_encoding,
        face_enrolled=True,
    )

    self._audit_svc.log(FACE_ENROLLMENT)
    return {"success": True}
```

---

## 10. Face Login Workflow

```mermaid
flowchart TD
    A[LoginPage displayed] --> B[User clicks Login with Face]
    B --> C[FaceController.login_face]
    C --> D[FaceRecognitionService.verify]

    D --> E[OpenCV VideoCapture opens<br>webcam device 0]
    E --> F[Capture single frame]
    F --> G[Convert to grayscale]
    G --> H[Haar Cascade: detect face]

    H --> I{Face detected?}
    I -->|No| J[Return error:<br>No face detected]
    J --> K[Toast: Position face<br>in camera view]

    I -->|Yes| L[Load all enrolled<br>face encodings from DB]
    L --> M[For each enrolled user:<br>compare with captured face]

    M --> N[LBPH .predict<br>on captured face]
    N --> O{Match found<br>below threshold?}

    O -->|No match| P[AuditService.log<br>FACE_LOGIN_FAILED<br>severity=WARNING]
    P --> Q[Return error:<br>No matching face]
    Q --> R[Toast: Face not recognized]

    O -->|Match found| S[Get matched user_id]
    S --> T[Fetch user from DB]
    T --> U[AuditService.log<br>FACE_LOGIN, INFO]

    U --> V[Return success<br>+ user data]
    V --> W[SDMSApp._handle_face_login]
    W --> X[Set _current_user]
    X --> Y[SessionManager.set_current_user]
    Y --> Z[_on_auth_success]
    Z --> AA[Toast: Welcome!]
    AA --> AB[Navigate to Dashboard]

    style A fill:#e1f5fe
    style K fill:#ffebee
    style R fill:#ffebee
    style AB fill:#e8f59
```

### Face Matching Algorithm

```python
# FaceRecognitionService.verify() core logic
def verify(self) -> dict:
    # 1. Capture frame
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return {"success": False, "error": "Camera error"}

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Detect face
    faces = self._face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return {"success": False, "error": "No face detected"}

    x, y, w, h = faces[0]
    face_roi = gray[y:y+h, x:x+w]

    # 3. Load all enrolled users with face encodings
    enrolled_users = self._user_repo.find_enrolled_users()

    best_match = None
    best_confidence = float("inf")

    for user in enrolled_users:
        # 4. Create temporary recognizer with enrolled face
        temp_recognizer = cv2.face.LBPHFaceRecognizer_create()
        enrolled_face = np.array(user.face_encoding, dtype=np.uint8)
        temp_recognizer.train([enrolled_face], np.array([0]))

        # 5. Predict
        label, confidence = temp_recognizer.predict(face_roi)

        # 6. Lower confidence = better match
        if confidence < best_confidence and confidence < THRESHOLD:
            best_confidence = confidence
            best_match = user

    if best_match is None:
        return {"success": False, "error": "No match found"}

    return {
        "success": True,
        "user_id": best_match.user_id,
        "username": best_match.username,
        "role": best_match.role,
    }
```

---

## 11. Audit Logging Throughout

Every significant user action is recorded. Here is the complete audit trail
coverage:

| Workflow | Action Logged | Severity | Trigger Point |
|----------|--------------|----------|---------------|
| Registration | `USER_REGISTRATION` | INFO | After successful DB insert |
| Login | `USER_LOGIN` | INFO | After password verification |
| Failed login | `USER_LOGIN_FAILED` | WARNING | After hash mismatch |
| Logout | `USER_LOGOUT` | INFO | On logout button click |
| Document upload | `DOCUMENT_UPLOAD` | INFO | After file + metadata stored |
| Document download | `DOCUMENT_DOWNLOAD` | INFO | After file written to disk |
| Document share | `DOCUMENT_SHARE` | INFO | After shared_with updated |
| Access denied | `PERMISSION_DENIED` | WARNING | When non-owner tries restricted action |
| Integrity failure | `INTEGRITY_FAILURE` | CRITICAL | When SHA-256 hash doesn't match |
| Face enrollment | `FACE_ENROLLMENT` | INFO | After face encoding stored |
| Face enrollment fail | `FACE_ENROLLMENT_FAILED` | WARNING | When no face detected |
| Face login | `FACE_LOGIN` | INFO | After successful match |
| Face login fail | `FACE_LOGIN_FAILED` | WARNING | When no match found |
| Audit log view | `AUDIT_LOG_VIEW` | INFO | When admin views audit page |
| Unauthorized access | `UNAUTHORIZED_ACCESS` | SECURITY_ALERT | When user accesses restricted resource |

### Audit Log Data Structure

```python
AuditLog(
    audit_id="AUD001",
    timestamp=datetime.now(UTC),
    user_id="a1b2c3...",
    username="john_doe",
    role="admin",
    action="DOCUMENT_UPLOAD",
    resource_type="DOCUMENT",
    resource_id="DOC001",
    resource_name="report.pdf",
    status="SUCCESS",
    message="Document uploaded and encrypted successfully",
    severity="INFO",
    session_id="sess_abc...",
    client_ip="192.168.1.100",
    device_info="Windows-10-Python3.11",
    metadata={"file_size": 1048576, "algorithm": "AES-256-CBC"},
)
```

---

## 12. Logout Workflow

```mermaid
flowchart TD
    A[User clicks Logout<br>in Sidebar or TopBar] --> B[App._logout]
    B --> C[AuthController.logout]
    C --> D[SessionManager.clear]
    D --> E[Clear _current_user]
    E --> F[Clear _page_cache]
    F --> G[Destroy authenticated<br>Sidebar menu]
    G --> H[Build unauthenticated<br>Sidebar menu]
    H --> I[Reset TopBar:<br>no user, no breadcrumb]
    I --> J[Navigate to LoginPage]
    J --> K[Toast: Logged out<br>successfully]
    K --> L[App window awaits<br>next login]

    M[User closes window] --> N[App._on_close]
    N --> O[AuthController.logout]
    O --> P[App.destroy]

    style A fill:#e1f5fe
    style K fill:#e8f5e9
```

### Session Cleanup

```python
def _logout(self):
    # 1. Service-layer cleanup
    if self.controller:
        self.controller["auth"].logout()   # Clears SessionManager

    # 2. GUI state cleanup
    self._current_user = None
    self._page_cache.clear()

    # 3. Reset UI to pre-auth state
    self._show_login()

    # 4. Inform user
    Toast(self, "Logged out successfully", "info")
```

---

## 13. Complete End-to-End Workflow

The following flowchart shows the entire application lifecycle from startup
through all major operations:

```mermaid
flowchart TD
    START([Application Start<br>python main.py]) --> INIT[Initialize Logging<br>Database Connection<br>Storage Directories]

    INIT --> LOGIN_SCREEN[Login Page]
    LOGIN_SCREEN -->|Credentials| AUTH_CHECK{Authenticate}
    AUTH_CHECK -->|Failed| LOGIN_SCREEN
    AUTH_CHECK -->|Success| DASH[Dashboard]

    DASH --> NAV{Navigation Choice}

    NAV -->|Upload| UPLOAD[Select File]
    UPLOAD --> ENCRYPT[AES-256-CBC Encrypt<br>SHA-256 Hash<br>RSA Key Wrap]
    ENCRYPT --> STORE[Save Encrypted File<br>Save Metadata to DB]
    STORE --> AUDIT_U[Audit: DOCUMENT_UPLOAD]
    AUDIT_U --> NAV

    NAV -->|Download| DL_SELECT[Select Document]
    DL_SELECT --> ACCESS{Access Check}
    ACCESS -->|Denied| AUDIT_DDENY[Audit: PERMISSION_DENIED]
    AUDIT_DDENY --> NAV
    ACCESS -->|Allowed| UNWRAP[RSA Unwrap AES Key<br>AES-256-CBC Decrypt]
    UNWRAP --> VERIFY{SHA-256 Verify}
    VERIFY -->|Failed| AUDIT_INT[Audit: INTEGRITY_FAILURE]
    AUDIT_INT --> ERROR_PAGE[Error: Tampered]
    VERIFY -->|Passed| SAVE_FILE[Save Decrypted File]
    SAVE_FILE --> AUDIT_D[Audit: DOCUMENT_DOWNLOAD]
    AUDIT_D --> NAV

    NAV -->|Share| SHARE_SELECT[Select Document + Recipient]
    SHARE_SELECT --> REWRAP[Re-encrypt AES Key<br>with Recipient's RSA Public Key]
    REWRAP --> UPDATE_DOC[Update shared_with in DB]
    UPDATE_DOC --> AUDIT_S[Audit: DOCUMENT_SHARE]
    AUDIT_S --> NAV

    NAV -->|Face Enroll| FACE_EN[Open Camera<br>Capture Face<br>LBPH Extract Features]
    FACE_EN --> STORE_FACE[Store Face Encoding<br>in User Record]
    STORE_FACE --> AUDIT_FE[Audit: FACE_ENROLLMENT]
    AUDIT_FE --> NAV

    NAV -->|Face Login| FACE_LG[Open Camera<br>Capture Face<br>LBPH Match Against DB]
    FACE_LG --> FACE_MATCH{Match?}
    FACE_MATCH -->|No| AUDIT_FLF[Audit: FACE_LOGIN_FAILED]
    AUDIT_FLF --> NAV
    FACE_MATCH -->|Yes| SESSION[Create Session<br>Navigate to Dashboard]
    SESSION --> DASH

    NAV -->|Audit Logs| AUDIT_VIEW[View/Search Audit Logs]
    AUDIT_VIEW --> AUDIT_LOG[Audit: AUDIT_LOG_VIEW]
    AUDIT_LOG --> NAV

    NAV -->|Logout| LOGOUT[Clear Session<br>Reset UI]
    LOGOUT --> LOGIN_SCREEN

    NAV -->|Close Window| SHUTDOWN[Logout + Destroy App<br>Disconnect MongoDB]
    SHUTDOWN --> END([Application End])

    style START fill:#e1f5fe
    style END fill:#ffebee
    style DASH fill:#e8f5e9
    style ENCRYPT fill:#fff3e0
    style UNWRAP fill:#fff3e0
    style REWRAP fill:#fff3e0
    style VERIFY fill:#f3e5f5
    style AUDIT_INT fill:#ffebee
    style ERROR_PAGE fill:#ffebee
```

### Lifecycle Summary Table

| Phase | Actions | Data Flows |
|-------|---------|-----------|
| **Startup** | Config → Logging → DB → Storage → GUI | `.env` → Settings → all modules |
| **Auth** | Login/Register → Session → Dashboard | User credentials → SHA-256 → MongoDB → Session |
| **Upload** | File → Encrypt → Hash → Store → Audit | Plaintext → AES → RSA → Disk + MongoDB |
| **List** | Query → Filter → Render | MongoDB → Document models → GUI cards |
| **Download** | Select → Access check → Decrypt → Verify → Save | MongoDB → RSA → AES → SHA-256 → Disk |
| **Share** | Select → Find recipient → Re-encrypt key → Update | Owner key → Recipient pubkey → MongoDB |
| **Face Enroll** | Camera → Detect → LBPH → Store | Webcam → OpenCV → NumPy → MongoDB |
| **Face Login** | Camera → Detect → Match → Session | Webcam → OpenCV → MongoDB → Session |
| **Audit** | Query logs → Filter → Render table | MongoDB → AuditLog models → GUI table |
| **Logout** | Clear session → Reset UI → Show login | Session → None → LoginPage |
| **Shutdown** | Final logout → Destroy window → Disconnect DB | App → MongoDB disconnect → Exit |

---

## Appendix: Request Lifecycle Example

A complete document upload request traverses every layer:

```
User clicks "Upload"
    │
    ▼
┌──────────────────────┐
│   PRESENTATION        │  UploadPage validates input, shows spinner
└──────────┬───────────┘
           │  document_controller.upload(path, user_id)
           ▼
┌──────────────────────┐
│   CONTROLLER          │  DocumentController (thin facade)
└──────────┬───────────┘
           │  document_upload_service.upload(path, user_id)
           ▼
┌──────────────────────┐
│   SERVICE             │  DocumentUploadService (orchestrates crypto + storage)
│                       │  1. Read file
│                       │  2. Generate AES key + IV
│                       │  3. AES encrypt → EncryptedPayload
│                       │  4. SHA-256 hash → hex string
│                       │  5. RSA wrap AES key → bytes
│                       │  6. Base64 encode → strings
│                       │  7. Write ciphertext to disk
│                       │  8. Build Document model
│                       │  9. Insert to DB
│                       │ 10. Log audit entry
└──────────┬───────────┘
           │  crypto modules + repositories
           ▼
┌──────────────────────┐
│   DATA ACCESS         │  DocumentRepository.insert(document.to_dict())
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   INFRASTRUCTURE      │  MongoDB insert / File I/O / AES / RSA / SHA-256
└──────────────────────┘
```

Every operation in SDMS follows this same layered traversal, ensuring clear
separation of concerns, testability at each layer, and maintainability.
