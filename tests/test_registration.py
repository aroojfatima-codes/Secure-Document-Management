"""Integration tests for user registration.

Tests cover the full registration flow: input validation, password
hashing, RSA key generation, repository persistence, and the
controller-level response formatting.
"""

from __future__ import annotations

import pytest

from controllers.auth_controller import AuthController
from database.repositories.user_repository import UserRepository
from exceptions.custom_exceptions import ValidationError
from services.registration_service import RegistrationService


# ======================================================================
# RegistrationService — direct unit / integration tests
# ======================================================================


class TestRegistrationValidation:
    """Input validation — no database or crypto side effects."""

    def test_valid_registration_succeeds(
        self, registration_service: RegistrationService
    ) -> None:
        result = registration_service.register(
            "valid_user", "Str0ngP@ss1", "editor"
        )
        assert result["username"] == "valid_user"
        assert result["role"] == "editor"
        assert len(result["user_id"]) == 32  # UUID4 hex

    @pytest.mark.parametrize(
        "username,expected_msg",
        [
            ("", "Username is required"),
            ("  ", "Username is required"),
            ("ab", "3–30 characters"),
            ("a" * 31, "3–30 characters"),
            ("user name", "letters, digits, and underscores"),
            ("user-name!", "letters, digits, and underscores"),
        ],
    )
    def test_invalid_username(
        self,
        registration_service: RegistrationService,
        username: str,
        expected_msg: str,
    ) -> None:
        with pytest.raises(ValidationError, match=expected_msg):
            registration_service.register(username, "Str0ngP@ss1", "viewer")

    @pytest.mark.parametrize(
        "password,expected_msg",
        [
            ("", "Password is required"),
            ("Short1A", "at least 8 characters"),
            ("nouppercase1", "uppercase letter"),
            ("NOLOWERCASE1", "lowercase letter"),
            ("NoDigits!!", "digit"),
        ],
    )
    def test_invalid_password(
        self,
        registration_service: RegistrationService,
        password: str,
        expected_msg: str,
    ) -> None:
        with pytest.raises(ValidationError, match=expected_msg):
            registration_service.register("user1", password, "viewer")

    @pytest.mark.parametrize(
        "role,expected_msg",
        [
            ("", "Role is required"),
            ("superadmin", "Invalid role"),
            ("user", "Invalid role"),
        ],
    )
    def test_invalid_role(
        self,
        registration_service: RegistrationService,
        role: str,
        expected_msg: str,
    ) -> None:
        with pytest.raises(ValidationError, match=expected_msg):
            registration_service.register("user1", "Str0ngP@ss1", role)


class TestRegistrationPersistence:
    """Full registration flow — stores data in MongoDB."""

    def test_registration_creates_user_in_db(
        self,
        registration_service: RegistrationService,
        user_repo: UserRepository,
    ) -> None:
        result = registration_service.register(
            "alice", "AliceP@ss1", "admin"
        )
        user = user_repo.get_by_username("alice")
        assert user is not None
        assert user.user_id == result["user_id"]
        assert user.role == "admin"

    def test_registration_stores_hashed_password(
        self,
        registration_service: RegistrationService,
        user_repo: UserRepository,
    ) -> None:
        registration_service.register("bob", "BobP@ss1", "editor")
        user = user_repo.get_by_username("bob")
        assert user is not None
        # Password should be a SHA-256 hex digest (64 chars)
        assert len(user.password_hash) == 64
        # Plaintext should NOT be stored
        assert user.password_hash != "BobP@ss1"

    def test_registration_generates_rsa_keys(
        self,
        registration_service: RegistrationService,
        user_repo: UserRepository,
    ) -> None:
        registration_service.register("carol", "CarolP@ss1", "viewer")
        user = user_repo.get_by_username("carol")
        assert user is not None
        # RSA keys should be non-empty PEM strings
        assert "BEGIN PUBLIC KEY" in user.rsa_public_key
        assert "BEGIN PRIVATE KEY" in user.rsa_private_key

    def test_duplicate_username_raises_validation_error(
        self,
        registration_service: RegistrationService,
    ) -> None:
        registration_service.register("dave", "DaveP@ss1", "admin")
        with pytest.raises(ValidationError, match="already taken"):
            registration_service.register("dave", "OtherP@ss2", "viewer")

    def test_multiple_users_can_register(
        self,
        registration_service: RegistrationService,
        user_repo: UserRepository,
    ) -> None:
        registration_service.register("user_a", "UserA@123", "admin")
        registration_service.register("user_b", "UserB@456", "editor")
        assert user_repo.get_by_username("user_a") is not None
        assert user_repo.get_by_username("user_b") is not None

    def test_password_hash_is_deterministic(
        self,
        registration_service: RegistrationService,
    ) -> None:
        # Same password should produce the same hash only if
        # the implementation uses no salt (SHA-256).
        # Here we just verify the hash is 64 hex chars.
        registration_service.register("eve", "EveP@ss1", "viewer")
        registration_service.register("frank", "EveP@ss1", "viewer")
        # Different usernames, same password — we can't retrieve
        # hashes from the service return, but we can check
        # they're stored correctly via the repo
        from database.manager import DatabaseManager
        mgr = DatabaseManager()
        users_coll = mgr.get_collection("users")
        eve_doc = users_coll.find_one({"username": "eve"})
        frank_doc = users_coll.find_one({"username": "frank"})
        assert eve_doc is not None and frank_doc is not None
        assert eve_doc["password_hash"] == frank_doc["password_hash"]


# ======================================================================
# AuthController — tests the presentation-coordination layer
# ======================================================================


class TestAuthControllerRegistration:
    def test_successful_registration_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register("grace", "GraceP@ss1", "admin")
        assert result["success"] is True
        assert result["username"] == "grace"
        assert result["role"] == "admin"
        assert "user_id" in result

    def test_duplicate_username_response(
        self, auth_controller: AuthController
    ) -> None:
        auth_controller.register("hank", "HankP@ss1", "viewer")
        result = auth_controller.register("hank", "HankP@ss2", "admin")
        assert result["success"] is False
        assert "already taken" in result["error"]

    def test_invalid_password_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register("iris", "weak", "editor")
        assert result["success"] is False
        assert "at least 8 characters" in result["error"]

    def test_invalid_role_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register("iris", "IrisP@ss1", "super")
        assert result["success"] is False
        assert "Invalid role" in result["error"]

    def test_empty_username_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register("", "IrisP@ss1", "viewer")
        assert result["success"] is False
        assert "Username is required" in result["error"]

    def test_whitespace_username_is_stripped(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register(
            "  jake  ", "JakeP@ss1", "editor"
        )
        assert result["success"] is True
        assert result["username"] == "jake"

    def test_role_is_lowercased(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.register(
            "kate", "KateP@ss1", "ADMIN"
        )
        assert result["success"] is True
        assert result["role"] == "admin"
