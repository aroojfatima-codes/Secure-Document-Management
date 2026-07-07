from __future__ import annotations

from typing import Any

import numpy as np

from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import SDMSException
from logger.logging_config import get_logger
from models.user import User
from services.session_manager import SessionManager

logger = get_logger(__name__)

_FACE_RECOGNITION_AVAILABLE: bool = False
_cv2: Any = None
_face_rec: Any = None

try:
    import cv2 as _cv2_mod

    _cv2 = _cv2_mod
    import face_recognition as _face_rec_mod

    _face_rec = _face_rec_mod
    _FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    logger.warning(
        "Face recognition libraries not installed. "
        "Run: pip install opencv-python face_recognition numpy"
    )

FACE_MATCH_THRESHOLD: float = 0.5
ENROLLMENT_SAMPLES: int = 5
CAMERA_INDEX: int = 0


class FaceRecognitionService:
    def __init__(self) -> None:
        self._user_repo: UserRepository = UserRepository()
        self._session_mgr: SessionManager = SessionManager()

    def is_available(self) -> bool:
        return _FACE_RECOGNITION_AVAILABLE

    @staticmethod
    def _check_camera() -> None:
        if not _FACE_RECOGNITION_AVAILABLE:
            raise SDMSException(
                "Face recognition libraries are not installed."
            )
        cap = _cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            cap.release()
            raise SDMSException(
                "Could not access the webcam. "
                "Please ensure your camera is connected and not in use."
            )
        cap.release()

    @staticmethod
    def _get_face_encoding(frame: np.ndarray) -> Any:
        rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
        face_locations = _face_rec.face_locations(rgb)
        if len(face_locations) == 0:
            raise SDMSException(
                "No face detected. Please ensure your face is visible."
            )
        if len(face_locations) > 1:
            raise SDMSException(
                "Multiple faces detected. "
                "Please ensure only one face is visible."
            )
        encodings = _face_rec.face_encodings(rgb, face_locations)
        if not encodings:
            raise SDMSException(
                "Could not generate facial encoding. "
                "Please try again with better lighting."
            )
        return encodings[0]

    @staticmethod
    def _capture_frame(
        cap: Any, instruction: str, delay_ms: int = 2000
    ) -> np.ndarray:
        fps = cap.get(_cv2.CAP_PROP_FPS)
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
            _cv2.putText(
                display,
                instruction,
                (30, 60),
                _cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
            )
            _cv2.imshow("Face Enrollment - Press Q to cancel", display)
            key = _cv2.waitKey(30) & 0xFF
            if key == ord("q"):
                raise SDMSException("Face enrollment cancelled by user.")
            count += 1
            final_frame = frame

        if final_frame is None:
            raise SDMSException(
                "Failed to capture image from webcam."
            )
        return final_frame

    @staticmethod
    def _capture_with_preview(
        instruction: str, duration_ms: int = 2000
    ) -> np.ndarray:
        cap = _cv2.VideoCapture(CAMERA_INDEX)
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
            _cv2.destroyAllWindows()
            cap.release()

    def enroll_face(self, user_id: str, username: str) -> dict[str, Any]:
        if not _FACE_RECOGNITION_AVAILABLE:
            return {
                "success": False,
                "error": "Face recognition libraries are not installed.",
            }

        try:
            self._check_camera()
            logger.info(
                "Starting face enrollment for user '%s'.", username
            )

            cap = _cv2.VideoCapture(CAMERA_INDEX)
            if not cap.isOpened():
                cap.release()
                raise SDMSException(
                    "Could not access the webcam. "
                    "Please ensure your camera is connected."
                )

            encodings: list[Any] = []
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
                    print(
                        f"  [{i + 1}/{ENROLLMENT_SAMPLES}] {instruction}..."
                    )
                    print("  (Preview will show - press Q to cancel)")

                    frame = self._capture_frame(
                        cap,
                        f"[{i + 1}/{ENROLLMENT_SAMPLES}] {instruction}",
                        delay_ms=2000,
                    )
                    encoding = self._get_face_encoding(frame)
                    encodings.append(encoding)
                    logger.debug(
                        "Captured sample %d/%d for user '%s'.",
                        i + 1,
                        ENROLLMENT_SAMPLES,
                        username,
                    )
            finally:
                _cv2.destroyAllWindows()
                cap.release()

            avg_encoding: list[float] = (
                np.mean(encodings, axis=0).tolist()
            )

            self._user_repo.update_face_encoding(user_id, avg_encoding)

            logger.info(
                "Face enrollment completed for user '%s'.", username
            )
            return {
                "success": True,
                "message": (
                    f"Face enrollment completed successfully for "
                    f"'{username}'."
                ),
                "samples_captured": len(encodings),
            }

        except SDMSException as exc:
            logger.warning(
                "Face enrollment failed for user '%s': %s",
                username,
                exc,
            )
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception(
                "Unexpected error during face enrollment for user '%s'.",
                username,
            )
            return {
                "success": False,
                "error": f"Face enrollment failed: {exc}",
            }

    def recognize_user(self) -> dict[str, Any]:
        if not _FACE_RECOGNITION_AVAILABLE:
            return {
                "success": False,
                "error": "Face recognition libraries are not installed.",
            }

        try:
            self._check_camera()

            enrolled_users: list[User] = (
                self._user_repo.get_enrolled_users()
            )
            if not enrolled_users:
                raise SDMSException(
                    "No users have enrolled in face recognition. "
                    "Please use password login."
                )

            known_encodings: list[Any] = []
            known_users: list[User] = []

            for u in enrolled_users:
                if u.face_encoding:
                    known_encodings.append(np.array(u.face_encoding))
                    known_users.append(u)

            if not known_encodings:
                raise SDMSException(
                    "No facial data available for comparison."
                )

            print()
            print("  Looking at camera for face recognition...")
            print("  (Press Q in preview window to cancel)")

            frame = self._capture_with_preview(
                "Face Recognition - Look at camera",
                duration_ms=2000,
            )

            rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
            face_locations = _face_rec.face_locations(rgb)

            if len(face_locations) == 0:
                raise SDMSException(
                    "No face detected. Please ensure your face is visible."
                )
            if len(face_locations) > 1:
                raise SDMSException(
                    "Multiple faces detected. "
                    "Please ensure only you are visible."
                )

            face_encodings = _face_rec.face_encodings(
                rgb, face_locations
            )
            if not face_encodings:
                raise SDMSException(
                    "Could not generate facial encoding."
                )

            live_encoding = face_encodings[0]
            distances = _face_rec.face_distance(
                known_encodings, live_encoding
            )
            best_match_index = int(np.argmin(distances))
            best_distance = float(distances[best_match_index])

            if best_distance > FACE_MATCH_THRESHOLD:
                logger.info(
                    "Face recognition failed — best distance=%.4f "
                    "(threshold=%.4f).",
                    best_distance,
                    FACE_MATCH_THRESHOLD,
                )
                raise SDMSException(
                    "Face does not match any enrolled user."
                )

            matched_user = known_users[best_match_index]

            if not matched_user.is_active:
                raise SDMSException(
                    "This account has been deactivated. "
                    "Contact an administrator."
                )

            self._session_mgr.create_session(
                user_id=matched_user.user_id,
                username=matched_user.username,
                role=matched_user.role,
                rsa_public_key=matched_user.rsa_public_key,
                rsa_private_key=matched_user.rsa_private_key,
            )

            logger.info(
                "User '%s' authenticated via face recognition "
                "(distance=%.4f).",
                matched_user.username,
                best_distance,
            )

            return {
                "success": True,
                "user_id": matched_user.user_id,
                "username": matched_user.username,
                "role": matched_user.role,
                "distance": best_distance,
                "message": (
                    f"Welcome back, {matched_user.username}!"
                ),
            }

        except SDMSException as exc:
            logger.warning("Face recognition login failed: %s", exc)
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            logger.exception(
                "Unexpected error during face recognition login."
            )
            return {
                "success": False,
                "error": f"Face recognition failed: {exc}",
            }

    def remove_enrollment(self, user_id: str) -> dict[str, Any]:
        try:
            self._user_repo.remove_face_encoding(user_id)
            logger.info(
                "Face enrollment removed for user_id='%s'.", user_id
            )
            return {
                "success": True,
                "message": "Face enrollment removed successfully.",
            }
        except Exception as exc:
            logger.exception(
                "Failed to remove face enrollment for user_id='%s'.",
                user_id,
            )
            return {
                "success": False,
                "error": f"Failed to remove face enrollment: {exc}",
            }

    def is_enrolled(self, user_id: str) -> bool:
        user = self._user_repo.get_by_user_id(user_id)
        return user is not None and user.face_enrolled
