# SDMS Function Documentation

> **Secure Document Management System — Standalone Function Reference**
> Version 1.0.0 | Generated from source code

---

## Table of Contents

1. [Application Entry Point](#1-application-entry-point)
2. [Logging Configuration](#2-logging-configuration)
3. [Theme Management](#3-theme-management)
4. [Utility Functions](#4-utility-functions)
5. [Cryptographic Key Generation](#5-cryptographic-key-generation)
6. [Base64 Utilities](#6-base64-utilities)
7. [GUI Animations](#7-gui-animations)
8. [Smooth Scrolling](#8-smooth-scrolling)
9. [GUI Assets](#9-gui-assets)
10. [Document Listing Helpers](#10-document-listing-helpers)
11. [Face Recognition Helpers](#11-face-recognition-helpers)

---

## 1. Application Entry Point

### `main()`

**File:** `main.py:24`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Application entry point orchestrating startup and shutdown. Initialises logging, connects to MongoDB, creates indexes, ensures storage directories, and launches either the GUI or CLI. |
| **Syntax** | `main() -> None` |
| **Parameters** | None |
| **Returns** | `None` |
| **Exceptions** | `SystemExit(1)` if database connection fails |

#### Step-by-Step Working

1. Call `setup_logging()` to configure root logger with file and stream handlers.
2. Log application name, version, and environment.
3. Create a `DatabaseManager` singleton and call `connect()`.
4. If connection fails, log the error and exit with code 1.
5. Call `create_indexes()` to ensure all MongoDB indexes exist.
6. Create a `StorageManager` and call `initialise()` to create storage directories.
7. If `--cli` flag is in `sys.argv`, import and run the CLI (`display_welcome()` + `run_cli()`).
8. Otherwise, instantiate all four controllers (`AuthController`, `DocumentController`, `AuditController`, `FaceController`), create `SDMSApp`, and call `mainloop()`.
9. On exit, disconnect from MongoDB and log shutdown.

#### Example

```bash
python main.py          # Launch GUI
python main.py --cli    # Launch CLI
```

---

## 2. Logging Configuration

### `setup_logging()`

**File:** `logger/logging_config.py:18`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Configure and return the root application logger (`"sdms"`). Sets up a rotating file handler and a stderr stream handler with different formatters. |
| **Syntax** | `setup_logging() -> logging.Logger` |
| **Parameters** | None |
| **Returns** | `logging.Logger` — the configured root `"sdms"` logger |
| **Exceptions** | None (creates log directory if missing) |

#### Step-by-Step Working

1. Read `LOG_LEVEL` from `settings` (default: `"DEBUG"`). Convert to numeric level.
2. Get the `"sdms"` root logger and set its level.
3. Clear any existing handlers (idempotent).
4. Create `logs/` directory if it doesn't exist.
5. Create a `RotatingFileHandler` writing to `logs/sdms.log`:
   - Max file size: 5 MB
   - Backup count: 3
   - Encoding: UTF-8
   - Format: `[2026-07-06 14:30:00] DEBUG    module.func:42 — message`
6. Create a `StreamHandler` writing to stderr:
   - Format: `[14:30:00] DEBUG    message`
7. Add both handlers to the root logger.
8. Return the configured logger.

#### Example

```python
from logger.logging_config import setup_logging

logger = setup_logging()
logger.info("Application started.")
```

---

### `get_logger(name)`

**File:** `logger/logging_config.py:67`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Return a child logger of the `"sdms"` namespace. Every module in the project obtains its logger via this function to ensure consistent formatting and hierarchical naming. |
| **Syntax** | `get_logger(name: str) -> logging.Logger` |
| **Parameters** | |
| `name` | `str` — Logger name (typically `__name__` of the calling module) |
| **Returns** | `logging.Logger` — A logger named `"sdms.<name>"` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Concatenate `"sdms."` with the provided `name`.
2. Call `logging.getLogger()` with the combined name.
3. Return the logger. All handlers and configuration are inherited from the root `"sdms"` logger.

#### Example

```python
from logger.logging_config import get_logger

logger = get_logger(__name__)  # e.g. "sdms.services.auth_service"
logger.info("User logged in successfully.")
logger.warning("Invalid password attempt.")
```

---

## 3. Theme Management

### `apply_theme(mode)`

**File:** `gui/theme.py:272`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Initialize the CustomTkinter theme. Sets the appearance mode and updates the `ThemeManager` singleton. Called at application startup. |
| **Syntax** | `apply_theme(mode: str = "dark") -> None` |
| **Parameters** | |
| `mode` | `str` — `"dark"` or `"light"` (default: `"dark"`) |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Call `ctk.set_appearance_mode()` with `"dark"` or `"light"` based on the mode.
2. Call `ctk.set_default_color_theme("blue")` for CustomTkinter's base theme.
3. Get the `ThemeManager` singleton.
4. Call `tm.set_mode(mode)` to update the internal mode state and notify any registered observers.

#### Example

```python
from gui.theme import apply_theme

apply_theme("dark")   # Dark mode (default)
apply_theme("light")  # Light mode
```

---

## 4. Utility Functions

### `generate_timestamp()`

**File:** `utilities/helpers.py:16`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Return the current UTC time as an ISO-8601 formatted string. |
| **Syntax** | `generate_timestamp() -> str` |
| **Parameters** | None |
| **Returns** | `str` — ISO-8601 timestamp, e.g. `"2026-07-06T14:30:00.123456+00:00"` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Call `datetime.now(timezone.utc)` to get the current UTC time.
2. Call `.isoformat()` on the datetime object.
3. Return the string.

#### Example

```python
from utilities.helpers import generate_timestamp

ts = generate_timestamp()  # "2026-07-06T14:30:00.123456+00:00"
```

---

### `generate_document_id()`

**File:** `utilities/helpers.py:25`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Return a cryptographically random, URL-safe document identifier using UUID4. |
| **Syntax** | `generate_document_id() -> str` |
| **Parameters** | None |
| **Returns** | `str` — A 32-character lowercase hex string (UUID4 without hyphens) |
| **Exceptions** | None |

#### Step-by-Step Working

1. Call `uuid.uuid4()` to generate a random UUID.
2. Access `.hex` to get the 32-character hex representation.
3. Return the string.

#### Example

```python
from utilities.helpers import generate_document_id

doc_id = generate_document_id()  # "a1b2c3d4e5f6..."
```

---

### `sanitize_filename(filename)`

**File:** `utilities/helpers.py:33`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Remove or replace characters that are unsafe in filenames across operating systems. |
| **Syntax** | `sanitize_filename(filename: str) -> str` |
| **Parameters** | |
| `filename` | `str` — The original filename to sanitize |
| **Returns** | `str` — A safe filename string |
| **Exceptions** | `ValueError` — If the resulting filename is empty |

#### Step-by-Step Working

1. Define safe characters: ASCII letters, digits, `-`, `_`, `.`, and spaces.
2. Iterate over each character in `filename`.
3. Keep the character if it is in the safe set; otherwise replace with `_`.
4. If the result is empty, raise `ValueError`.
5. Return the sanitized string.

#### Example

```python
from utilities.helpers import sanitize_filename

safe = sanitize_filename("My File (2).pdf")   # "My_File__2_.pdf"
safe = sanitize_filename("../../../etc/passwd")  # "__________etc_passwd"
```

---

### `validate_file_path(file_path)`

**File:** `utilities/helpers.py:56`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Resolve and validate that a file path exists and is actually a file (not a directory). |
| **Syntax** | `validate_file_path(file_path: str | Path) -> Path` |
| **Parameters** | |
| `file_path` | `str | Path` — Path to validate |
| **Returns** | `Path` — Resolved `pathlib.Path` object |
| **Exceptions** | |
| `FileNotFoundError` | If the path does not exist |
| `ValueError` | If the path is not a file |

#### Step-by-Step Working

1. Convert `file_path` to a `Path` object and call `.resolve()` to get the absolute path.
2. Check `path.exists()`. If `False`, raise `FileNotFoundError`.
3. Check `path.is_file()`. If `False`, raise `ValueError`.
4. Return the resolved path.

#### Example

```python
from utilities.helpers import validate_file_path

path = validate_file_path("documents/report.pdf")
# Returns: PosixPath("/home/user/documents/report.pdf")
```

---

### `ensure_directory(path)`

**File:** `utilities/helpers.py:77`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Create the directory at `path` (and all parent directories) if it does not exist. Safe to call multiple times. |
| **Syntax** | `ensure_directory(path: str | Path) -> Path` |
| **Parameters** | |
| `path` | `str | Path` — Directory path to ensure |
| **Returns** | `Path` — Resolved `pathlib.Path` object |
| **Exceptions** | None |

#### Step-by-Step Working

1. Convert `path` to a `Path` object and call `.resolve()`.
2. Call `resolved.mkdir(parents=True, exist_ok=True)` to create the directory and any missing parents.
3. Return the resolved path.

#### Example

```python
from utilities.helpers import ensure_directory

ensure_directory("storage/encrypted_documents")  # Creates if missing
```

---

### `is_valid_object_id(id_string)`

**File:** `utilities/helpers.py:91`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Check whether a string is a valid 24-hex-character MongoDB ObjectId. |
| **Syntax** | `is_valid_object_id(id_string: str) -> bool` |
| **Parameters** | |
| `id_string` | `str` — The string to test |
| **Returns** | `bool` — `True` if the string matches the ObjectId pattern |
| **Exceptions** | None |

#### Step-by-Step Working

1. Apply the regex `^[0-9a-fA-F]{24}$` using `re.fullmatch()`.
2. Return the boolean result.

#### Example

```python
from utilities.helpers import is_valid_object_id

is_valid_object_id("507f1f77bcf86cd799439011")  # True
is_valid_object_id("not-an-id")                   # False
```

---

## 5. Cryptographic Key Generation

### `generate_aes_key()`

**File:** `crypto/key_generator.py:20`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generate a cryptographically random 256-bit (32-byte) AES key. |
| **Syntax** | `generate_aes_key() -> bytes` |
| **Parameters** | None |
| **Returns** | `bytes` — 32 random bytes suitable as an AES-256 key |
| **Exceptions** | `KeyGenerationError` — If the OS entropy source fails |

#### Step-by-Step Working

1. Call `os.urandom(32)` to draw 32 bytes from the OS cryptographically secure random number generator.
2. Return the bytes.
3. On `OSError`, wrap and raise as `KeyGenerationError`.

#### Example

```python
from crypto.key_generator import generate_aes_key

key = generate_aes_key()  # b'\xa3\x8f...\x12' (32 bytes)
len(key)  # 32
```

---

### `generate_iv()`

**File:** `crypto/key_generator.py:37`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generate a cryptographically random 128-bit (16-byte) initialisation vector for AES-CBC. |
| **Syntax** | `generate_iv() -> bytes` |
| **Parameters** | None |
| **Returns** | `bytes` — 16 random bytes |
| **Exceptions** | `KeyGenerationError` — If the OS entropy source fails |

#### Step-by-Step Working

1. Call `os.urandom(16)`.
2. Return the bytes.
3. On `OSError`, wrap and raise as `KeyGenerationError`.

#### Example

```python
from crypto.key_generator import generate_iv

iv = generate_iv()  # b'\x4e\x7a...\x9f' (16 bytes)
len(iv)  # 16
```

---

### `generate_salt()`

**File:** `crypto/key_generator.py:54`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generate a cryptographically random 16-byte salt value for password hashing. |
| **Syntax** | `generate_salt() -> bytes` |
| **Parameters** | None |
| **Returns** | `bytes` — 16 random bytes |
| **Exceptions** | `KeyGenerationError` — If the OS entropy source fails |

#### Step-by-Step Working

1. Call `os.urandom(16)`.
2. Return the bytes.
3. On `OSError`, wrap and raise as `KeyGenerationError`.

#### Example

```python
from crypto.key_generator import generate_salt

salt = generate_salt()  # b'\xd2\x1c...\x8b' (16 bytes)
```

---

### `generate_secure_token(length)`

**File:** `crypto/key_generator.py:68`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Generate a URL-safe hex token suitable for session IDs or nonces. |
| **Syntax** | `generate_secure_token(length: int = 32) -> str` |
| **Parameters** | |
| `length` | `int` — Number of random bytes to draw (default: 32 → 64 hex characters) |
| **Returns** | `str` — Lower-case hex-encoded secure token |
| **Exceptions** | `KeyGenerationError` — If the OS entropy source fails |

#### Step-by-Step Working

1. Call `os.urandom(length)` to draw `length` random bytes.
2. Call `.hex()` to get the hex-encoded string (twice the byte length in characters).
3. Return the string.
4. On `OSError`, wrap and raise as `KeyGenerationError`.

#### Example

```python
from crypto.key_generator import generate_secure_token

token = generate_secure_token()    # "a3f8b2..." (64 hex chars)
token = generate_secure_token(16)  # "d4c1..." (32 hex chars)
```

---

### `generate_crypto_id()`

**File:** `crypto/key_generator.py:89`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Return a random UUID4 hex string for use as a cryptographic identifier (user IDs, document internal IDs, audit IDs, session IDs). |
| **Syntax** | `generate_crypto_id() -> str` |
| **Parameters** | None |
| **Returns** | `str` — A 32-character hex string (UUID4 without hyphens) |
| **Exceptions** | None |

#### Step-by-Step Working

1. Call `uuid.uuid4()` to generate a cryptographically random UUID.
2. Access `.hex` to get the 32-character hex representation.
3. Return the string.

#### Example

```python
from crypto.key_generator import generate_crypto_id

uid = generate_crypto_id()  # "7c9e667974250e0aa3b6330d59c48b06"
```

---

## 6. Base64 Utilities

### `b64_encode(data)`

**File:** `crypto/base64_utils.py:17`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Encode binary data to a Base64 UTF-8 string. Used for storing ciphertext, IVs, and RSA keys in MongoDB as text. |
| **Syntax** | `b64_encode(data: bytes) -> str` |
| **Parameters** | |
| `data` | `bytes` — Arbitrary binary data to encode |
| **Returns** | `str` — Base64-encoded string (standard alphabet, with padding) |
| **Exceptions** | `Base64Error` — If encoding fails |

#### Step-by-Step Working

1. Call `base64.b64encode(data)` to get Base64 bytes.
2. Call `.decode("utf-8")` to convert to a string.
3. Return the string.
4. On `ValueError` or `TypeError`, wrap and raise as `Base64Error`.

#### Example

```python
from crypto.base64_utils import b64_encode

encoded = b64_encode(b"\x00\x01\x02")  # "AAEC"
```

---

### `b64_decode(encoded)`

**File:** `crypto/base64_utils.py:35`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Decode a Base64-encoded string back to raw bytes. Used for recovering ciphertext, IVs, and RSA keys from MongoDB. |
| **Syntax** | `b64_decode(encoded: str) -> bytes` |
| **Parameters** | |
| `encoded` | `str` — Base64-encoded string (standard alphabet, may include padding) |
| **Returns** | `bytes` — Decoded binary data |
| **Exceptions** | `Base64Error` — If the string is not valid Base64 |

#### Step-by-Step Working

1. Call `base64.b64decode(encoded, validate=True)` with strict validation.
2. Return the decoded bytes.
3. On `ValueError`, `TypeError`, or `binascii.Error`, wrap and raise as `Base64Error`.

#### Example

```python
from crypto.base64_utils import b64_decode

decoded = b64_decode("AAEC")  # b"\x00\x01\x02"
```

---

## 7. GUI Animations

### `_ease_out_cubic(t)`

**File:** `gui/animations.py:12`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Cubic ease-out curve for natural deceleration. Used by slide and fade animations to create smooth endings. |
| **Syntax** | `_ease_out_cubic(t: float) -> float` |
| **Parameters** | |
| `t` | `float` — Progress value in `[0.0, 1.0]` |
| **Returns** | `float` — Eased value in `[0.0, 1.0]` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Compute `1 - (1 - t)^3`.
2. Return the result. When `t=0` returns `0.0`; when `t=1` returns `1.0`; values near 1 decelerate.

#### Example

```python
from gui.animations import _ease_out_cubic

_ease_out_cubic(0.0)   # 0.0
_ease_out_cubic(0.5)   # 0.875
_ease_out_cubic(1.0)   # 1.0
```

---

### `_ease_in_out_cubic(t)`

**File:** `gui/animations.py:17`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Cubic ease-in-out for smooth acceleration and deceleration. Symmetric curve — slow at start and end, fast in the middle. |
| **Syntax** | `_ease_in_out_cubic(t: float) -> float` |
| **Parameters** | |
| `t` | `float` — Progress value in `[0.0, 1.0]` |
| **Returns** | `float` — Eased value in `[0.0, 1.0]` |
| **Exceptions** | None |

#### Step-by-Step Working

1. If `t < 0.5`: compute `4 * t^3`.
2. If `t >= 0.5`: compute `1 - (-2*t + 2)^3 / 2`.
3. Return the result. The transition at `t=0.5` is smooth (C1 continuous).

#### Example

```python
from gui.animations import _ease_in_out_cubic

_ease_in_out_cubic(0.0)   # 0.0
_ease_in_out_cubic(0.25)  # 0.0625
_ease_in_out_cubic(0.5)   # 0.5
_ease_in_out_cubic(1.0)   # 1.0
```

---

### `fade_in(widget, steps, delay)`

**File:** `gui/animations.py:24`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Fade in a widget by interpolating its background colour from the dark background to its target colour. Works with grid, pack, or place geometry managers. |
| **Syntax** | `fade_in(widget: ctk.CTkBaseClass, steps: int = 8, delay: int = 16) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — The widget to fade in |
| `steps` | `int` — Number of animation steps (default: 8) |
| `delay` | `int` — Milliseconds between steps (default: 16 ≈ 60fps) |
| **Returns** | `None` |
| **Exceptions** | None (silently handles geometry manager conflicts) |

#### Step-by-Step Working

1. Attempt to `grid()` the widget. If that fails, try `pack()`.
2. Lift the widget to the top of the stacking order.
3. Read the widget's target `fg_color`.
4. If it's a hex colour string, begin interpolation from the dark background `[15, 23, 42]` to the target RGB.
5. Each step: compute eased progress via `_ease_out_cubic`, interpolate RGB, apply the colour.
6. Schedule the next step with `widget.after(delay, ...)`.

#### Example

```python
from gui.animations import fade_in

page = LoginPage(container, ...)
fade_in(page)  # Fades in over ~128ms (8 steps × 16ms)
```

---

### `fade_out(widget, steps, delay, callback)`

**File:** `gui/animations.py:47`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Fade out a widget by hiding it, then optionally call a callback. |
| **Syntax** | `fade_out(widget: ctk.CTkBaseClass, steps: int = 8, delay: int = 16, callback: Callable | None = None) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — The widget to fade out |
| `steps` | `int` — Number of animation steps (unused in current implementation) |
| `delay` | `int` — Delay in ms (unused in current implementation) |
| `callback` | `Callable | None` — Optional function to call after hiding |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Attempt to `grid_forget()` the widget. If that fails, try `pack_forget()`.
2. If a `callback` is provided, invoke it.

#### Example

```python
from gui.animations import fade_out

fade_out(old_page, callback=lambda: new_page.grid(row=0, column=0))
```

---

### `slide_in_from_left(widget, target_x, start_x, steps, delay)`

**File:** `gui/animations.py:92`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Slide a widget in from the left with ease-out deceleration. |
| **Syntax** | `slide_in_from_left(widget: ctk.CTkBaseClass, target_x: int = 0, start_x: int = -200, steps: int = 12, delay: int = 15) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — Widget to animate |
| `target_x` | `int` — Final x position (default: 0) |
| `start_x` | `int` — Starting x position (default: -200) |
| `steps` | `int` — Number of animation frames (default: 12) |
| `delay` | `int` — Milliseconds between frames (default: 15) |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Place the widget at `start_x` using `.place(x=start_x, rely=0.5, anchor="w")`.
2. Start the animation loop via `_slide_step()`.
3. Each frame: compute eased progress, interpolate x, update `.place()`.
4. Continue until `step == total`.

---

### `slide_in_from_right(widget, container_w, widget_w, steps, delay)`

**File:** `gui/animations.py:99`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Slide a widget in from the right edge of the container with ease-out. |
| **Syntax** | `slide_in_from_right(widget: ctk.CTkBaseClass, container_w: int, widget_w: int, steps: int = 12, delay: int = 15) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — Widget to animate |
| `container_w` | `int` — Container width |
| `widget_w` | `int` — Widget width |
| `steps` | `int` — Number of animation frames (default: 12) |
| `delay` | `int` — Milliseconds between frames (default: 15) |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Compute `start_x = container_w` and `target_x = container_w - widget_w`.
2. Place the widget at `start_x`.
3. Animate to `target_x` using the same `_slide_step()` loop.

---

### `pulse_color(widget, property_name, colors, interval)`

**File:** `gui/animations.py:120`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Cycle through a list of colours on a widget property (e.g., `fg_color` or `text_color`) for a pulse effect. |
| **Syntax** | `pulse_color(widget: ctk.CTkBaseClass, property_name: str, colors: list[str], interval: int = 500) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — Widget to animate |
| `property_name` | `str` — `"fg_color"` or `"text_color"` |
| `colors` | `list[str]` — List of hex colour strings to cycle through |
| `interval` | `int` — Milliseconds between colour changes (default: 500) |
| **Returns** | `None` |
| **Exceptions** | None (stops silently on widget destruction) |

#### Step-by-Step Working

1. Maintain an index counter (starting at 0).
2. After `interval` ms, set the widget property to `colors[index % len(colors)]`.
3. Increment the index.
4. Schedule the next cycle.
5. Stop if the widget has been destroyed.

---

### `scale_in(widget, steps, delay)`

**File:** `gui/animations.py:139`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Scale-in animation by progressively setting width/height from 1 to the final size. Useful for dialog pop-in effects. |
| **Syntax** | `scale_in(widget: ctk.CTkBaseClass, steps: int = 10, delay: int = 16) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — Widget to animate |
| `steps` | `int` — Number of animation frames (default: 10) |
| `delay` | `int` — Milliseconds between frames (default: 16) |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Read the widget's required width and height (`winfo_reqwidth()`, `winfo_reqheight()`).
2. Set the widget to `width=1, height=1`.
3. Grid or pack the widget.
4. Each frame: compute eased progress, interpolate width/height, apply via `configure()`.
5. On the final frame, restore the full size.

---

## 8. Smooth Scrolling

### `bind_smooth_scroll(widget)`

**File:** `gui/smooth_scrolling.py:13`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Bind cross-platform mousewheel scrolling to a widget and all its children. Handles Windows (`MouseWheel`), macOS (`Shift+MouseWheel`), and Linux (`Button-4/5`). |
| **Syntax** | `bind_smooth_scroll(widget: ctk.CTkBaseClass) -> None` |
| **Parameters** | |
| `widget` | `ctk.CTkBaseClass` — The root scrollable widget to bind |
| **Returns** | `None` |
| **Exceptions** | None (silently handles binding errors) |

#### Step-by-Step Working

1. Check the current platform (`sys.platform`).
2. If Linux: bind `<Button-4>` (scroll up) and `<Button-5>` (scroll down) to the widget.
3. If Windows/macOS: bind `<MouseWheel>` to the widget.
4. Bind `<Map>` to recursively bind all children when they appear.
5. Recursively bind all existing children via `_bind_children()`.
6. Each child's scroll event triggers a walk up the widget tree to find the nearest `CTkScrollableFrame`, then scroll its internal canvas.

#### Example

```python
from gui.smooth_scrolling import bind_smooth_scroll

scrollable = ctk.CTkScrollableFrame(container)
# ... add children ...
bind_smooth_scroll(scrollable)  # All children now scroll smoothly
```

---

### `rebind_scroll(content_frame)`

**File:** `gui/smooth_scrolling.py:105`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Rebind scroll events after content changes (e.g., when new widgets are dynamically added or removed). |
| **Syntax** | `rebind_scroll(content_frame: ctk.CTkFrame) -> None` |
| **Parameters** | |
| `content_frame` | `ctk.CTkFrame` — The content frame whose ancestors may need rebinding |
| **Returns** | `None` |
| **Exceptions** | None |

#### Step-by-Step Working

1. Walk up the widget tree from `content_frame`.
2. If a `CTkScrollableFrame` ancestor is found, call `bind_smooth_scroll()` on it.
3. Return immediately after rebinding.

---

## 9. GUI Assets

### `icon(name)`

**File:** `gui/assets.py:112`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Look up a semantic icon name and return the corresponding Unicode character. Works without any external font or SVG library. |
| **Syntax** | `icon(name: str) -> str` |
| **Parameters** | |
| `name` | `str` — Semantic icon name (e.g. `"dashboard"`, `"upload"`, `"search"`) |
| **Returns** | `str` — Unicode character, or the default `"☐"` if not found |
| **Exceptions** | None |

#### Available Names

`dashboard`, `documents`, `upload`, `download`, `encrypt`, `decrypt`, `profile`, `activity`, `settings`, `dark_mode`, `light_mode`, `logout`, `login`, `register`, `search`, `share`, `shared`, `face`, `audit`, `home`, `chart`, `lock`, `unlock`, `shield`, `key`, `user`, `users`, `file`, `folder`, `trash`, `edit`, `check`, `close`, `warning`, `info`, `success`, `error`, `refresh`, `add`, `remove`, `sort`, `filter`, `grid`, `list`, `star`, `mail`, `phone`, `camera`, `save`, `cancel`, `back`, `forward`, `chevron_right`, `chevron_left`, `more`, `notification`, `calendar`, `clock`, `cloud`, `database`, `server`, `sync`, `import`, `export`, `backup`, `restore`, `copy`, `paste`, `maximize`, `minimize`, `fullscreen`, `menu`, `close_sidebar`, `open_sidebar`, `pdf`, `image`, `text_file`, `code`, `zip`, `doc`, `default_file`

#### Example

```python
from gui.assets import icon

icon("dashboard")  # "⌂"
icon("upload")     # "⬆"
icon("search")     # "➲"
```

---

### `file_icon(extension)`

**File:** `gui/assets.py:115`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Look up a file extension and return the appropriate icon character. |
| **Syntax** | `file_icon(extension: str) -> str` |
| **Parameters** | |
| `extension` | `str` — File extension including dot (e.g. `".pdf"`, `".docx"`) |
| **Returns** | `str` — Unicode character for that file type, or the default file icon |
| **Exceptions** | None |

#### Supported Extensions

| Extension | Icon |
|-----------|------|
| `.pdf` | `"■"` |
| `.doc`, `.docx` | `"▩"` |
| `.txt` | `"▤"` |
| `.png`, `.jpg`, `.jpeg`, `.gif` | `"▧"` |
| `.py`, `.js`, `.html`, `.css` | `"▩"` |
| `.zip`, `.rar` | `"▩"` |
| `.csv`, `.xlsx`, `.pptx` | `"▩"` |
| *(unknown)* | `"☐"` (default) |

#### Example

```python
from gui.assets import file_icon

file_icon(".pdf")  # "■"
file_icon(".txt")  # "▤"
file_icon(".xyz")  # "☐" (unknown)
```

---

## 10. Document Listing Helpers

The following module-level functions are in `services/document_listing_service.py` and support the `DocumentListingService` class.

### `_format_file_size(size_bytes)`

**File:** `services/document_listing_service.py:31`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Convert a file size in bytes to a human-readable string with appropriate units. |
| **Syntax** | `_format_file_size(size_bytes: int) -> str` |
| **Parameters** | |
| `size_bytes` | `int` — File size in bytes |
| **Returns** | `str` — Human-readable string (e.g., `"512 B"`, `"12.3 KB"`, `"1.5 MB"`, `"2.1 GB"`) |
| **Exceptions** | None |

#### Step-by-Step Working

1. If `size_bytes < 1024`, return `f"{size_bytes} B"`.
2. Divide by 1024.0 iteratively for `KB`, `MB`, `GB`.
3. At each step, if the value is < 1024, return the formatted string with 1 decimal place.
4. If all units exhausted (≥ 1 TB), return the value in TB.

#### Example

```python
_format_file_size(0)          # "0 B"
_format_file_size(512)        # "512 B"
_format_file_size(1536)       # "1.5 KB"
_format_file_size(5242880)    # "5.0 MB"
_format_file_size(1073741824) # "1.0 GB"
```

---

### `_get_file_extension(filename)`

**File:** `services/document_listing_service.py:47`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Return the lowercase file extension including the dot. |
| **Syntax** | `_get_file_extension(filename: str) -> str` |
| **Parameters** | |
| `filename` | `str` — The filename to extract the extension from |
| **Returns** | `str` — Lowercase extension (e.g., `".pdf"`) or `""` if none |
| **Exceptions** | None |

#### Step-by-Step Working

1. Create a `Path` from `filename`.
2. Access `.suffix.lower()`.
3. Return the result.

#### Example

```python
_get_file_extension("report.PDF")   # ".pdf"
_get_file_extension("README")       # ""
_get_file_extension("archive.tar.gz")  # ".gz"
```

---

### `_safe_document_info(doc)`

**File:** `services/document_listing_service.py:55`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Extract only safe metadata fields from a raw MongoDB document dict for display. Sensitive fields (`encrypted_aes_key`, `iv`, `encrypted_filename`, `algorithm`) are never included. |
| **Syntax** | `_safe_document_info(doc: dict[str, Any]) -> dict[str, Any]` |
| **Parameters** | |
| `doc` | `dict[str, Any]` — Raw MongoDB document dict |
| **Returns** | `dict[str, Any]` — Safe metadata dict with computed display fields |
| **Exceptions** | None |

#### Step-by-Step Working

1. Extract and format timestamps (`.isoformat()`).
2. Compute `file_size_display` via `_format_file_size()`.
3. Compute `file_extension` via `_get_file_extension()`.
4. Determine `status` (`"deleted"` if `is_deleted`, else `"active"`).
5. Count `shared_with_count` from the `shared_with` list.
6. Return a dict with only safe fields: `document_id`, `original_filename`, `file_extension`, `mime_type`, `file_size`, `file_size_display`, `sha256_hash`, `owner_id`, `is_deleted`, `status`, `created_at`, `updated_at`, `shared_with_count`.

---

### `_build_pagination_meta(total, page, per_page)`

**File:** `services/document_listing_service.py:85`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Build pagination metadata for API responses. |
| **Syntax** | `_build_pagination_meta(total: int, page: int, per_page: int) -> dict[str, Any]` |
| **Parameters** | |
| `total` | `int` — Total number of matching documents |
| `page` | `int` — Current page number (1-indexed) |
| `per_page` | `int` — Items per page |
| **Returns** | `dict[str, Any]` — Pagination metadata |
| **Exceptions** | None |

#### Step-by-Step Working

1. Compute `total_pages = max(1, ceil(total / per_page))`.
2. Build the result dict:
   - `page`: current page
   - `per_page`: items per page
   - `total`: total items
   - `total_pages`: computed total pages
   - `has_next`: `page < total_pages`
   - `has_previous`: `page > 1`

#### Example

```python
meta = _build_pagination_meta(total=85, page=2, per_page=20)
# {
#     "page": 2, "per_page": 20, "total": 85,
#     "total_pages": 5, "has_next": True, "has_previous": True
# }
```

---

## 11. Face Recognition Helpers

### `_download_cascade(dest_path)`

**File:** `services/face_recognition_service.py:27`

| Aspect | Detail |
|--------|--------|
| **Purpose** | Download the Haar cascade XML classifier file from OpenCV's GitHub repository when it's not found locally. Used as a fallback during module initialisation. |
| **Syntax** | `_download_cascade(dest_path: str) -> None` |
| **Parameters** | |
| `dest_path` | `str` — Absolute path where the cascade XML should be saved |
| **Returns** | `None` |
| **Exceptions** | None (logs warning on failure; does not raise) |

#### Step-by-Step Working

1. Import `urllib.request` (lazy import).
2. Construct the URL to `haarcascade_frontalface_default.xml` from OpenCV's GitHub `master` branch.
3. Log that the download is starting.
4. Call `urllib.request.urlretrieve(url, dest_path)` to download the file.
5. Log success.
6. On any exception, log a warning with the error details (does not propagate).

#### Example

```python
_download_cascade("/path/to/haarcascade_frontalface_default.xml")
# Downloads from GitHub if not present locally
```

---

## Summary of All Standalone Functions

| Function | Module | Purpose |
|----------|--------|---------|
| `main()` | `main.py` | Application entry point |
| `setup_logging()` | `logger/logging_config.py` | Configure root logger with file + stream handlers |
| `get_logger(name)` | `logger/logging_config.py` | Get a child logger of the `"sdms"` namespace |
| `apply_theme(mode)` | `gui/theme.py` | Initialize CustomTkinter theme |
| `generate_timestamp()` | `utilities/helpers.py` | Current UTC time as ISO-8601 string |
| `generate_document_id()` | `utilities/helpers.py` | Random UUID4 hex document ID |
| `sanitize_filename(filename)` | `utilities/helpers.py` | Remove unsafe characters from filenames |
| `validate_file_path(file_path)` | `utilities/helpers.py` | Resolve and validate a file path |
| `ensure_directory(path)` | `utilities/helpers.py` | Create directory (and parents) if missing |
| `is_valid_object_id(id_string)` | `utilities/helpers.py` | Validate a 24-char hex MongoDB ObjectId |
| `generate_aes_key()` | `crypto/key_generator.py` | 32-byte random AES-256 key |
| `generate_iv()` | `crypto/key_generator.py` | 16-byte random AES-CBC IV |
| `generate_salt()` | `crypto/key_generator.py` | 16-byte random salt |
| `generate_secure_token(length)` | `crypto/key_generator.py` | URL-safe hex token |
| `generate_crypto_id()` | `crypto/key_generator.py` | UUID4 hex identifier |
| `b64_encode(data)` | `crypto/base64_utils.py` | Encode bytes to Base64 string |
| `b64_decode(encoded)` | `crypto/base64_utils.py` | Decode Base64 string to bytes |
| `_ease_out_cubic(t)` | `gui/animations.py` | Cubic ease-out curve |
| `_ease_in_out_cubic(t)` | `gui/animations.py` | Cubic ease-in-out curve |
| `fade_in(widget, steps, delay)` | `gui/animations.py` | Fade in a widget |
| `fade_out(widget, steps, delay, callback)` | `gui/animations.py` | Fade out a widget |
| `slide_in_from_left(...)` | `gui/animations.py` | Slide widget in from left |
| `slide_in_from_right(...)` | `gui/animations.py` | Slide widget in from right |
| `pulse_color(widget, prop, colors, interval)` | `gui/animations.py` | Cycle colours on a widget property |
| `scale_in(widget, steps, delay)` | `gui/animations.py` | Scale-in animation |
| `bind_smooth_scroll(widget)` | `gui/smooth_scrolling.py` | Bind cross-platform mousewheel scrolling |
| `rebind_scroll(content_frame)` | `gui/smooth_scrolling.py` | Rebind scroll events after content changes |
| `icon(name)` | `gui/assets.py` | Look up semantic icon Unicode character |
| `file_icon(extension)` | `gui/assets.py` | Look up file type icon by extension |
| `_format_file_size(size_bytes)` | `document_listing_service.py` | Human-readable file size string |
| `_get_file_extension(filename)` | `document_listing_service.py` | Lowercase file extension with dot |
| `_safe_document_info(doc)` | `document_listing_service.py` | Extract safe metadata (no crypto fields) |
| `_build_pagination_meta(total, page, per_page)` | `document_listing_service.py` | Build pagination response metadata |
| `_download_cascade(dest_path)` | `face_recognition_service.py` | Download Haar cascade XML from GitHub |

---

*End of Function Documentation*
