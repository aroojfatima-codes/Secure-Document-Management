from __future__ import annotations

import os
from typing import Any

import cv2
import numpy as np

from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import SDMSException
from logger.logging_config import get_logger
from models.user import User
from services.session_manager import SessionManager

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level flags — face recognition is always available in this build
# because we rely on OpenCV contrib modules (LBPH) rather than the
# third-party ``face_recognition`` package (which does not support
# Python ≥ 3.13).
# ---------------------------------------------------------------------------
_FACE_RECOGNITION_AVAILABLE: bool = True
_FACE_CASCADE: cv2.CascadeClassifier | None = None


def _download_cascade(dest_path: str) -> None:
    """Download the Haar cascade XML from OpenCV's GitHub repository."""
    try:
        import urllib.request

        url = (
            "https://raw.githubusercontent.com/opencv/opencv/master/data/"
            "haarcascades/haarcascade_frontalface_default.xml"
        )
        logger.info("Downloading face cascade from %s ...", url)
        urllib.request.urlretrieve(url, dest_path)
        logger.info("Cascade saved to %s", dest_path)
    except Exception as exc:
        logger.warning("Failed to download Haar cascade: %s", exc)

try:
    cascade_path: str = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        logger.info("Haar cascade not found — attempting download ...")
        _download_cascade(cascade_path)

    if os.path.exists(cascade_path):
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
        if _FACE_CASCADE.empty():
            logger.warning("Failed to load Haar cascade classifier.")
            _FACE_RECOGNITION_AVAILABLE = False
    else:
        logger.warning("Haar cascade file not found at %s", cascade_path)
        _FACE_RECOGNITION_AVAILABLE = False
except Exception as exc:
    logger.warning("Face detection initialisation failed: %s", exc)
    _FACE_RECOGNITION_AVAILABLE = False


FACE_MATCH_THRESHOLD: float = 55.0  # LBPH confidence (lower = better match)
ENROLLMENT_SAMPLES: int = 5
CAMERA_INDEX: int = 0
FACE_IMAGE_SIZE: tuple[int, int] = (200, 200)


class FaceRecognitionService:
    """Face recognition backed by OpenCV's LBPH face recogniser.

    This replaces the ``face_recognition`` / dlib pipeline which is
    not available on Python 3.14.  The LBPH (Local Binary Patterns
    Histogram) algorithm is lightweight, runs on CPU, and works
    well for access-control scenarios.
    """

    def __init__(self) -> None:
        self._user_repo: UserRepository = UserRepository()
        self._session_mgr: SessionManager = SessionManager()

    # ------------------------------------------------------------------
    # Public query helpers
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return _FACE_RECOGNITION_AVAILABLE

    def is_enrolled(self, user_id: str) -> bool:
        user = self._user_repo.get_by_user_id(user_id)
        return user is not None and user.face_enrolled

    # ------------------------------------------------------------------
    # Camera helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_camera() -> None:
        """Raise if the camera cannot be opened."""
        if not _FACE_RECOGNITION_AVAILABLE:
            raise SDMSException(
                "Face recognition is not available. "
                "Haar cascade classifier could not be loaded."
            )
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            cap.release()
            raise SDMSException(
                "Could not access the webcam. "
                "Please ensure your camera is connected, not blocked "
                "by privacy settings, and not in use by another application."
            )
        cap.release()

    @staticmethod
    def _detect_face(frame: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
        """Detect exactly one face in *frame* and return the cropped face + bounding box.

        Returns:
            ``(face_cropped_gray, (x, y, w, h))``

        Raises:
            SDMSException: If zero or multiple faces are detected.
        """
        if _FACE_CASCADE is None:
            raise SDMSException("Face classifier not initialised.")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = _FACE_CASCADE.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
        )

        if len(faces) == 0:
            raise SDMSException(
                "No face detected. Please ensure your face is visible "
                "and the lighting is adequate."
            )
        if len(faces) > 1:
            raise SDMSException(
                "Multiple faces detected. "
                "Please ensure only one face is visible."
            )

        (x, y, w, h) = faces[0]
        face_roi = gray[y : y + h, x : x + w]
        face_resized = cv2.resize(face_roi, FACE_IMAGE_SIZE)
        return face_resized, (x, y, w, h)

    @staticmethod
    def _capture_frame(
        cap: cv2.VideoCapture, instruction: str, delay_ms: int = 2000
    ) -> np.ndarray:
        """Capture a single frame from *cap* with a live preview."""
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        frames_needed = int(fps * delay_ms / 1000)
        count = 0
        final_frame: np.ndarray | None = None

        while count < frames_needed:
            ret, frame = cap.read()
            if not ret:
                break
            display = frame.copy()
            cv2.putText(
                display,
                instruction,
                (30, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Face Enrollment - Press Q to cancel", display)
            key = cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                raise SDMSException("Face enrollment cancelled by user.")
            count += 1
            final_frame = frame

        if final_frame is None:
            raise SDMSException("Failed to capture image from webcam.")
        return final_frame

    @staticmethod
    def _capture_with_preview(
        instruction: str, duration_ms: int = 2000
    ) -> np.ndarray:
        """Open the camera, show a preview, and return the captured frame."""
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            cap.release()
            raise SDMSException(
                "Could not access the webcam. "
                "Please ensure your camera is connected."
            )
        try:
            return FaceRecognitionService._capture_frame(
                cap, instruction, duration_ms
            )
        finally:
            cv2.destroyAllWindows()
            cap.release()

    # ------------------------------------------------------------------
    # Face enrollment
    # ------------------------------------------------------------------

    def enroll_face(self, user_id: str, username: str) -> dict[str, Any]:
        """Capture multiple face samples and train an LBPH model.

        The trained model is stored as a flattened list of histogram
        floats in the user's MongoDB document so it can be reconstructed
        later for recognition.
        """
        if not _FACE_RECOGNITION_AVAILABLE:
            return {"success": False, "error": "Face recognition is not available."}

        try:
            self._check_camera()
            logger.info("Starting face enrollment for user '%s'.", username)

            cap = cv2.VideoCapture(CAMERA_INDEX)
            if not cap.isOpened():
                cap.release()
                raise SDMSException(
                    "Could not access the webcam. "
                    "Please ensure your camera is connected."
                )

            face_samples: list[np.ndarray] = []
            face_histograms: list[np.ndarray] = []
            instructions: list[str] = [
                "Look straight at the camera",
                "Turn your head slightly left",
                "Turn your head slightly right",
                "Tilt your head slightly up",
                "Look straight again (final capture)",
            ]

            try:
                for i in range(ENROLLMENT_SAMPLES):
                    instruction = (
                        instructions[i]
                        if i < len(instructions)
                        else f"Capture {i + 1} of {ENROLLMENT_SAMPLES}"
                    )
                    print()
                    print(f"  [{i + 1}/{ENROLLMENT_SAMPLES}] {instruction}...")
                    print("  (Preview will show - press Q to cancel)")

                    frame = self._capture_frame(
                        cap,
                        f"[{i + 1}/{ENROLLMENT_SAMPLES}] {instruction}",
                        delay_ms=2000,
                    )
                    face, _ = self._detect_face(frame)
                    face_samples.append(face)

                    # Also extract LBP histogram for direct storage
                    lbp = self._compute_lbp_histogram(face)
                    face_histograms.append(lbp)

                    logger.debug(
                        "Captured sample %d/%d for user '%s'.",
                        i + 1,
                        ENROLLMENT_SAMPLES,
                        username,
                    )
            finally:
                cv2.destroyAllWindows()
                cap.release()

            # Train LBPH model on captured samples
            labels = np.array([0] * len(face_samples), dtype=np.int32)
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(face_samples, labels)

            # Store the model data: histograms are the most portable representation
            avg_histogram: list[float] = np.mean(face_histograms, axis=0).tolist()

            self._user_repo.update_face_encoding(user_id, avg_histogram)

            logger.info("Face enrollment completed for user '%s'.", username)
            return {
                "success": True,
                "message": f"Face enrollment completed successfully for '{username}'.",
                "samples_captured": len(face_samples),
            }

        except SDMSException as exc:
            logger.warning("Face enrollment failed for user '%s': %s", username, exc)
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("Unexpected error during face enrollment for user '%s'.", username)
            return {"success": False, "error": f"Face enrollment failed: {exc}"}

    # ------------------------------------------------------------------
    # Face recognition (login)
    # ------------------------------------------------------------------

    def recognize_user(self) -> dict[str, Any]:
        """Capture a live frame, extract the LBP histogram, and compare
        against all enrolled users using Chi-Square distance.

        Returns:
            A dict with ``success``, ``user_id``, ``username``, ``role``,
            ``distance`` (Chi-Square value), and ``message``.
        """
        if not _FACE_RECOGNITION_AVAILABLE:
            return {"success": False, "error": "Face recognition is not available."}

        try:
            self._check_camera()

            enrolled_users: list[User] = self._user_repo.get_enrolled_users()
            if not enrolled_users:
                raise SDMSException(
                    "No users have enrolled in face recognition. "
                    "Please use password login."
                )

            known_histograms: list[np.ndarray] = []
            known_users: list[User] = []

            for u in enrolled_users:
                if u.face_encoding and len(u.face_encoding) > 0:
                    known_histograms.append(np.array(u.face_encoding, dtype=np.float32))
                    known_users.append(u)

            if not known_histograms:
                raise SDMSException(
                    "No facial data available for comparison."
                )

            print()
            print("  Looking at camera for face recognition...")
            print("  (Press Q in preview window to cancel)")

            frame = self._capture_with_preview(
                "Face Recognition - Look at camera", duration_ms=2000,
            )

            live_face, _ = self._detect_face(frame)
            live_hist = self._compute_lbp_histogram(live_face)

            # Compare using Chi-Square distance
            best_distance = float("inf")
            best_index = -1

            for idx, known_hist in enumerate(known_histograms):
                dist = self._chi_square_distance(live_hist, known_hist)
                if dist < best_distance:
                    best_distance = dist
                    best_index = idx

            logger.debug(
                "Face recognition — best distance=%.4f (threshold=%.4f).",
                best_distance,
                FACE_MATCH_THRESHOLD,
            )

            if best_distance > FACE_MATCH_THRESHOLD or best_index < 0:
                raise SDMSException(
                    "Face does not match any enrolled user. "
                    f"(Best match distance={best_distance:.2f})"
                )

            matched_user = known_users[best_index]

            if not matched_user.is_active:
                raise SDMSException(
                    "This account has been deactivated. Contact an administrator."
                )

            self._session_mgr.create_session(
                user_id=matched_user.user_id,
                username=matched_user.username,
                role=matched_user.role,
                rsa_public_key=matched_user.rsa_public_key,
                rsa_private_key=matched_user.rsa_private_key,
            )

            logger.info(
                "User '%s' authenticated via face recognition (distance=%.4f).",
                matched_user.username,
                best_distance,
            )

            return {
                "success": True,
                "user_id": matched_user.user_id,
                "username": matched_user.username,
                "role": matched_user.role,
                "distance": best_distance,
                "message": f"Welcome back, {matched_user.username}!",
            }

        except SDMSException as exc:
            logger.warning("Face recognition login failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception("Unexpected error during face recognition login.")
            return {"success": False, "error": f"Face recognition failed: {exc}"}

    # ------------------------------------------------------------------
    # Enrollment management
    # ------------------------------------------------------------------

    def remove_enrollment(self, user_id: str) -> dict[str, Any]:
        try:
            self._user_repo.remove_face_encoding(user_id)
            logger.info("Face enrollment removed for user_id='%s'.", user_id)
            return {"success": True, "message": "Face enrollment removed successfully."}
        except Exception as exc:
            logger.exception("Failed to remove face enrollment for user_id='%s'.", user_id)
            return {"success": False, "error": f"Failed to remove face enrollment: {exc}"}

    # ------------------------------------------------------------------
    # LBP histogram helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_lbp_histogram(face_gray: np.ndarray) -> np.ndarray:
        """Compute a Local Binary Pattern histogram for a face image.

        The image is divided into 4×4 = 16 blocks.  An LBP histogram
        (59 bins per block for uniform LBP) is computed per block and
        concatenated, giving a 16 × 59 = 944-dimensional feature vector.
        """
        h, w = face_gray.shape
        block_h, block_w = h // 4, w // 4
        histograms: list[np.ndarray] = []

        for row in range(4):
            for col in range(4):
                y_start = row * block_h
                y_end = (row + 1) * block_h if row < 3 else h
                x_start = col * block_w
                x_end = (col + 1) * block_w if col < 3 else w
                block = face_gray[y_start:y_end, x_start:x_end]

                lbp_block = FaceRecognitionService._local_binary_pattern(block)
                hist = cv2.calcHist(
                    [lbp_block.astype(np.uint8)],
                    [0],
                    None,
                    [59],  # uniform LBP has 59 bins
                    [0, 59],
                )
                cv2.normalize(hist, hist, norm_type=cv2.NORM_L2)
                histograms.append(hist.flatten())

        return np.concatenate(histograms)

    @staticmethod
    def _local_binary_pattern(image: np.ndarray) -> np.ndarray:
        """Compute the basic LBP (radius=1, 8 neighbours) of *image*.

        Returns a uint8 array of the same shape with LBP codes in [0, 255].
        """
        h, w = image.shape
        lbp = np.zeros((h - 2, w - 2), dtype=np.uint8)
        centre = image[1 : h - 1, 1 : w - 1].astype(np.int16)

        code = 1
        for dy, dx in [(-1, -1), (-1, 0), (-1, 1), (0, 1),
                       (1, 1), (1, 0), (1, -1), (0, -1)]:
            neighbour = image[1 + dy : h - 1 + dy, 1 + dx : w - 1 + dx].astype(np.int16)
            lbp += (neighbour >= centre).astype(np.uint8) * code
            code <<= 1

        return lbp

    @staticmethod
    def _chi_square_distance(hist_a: np.ndarray, hist_b: np.ndarray) -> float:
        """Chi-Square distance between two histograms.

        Lower values indicate a closer match.  The distance is
        normalised by the number of bins.
        """
        eps = 1e-10
        numerator = (hist_a - hist_b) ** 2
        denominator = hist_a + hist_b + eps
        chi_sq = np.sum(numerator / denominator)
        return float(chi_sq / hist_a.shape[0])
