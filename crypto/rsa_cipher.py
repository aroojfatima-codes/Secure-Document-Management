"""RSA-2048 asymmetric encryption module.

Supports key-pair generation, PEM serialisation, and OAEP-based
encrypt / decrypt operations suitable for wrapping AES keys in a
hybrid encryption scheme.
"""

from __future__ import annotations

from pathlib import Path

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

from crypto.exceptions import KeySerializationError, RSAError
from crypto.interfaces import BaseCipher

RSA_KEY_SIZE: int = 2048


class RSACipher(BaseCipher[bytes]):
    """RSA-2048 encrypt / decrypt using OAEP padding with SHA-256.

    Usage::

        cipher = RSACipher()
        cipher.generate_keypair()

        encrypted = cipher.encrypt(b"wrapped-aes-key")
        decrypted = cipher.decrypt(encrypted)
    """

    def __init__(self, key_pair: RSA.RsaKey | None = None) -> None:
        """Initialise the cipher with an optional existing RSA key pair.

        Args:
            key_pair: An existing ``RSA.RsaKey`` object.  If ``None``,
                call :meth:`generate_keypair` or :meth:`load_private_key`
                before using encrypt / decrypt.
        """
        self._key_pair: RSA.RsaKey | None = key_pair

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def generate_keypair(self) -> None:
        """Generate a new 2048-bit RSA key pair.

        The key is stored internally and will be used for subsequent
        encrypt / decrypt calls.

        Raises:
            RSAError: If key generation fails.
        """
        try:
            self._key_pair = RSA.generate(RSA_KEY_SIZE)
        except (ValueError, TypeError) as exc:
            raise RSAError(
                f"RSA key-pair generation failed: {exc}"
            ) from exc

    def export_private_key(self, password: str | None = None) -> bytes:
        """Export the private key in PEM format, optionally encrypted.

        Args:
            password: If provided, the PEM data is encrypted with this
                passphrase using AES-256-CBC.

        Returns:
            PEM-encoded private key bytes.

        Raises:
            KeySerializationError: If no key is loaded or export fails.
        """
        key = self._require_key()
        try:
            return key.export_key(
                format="PEM",
                passphrase=password,
                pkcs=8,
                protection="PBKDF2WithHMAC-SHA1AndAES256-CBC"
                if password
                else None,
            )
        except (ValueError, TypeError) as exc:
            raise KeySerializationError(
                f"Failed to export private key: {exc}"
            ) from exc

    def export_public_key(self) -> bytes:
        """Export the public key in PEM format (unencrypted).

        Returns:
            PEM-encoded public key bytes.

        Raises:
            KeySerializationError: If no key is loaded or export fails.
        """
        key = self._require_key()
        try:
            return key.publickey().export_key(format="PEM")
        except (ValueError, TypeError) as exc:
            raise KeySerializationError(
                f"Failed to export public key: {exc}"
            ) from exc

    def load_private_key(self, pem_data: bytes, password: str | None = None) -> None:
        """Load a private key from PEM-encoded bytes.

        Raises:
            KeySerializationError: If the PEM data is invalid or the
                password is incorrect.
        """
        try:
            self._key_pair = RSA.import_key(pem_data, passphrase=password)
        except (ValueError, TypeError, IndexError) as exc:
            raise KeySerializationError(
                f"Failed to load private key: {exc}"
            ) from exc

    def load_public_key(self, pem_data: bytes) -> None:
        """Load a public key from PEM-encoded bytes.

        Raises:
            KeySerializationError: If the PEM data is invalid.
        """
        try:
            self._key_pair = RSA.import_key(pem_data)
        except (ValueError, TypeError, IndexError) as exc:
            raise KeySerializationError(
                f"Failed to load public key: {exc}"
            ) from exc

    def _load_key_from_file(
        self, file_path: str | Path, purpose: str,
    ) -> bytes:
        """Read a PEM file from disk, raising on missing file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            raise KeySerializationError(
                f"{purpose} key file not found: {path}"
            )
        return path.read_bytes()

    def load_private_key_from_file(
        self, file_path: str | Path, password: str | None = None,
    ) -> None:
        """Load a private key from a PEM file on disk."""
        pem_data = self._load_key_from_file(file_path, "Private")
        self.load_private_key(pem_data, password=password)

    def load_public_key_from_file(self, file_path: str | Path) -> None:
        """Load a public key from a PEM file on disk."""
        pem_data = self._load_key_from_file(file_path, "Public")
        self.load_public_key(pem_data)

    # ------------------------------------------------------------------
    # Encrypt / Decrypt
    # ------------------------------------------------------------------

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt *data* using RSA-OAEP with SHA-256.

        Because RSA-2048 can only encrypt ~190 bytes at a time, this
        method is intended for small payloads such as AES keys.

        Args:
            data: The plaintext bytes to encrypt (max ~190 bytes).

        Returns:
            Encrypted bytes.

        Raises:
            RSAError: If encryption fails or data is too large.
        """
        key = self._require_key()
        if not isinstance(data, bytes):
            raise RSAError("Data to encrypt must be bytes.")
        if not data:
            raise RSAError("Cannot encrypt empty data.")
        try:
            public_key = key.publickey()
            cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
            return cipher.encrypt(data)
        except (ValueError, TypeError) as exc:
            raise RSAError(
                f"RSA encryption failed — data may be too large: {exc}"
            ) from exc

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt *ciphertext* using the private key.

        Args:
            ciphertext: The encrypted bytes (must be exactly 256 bytes
                for RSA-2048).

        Returns:
            Original plaintext bytes.

        Raises:
            RSAError: If decryption fails (wrong key, corrupted data).
        """
        key = self._require_key()
        if not isinstance(ciphertext, bytes):
            raise RSAError("Ciphertext must be bytes.")
        if not ciphertext:
            raise RSAError("Cannot decrypt empty data.")
        try:
            cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
            return cipher.decrypt(ciphertext)
        except (ValueError, TypeError, IndexError) as exc:
            raise RSAError(
                f"RSA decryption failed — possible key mismatch "
                f"or corrupted data: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def has_private_key(self) -> bool:
        """Check whether the loaded key contains a private component."""
        return self._key_pair is not None and self._key_pair.has_private()

    @property
    def has_public_key(self) -> bool:
        """Check whether any key is currently loaded."""
        return self._key_pair is not None

    def _require_key(self) -> RSA.RsaKey:
        """Guard method that raises if no key is loaded.

        Returns:
            The internal ``RsaKey``, guaranteed not ``None``.
        """
        if self._key_pair is None:
            raise RSAError(
                "No RSA key loaded. Call generate_keypair(), "
                "load_private_key(), or load_public_key() first."
            )
        return self._key_pair
