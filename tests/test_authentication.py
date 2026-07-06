"""Integration tests for authentication — login, logout, session
management, and error handling.
"""

from __future__ import annotations

import pytest

from controllers.auth_controller import AuthController
from exceptions.custom_exceptions import AuthenticationError
from services.auth_service import AuthService
from services.session_manager import SessionManager


# ======================================================================
# SessionManager
# ======================================================================


class TestSessionManager:
    def test_create_session(self, session_mgr: SessionManager) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="editor",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        assert session_mgr.is_authenticated is True
        s = session_mgr.get_current_session()
        assert s.user_id == "u1"
        assert s.username == "alice"
        assert s.role == "editor"

    def test_logout_destroys_session(
        self, session_mgr: SessionManager
    ) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="editor",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        session_mgr.logout()
        assert session_mgr.is_authenticated is False
        with pytest.raises(AuthenticationError):
            session_mgr.get_current_session()

    def test_get_current_session_raises_when_unauthenticated(
        self, session_mgr: SessionManager
    ) -> None:
        with pytest.raises(AuthenticationError, match="No active session"):
            session_mgr.get_current_session()

    def test_get_current_user_id(self, session_mgr: SessionManager) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="editor",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        assert session_mgr.get_current_user_id() == "u1"

    def test_require_role_passes(self, session_mgr: SessionManager) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="admin",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        session_mgr.require_role("admin", "editor")

    def test_require_role_fails(
        self, session_mgr: SessionManager
    ) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="viewer",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        from exceptions.custom_exceptions import AuthorizationError

        with pytest.raises(AuthorizationError, match="not authorised"):
            session_mgr.require_role("admin")

    def test_session_to_dict(self, session_mgr: SessionManager) -> None:
        session_mgr.create_session(
            user_id="u1",
            username="alice",
            role="editor",
            rsa_public_key="pub",
            rsa_private_key="priv",
        )
        d = session_mgr.get_current_session().to_dict()
        assert d["user_id"] == "u1"
        assert d["username"] == "alice"
        assert d["role"] == "editor"
        assert "login_timestamp" in d
        # RSA keys must never appear in the dict
        assert "rsa_public_key" not in d
        assert "rsa_private_key" not in d


# ======================================================================
# AuthService
# ======================================================================


class TestAuthServiceLogin:
    def test_login_success(
        self,
        auth_service: AuthService,
        registered_user: dict,
    ) -> None:
        result = auth_service.login("login_test", "TestP@ss123")
        assert result["username"] == "login_test"
        assert result["role"] == "editor"
        assert auth_service.is_authenticated() is True

    def test_login_invalid_username(
        self, auth_service: AuthService
    ) -> None:
        with pytest.raises(AuthenticationError, match="Invalid"):
            auth_service.login("nonexistent", "TestP@ss123")

    def test_login_invalid_password(
        self,
        auth_service: AuthService,
        registered_user: dict,
    ) -> None:
        with pytest.raises(AuthenticationError, match="Invalid"):
            auth_service.login("login_test", "WrongP@ss456")

    @pytest.mark.parametrize(
        "username,password,expected",
        [
            ("", "TestP@ss123", "Username is required"),
            ("  ", "TestP@ss123", "Username is required"),
            ("alice", "", "Password is required"),
        ],
    )
    def test_login_empty_fields(
        self,
        auth_service: AuthService,
        username: str,
        password: str,
        expected: str,
    ) -> None:
        from exceptions.custom_exceptions import ValidationError

        with pytest.raises(ValidationError, match=expected):
            auth_service.login(username, password)


class TestAuthServiceLogout:
    def test_logout_after_login(
        self,
        auth_service: AuthService,
        registered_user: dict,
    ) -> None:
        auth_service.login("login_test", "TestP@ss123")
        assert auth_service.is_authenticated() is True
        result = auth_service.logout()
        assert result["success"] is True
        assert auth_service.is_authenticated() is False

    def test_logout_without_login(
        self, auth_service: AuthService
    ) -> None:
        result = auth_service.logout()
        assert result["success"] is False
        assert "No active session" in result["message"]

    def test_get_current_user_after_login(
        self,
        auth_service: AuthService,
        registered_user: dict,
    ) -> None:
        auth_service.login("login_test", "TestP@ss123")
        info = auth_service.get_current_user()
        assert info is not None
        assert info["username"] == "login_test"
        assert info["role"] == "editor"

    def test_get_current_user_without_login(
        self, auth_service: AuthService
    ) -> None:
        assert auth_service.get_current_user() is None


# ======================================================================
# AuthController
# ======================================================================


class TestAuthControllerLogin:
    def test_login_success_response(
        self, auth_controller: AuthController, registered_user: dict
    ) -> None:
        result = auth_controller.login("login_test", "TestP@ss123")
        assert result["success"] is True
        assert "Welcome back" in result["message"]
        assert auth_controller.is_authenticated() is True

    def test_login_wrong_password_response(
        self, auth_controller: AuthController, registered_user: dict
    ) -> None:
        result = auth_controller.login("login_test", "WrongP@ss!")
        assert result["success"] is False
        assert "Invalid" in result["error"]

    def test_login_nonexistent_user_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.login("ghost", "SomeP@ss1")
        assert result["success"] is False
        assert "Invalid" in result["error"]

    def test_login_empty_fields_response(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.login("", "TestP@ss123")
        assert result["success"] is False
        assert "Username is required" in result["error"]


class TestAuthControllerLogout:
    def test_logout_flow(
        self, auth_controller: AuthController, registered_user: dict
    ) -> None:
        auth_controller.login("login_test", "TestP@ss123")
        assert auth_controller.is_authenticated() is True
        result = auth_controller.logout()
        assert result["success"] is True
        assert auth_controller.is_authenticated() is False

    def test_logout_without_login(
        self, auth_controller: AuthController
    ) -> None:
        result = auth_controller.logout()
        assert result["success"] is False
