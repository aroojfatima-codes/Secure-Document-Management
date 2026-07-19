# SDMS GUI Documentation

> **Secure Document Management System** — Complete GUI screen reference.
> Python 3.11+ | CustomTkinter | Dark/Light Theme | Animated Interfaces

---

## Table of Contents

1. [Login Page](#1-login-page)
2. [Register Page](#2-register-page)
3. [Dashboard Page](#3-dashboard-page)
4. [Documents Page](#4-documents-page)
5. [Upload Page](#5-upload-page)
6. [Download Page](#6-download-page)
7. [Share Page](#7-share-page)
8. [Shared Page](#8-shared-page)
9. [Search Page](#9-search-page)
10. [Face Recognition Page](#10-face-recognition-page)
11. [Audit Page](#11-audit-page)
12. [Settings Page](#12-settings-page)
13. [Profile Page](#13-profile-page)
14. [Document Detail Page](#14-document-detail-page)

---

## 1. Login Page

**File:** `gui/pages/login_page.py` (216 lines)
**Class:** `LoginPage(ctk.CTkFrame)`

### Purpose

Primary entry point for authenticated users. Provides username/password login with optional face recognition and new user registration pathway. Features a glassmorphism card aesthetic with animated floating orb background.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page container | `CTkFrame` | root frame | `fg_color="transparent"`, full width/height | Hosts background and card layers |
| Orb 1 | `CTkLabel` | — | `text="●"`, `font=("Arial", 120)`, `fg_color="#6C63FF"` | Animated purple floating orb (top-left) |
| Orb 2 | `CTkLabel` | — | `text="●"`, `font=("Arial", 90)`, `fg_color="#FF6584"` | Animated pink floating orb (center) |
| Orb 3 | `CTkLabel` | — | `text="●"`, `font=("Arial", 70)`, `fg_color="#43E97B"` | Animated green floating orb (bottom-right) |
| Login card | `CTkFrame` | — | `fg_color=("white", "gray85")`, `corner_radius=20`, `width=400`, `height=520` | Glassmorphism card container |
| App title | `CTkLabel` | — | `text="Secure Document Manager"`, `font=("Helvetica", 22, "bold")` | Application name |
| Subtitle | `CTkLabel` | — | `text="Sign in to your account"`, `font=("Helvetica", 12)`, `fg_color="gray60"` | Subheading text |
| Username entry | `StyledEntry` | — | `placeholder_text="Username"`, `width=320` | Username input field |
| Password entry | `PasswordEntry` | — | `placeholder_text="Password"`, `width=320` | Password input with show/hide toggle |
| Remember me | `CTkCheckBox` | — | `text="Remember Me"`, `font=("Helvetica", 11)` | Persistent session toggle |
| Forgot password | `CTkLabel` | — | `text="Forgot Password?"`, `text_color="#6C63FF"`, cursor="hand2"` | Clickable link (shows info toast) |
| Sign In button | `StyledButton` | — | `text="Sign In"`, `width=320`, `height=40`, `fg_color="#6C63FF"` | Primary login action |
| Divider | `CTkFrame` | — | `height=1`, `fg_color="gray80"` | Visual separator |
| Face login button | `StyledButton` | — | `text="Login with Face ID"`, `width=320`, `fg_color="transparent"`, `border_width=2`, `border_color="#6C63FF"` | Navigate to face login page |
| Register link | `CTkLabel` | — | `text="Don't have an account? Register"`, `text_color="#6C63FF"`, cursor="hand2"` | Navigate to register page |

### Layout

```
┌──────────────────────────────────────────────────┐
│  ○ Orb1 (bouncing, top-left)                     │
│                        ○ Orb2 (bouncing, center)  │
│                                                  │
│          ┌──────────────────────┐                │
│          │  Secure Doc Manager  │                │
│          │  Sign in to account  │                │
│          │                      │                │
│          │  [  Username       ] │                │
│          │  [  Password    👁 ] │                │
│          │  ☑ Remember Me       │                │
│          │     Forgot Password? │                │
│          │                      │                │
│          │  [    Sign In      ] │                │
│          │  ──── or ───────────│                │
│          │  [ Login with Face ] │                │
│          │                      │                │
│          │  Don't have account? │                │
│          │      Register        │                │
│          └──────────────────────┘                │
│                    ○ Orb3 (bouncing, bottom-right)│
└──────────────────────────────────────────────────┘
```

### Navigation

- **Sign In (success):** → `app.show_page("dashboard")`
- **Register link:** → `app.show_page("register")`
- **Face login button:** → `app.show_page("face")`
- **Forgot Password:** Shows `Toast` with "Contact administrator" message

### Backend Integration

- Calls `AuthController.handle_login(username, password)` on Sign In click
- On success: stores user in `SessionManager`, navigates to dashboard
- On failure: shows `ErrorDialog` with server message
- Remember Me checkbox: if checked, `SessionManager` persists token across restarts

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Username | Required, non-empty after strip | "Please enter your username" |
| Password | Required, non-empty after strip | "Please enter your password" |

### Visual Design

- **Background:** Three animated floating orbs with sine-wave motion
  - Orb 1: Purple (`#6C63FF`), radius 120, amplitude 30px, period 6s
  - Orb 2: Pink (`#FF6584`), radius 90, amplitude 20px, period 8s
  - Orb 3: Green (`#43E97B`), radius 70, amplitude 25px, period 7s
  - Animation uses `after(50, animate)` recursive scheduling
  - Each orb moves in x and y with `sin(time * speed) * amplitude`
- **Card:** Glassmorphism effect via layered semi-transparent frames
  - Outer frame: `fg_color=("white", "gray85")`, `corner_radius=20`
  - Slight opacity simulation with dual-layer approach (main + inner tinted frame)
- **Animations:**
  - Card fades in on page load via `gui.animations.fade_in(card, duration=400)`
  - Orbs start animating on `<Map>` event (page becomes visible)
  - Orbs stop animating on page change (timer cancelled)
- **Color scheme:** Purple primary (`#6C63FF`), white/dark glass, gray text
- **Font hierarchy:** Title 22pt bold, subtitle 12pt regular, inputs 13pt

---

## 2. Register Page

**File:** `gui/pages/register_page.py` (188 lines)
**Class:** `RegisterPage(ctk.CTkFrame)`

### Purpose

New user registration form with real-time password strength validation and comprehensive input fields. Scrollable to accommodate all fields on smaller screens.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Scroll container | `SmoothScrollFrame` | — | `fg_color="transparent"` | Scrollable page wrapper |
| Page header | `PageHeader` | — | `title="Create Account"`, `subtitle="Join Secure Document Manager"` | Page title section |
| Username entry | `StyledEntry` | — | `placeholder_text="Username"`, `width=400` | Unique username input |
| Full name entry | `StyledEntry` | — | `placeholder_text="Full Name"`, `width=400` | Display name input |
| Email entry | `StyledEntry` | — | `placeholder_text="Email Address"`, `width=400` | Email input |
| Role combo | `StyledComboBox` | — | `values=["User", "Admin"]`, `width=400` | Role selection |
| Password entry | `PasswordEntry` | — | `placeholder_text="Password"`, `width=400` | Password input |
| Strength meter frame | `CTkFrame` | — | `height=6`, `fg_color="gray80"` | Strength bar background |
| Strength segment 1 | `CTkFrame` | — | `height=6`, `width=75` | Red segment (min length) |
| Strength segment 2 | `CTkFrame` | — | `height=6`, `width=75` | Orange segment (has upper) |
| Strength segment 3 | `CTkFrame` | — | `height=6`, `width=75` | Yellow segment (has digit) |
| Strength segment 4 | `CTkFrame` | — | `height=6`, `width=75` | Green segment (has special) |
| Strength label | `CTkLabel` | — | `text=""`, `font=("Helvetica", 10)` | Strength description text |
| Confirm password | `PasswordEntry` | — | `placeholder_text="Confirm Password"`, `width=400` | Password confirmation |
| Terms checkbox | `CTkCheckBox` | — | `text="I agree to the Terms of Service"`, `font=("Helvetica", 11)` | Terms acceptance |
| Register button | `StyledButton` | — | `text="Create Account"`, `width=400`, `height=42`, `fg_color="#6C63FF"` | Submit registration |
| Login link | `CTkLabel` | — | `text="Already have an account? Sign In"`, `text_color="#6C63FF"`, cursor="hand2"` | Navigate to login |

### Layout

```
┌──────────────────────────────────────────────────┐
│         Create Account                           │
│    Join Secure Document Manager                  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  [  Username                          ]    │  │
│  │  [  Full Name                         ]    │  │
│  │  [  Email Address                     ]    │  │
│  │  [  Role          ▼  User/Admin       ]    │  │
│  │  [  Password                          ]    │  │
│  │  ██████████████████████████████████████    │  │
│  │  Strength: Strong                          │  │
│  │  [  Confirm Password                  ]    │  │
│  │  ☑ I agree to Terms of Service             │  │
│  │                                            │  │
│  │  [      Create Account                  ]  │  │
│  │                                            │  │
│  │  Already have account? Sign In             │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### Navigation

- **Sign In link:** → `app.show_page("login")`
- **Successful registration:** → `app.show_page("login")` + `SuccessDialog` ("Account created successfully")

### Backend Integration

- Calls `AuthController.handle_register(data)` where `data` is a dict:
  ```python
  {"username", "full_name", "email", "role", "password"}
  ```
- On success: navigates to login with success message
- On failure: shows `ErrorDialog` with validation or server error

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| Username | Required, 3–20 chars, alphanumeric + underscore only | "Username must be 3-20 characters" |
| Full Name | Required, 2–100 chars, letters + spaces only | "Please enter your full name" |
| Email | Required, valid format: `^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$` | "Please enter a valid email" |
| Role | Required, must be "User" or "Admin" | "Please select a role" |
| Password | Required, min 8 chars | "Password must be at least 8 characters" |
| Password | At least 1 uppercase letter | "Include an uppercase letter" |
| Password | At least 1 lowercase letter | "Include a lowercase letter" |
| Password | At least 1 digit | "Include a number" |
| Password | At least 1 special character `!@#$%^&*` | "Include a special character" |
| Confirm | Must match password | "Passwords do not match" |
| Terms | Checkbox must be checked | "You must agree to the terms" |

### Visual Design

- **Password strength meter:** 4 horizontal segments, each fills with color progressively:
  - Segment 1 (red `#FF6B6B`): ≥ 8 characters
  - Segment 2 (orange `#FFA726`): contains uppercase letter
  - Segment 3 (yellow `#FFEE58`): contains digit
  - Segment 4 (green `#66BB6A`): contains special character
  - Label updates: "Weak" → "Fair" → "Good" → "Strong"
  - Real-time update via `<Key>` binding on password entry
- **Scrollable:** `SmoothScrollFrame` enables scrolling on screens shorter than ~700px
- **Card style:** Consistent with login page, centered 400px-wide form

---

## 3. Dashboard Page

**File:** `gui/pages/dashboard_page.py` (209 lines)
**Class:** `DashboardPage(ctk.CTkFrame)`

### Purpose

Main landing page after login. Provides an overview of the user's document ecosystem with statistics, charts, quick actions, and recent activity.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page container | `SmoothScrollFrame` | — | `fg_color="transparent"` | Scrollable wrapper |
| Welcome header | `CTkLabel` | — | `text="Good Morning, username"`, `font=("Helvetica", 26, "bold")` | Time-based greeting |
| Subtitle | `CTkLabel` | — | `text="Here's your document overview"`, `fg_color="gray60"` | Greeting subtitle |
| Stat card 1 | `StatCard` | "total_docs" | `title="Total Documents"`, `icon="📁"`, `color="#6C63FF"` | Document count |
| Stat card 2 | `StatCard` | "shared" | `title="Shared With Me"`, `icon="🔗"`, `color="#43E97B"` | Incoming shares count |
| Stat card 3 | `StatCard` | "storage" | `title="Storage Used"`, `icon="💾"`, `color="#FF6584"` | Total storage size |
| Stat card 4 | `StatCard` | "status" | `title="Account Status"`, `icon="✅"`, `color="#FFD93D"` | Account health |
| Donut chart | `DonutChart` | — | `size=200`, `center_text="Types"` | Document type distribution |
| Donut legend | `CTkFrame` | — | `fg_color="transparent"` | Color-coded legend for donut |
| Bar chart | `BarChart` | — | `width=300`, `height=150` | Monthly upload trends |
| Quick actions header | `CTkLabel` | — | `text="Quick Actions"`, `font=("Helvetica", 18, "bold")` | Section header |
| Action card 1 | `ActionCard` | — | `title="Upload"`, `icon="📤"`, `color="#6C63FF"` | Navigate to upload |
| Action card 2 | `ActionCard` | — | `title="Search"`, `icon="🔍"`, `color="#43E97B"` | Navigate to search |
| Action card 3 | `ActionCard` | — | `title="Share"`, `icon="🔗"`, `color="#FF6584"` | Navigate to share |
| Action card 4 | `ActionCard` | — | `title="Face ID"`, `icon="👤"`, `color="#FFD93D"` | Navigate to face page |
| Activity header | `CTkLabel` | — | `text="Recent Activity"`, `font=("Helvetica", 18, "bold")` | Section header |
| Activity row ×5 | `CTkFrame` | — | `fg_color=("gray95", "gray20")` | Recent audit log entries |
| Activity icon | `CTkLabel` | — | per row | Action icon |
| Activity text | `CTkLabel` | — | per row | "You uploaded report.pdf" |
| Activity time | `CTkLabel` | — | per row, `fg_color="gray60"` | "2 minutes ago" |
| System status header | `CTkLabel` | — | `text="System Status"`, `font=("Helvetica", 18, "bold")` | Section header |
| Encryption badge | `StatusBadge` | — | `status="active"`, `text="AES-256 + RSA-2048"` | Encryption status indicator |
| Database badge | `StatusBadge` | — | `status="active"`, `text="MongoDB Connected"` | Database connection status |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Good Morning, username                              │
│  Here's your document overview                       │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ 📁 Total │ │ 🔗 Shared│ │ 💾 Store │ │ ✅ Acct│ │
│  │   Docs   │ │  With Me │ │   Used   │ │ Status │ │
│  │    12    │ │     5    │ │  45.2MB  │ │ Active │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│                                                      │
│  ┌────────────────────┐  ┌────────────────────────┐  │
│  │   Donut Chart      │  │    Bar Chart           │  │
│  │  (Doc Types)       │  │  (Monthly Uploads)     │  │
│  │   ┌───┐            │  │  █                     │  │
│  │  │ 42%│ PDF        │  │  █ █    █              │  │
│  │  │   │             │  │  █ █ █  █  █           │  │
│  │   └───┘            │  │  Jan Feb Mar Apr May   │  │
│  │  28% DOC  30% IMG  │  │                        │  │
│  └────────────────────┘  └────────────────────────┘  │
│                                                      │
│  Quick Actions                                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │Upload│ │Search│ │Share │ │FaceID│              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                      │
│  Recent Activity                                     │
│  📤 You uploaded report.pdf          2 min ago       │
│  📥 You downloaded data.csv          15 min ago      │
│  🔗 You shared notes.doc with bob    1 hour ago      │
│  🔍 You searched for "project"       2 hours ago     │
│  👤 You logged in                     3 hours ago     │
│                                                      │
│  System Status                                       │
│  ✅ AES-256 + RSA-2048    ✅ MongoDB Connected       │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Upload action card:** → `app.show_page("upload")`
- **Search action card:** → `app.show_page("search")`
- **Share action card:** → `app.show_page("share")`
- **Face ID action card:** → `app.show_page("face")`

### Backend Integration

- Calls `DocumentController.handle_get_stats()` on page show:
  - Returns `total_documents`, `shared_count`, `storage_used`, `documents_by_type` (dict), `monthly_uploads` (dict)
- Calls `DocumentController.handle_get_activity()` for recent feed:
  - Returns last 5 `AuditLog` entries
- Stat cards, charts, and activity feed populate from response data
- System status checks: `DatabaseManager.instance().is_connected()`, always shows encryption status

### Validation Rules

- No input validation (read-only dashboard)
- Gracefully handles empty data (shows "No documents yet" placeholder)

### Visual Design

- **Greeting logic:** Time-based greeting:
  - `hour < 12` → "Good Morning"
  - `hour < 17` → "Good Afternoon"
  - `hour >= 17` → "Good Evening"
- **Stat cards:** Entrance animation via `gui.animations.fade_in()` with staggered delays (0ms, 100ms, 200ms, 300ms)
- **Charts:** Canvas-based rendering with theme-aware colors
  - Donut: segments colored by document type (PDF=red, DOC=blue, IMG=green, etc.)
  - Bar: gradient fill from primary color to lighter shade
- **Activity feed:** Each row has subtle hover effect (background lightens)
- **Responsive:** Grid layout with `weight=1` columns for cards

---

## 4. Documents Page

**File:** `gui/pages/documents_page.py` (250 lines)
**Class:** `DocumentsPage(ctk.CTkFrame)`

### Purpose

Primary document management view with toggle between grid (card-based) and table (spreadsheet) display modes. Supports search, sort, and context-menu actions.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="My Documents"`, action_button_text="Upload"` | Title + upload shortcut |
| Search entry | `StyledEntry` | — | `placeholder_text="Search documents..."`, `width=300` | Live search filter |
| View toggle | `StyledButton` | — | `text="☰ Table"` / `text="▦ Grid"` | Switch between views |
| Table view | `StyledTable` | — | `columns=["ID","Filename","Type","Size","Owner","Shared","Date"]` | Tabular document list |
| Grid container | `CTkFrame` | — | `fg_color="transparent"` | Grid card layout wrapper |
| Grid card ×N | `CTkFrame` | — | `width=160`, `corner_radius=12` | Individual document card |
| Card icon | `CTkLabel` | — | `font=("Arial", 36)` | File type emoji icon |
| Card filename | `CTkLabel` | — | `font=("Helvetica", 12, "bold")`, `wraplength=140` | Truncated filename |
| Card meta | `CTkLabel` | — | `font=("Helvetica", 10)`, `fg_color="gray60"` | "PDF · 2.4 MB · Jan 15" |
| Context menu | `CTkMenu` | — | `values=["Download", "Share", "View Details", "Delete"]` | Right-click actions |
| Empty state | `CTkLabel` | — | `text="No documents found"`, `font=("Helvetica", 14)` | Shown when list is empty |

### Layout

**Table View:**
```
┌──────────────────────────────────────────────────────┐
│  My Documents                    [Upload]            │
│  [Search documents...         ] [☰ Table]           │
│                                                      │
│  ID     │ Filename     │ Type │ Size  │ Owner │ ...  │
│  ───────┼──────────────┼──────┼───────┼───────┼────  │
│  DOC-001│ report.pdf   │ PDF  │ 2.4MB │ alice │ ...  │
│  DOC-002│ data.xlsx    │ XLSX │ 890KB │ alice │ ...  │
│  DOC-003│ photo.png    │ PNG  │ 5.1MB │ bob   │ ...  │
│                                                      │
│  Right-click menu:                                   │
│  ┌──────────────────┐                               │
│  │ 📥 Download      │                               │
│  │ 🔗 Share         │                               │
│  │ 👁 View Details  │                               │
│  │ 🗑 Delete        │                               │
│  └──────────────────┘                               │
└──────────────────────────────────────────────────────┘
```

**Grid View:**
```
┌──────────────────────────────────────────────────────┐
│  My Documents                    [Upload]            │
│  [Search documents...         ] [▦ Grid]           │
│                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │  📄    │ │  📊    │ │  🖼    │ │  📝    │       │
│  │ report │ │ data   │ │ photo  │ │ notes  │       │
│  │  .pdf  │ │ .xlsx  │ │  .png  │ │  .doc  │       │
│  │ 2.4MB  │ │ 890KB  │ │ 5.1MB  │ │ 120KB  │       │
│  │ Jan 15 │ │ Jan 14 │ │ Jan 13 │ │ Jan 12 │       │
│  └────────┘ └────────┘ └────────┘ └────────┘       │
│  ┌────────┐                                         │
│  │  📁    │                                         │
│  │ backup │                                         │
│  │  .zip  │                                         │
│  │ 12MB   │                                         │
│  │ Jan 11 │                                         │
│  └────────┘                                         │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Upload button:** → `app.show_page("upload")`
- **Context menu "Download":** → `app.show_page("download")` + sets selected doc
- **Context menu "Share":** → `app.show_page("share")` + sets selected doc
- **Context menu "View Details":** → `app.show_page("document_detail")` + passes doc_id

### Backend Integration

- Calls `DocumentController.handle_list_documents()` on page show
- Search: filters loaded data locally with regex (`re.search(query, filename, re.IGNORECASE)`)
- Context menu actions delegate to `DocumentController` methods
- Page refreshes data on every `on_show()` callback

### Validation Rules

- Search: client-side regex filter, no minimum query length
- Delete: shows `ConfirmDialog` ("Are you sure you want to delete {filename}?")
- Grid card click: selects the document (visual highlight)

### Visual Design

- **File type icons:** Mapped by extension:
  - `.pdf` → `📄` (red tint `#FF6B6B`)
  - `.doc`, `.docx` → `📝` (blue tint `#4A90D9`)
  - `.xls`, `.xlsx` → `📊` (green tint `#43E97B`)
  - `.png`, `.jpg`, `.jpeg`, `.gif` → `🖼` (purple tint `#9B59B6`)
  - `.txt` → `📃` (gray tint `#95A5A6`)
  - `.zip`, `.rar` → `📦` (orange tint `#FFA726`)
  - Default → `📄`
- **Table:** Alternating row colors (`gray95`/`gray90` in dark mode), column header click sorts ascending/descending
- **Grid cards:** `width=160`, `height=180`, `corner_radius=12`, hover effect (background lightens + 2px scale via animation)
- **Context menu:** Appears at cursor position on right-click, styled with theme colors
- **View toggle:** Icon changes between `☰` (table) and `▦` (grid)
- **Live search:** Typing in search entry triggers filter after 300ms debounce

---

## 5. Upload Page

**File:** `gui/pages/upload_page.py` (272 lines)
**Class:** `UploadPage(ctk.CTkFrame)`

### Purpose

Document upload interface with drag-and-drop zone, file metadata form, progress tracking, and success confirmation.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Upload Document"` | Page title |
| Drag-drop zone | `CTkFrame` | — | `border_width=2`, `border_style="dashed"`, `border_color="gray60"`, `corner_radius=16` | Drop target / click to browse |
| Drop icon | `CTkLabel` | — | `text="📤"`, `font=("Arial", 48)` | Upload icon |
| Drop text | `CTkLabel` | — | `text="Drop file here or click to browse"` | Instruction text |
| File info frame | `CTkFrame` | — | `fg_color=("gray95", "gray20")`, `corner_radius=10` | Selected file details |
| File name label | `CTkLabel` | — | `font=("Helvetica", 13, "bold")` | Selected filename |
| File size label | `CTkLabel` | — | `fg_color="gray60"` | File size (human-readable) |
| File type label | `CTkLabel` | — | `fg_color="gray60"` | MIME type / extension |
| Description entry | `StyledText` | — | `height=80`, `width=400`, `placeholder_text="Add a description..."` | Document description |
| Tags entry | `StyledEntry` | — | `placeholder_text="Tags (comma-separated)"`, `width=400` | Comma-separated tags |
| Progress frame | `CTkFrame` | — | `fg_color="transparent"`, initially hidden | Progress display |
| Progress label | `CTkLabel` | — | `text="Encrypting..."` | Current phase text |
| Progress bar | `AnimatedProgressBar` | — | `width=400`, `height=12` | Visual progress indicator |
| Upload button | `StyledButton` | — | `text="Upload & Encrypt"`, `width=400`, `height=44`, `fg_color="#6C63FF"` | Start upload process |
| Success frame | `CTkFrame` | — | initially hidden | Post-upload confirmation |
| Success icon | `CTkLabel` | — | `text="✅"`, `font=("Arial", 48)` | Success indicator |
| Success title | `CTkLabel` | — | `text="Upload Successful!"`, `font=("Helvetica", 20, "bold")` | Success heading |
| Success detail | `CTkLabel` | — | `text="DOC-XXXX encrypted and saved"` | Doc ID reference |
| View documents btn | `StyledButton` | — | `text="View Documents"` | Navigate to documents |
| Upload another btn | `StyledButton` | — | `text="Upload Another"`, `fg_color="transparent"`, `border_width=2` | Reset form |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Upload Document                                     │
│                                                      │
│  ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐  │
│  │  📤                                            │  │
│  │  Drop file here or click to browse             │  │
│  │  (dashed border, 200px tall)                   │  │
│  └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘  │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 📄 report.pdf  ·  2.4 MB  ·  PDF            │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  Description:                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │ (multiline text area)                         │   │
│  └──────────────────────────────────────────────┘   │
│  Tags: [project, report, 2024                   ]   │
│                                                      │
│  Encrypting...                                      │
│  ████████████████████████████░░░░░  78%             │
│                                                      │
│  [        Upload & Encrypt                        ]  │
│                                                      │
│  ── OR (after success) ──                            │
│                                                      │
│              ✅                                      │
│       Upload Successful!                             │
│     DOC-0042 encrypted and saved                     │
│                                                      │
│  [ View Documents ]  [ Upload Another ]              │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **View Documents (post-upload):** → `app.show_page("documents")`
- **Upload Another:** Resets form to initial state (no navigation)
- **Drag-drop click:** Opens `filedialog.askopenfilename()`

### Backend Integration

- Calls `DocumentController.handle_upload(file_path, description, tags)` on Upload click
- Progress updates are simulated in phases:
  1. "Computing hash..." → 10-20%
  2. "Generating encryption keys..." → 20-40%
  3. "Encrypting file (AES-256)..." → 40-70%
  4. "Encrypting key (RSA-2048)..." → 70-85%
  5. "Saving to storage..." → 85-95%
  6. "Recording metadata..." → 95-100%
- Each phase uses `after()` with delays to simulate real processing time
- Actual encryption happens in the service layer (not blocking GUI)

### Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| File | Must be selected before upload | `ErrorDialog`: "Please select a file" |
| Description | Optional (max 500 chars) | Warning if over limit |
| Tags | Optional, comma-separated | Parsed and stripped automatically |
| File size | Configurable max (default 100MB) | `ErrorDialog`: "File exceeds maximum size" |

### Visual Design

- **Drag-drop zone:** Dashed border (`border_style="dashed"`, `border_width=2`)
  - Hover state: `border_color="#6C63FF"`, background lightens
  - Drag-over state: `border_color="#43E97B"`, pulse animation
  - Drop state: validates file, shows file info frame
- **File info:** Animated slide-in from top when file selected
- **Progress bar:** `AnimatedProgressBar` with smooth interpolation between values
  - Color transitions: blue → purple → green as progress increases
  - Percentage label updates alongside bar fill
- **Success frame:** `fade_in()` animation with scale effect on checkmark icon
- **Phases shown as:** "Encrypting..." text updates per phase

---

## 6. Download Page

**File:** `gui/pages/download_page.py` (182 lines)
**Class:** `DownloadPage(ctk.CTkFrame)`

### Purpose

Document download interface showing available documents, download progress, and post-download file access options.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Download Documents"` | Page title |
| Document table | `StyledTable` | — | `columns=["ID","Filename","Type","Size","Owner","Date"]` | List of downloadable docs |
| Selection info | `CTkLabel` | — | `text="Select a document to download"` | Selection prompt |
| Download button | `StyledButton` | — | `text="Download & Decrypt"`, `width=300`, `height=42`, `fg_color="#6C63FF"` | Start download |
| Progress frame | `CTkFrame` | — | `fg_color="transparent"`, initially hidden | Progress display |
| Progress label | `CTkLabel` | — | `text="Decrypting..."` | Current phase text |
| Progress bar | `AnimatedProgressBar` | — | `width=400`, `height=12` | Download/decrypt progress |
| Post-download frame | `CTkFrame` | — | initially hidden | Post-download actions |
| Open file button | `StyledButton` | — | `text="📂 Open File"` | Open downloaded file |
| Open folder button | `StyledButton` | — | `text="📁 Open Folder"` | Open download directory |
| Download another | `StyledButton` | — | `text="Download Another"`, `fg_color="transparent"` | Reset for next download |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Download Documents                                  │
│                                                      │
│  ID     │ Filename      │ Type │ Size  │ Owner       │
│  ───────┼───────────────┼──────┼───────┼───────      │
│  DOC-001│ report.pdf    │ PDF  │ 2.4MB │ alice       │
│  DOC-002│ data.xlsx     │ XLSX │ 890KB │ alice    ◄── selected
│  DOC-003│ photo.png     │ PNG  │ 5.1MB │ bob        │
│                                                      │
│  Selected: DOC-002 - data.xlsx                       │
│                                                      │
│  [      Download & Decrypt                         ] │
│                                                      │
│  Decrypting key (RSA-2048)...                        │
│  ████████████████████████████████░░░  85%            │
│                                                      │
│  ── OR (after download) ──                           │
│                                                      │
│  ✅ Download complete!                               │
│  [ 📂 Open File ]  [ 📁 Open Folder ]               │
│  [        Download Another                         ] │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Open File:** Opens file using `os.startfile(downloaded_path)` (Windows) or `subprocess.Popen(["open", path])` (macOS)
- **Open Folder:** Opens download directory via `os.startfile("download/")` or `subprocess.Popen(["explorer", download_dir])`
- **Download Another:** Resets to table view

### Backend Integration

- Calls `DocumentController.handle_list_documents()` on page show to populate table
- Calls `DocumentController.handle_download(doc_id)` on Download click
- Progress phases:
  1. "Verifying access..." → 5-15%
  2. "Decrypting key (RSA-2048)..." → 15-40%
  3. "Decrypting file (AES-256)..." → 40-80%
  4. "Verifying integrity (SHA-256)..." → 80-95%
  5. "Saving..." → 95-100%
- Downloaded file saved to `download/` directory

### Validation Rules

| Check | Rule | Error |
|-------|------|-------|
| Row selection | Must select a row before download | `ErrorDialog`: "Please select a document" |
| Access | Must be owner or shared user | `ErrorDialog`: "Access denied" |

### Visual Design

- **Table:** Same styled table as Documents Page with row selection highlighting
- **Progress bar:** Color transitions: blue (decrypting) → green (complete)
- **Post-download frame:** `fade_in()` animation, shows file path in success detail
- **Button states:** Download button disabled when no row selected, re-enabled after

---

## 7. Share Page

**File:** `gui/pages/share_page.py` (146 lines)
**Class:** `SharePage(ctk.CTkFrame)`

### Purpose

Share documents with other users. Select a document, specify recipient and permissions, and manage existing shares.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Share Documents"` | Page title |
| Document table | `StyledTable` | — | `columns=["ID","Filename","Type","Size","Date"]` | Select document to share |
| Share form frame | `CTkFrame` | — | `fg_color=("gray95", "gray20")`, `corner_radius=12` | Share input container |
| Recipient entry | `StyledEntry` | — | `placeholder_text="Recipient username"`, `width=250` | Username of recipient |
| Permission combo | `StyledComboBox` | — | `values=["View Only", "View & Download"]` | Access level |
| Share button | `StyledButton` | — | `text="Share Document"`, `fg_color="#43E97B"` | Execute share |
| Current shares header | `CTkLabel` | — | `text="Currently Shared With:"` | Section label |
| Share entry ×N | `CTkFrame` | — | `fg_color="transparent"` | Per-user share row |
| Share username | `CTkLabel` | — | per row | Recipient name |
| Share permission | `StatusBadge` | — | per row | "View" or "Download" badge |
| Revoke button | `StyledButton` | — | per row, `fg_color="#FF6B6B"`, `text="Revoke"` | Remove share |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Share Documents                                     │
│                                                      │
│  ID     │ Filename      │ Type │ Size  │ Date        │
│  ───────┼───────────────┼──────┼───────┼──────       │
│  DOC-001│ report.pdf    │ PDF  │ 2.4MB │ Jan 15  ◄── selected
│  DOC-002│ data.xlsx     │ XLSX │ 890KB │ Jan 14      │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Share with:                                    │ │
│  │  [Recipient username          ]                 │ │
│  │  Permission: [View Only ▼]                      │ │
│  │                                                 │ │
│  │  [Share Document]                               │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  Currently Shared With:                              │
│  ┌─────────────────────────────────────────────────┐ │
│  │ 👤 bob     [View & Download] [Revoke]           │ │
│  │ 👤 charlie [View Only]       [Revoke]           │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Navigation

- No page transitions (stays on share page)
- Successful share: refreshes "Currently Shared With" list
- Successful revoke: removes entry from list with `fade_out()` animation

### Backend Integration

- Calls `DocumentController.handle_list_documents()` on show (own documents only)
- Calls `DocumentController.handle_share(doc_id, username, permission)` on Share click
- Calls `DocumentController.handle_revoke(doc_id, username)` on Revoke click
- After share/revoke: refreshes current shares list

### Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| Document | Must select a document | `ErrorDialog`: "Please select a document" |
| Recipient | Required, non-empty | `ErrorDialog`: "Please enter a username" |
| Recipient | Cannot be self | `ErrorDialog`: "Cannot share with yourself" |
| Recipient | Must exist in system | `ErrorDialog`: "User not found" |
| Recipient | Must not already have access | `WarningDialog`: "Already shared with this user" |
| Permission | Must select one | `ErrorDialog`: "Please select permission level" |

### Visual Design

- **Share form:** Highlighted card (`fg_color` slightly different from background)
- **Current shares:** Each share row has avatar initial circle + username + permission badge + revoke button
- **Revoke button:** Red (`#FF6B6B`), shows `ConfirmDialog` before executing
- **Share success:** `Toast` notification ("Document shared successfully with {username}")
- **Revoke success:** `Toast` notification ("Access revoked for {username}")

---

## 8. Shared Page

**File:** `gui/pages/shared_page.py` (116 lines)
|  Revoke success | `Toast` notification ("Access revoked for {username}")

---

## 8. Shared Page

**File:** `gui/pages/shared_page.py` (116 lines)
**Class:** `SharedPage(ctk.CTkFrame)`

### Purpose

View documents shared with you and documents you've shared with others. Filter between incoming and outgoing shares.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Shared Documents"` | Page title |
| Filter combo | `StyledComboBox` | — | `values=["Shared With Me", "Shared By Me"]` | Share direction filter |
| Search entry | `StyledEntry` | — | `placeholder_text="Search shared documents..."` | Search within results |
| Table | `StyledTable` | — | `columns=["ID","Filename","Owner","Permission","Shared Date"]` | Shared documents list |
| Revoke button | `StyledButton` | — | `text="Revoke Access"`, `fg_color="#FF6B6B"`, initially disabled | Remove share (owner only) |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Shared Documents                                    │
│                                                      │
│  Filter: [Shared With Me ▼]  [Search...]             │
│                                                      │
│  ID     │ Filename     │ Owner/To │ Permission │ Date│
│  ───────┼──────────────┼──────────┼────────────┼─────│
│  DOC-003│ photo.png    │ bob      │ View Only  │ 1/14│
│  DOC-005│ notes.doc    │ alice    │ Download   │ 1/13│
│                                                      │
│  [Revoke Access]  (enabled only in "Shared By Me")  │
└──────────────────────────────────────────────────────┘
```

### Navigation

- No page transitions (stays on shared page)
- Revoke updates the table in place

### Backend Integration

- Calls `DocumentController.handle_list_documents()` on show and filter change
- Filter "Shared With Me": shows documents where user is in `shared_users`
- Filter "Shared By Me": shows documents where user is `owner` with `shared_users` non-empty
- Revoke calls `DocumentController.handle_revoke(doc_id, recipient_username)`

### Validation Rules

| Check | Rule | Error |
|-------|------|-------|
| Row selection | Must select a row for revoke | Button stays disabled |
| Filter mode | Revoke only in "Shared By Me" | Button disabled in "Shared With Me" |

### Visual Design

- **Filter combo:** Changing filter triggers full table refresh
- **Revoke button:** Disabled (grayed out) unless: a row is selected AND filter is "Shared By Me"
- **Table columns:** "Owner" shows the owner name (Shared With Me) or recipient name (Shared By Me)
- **Empty state:** "No shared documents found" centered message

---

## 9. Search Page

**File:** `gui/pages/search_page.py` (210 lines)
**Class:** `SearchPage(ctk.CTkFrame)`

### Purpose

Advanced document search with multiple search modes and result display.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Search Documents"` | Page title |
| Search mode frame | `CTkFrame` | — | `fg_color="transparent"` | Radio button container |
| Mode: Filename | `CTkRadioButton` | — | `text="Filename"`, `value="filename"`, `variable=search_mode` | Search by filename |
| Mode: Type | `CTkRadioButton` | — | `text="Type"`, `value="type"`, `variable=search_mode` | Search by file type |
| Mode: Owner | `CTkRadioButton` | — | `text="Owner"`, `value="owner"`, `variable=search_mode` | Search by owner |
| Mode: All | `CTkRadioButton` | — | `text="All Fields"`, `value="all"`, `variable=search_mode` | Search all fields |
| Search entry | `StyledEntry` | — | `placeholder_text="Enter search term..."`, `width=350` | Search query input |
| Search button | `StyledButton` | — | `text="Search"`, `width=120`, `fg_color="#6C63FF"` | Execute search |
| Results count | `CTkLabel` | — | `text=""`, `fg_color="gray60"` | "Found 5 documents" |
| Results table | `StyledTable` | — | `columns=["ID","Filename","Type","Size","Owner","Shared","Date"]` | Search results |
| Empty state | `CTkLabel` | — | `text="No results found"` | Shown when 0 results |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Search Documents                                    │
│                                                      │
│  Search by:                                          │
│  (●) Filename  (○) Type  (○) Owner  (○) All Fields  │
│                                                      │
│  [Enter search term...                      ] [Search]│
│                                                      │
│  Found 3 documents                                   │
│                                                      │
│  ID     │ Filename      │ Type │ Size  │ Owner       │
│  ───────┼───────────────┼──────┼───────┼───────      │
│  DOC-001│ report.pdf    │ PDF  │ 2.4MB │ alice       │
│  DOC-004│ report_v2.pdf │ PDF  │ 3.1MB │ alice       │
│  DOC-007│ summary.pdf   │ PDF  │ 150KB │ bob         │
└──────────────────────────────────────────────────────┘
```

### Navigation

- No page transitions from this page
- Results table supports right-click context menu (Download, View Details)

### Backend Integration

- Calls `DocumentController.handle_search(query, mode)` on Search button click or Enter key
- `mode` is one of: `"filename"`, `"type"`, `"owner"`, `"all"`
- Results populate the table immediately
- Default mode: "Filename" selected on page load

### Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| Search query | Required, non-empty after strip | `Toast`: "Please enter a search term" |
| Search query | Min 2 characters | `Toast`: "Search term too short" |

### Visual Design

- **Radio buttons:** Custom-styled with theme accent color for selected state
- **Search entry:** Enter key bound to search execution
- **Results count:** Updates dynamically: "Found {n} documents" or "No documents found"
- **Table:** Same styled table as Documents Page, results fade in after search

---

## 10. Face Recognition Page

**File:** `gui/pages/face_page.py` (261 lines)
**Class:** `FacePage(ctk.CTkFrame)`

### Purpose

Biometric face enrollment and verification interface using OpenCV camera feed.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Face Recognition"` | Page title |
| **Left column (Enroll):** | | | | |
| Enroll header | `CTkLabel` | — | `text="Enroll Face"`, `font=("Helvetica", 16, "bold")` | Section header |
| Username entry | `StyledEntry` | — | `placeholder_text="Your username"`, `width=280` | Identify user to enroll |
| Camera frame (enroll) | `CTkLabel` | — | `width=320`, `height=240`, `fg_color="black"` | Live camera preview |
| Start camera btn | `StyledButton` | — | `text="Start Camera"`, `width=140` | Activate camera |
| Stop camera btn | `StyledButton` | — | `text="Stop Camera"`, `width=140`, `fg_color="#FF6B6B"` | Deactivate camera |
| Enroll button | `StyledButton` | — | `text="Enroll Face"`, `width=280`, `fg_color="#43E97B"` | Capture & enroll |
| Enroll spinner | `LoadingSpinner` | — | initially hidden | Processing indicator |
| Enroll status | `CTkLabel` | — | `text=""` | Success/failure message |
| **Right column (Verify):** | | | | |
| Verify header | `CTkLabel` | — | `text="Verify Identity"`, `font=("Helvetica", 16, "bold")` | Section header |
| Camera frame (verify) | `CTkLabel` | — | `width=320`, `height=240`, `fg_color="black"` | Live camera preview |
| Start camera btn | `StyledButton` | — | `text="Start Camera"`, `width=140` | Activate camera |
| Stop camera btn | `StyledButton` | — | `text="Stop Camera"`, `width=140`, `fg_color="#FF6B6B"` | Deactivate camera |
| Verify button | `StyledButton` | — | `text="Verify Face"`, `width=280`, `fg_color="#6C63FF"` | Capture & verify |
| Verify spinner | `LoadingSpinner` | — | initially hidden | Processing indicator |
| Result frame | `CTkFrame` | — | initially hidden | Verification result |
| Result icon | `CTkLabel` | — | `font=("Arial", 36)` | ✅ or ❌ |
| Result text | `CTkLabel` | — | `font=("Helvetica", 14)` | "Welcome, {username}!" or "Not recognized" |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Face Recognition                                    │
│                                                      │
│  ┌─ Enroll Face ─────────┐  ┌─ Verify Identity ───┐ │
│  │                        │  │                      │ │
│  │ [Your username      ]  │  │                      │ │
│  │                        │  │                      │ │
│  │ ┌──────────────────┐  │  │ ┌──────────────────┐ │ │
│  │ │                  │  │  │ │                  │ │ │
│  │ │  Camera Preview  │  │  │ │  Camera Preview  │ │ │
│  │ │    (320×240)     │  │  │ │    (320×240)     │ │ │
│  │ │                  │  │  │ │                  │ │ │
│  │ └──────────────────┘  │  │ └──────────────────┘ │ │
│  │                        │  │                      │ │
│  │ [Start] [Stop]        │  │ [Start] [Stop]       │ │
│  │                        │  │                      │ │
│  │ [    Enroll Face    ]  │  │ [   Verify Face    ] │ │
│  │                        │  │                      │ │
│  │  ⏳ Processing...     │  │  ⏳ Processing...     │ │
│  │                        │  │                      │ │
│  │  ✅ Face enrolled!    │  │  ┌──────────────────┐ │ │
│  │                        │  │  │ ✅ Welcome, bob! │ │ │
│  │                        │  │  └──────────────────┘ │ │
│  └────────────────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Successful verify (auto-login):** → `app.show_page("dashboard")` + session created
- No manual navigation on enroll success

### Backend Integration

- Camera: `cv2.VideoCapture(0)` with `after(30)` refresh loop
  - Frame: BGR → RGB conversion → PIL Image → `CTkImage` → displayed in `CTkLabel`
- **Enroll:** Calls `FaceController.handle_enroll(username, frame)`
  - Sends the current OpenCV frame (numpy array) to controller
  - Controller delegates to `FaceRecognitionService.enroll_face()`
- **Verify:** Calls `FaceController.handle_verify(frame)`
  - Sends the current frame for recognition
  - On success: `SessionManager.instance().create_session(user)` for auto-login
  - On success: navigates to dashboard after 1.5s delay (allows user to see result)
- Camera cleanup: `video_capture.release()` called on page change and stop button

### Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| Username (enroll) | Required, must exist | `ErrorDialog`: "User not found" |
| Camera (enroll) | Must be active | `Toast`: "Start the camera first" |
| Camera (verify) | Must be active | `Toast`: "Start the camera first" |
| Face detection | Must detect a face in frame | `ErrorDialog`: "No face detected. Look at the camera." |

### Visual Design

- **Two-column layout:** `grid(column=0, weight=1)` and `grid(column=1, weight=1)` for equal split
- **Camera preview:** Black background with live video feed (`CTkImage` updated every 30ms)
- **Loading spinner:** `LoadingSpinner` component visible during enroll/verify processing
- **Result frame:** Appears with `fade_in()` animation
  - Success: green checkmark + "Welcome, {username}!" in green text
  - Failure: red X + "Face not recognized" in red text
- **Button states:** Start/Stop camera toggle; Enroll/Verify buttons disabled when camera inactive

---

## 11. Audit Page

**File:** `gui/pages/audit_page.py` (140 lines)
**Class:** `AuditPage(ctk.CTkFrame)`

### Purpose

View and export system audit logs with filtering by action type, user, and date range.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Audit Logs"` | Page title |
| Filter frame | `CTkFrame` | — | `fg_color="transparent"` | Filter controls row |
| Action filter | `StyledComboBox` | — | `values=["All","LOGIN","LOGOUT","UPLOAD","DOWNLOAD","SHARE","REVOKE","SEARCH","FACE_ENROLL","FACE_VERIFY","PASSWORD_CHANGE"]` | Filter by action type |
| User filter | `StyledEntry` | — | `placeholder_text="Filter by username..."`, `width=200` | Filter by user |
| Search entry | `StyledEntry` | — | `placeholder_text="Search logs..."`, `width=200` | General text search |
| Export CSV button | `StyledButton` | — | `text="📄 Export CSV"`, `fg_color="#43E97B"` | Export filtered logs |
| Table | `StyledTable` | — | `columns=["Timestamp","User","Action","Document","Details","Status","IP"]` | Log entries |
| Entry count | `CTkLabel` | — | `fg_color="gray60"` | "Showing 42 entries" |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Audit Logs                                          │
│                                                      │
│  Action: [All ▼]  User: [          ]  Search: [    ] │
│  [📄 Export CSV]                                     │
│                                                      │
│  Timestamp      │ User  │ Action  │ Doc    │ Status  │
│  ───────────────┼───────┼─────────┼────────┼───────  │
│  Jan 15 10:30   │ alice │ UPLOAD  │ DOC-001│ ✅ OK   │
│  Jan 15 10:28   │ alice │ LOGIN   │ —      │ ✅ OK   │
│  Jan 15 09:15   │ bob   │ DOWNLOAD│ DOC-003│ ✅ OK   │
│  Jan 14 16:45   │ charlie│LOGIN   │ —      │ ❌ FAIL │
│  Jan 14 14:20   │ alice │ SHARE   │ DOC-002│ ✅ OK   │
│                                                      │
│  Showing 5 entries                                   │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Export CSV:** Opens `filedialog.asksaveasfilename()` for save location, writes CSV
- No page transitions

### Backend Integration

- Calls `AuditController.handle_get_logs(filters)` on page show and filter change
- `filters` dict: `{"action": str, "user": str, "search": str}`
- Export calls `AuditController.handle_export_csv(filters)` → writes to user-chosen path
- Table auto-refreshes when any filter changes (debounced 300ms)

### Validation Rules

- No required field validation (all filters optional)
- Export: shows `Toast` if no logs match current filters

### Visual Design

- **Action filter combo:** Color-coded action badges in table:
  - LOGIN/LOGOUT → blue
  - UPLOAD/DOWNLOAD → green
  - SHARE/REVOKE → purple
  - SEARCH → gray
  - FACE_ENROLL/FACE_VERIFY → orange
  - PASSWORD_CHANGE → yellow
- **Status column:** `StatusBadge` — green for success, red for failure
- **Table:** Scrollable, timestamp column formatted as "Mon DD HH:MM"
- **Export:** CSV written with headers: `Timestamp,User,Action,Document,Details,Status,IP`

---

## 12. Settings Page

**File:** `gui/pages/settings_page.py` (151 lines)
**Class:** `SettingsPage(ctk.CTkFrame)`

### Purpose

Application configuration including appearance, security, and backup/restore settings.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="Settings"` | Page title |
| **Appearance Section:** | | | | |
| Section header | `CTkLabel` | — | `text="Appearance"`, `font=("Helvetica", 16, "bold")` | Section title |
| Theme combo | `StyledComboBox` | — | `values=["Dark", "Light", "System"]` | Theme mode selector |
| Accent label | `CTkLabel` | — | `text="Accent Color"` | Label |
| Color swatch ×8 | `StyledButton` | — | `width=36`, `height=36`, `corner_radius=18` | Color selection buttons |
| **Security Section:** | | | | |
| Section header | `CTkLabel` | — | `text="Security"`, `font=("Helvetica", 16, "bold")` | Section title |
| 2FA toggle | `CTkButton` | — | `text="Enable 2FA"` / `text="Disable 2FA"` | Two-factor auth toggle |
| 2FA status | `StatusBadge` | — | `status="active"/"inactive"` | Current 2FA state |
| Session timeout combo | `StyledComboBox` | — | `values=["15 min", "30 min", "60 min", "120 min"]` | Session expiry duration |
| **Backup Section:** | | | | |
| Section header | `CTkLabel` | — | `text="Backup & Restore"`, `font=("Helvetica", 16, "bold")` | Section title |
| Backup button | `StyledButton` | — | `text="📦 Create Backup"`, `fg_color="#43E97B"` | Start backup |
| Restore button | `StyledButton` | — | `text="📂 Restore Backup"`, `fg_color="#FFA726"` | Start restore |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  Settings                                            │
│                                                      │
│  ┌─ Appearance ────────────────────────────────────┐ │
│  │ Theme: [Dark ▼]                                │ │
│  │                                                 │ │
│  │ Accent Color:                                   │ │
│  │ 🔵 🟣 🟢 🔴 🟡 🟠 ⚪ 🔵  (8 color swatches)  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Security ─────────────────────────────────────┐ │
│  │ Two-Factor Authentication:                     │ │
│  │ [Enable 2FA]  ✅ Active                        │ │
│  │                                                 │ │
│  │ Session Timeout: [30 min ▼]                    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Backup & Restore ────────────────────────────┐  │
│  │ [📦 Create Backup]  [📂 Restore Backup]        │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Navigation

- No page navigation (settings apply in place)
- Theme change takes effect immediately

### Backend Integration

- **Theme change:** Calls `customtkinter.set_appearance_mode(mode)` + `ThemeManager.instance().set_mode(mode)`
- **Accent color:** Updates `ThemeManager.instance().COLORS["primary"]` and refreshes all widgets
- **2FA toggle:** Calls `AuthController` to enable/disable 2FA
- **Session timeout:** Updates `Settings.instance().session_timeout` and `SessionManager`
- **Backup:** Calls `StorageManager.instance().create_backup(destination_path)` via `filedialog.asksaveasfilename()`
- **Restore:** Calls `StorageManager.instance().restore_backup(backup_path)` via `filedialog.askopenfilename()`

### Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| Session timeout | Must select a value | Defaults to 30 min |
| Backup destination | Must choose save location | `filedialog` enforces |
| Restore file | Must select a valid backup file | `ErrorDialog`: "Invalid backup file" |

### Visual Design

- **Color swatches:** 8 circular buttons (36×36px, `corner_radius=18`):
  - `#6C63FF` (purple), `#43E97B` (green), `#FF6584` (pink), `#FFD93D` (yellow)
  - `#FFA726` (orange), `#2196F3` (blue), `#95A5A6` (gray), `#E91E63` (magenta)
  - Active swatch: `border_width=3`, `border_color=white`
- **Sections:** Each section in an `InfoCard` with bold header
- **2FA toggle:** Button text and badge update on toggle
- **Theme switch:** Instant effect — entire UI updates colors immediately

---

## 13. Profile Page

**File:** `gui/pages/profile_page.py` (187 lines)
**Class:** `ProfilePage(ctk.CTkFrame)`

### Purpose

View and edit user profile information and change password.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Page header | `PageHeader` | — | `title="My Profile"` | Page title |
| Avatar frame | `CTkFrame` | — | `width=80`, `height=80`, `corner_radius=40`, `fg_color="#6C63FF"` | Circular avatar |
| Avatar initial | `CTkLabel` | — | `text="A"`, `font=("Helvetica", 32, "bold")`, `text_color="white"` | User initial letter |
| Username label | `CTkLabel` | — | `text="alice", `font=("Helvetica", 18, "bold")` | Display username |
| Role badge | `StatusBadge` | — | `status="admin"` or `status="user"` | Role indicator |
| **Profile Form:** | | | | |
| Section header | `CTkLabel` | — | `text="Profile Information"` | Section title |
| Full name entry | `StyledEntry` | — | `width=350`, current value loaded | Editable full name |
| Email entry | `StyledEntry` | — | `width=350`, current value loaded | Editable email |
| Save button | `StyledButton` | — | `text="Save Changes"`, `fg_color="#6C63FF"` | Save profile |
| **Password Form:** | | | | |
| Section header | `CTkLabel` | — | `text="Change Password"` | Section title |
| Current password | `PasswordEntry` | — | `width=350` | Current password verification |
| New password | `PasswordEntry` | — | `width=350` | New password input |
| Strength meter | `CTkFrame` | — | same as Register Page | Visual strength indicator |
| Confirm new password | `PasswordEntry` | — | `width=350` | Confirmation |
| Update password btn | `StyledButton` | — | `text="Update Password"`, `fg_color="#FF6584"` | Change password |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  My Profile                                          │
│                                                      │
│       ┌──────┐                                       │
│       │  A   │  alice                                │
│       │(blue)│  [Admin]                              │
│       └──────┘                                       │
│                                                      │
│  ── Profile Information ──                           │
│  Full Name: [Alice Smith                         ]   │
│  Email:     [alice@example.com                   ]   │
│                                                      │
│  [Save Changes]                                      │
│                                                      │
│  ── Change Password ──                               │
│  Current Password: [••••••••                      ]   │
│  New Password:     [••••••••                      ]   │
│                     ████████████████████ (strength)   │
│  Confirm Password:  [••••••••                      ]   │
│                                                      │
│  [Update Password]                                   │
└──────────────────────────────────────────────────────┘
```

### Navigation

- No page transitions (stays on profile page)
- Save/Update show `SuccessDialog` or `ErrorDialog`

### Backend Integration

- Profile load: `SessionManager.instance().get_current_user()` populates fields
- Save profile: Calls `AuthController.handle_update_profile(full_name, email)`
- Change password: Calls `AuthController.handle_password_change(current_password, new_password)`
- After password change: shows success message, clears password fields

### Validation Rules

| Field | Rule | Error |
|-------|------|-------|
| Full Name | Required, 2–100 chars | "Please enter your name" |
| Email | Required, valid format | "Please enter a valid email" |
| Current Password | Required | "Please enter current password" |
| New Password | Same strength rules as Register | "Password too weak" |
| Confirm | Must match new password | "Passwords do not match" |
| New ≠ Current | New password must differ | "New password must be different" |

### Visual Design

- **Avatar:** 80px circle with user initial centered
  - Background color derived from username hash (consistent per user)
  - First letter of username in white, bold, 32pt
- **Two-form layout:** Profile info above, password below, separated by visual dividers
- **Strength meter:** Same 4-segment bar as Register Page
- **Role badge:** `StatusBadge` with color: admin = purple, user = blue
- **Section headers:** 16pt bold with bottom border accent line

---

## 14. Document Detail Page

**File:** `gui/pages/document_detail_page.py` (162 lines)
**Class:** `DocumentDetailPage(ctk.CTkFrame)`

### Purpose

Detailed view of a single document's metadata with action buttons for download, share, and delete.

### All Widgets

| Widget | Type | Name/ID | Properties | Purpose |
|--------|------|---------|------------|---------|
| Back button | `CTkButton` | — | `text="← Back"`, `fg_color="transparent"`, `text_color="#6C63FF"` | Return to documents list |
| Page header | `PageHeader` | — | `title="{filename}"` | Document name |
| Detail card | `InfoCard` | — | `width=600`, 10 rows | Metadata display |
| Row 1: Doc ID | `CTkLabel` | — | `text="DOC-0042"` | Document identifier |
| Row 2: Filename | `CTkLabel` | — | `text="report.pdf"` | Stored filename |
| Row 3: Original | `CTkLabel` | — | `text="Q3 Report (final).pdf"` | Original filename |
| Row 4: Type | `CTkLabel` | — | `text="PDF"` | File type |
| Row 5: Size | `CTkLabel` | — | `text="2.4 MB"` | Human-readable size |
| Row 6: Owner | `CTkLabel` | — | `text="alice"` | Document owner |
| Row 7: Upload Date | `CTkLabel` | — | `text="January 15, 2024 10:30 AM"` | Upload timestamp |
| Row 8: SHA-256 Hash | `CTkLabel` | — | `text="a1b2c3d4..."`, cursor="hand2" | Truncated hash (click to copy) |
| Row 9: Description | `CTkLabel` | — | `text="..."`, `wraplength=500` | User description |
| Row 10: Tags | `CTkLabel` | — | `text="project, report, 2024"` | Comma-separated tags |
| Action frame | `CTkFrame` | — | `fg_color="transparent"` | Action buttons row |
| Download button | `StyledButton` | — | `text="📥 Download"`, `fg_color="#6C63FF"` | Download document |
| Share button | `StyledButton` | — | `text="🔗 Share"`, `fg_color="#43E97B"` | Navigate to share |
| Delete button | `StyledButton` | — | `text="🗑 Delete"`, `fg_color="#FF6B6B"` | Delete with confirmation |

### Layout

```
┌──────────────────────────────────────────────────────┐
│  ← Back                                             │
│                                                      │
│  report.pdf                                          │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ Document ID      │ DOC-0042                     │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Filename         │ report.pdf                   │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Original Name    │ Q3 Report (final).pdf        │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Type             │ PDF                          │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Size             │ 2.4 MB                       │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Owner            │ alice                        │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Upload Date      │ January 15, 2024 10:30 AM    │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ SHA-256          │ a1b2c3d4e5f6...  📋         │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Description      │ Quarterly financial report   │ │
│  ├──────────────────┼──────────────────────────────┤ │
│  │ Tags             │ project, report, 2024        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  [📥 Download]  [🔗 Share]  [🗑 Delete]              │
└──────────────────────────────────────────────────────┘
```

### Navigation

- **Back button:** → `app.show_page("documents")`
- **Share button:** → `app.show_page("share")` (pre-selects this document)
- **Download button:** → `app.show_page("download")` (pre-selects this document)

### Backend Integration

- Page receives `doc_id` as navigation parameter: `app.show_page("document_detail", doc_id="DOC-0042")`
- Calls `DocumentController.handle_get_detail(doc_id)` on page show
- Populates all 10 rows from response data
- Delete calls `DocumentController.handle_delete(doc_id)` after confirmation
- Hash copy: clicking the hash label copies full hash to clipboard via `root.clipboard_clear()` + `root.clipboard_append()`

### Validation Rules

| Check | Rule | Error |
|-------|------|-------|
| Delete | Shows `ConfirmDialog`: "Permanently delete {filename}?" | Cancel aborts delete |
| Delete success | Shows `SuccessDialog` + navigates to documents | — |

### Visual Design

- **InfoCard:** 10-row key-value layout
  - Left column (key): `width=150`, `font=("Helvetica", 12, "bold")`, `fg_color="gray60"`
  - Right column (value): `width=400`, `font=("Helvetica", 12)`
  - Alternating row backgrounds
- **Hash row:** Truncated to first 32 characters + "..." with clipboard icon
  - Hover: shows full hash in tooltip
  - Click: copies full hash to clipboard, shows `Toast` ("Hash copied to clipboard")
- **Action buttons:** Horizontal row, evenly spaced
  - Download: blue, navigates with pre-selection
  - Share: green, navigates with pre-selection
  - Delete: red, triggers confirmation dialog
- **Back button:** Top-left, text-style (no background), with left arrow character

---

## Global Navigation Map

```
                    ┌─────────────┐
                    │  Login Page  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌──────▼──────┐  ┌─▼────────────┐
    │  Register   │  │  Dashboard  │  │   Face Page   │
    │   Page      │  │    Page     │  │  (face login) │
    └─────────┬──┘  └──────┬──────┘  └───────┬───────┘
              │            │                  │
              └──────►─────┘          auto-login on
                       │               success → Dashboard
           ┌───────────┼───────────────────────────────┐
           │           │           │         │         │
    ┌──────▼──┐  ┌─────▼────┐ ┌───▼──┐ ┌───▼──┐ ┌───▼────┐
    │Documents│  │  Upload  │ │Share │ │Search│ │ Face   │
    │  Page   │  │  Page    │ │ Page │ │ Page │ │ Page   │
    └────┬────┘  └──────────┘ └──────┘ └──────┘ └────────┘
         │
    ┌────▼──────────┐     ┌──────────────┐
    │ Document      │     │   Shared     │
    │ Detail Page   │     │    Page      │
    └───────────────┘     └──────────────┘
    
    Sidebar routes to all pages:
    Dashboard │ Documents │ Upload │ Download │ Share │
    Shared │ Search │ Face ID │ Audit │ Settings │ Profile
```

---

## Shared Visual Language

### Color Palette

| Token | Hex (Dark) | Hex (Light) | Usage |
|-------|-----------|-------------|-------|
| Primary | `#6C63FF` | `#5A52D5` | Buttons, links, accents |
| Secondary | `#43E97B` | `#2ECC71` | Success states, share |
| Accent | `#FF6584` | `#E74C3C` | Error states, danger |
| Warning | `#FFD93D` | `#F1C40F` | Warning states |
| Background | `#1a1a2e` | `#FFFFFF` | Page background |
| Surface | `#16213e` | `#F5F5F5` | Card background |
| Text Primary | `#FFFFFF` | `#2C3E50` | Main text |
| Text Secondary | `#A0A0A0` | `#7F8C8D` | Subtitle/muted text |

### Typography

| Style | Font | Size | Weight | Usage |
|-------|------|------|--------|-------|
| Heading | Helvetica | 22-26pt | Bold | Page titles, welcome text |
| Subheading | Helvetica | 16-18pt | Bold | Section headers |
| Body | Helvetica | 12-13pt | Regular | Labels, descriptions |
| Small | Helvetica | 10-11pt | Regular | Captions, timestamps |
| Mono | Courier | 11pt | Regular | Hashes, doc IDs |

### Component Dimensions

| Element | Width | Height | Corner Radius |
|---------|-------|--------|---------------|
| Sidebar | 240px | full | 0 |
| TopBar | full | 60px | 0 |
| Login Card | 400px | 520px | 20 |
| Stat Card | 180px | 120px | 12 |
| Grid Card | 160px | 180px | 12 |
| Action Card | 160px | 100px | 12 |
| Form Entry | 350-400px | 40px | 8 |
| Button | auto | 40-44px | 8 |
| Table | full | auto | 8 |

### Animation Specifications

| Animation | Duration | Easing | Trigger |
|-----------|----------|--------|---------|
| Page fade-in | 400ms | ease-out | Page becomes visible |
| Card entrance | 300ms | ease-out | Staggered 100ms apart |
| Orb bounce | 6-8s loop | sinusoidal | Continuous (login page) |
| Progress bar | 500ms per phase | linear | Upload/download |
| Dialog entrance | 250ms | ease-out | Dialog opens |
| Toast auto-dismiss | 3000ms | — | After display |
| Button hover | 150ms | ease | Mouse enter |
| Strength meter | 200ms | ease | Keystroke |
