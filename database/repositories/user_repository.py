"""Repository for User CRUD operations.

Translates between :class:`~models.user.User` objects and MongoDB
documents.  No authentication, password hashing, or cryptographic
logic lives here.
"""

from __future__ import annotations

from typing import Any

import pymongo

from database.exceptions import UserNotFoundError
from database.repositories.base import BaseRepository
from exceptions.custom_exceptions import ValidationError
from logger.logging_config import get_logger
from models.user import User

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    """CRUD operations for the ``users`` collection.

    Usage::

        repo = UserRepository()
        user = User(username="alice", password_hash="...", role="editor")
        user_id = repo.create_user(user)
        fetched = repo.get_by_username("alice")
    """

    _collection_name: str = "users"
    _id_field: str = "user_id"

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_user(self, user: User) -> str:
        """Persist a new User and return its ``user_id``.

        Args:
            user: A validated User instance.

        Returns:
            The assigned ``user_id``.

        Raises:
            ValidationError: If the user data is invalid.
            DuplicateKeyError: If the ``user_id`` or ``username``
                already exists.
        """
        user.validate()
        if not user.user_id:
            raise ValidationError(
                "user_id must be set before calling create_user."
            )

        doc = user.to_dict()
        return self.create(doc)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_username(self, username: str) -> User | None:
        """Look up a user by username.

        Args:
            username: The login name to search for.

        Returns:
            A User instance, or ``None``.
        """
        doc = self.find_one({"username": username})
        return User.from_dict(doc) if doc else None

    def get_by_user_id(self, user_id: str) -> User | None:
        """Look up a user by their unique identifier.

        Args:
            user_id: The UUID4 hex user identifier.

        Returns:
            A User instance, or ``None``.
        """
        doc = self.get_by_id(user_id)
        return User.from_dict(doc) if doc else None

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_user(
        self, user_id: str, updates: dict[str, Any]
    ) -> User:
        """Update fields on an existing user.

        Args:
            user_id: The target user's identifier.
            updates: A dict of fields to change (e.g. ``{"role": "admin"}``).

        Returns:
            The updated User instance.

        Raises:
            UserNotFoundError: If no user with that ``user_id`` exists.
        """
        from datetime import datetime, timezone
        updates["updated_at"] = datetime.now(timezone.utc)
        result = self.update(user_id, updates)
        if result is None:
            raise UserNotFoundError(
                f"Cannot update — user '{user_id}' not found."
            )
        return User.from_dict(result)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_user(self, user_id: str) -> None:
        """Permanently remove a user from the database.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        deleted = self.delete(user_id)
        if not deleted:
            raise UserNotFoundError(
                f"Cannot delete — user '{user_id}' not found."
            )

    def soft_delete_user(self, user_id: str) -> User:
        """Mark a user as inactive (preferred over permanent delete).

        Returns:
            The updated User instance.
        """
        return self.update_user(user_id, {"is_active": False})

    # ------------------------------------------------------------------
    # Existence helpers
    # ------------------------------------------------------------------

    def username_exists(self, username: str) -> bool:
        """Check whether a username is already taken.

        Returns:
            ``True`` if the username exists.
        """
        return self.exists({"username": username})

    def user_id_exists(self, user_id: str) -> bool:
        """Check whether a user identifier already exists.

        Returns:
            ``True`` if the user_id exists.
        """
        return self.exists({"user_id": user_id})

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_users(
        self,
        query: str = "",
        role: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[User]:
        """Search users with optional filters.

        Args:
            query:     Search term matched against ``username``
                       (case-insensitive regex).
            role:      Optional role filter (``"admin"``, ``"editor"``,
                       ``"viewer"``).
            is_active: Filter by account status.
            skip:      Pagination offset.
            limit:     Page size.

        Returns:
            A list of matching User instances.
        """
        filters: dict[str, Any] = {}

        if query:
            filters["username"] = {
                "$regex": query,
                "$options": "i",
            }
        if role:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        docs = self.find(
            filters=filters,
            skip=skip,
            limit=limit,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [User.from_dict(d) for d in docs]

    def get_all_users(
        self, skip: int = 0, limit: int = 50
    ) -> list[User]:
        """Retrieve all users (paginated).

        Returns:
            A list of User instances.
        """
        docs = self.find(
            skip=skip,
            limit=limit,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [User.from_dict(d) for d in docs]

    # ------------------------------------------------------------------
    # Biometric helpers
    # ------------------------------------------------------------------

    def get_enrolled_users(self) -> list[User]:
        """Retrieve all users who have enrolled facial biometrics.

        Returns:
            A list of User instances with face_enrolled == True.
        """
        docs = self.find(
            filters={"face_enrolled": True},
            limit=0,
            sort=[("created_at", pymongo.DESCENDING)],
        )
        return [User.from_dict(d) for d in docs]

    def update_face_encoding(
        self,
        user_id: str,
        encoding: list[float],
    ) -> User:
        """Store a facial encoding and mark the user as enrolled.

        Args:
            user_id:  The target user's identifier.
            encoding: The 128-dimensional face encoding as a float list.

        Returns:
            The updated User instance.
        """
        return self.update_user(
            user_id,
            {
                "face_encoding": encoding,
                "face_enrolled": True,
            },
        )

    def remove_face_encoding(self, user_id: str) -> User:
        """Clear the facial encoding and mark as not enrolled.

        Args:
            user_id: The target user's identifier.

        Returns:
            The updated User instance.
        """
        return self.update_user(
            user_id,
            {
                "face_encoding": [],
                "face_enrolled": False,
            },
        )
