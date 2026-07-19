# SDMS Face Recognition Documentation

## Table of Contents

1. [Overview](#1-overview)
2. [Libraries and Dependencies](#2-libraries-and-dependencies)
3. [Constants and Configuration](#3-constants-and-configuration)
4. [Process Pipeline](#4-process-pipeline)
5. [Enrollment Flow](#5-enrollment-flow)
6. [Recognition (Authentication) Flow](#6-recognition-authentication-flow)
7. [Feature Extraction Details](#7-feature-extraction-details)
8. [Matching Algorithm](#8-matching-algorithm)
9. [Error Handling](#9-error-handling)
10. [Possible Improvements](#10-possible-improvements)

---

## 1. Overview

The SDMS face recognition module provides biometric authentication using **OpenCV's Local Binary Pattern Histograms (LBPH)** combined with **Haar cascade face detection**. It runs entirely locally on the user's machine — no cloud services, APIs, or external servers are involved.

### High-Level Architecture

```
┌──────────────────────────────────────────────────────┐
│                  USER INTERACTION                     │
│          (Tkinter GUI → Camera Feed)                 │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│              CAMERA ACCESS LAYER                      │
│          cv2.VideoCapture(0) → frame capture         │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│            FACE DETECTION LAYER                       │
│    Haar Cascade → face bounding box extraction       │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│          FACE PREPROCESSING LAYER                     │
│    Grayscale → Resize 200×200 → Crop to face ROI     │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│         FEATURE EXTRACTION LAYER                      │
│    LBP computation → Histogram (4×4 blocks)          │
│    → Concatenated 944-dim feature vector             │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│            MATCHING LAYER                             │
│    Chi-Square distance vs enrolled users             │
│    → Threshold comparison (≤ 55.0)                   │
└──────────────────┬───────────────────────────────────┘
                   │
                   v
┌──────────────────────────────────────────────────────┐
│           SESSION CREATION                            │
│    If match → Create session with user credentials   │
│    If no match → Reject with error                   │
└──────────────────────────────────────────────────────┘
```

---

## 2. Libraries and Dependencies

### Required Packages

| Package | Import | Version | Purpose |
|---------|--------|---------|---------|
| opencv-contrib-python | `cv2` | 4.8+ | Camera access, face detection, LBP features |
| opencv-contrib-python | `cv2.face.LBPHFaceRecognizer` | — | LBP histogram computation |
| numpy | `numpy` | 1.24+ | Array operations, histogram averaging |

### Installation

```bash
pip install opencv-contrib-python numpy
```

> **Note:** The `cv2.face` module is only available in `opencv-contrib-python`, not the base `opencv-python` package. Using the wrong package will result in `AttributeError: module 'cv2' has no attribute 'face'`.

### Haar Cascade File

| Property | Details |
|----------|---------|
| Filename | `haarcascade_frontalface_default.xml` |
| Source | OpenCV's pre-trained classifier data |
| Location | OpenCV's data directory or downloaded to project |
| Auto-download | Yes — if the file is not found locally, it is downloaded from OpenCV's GitHub repository |

---

## 3. Constants and Configuration

| Constant | Value | Description |
|----------|-------|-------------|
| `FACE_MATCH_THRESHOLD` | `55.0` | Maximum Chi-Square distance for a face match |
| `ENROLLMENT_SAMPLES` | `5` | Number of face samples captured during enrollment |
| `CAMERA_INDEX` | `0` | Index of the camera device to use |
| `FACE_IMAGE_SIZE` | `(200, 200)` | Target size for preprocessed face images |
| `LBP_RADIUS` | `1` | Radius for LBP computation |
| `LBP_NEIGHBORS` | `8` | Number of neighboring pixels for LBP |
| `LBP_GRID_X` | `4` | Horizontal grid blocks for spatial histogram |
| `LBP_GRID_Y` | `4` | Vertical grid blocks for spatial histogram |
| `HISTOGRAM_BINS` | `59` | Number of bins per LBP histogram block |
| `FEATURE_VECTOR_SIZE` | `944` | Total feature vector size (4×4×59) |

---

## 4. Process Pipeline

### 4.1 Camera Access

```python
import cv2

cap = cv2.VideoCapture(0)  # CAMER_INDEX = 0

if not cap.isOpened():
    raise RuntimeError("Camera not available")

ret, frame = cap.read()
if not ret:
    raise RuntimeError("Failed to capture frame from camera")

# Display camera feed in GUI
cv2.imshow("Camera Feed", frame)
```

| Step | Action |
|------|--------|
| 1 | Open camera device at index 0 |
| 2 | Verify camera is accessible (`cap.isOpened()`) |
| 3 | Read a frame (`cap.read()`) |
| 4 | Display frame in GUI window (optional, for user feedback) |
| 5 | Release camera when done (`cap.release()`) |

### 4.2 Face Detection

```python
import cv2

# Load Haar cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# Convert to grayscale for detection
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Detect faces
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
)
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| Input | Grayscale frame | Haar cascades work on single-channel images |
| `scaleFactor` | 1.1 | Scale reduction per image pyramid level |
| `minNeighbors` | 5 | Minimum neighbors for a detection to be accepted |
| `minSize` | (30, 30) | Minimum face size in pixels |
| Output | Array of `(x, y, w, h)` bounding boxes | One per detected face |

### 4.3 Face Preprocessing

| Step | Operation | Detail |
|------|-----------|--------|
| 1 | Convert to grayscale | `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` |
| 2 | Crop to face bounding box | `gray[y:y+h, x:x+w]` |
| 3 | Resize to 200×200 | `cv2.resize(cropped_face, (200, 200))` |
| 4 | (Optional) Histogram equalization | Improve contrast for varying lighting |

### 4.4 Feature Extraction (LBP + Histogram)

| Step | Operation | Output |
|------|-----------|--------|
| 1 | Compute LBP image | 200×200 image where each pixel holds its LBP code |
| 2 | Divide into 4×4 grid | 16 spatial blocks |
| 3 | Compute histogram per block | 59-bin histogram per block |
| 4 | Concatenate histograms | 16 × 59 = **944-dimensional** feature vector |

*(Detailed in Section 7)*

### 4.5 Matching

| Step | Operation |
|------|-----------|
| 1 | Get all enrolled users' face encodings from database |
| 2 | Compute Chi-Square distance between input histogram and each enrolled histogram |
| 3 | Find the minimum distance |
| 4 | If min_distance ≤ `FACE_MATCH_THRESHOLD` (55.0) → **Match found** |
| 5 | If min_distance > 55.0 → **No match** |

*(Detailed in Section 8)*

---

## 5. Enrollment Flow

Face enrollment captures multiple samples of the user's face and averages them to create a robust face encoding.

### Step-by-Step Process

```
┌───────────────────────────────────────────────────────┐
│              ENROLLMENT FLOW (5 samples)              │
│                                                       │
│  Sample 1: "Look straight at camera"                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Capture  │→ │ Detect   │→ │ Compute LBP      │   │
│  │ Frame    │  │ Face     │  │ Histogram #1     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  Sample 2: "Turn slightly left"                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Capture  │→ │ Detect   │→ │ Compute LBP      │   │
│  │ Frame    │  │ Face     │  │ Histogram #2     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  Sample 3: "Turn slightly right"                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Capture  │→ │ Detect   │→ │ Compute LBP      │   │
│  │ Frame    │  │ Face     │  │ Histogram #3     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  Sample 4: "Tilt head up"                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Capture  │→ │ Detect   │→ │ Compute LBP      │   │
│  │ Frame    │  │ Face     │  │ Histogram #4     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  Sample 5: "Look straight (final)"                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Capture  │→ │ Detect   │→ │ Compute LBP      │   │
│  │ Frame    │  │ Face     │  │ Histogram #5     │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Average all 5 histograms element-wise            │ │
│  │ averaged_hist[i] = (h1[i]+h2[i]+...+h5[i]) / 5 │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Store averaged_hist in users.face_encoding       │ │
│  │ Set users.face_enrolled = True                   │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

### Enrollment Pseudocode

```python
def enroll_face(user_id):
    histograms = []
    prompts = [
        "Look straight at the camera",
        "Turn slightly to the left",
        "Turn slightly to the right",
        "Tilt your head up slightly",
        "Look straight at the camera (final)"
    ]

    for i in range(ENROLLMENT_SAMPLES):  # 5 iterations
        display_instruction(prompts[i])
        frame = capture_frame()
        face = detect_face(frame)
        if face is None:
            raise Error("No face detected")
        preprocessed = preprocess_face(face)
        hist = compute_lbp_histogram(preprocessed)
        histograms.append(hist)

    # Average all histograms
    averaged = np.mean(histograms, axis=0)

    # Store in database
    update_user(user_id, {
        "face_encoding": averaged.tolist(),
        "face_enrolled": True
    })
```

---

## 6. Recognition (Authentication) Flow

### Step-by-Step Process

```
┌───────────────────────────────────────────────────────┐
│              RECOGNITION FLOW                          │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 1. Retrieve all enrolled users from database    │ │
│  │    SELECT user_id, face_encoding                │ │
│  │    FROM users WHERE face_enrolled = True        │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 2. Open camera and capture single frame         │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 3. Detect face in frame                         │ │
│  │    - No face → Error: "No face detected"        │ │
│  │    - Multiple faces → Error: "Multiple faces"   │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 4. Preprocess face                              │ │
│  │    Grayscale → Resize 200×200 → Crop to ROI     │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 5. Compute LBP histogram (944-dim vector)       │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 6. Compare against all enrolled users           │ │
│  │                                                  │ │
│  │    For each enrolled user:                      │ │
│  │      distance = chi_square_distance(             │ │
│  │          input_hist,                             │ │
│  │          enrolled_user.face_encoding             │ │
│  │      )                                          │ │
│  │                                                  │ │
│  │    best_match = min(distances)                  │ │
│  │    matched_user = argmin(distances)             │ │
│  └──────────────────────────────────────────────────┘ │
│                       │                               │
│                       v                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 7. Decision                                     │ │
│  │                                                  │ │
│  │    best_distance ≤ 55.0?                        │ │
│  │    ├── YES → Create session for matched_user    │ │
│  │    └── NO  → Reject: "Face not recognized"     │ │
│  └──────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────┘
```

### Recognition Pseudocode

```python
def recognize_face():
    # Step 1: Get all enrolled users
    enrolled_users = db.users.find({"face_enrolled": True})
    if not enrolled_users:
        raise Error("No enrolled users in database")

    # Step 2: Capture frame
    frame = capture_frame()

    # Step 3: Detect face
    faces = detect_faces(frame)
    if len(faces) == 0:
        raise Error("No face detected in camera frame")
    if len(faces) > 1:
        raise Error("Multiple faces detected — only one person allowed")
    face = faces[0]

    # Step 4-5: Preprocess and extract features
    preprocessed = preprocess_face(face)
    input_hist = compute_lbp_histogram(preprocessed)

    # Step 6: Compare against all enrolled users
    best_distance = float('inf')
    best_user = None

    for user in enrolled_users:
        enrolled_hist = np.array(user["face_encoding"])
        distance = chi_square_distance(input_hist, enrolled_hist)
        if distance < best_distance:
            best_distance = distance
            best_user = user

    # Step 7: Make decision
    if best_distance <= FACE_MATCH_THRESHOLD:  # 55.0
        session = create_session(best_user)
        return session
    else:
        raise AuthenticationError("Face not recognized")
```

---

## 7. Feature Extraction Details

### 7.1 Local Binary Pattern (LBP)

LBP is a texture descriptor that labels each pixel of an image by thresholding its neighborhood and treating the result as a binary number.

#### LBP Computation (3×3 neighborhood)

For a center pixel `c` with intensity value, and 8 neighbors:

```
P7  P6  P5
P4  C   P3
P0  P1  P2
```

**LBP code computation:**

```
For each neighbor Pᵢ:
  if Pᵢ ≥ C: bitᵢ = 1
  else:       bitᵢ = 0

LBP code = bit₇ bit₆ bit₅ bit₄ bit₃ bit₂ bit₇ bit₁  (8-bit binary)
         = value between 0 and 255
```

#### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Radius | 1 | Distance from center pixel to neighbors |
| Neighbors | 8 | Number of neighboring pixels sampled |

### 7.2 LBP Histogram (Uniform Patterns)

Raw LBP codes produce 256 possible values (2^8). OpenCV's LBPH implementation uses **uniform patterns** to reduce dimensionality:

- A pattern is **uniform** if it contains at most 2 bitwise transitions (0→1 or 1→0)
- Uniform patterns are mapped to 59 unique codes
- Non-uniform patterns are grouped into a single bin

| Pattern Type | Count | Bins |
|-------------|-------|------|
| Uniform patterns | 58 | 0–57 |
| Non-uniform patterns | 1 | 58 |
| **Total bins** | | **59** |

### 7.3 Spatial Histogram (4×4 Grid)

The preprocessed face image (200×200) is divided into a 4×4 spatial grid:

```
┌─────────┬─────────┬─────────┬─────────┐
│ Block 0 │ Block 1 │ Block 2 │ Block 3 │
│ 50×50px │ 50×50px │ 50×50px │ 50×50px │
├─────────┼─────────┼─────────┼─────────┤
│ Block 4 │ Block 5 │ Block 6 │ Block 7 │
├─────────┼─────────┼─────────┼─────────┤
│ Block 8 │ Block 9 │Block 10 │Block 11 │
├─────────┼─────────┼─────────┼─────────┤
│Block 12 │Block 13 │Block 14 │Block 15 │
└─────────┴─────────┴─────────┴─────────┘
```

Each block produces a **59-bin histogram** of LBP codes within that region.

### 7.4 Feature Vector Construction

```
Feature Vector = [hist_block_0 | hist_block_1 | ... | hist_block_15]

Each hist_block_i = 59 values

Total length = 16 blocks × 59 bins = 944 dimensions
```

| Property | Value |
|----------|-------|
| Feature vector length | 944 |
| Data type | Float (numpy array) |
| Normalization | Histogram normalization per block |

### 7.5 Code Example

```python
import cv2
import numpy as np

def compute_lbp_histogram(face_image):
    """
    Compute LBPH feature vector from a preprocessed face image.

    Args:
        face_image: Grayscale image (200x200 numpy array)

    Returns:
        numpy array of shape (944,) — concatenated histograms
    """
    # Create LBPH face recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=4,
        grid_y=4
    )

    # Compute LBP and histograms internally
    # The recognizer stores the histogram of the training image
    recognizer.train([face_image], np.array([0]))

    # Extract the histogram from the trained recognizer
    histograms = recognizer.getHistograms()

    # Concatenate all block histograms into single vector
    feature_vector = np.concatenate(histograms)

    return feature_vector
```

---

## 8. Matching Algorithm

### 8.1 Chi-Square Distance

The Chi-Square distance measures the dissimilarity between two histograms:

```
χ²(A, B) = Σᵢ (Aᵢ - Bᵢ)² / (Aᵢ + Bᵢ)
```

Where:
- `A` = input face histogram (944 dimensions)
- `B` = enrolled face histogram (944 dimensions)
- `Aᵢ`, `Bᵢ` = values in the i-th bin

### 8.2 Distance Interpretation

| Distance Range | Interpretation | Decision |
|----------------|---------------|----------|
| 0.0 | Identical histograms (perfect match) | Accept |
| 0.0 – 10.0 | Very strong match | Accept |
| 10.0 – 30.0 | Strong match | Accept |
| 30.0 – 55.0 | Moderate match (within threshold) | **Accept** |
| > 55.0 | Weak or no match | **Reject** |

### 8.3 Decision Flow

```
Input histogram vs Enrolled histogram #1 → distance₁
Input histogram vs Enrolled histogram #2 → distance₂
Input histogram vs Enrolled histogram #3 → distance₃
...
Input histogram vs Enrolled histogram #N → distanceₙ

best_distance = min(distance₁, distance₂, ..., distanceₙ)
best_user = argmin(distance₁, distance₂, ..., distanceₙ)

if best_distance ≤ 55.0:
    return MATCH → Authenticate best_user
else:
    return NO_MATCH → Reject
```

### 8.4 Chi-Square Implementation

```python
def chi_square_distance(hist1, hist2):
    """
    Compute Chi-Square distance between two histograms.

    Args:
        hist1: numpy array (944,)
        hist2: numpy array (944,)

    Returns:
        float: Chi-Square distance (0.0 = identical)
    """
    hist1 = hist1.astype(float)
    hist2 = hist2.astype(float)

    # Avoid division by zero
    denominator = hist1 + hist2
    denominator[denominator == 0] = 1e-10

    distance = np.sum((hist1 - hist2) ** 2 / denominator)
    return distance
```

### 8.5 Alternative Matching Methods

| Method | Pros | Cons | Current Status |
|--------|------|------|---------------|
| Chi-Square | Good for histograms, fast | Sensitive to bin alignment | **Used** |
| Euclidean | Simple, fast | Less suited for histograms | Not used |
| Cosine similarity | Scale-invariant | Less interpretable for LBPH | Not used |
| Correlation | Robust to brightness changes | Slower | Not used |

---

## 9. Error Handling

### 9.1 Error Cases and Responses

| Error | Cause | Response |
|-------|-------|----------|
| `Camera not available` | Camera index invalid or hardware missing | Display error message; suggest checking camera connection |
| `Failed to capture frame` | Camera disconnected or blocked by another app | Retry capture; display error |
| `No face detected` | User's face not visible, poor lighting, too far from camera | Prompt user to adjust position or lighting |
| `Multiple faces detected` | More than one person in camera frame | Prompt user to ensure only one face is visible |
| `Cascade not loaded` | Haar cascade XML file missing or corrupted | Auto-download from OpenCV GitHub; raise error if download fails |
| `No enrolled users` | No users have completed face enrollment | Prompt user to enroll face first |
| `Face not recognized` | Best distance exceeds threshold | Display "Face not recognized" error; suggest password login |
| `Database error` | MongoDB connection issue | Log error; display generic error message |

### 9.2 Haar Cascade Auto-Download

```python
import cv2
import urllib.request
import os

CASCADE_URL = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

def load_face_cascade():
    if not os.path.exists(CASCADE_PATH):
        urllib.request.urlretrieve(CASCADE_URL, CASCADE_PATH)

    cascade = cv2.CascadeClassifier(CASCADE_PATH)
    if cascade.empty():
        raise RuntimeError("Failed to load Haar cascade classifier")
    return cascade
```

### 9.3 Error Handling Flow

```python
def safe_recognize_face():
    try:
        # Step 1: Load cascade
        cascade = load_face_cascade()

        # Step 2: Open camera
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            return {"status": "error", "message": "Camera not available"}

        # Step 3: Capture and detect
        ret, frame = cap.read()
        if not ret:
            return {"status": "error", "message": "Failed to capture frame"}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        if len(faces) == 0:
            return {"status": "error", "message": "No face detected"}
        if len(faces) > 1:
            return {"status": "error", "message": "Multiple faces detected"}

        # Step 4-6: Preprocess, extract, match
        # ...

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cap.release()
```

---

## 10. Possible Improvements

### 10.1 Deep Learning-Based Recognition

| Approach | Model | Advantage |
|----------|-------|-----------|
| FaceNet | Google's Inception-based network | High accuracy, discriminative embeddings |
| ArcFace | Angular margin-based loss | State-of-the-art accuracy |
| dlib | ResNet-based face recognition | Good balance of speed and accuracy |
| OpenCV DNN | Caffe/TensorFlow models | Integrates with existing OpenCV setup |

### 10.2 Threshold Tuning

| Improvement | Description |
|-------------|-------------|
| Calibration dataset | Test with labeled face images to find optimal threshold |
| Per-user thresholds | Different thresholds per user based on enrollment quality |
| Dynamic threshold | Adjust threshold based on lighting/quality conditions |
| ROC curve analysis | Plot true positive rate vs false positive rate |

### 10.3 Liveness Detection

| Method | Description | Protects Against |
|--------|-------------|------------------|
| Blink detection | Detect eye blinks using facial landmarks | Photo attacks |
| Head movement | Require user to turn head slightly | Static photo |
| Texture analysis | Detect screen/printed paper textures | Screen replay |
| Depth estimation | Use depth camera if available | 3D mask attacks |
| Infrared | Thermal camera to detect living tissue | Silicone masks |

### 10.4 Preprocessing Improvements

| Improvement | Description |
|-------------|-------------|
| Histogram equalization | CLAHE (Contrast Limited Adaptive Histogram Equalization) |
| Illumination normalization | Remove lighting variations |
| Face alignment | Align eyes to horizontal axis |
| Skin segmentation | Isolate face region more precisely |
| Noise reduction | Gaussian blur before detection |

### 10.5 Performance Optimizations

| Optimization | Description |
|--------------|-------------|
| GPU acceleration | Use CUDA-enabled OpenCV for faster LBP computation |
| Caching enrolled histograms | Load all histograms into memory at startup |
| Batch comparison | Vectorized distance computation across all users |
| Early termination | Skip remaining users if distance exceeds threshold |
| Frame skipping | Process every Nth frame instead of every frame |

### 10.6 Additional Features

| Feature | Description |
|---------|-------------|
| Multi-face enrollment | Allow enrolling multiple face variations |
| Confidence score | Display match confidence to user |
| Re-enrollment | Allow users to improve their face encoding |
| Face quality check | Reject low-quality captures (blur, darkness) |
| Enrollment quality score | Rate enrollment quality and prompt re-enrollment if low |

---

## Appendix: Quick Reference

### Constants Summary

```python
FACE_MATCH_THRESHOLD = 55.0    # Maximum Chi-Square distance for match
ENROLLMENT_SAMPLES = 5         # Face samples during enrollment
CAMERA_INDEX = 0               # Default camera device
FACE_IMAGE_SIZE = (200, 200)   # Preprocessed face dimensions
LBP_RADIUS = 1                 # LBP neighborhood radius
LBP_NEIGHBORS = 8              # LBP neighbor count
LBP_GRID_X = 4                 # Horizontal histogram grid
LBP_GRID_Y = 4                 # Vertical histogram grid
HISTOGRAM_BINS = 59            # Bins per LBP block histogram
FEATURE_VECTOR_SIZE = 944      # Total feature dimensions (4×4×59)
```

### File Reference

| File | Purpose |
|------|---------|
| `haarcascade_frontalface_default.xml` | Pre-trained Haar cascade for frontal face detection |
| `face_recognizer.py` | Core face recognition module (enrollment + recognition) |
| `camera_manager.py` | Camera access and frame capture |
| `users` collection (`face_encoding` field) | Stored LBP histograms for enrolled users |
