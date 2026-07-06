"""AES-256-CBC symmetric encryption module.

Provides encrypt / decrypt operations on raw bytes using the AES
algorithm in CBC mode with PKCS7 padding.  All keys are 256 bits
(32 bytes) and all initialisation vectors are 128 bits (16 bytes).
"""

from __future__ import annotations

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from crypto.exceptions import AESError, PaddingError
from crypto.interfaces import BaseCipher
from crypto.key_generator import generate_iv
from crypto.payload import EncryptedPayload

AES_KEY_SIZE: int = 32
AES_BLOCK_SIZE: int = 16
ALGORITHM_NAME: str = "AES-256-CBC"


class AESCipher(BaseCipher[EncryptedPayload]):
    """AES-256-CBC encrypt / decrypt with PKCS7 padding.

    Usage::

        cipher = AESCipher(key)
        payload = cipher.encrypt(b"plaintext data")
        plaintext = cipher.decrypt(payload)
    """

    def __init__(self, key: bytes) -> None:
        """Initialise the cipher with a 256-bit AES key.

        Args:
            key: 32-byte AES-256 key.

        Raises:
            AESError: If the key is not exactly 32 bytes.
        """
        if not isinstance(key, bytes) or len(key) != AES_KEY_SIZE:
            raise AESError(
                f"AES key must be exactly {AES_KEY_SIZE} bytes "
                f"(got {len(key) if isinstance(key, bytes) else 'invalid type'})."
            )
        self._key: bytes = key

    def encrypt(self, data: bytes) -> EncryptedPayload:
        """Encrypt *data* with AES-256-CBC.

        A fresh random IV is generated for every call.

        Args:
            data: The plaintext bytes to encrypt (any length).

        Returns:
            An :class:`~crypto.payload.EncryptedPayload` containing
            the ciphertext, IV, and algorithm name.

        Raises:
            AESError: If encryption fails.
        """
        if not isinstance(data, bytes):
            raise AESError("Data to encrypt must be bytes.")

        try:
            iv: bytes = generate_iv()
            cipher = AES.new(self._key, AES.MODE_CBC, iv)
            padded: bytes = pad(data, AES_BLOCK_SIZE, style="pkcs7")
            ciphertext: bytes = cipher.encrypt(padded)
            return EncryptedPayload(
                ciphertext=ciphertext,
                iv=iv,
                algorithm=ALGORITHM_NAME,
            )
        except (ValueError, TypeError, PaddingError) as exc:
            raise AESError(f"AES encryption failed: {exc}") from exc

    def decrypt(self, payload: EncryptedPayload) -> bytes:
        """Decrypt an :class:`~crypto.payload.EncryptedPayload`.

        Args:
            payload: The encrypted payload (ciphertext + IV).

        Returns:
            Original plaintext bytes.

        Raises:
            AESError: If decryption or unpadding fails (wrong key,
                corrupted data, etc.).
        """
        if not isinstance(payload, EncryptedPayload):
            raise AESError("Expected an EncryptedPayload instance.")

        try:
            cipher = AES.new(self._key, AES.MODE_CBC, payload.iv)
            decrypted_padded: bytes = cipher.decrypt(payload.ciphertext)
            plaintext: bytes = unpad(
                decrypted_padded, AES_BLOCK_SIZE, style="pkcs7"
            )
            return plaintext
        except (ValueError, TypeError, KeyError) as exc:
            raise AESError(
                f"AES decryption failed — possible key mismatch "
                f"or corrupted data: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Convenience: raw bytes interface (for callers that manage IVs
    # separately, e.g. when stored in an EncryptedKeyPayload)
    # ------------------------------------------------------------------

    def encrypt_bytes(self, data: bytes, iv: bytes | None = None) -> tuple[bytes, bytes]:
        """Encrypt *data* with a caller-supplied or fresh IV.

        Args:
            data: Plaintext bytes.
            iv:   Optional 16-byte IV.  If ``None``, a random IV is
                  generated.

        Returns:
            ``(ciphertext, iv)`` tuple.
        """
        if iv is None:
            iv = generate_iv()
        if len(iv) != AES_BLOCK_SIZE:
            raise AESError(
                f"IV must be exactly {AES_BLOCK_SIZE} bytes "
                f"(got {len(iv)})."
            )
        cipher = AES.new(self._key, AES.MODE_CBC, iv)
        padded = pad(data, AES_BLOCK_SIZE, style="pkcs7")
        return cipher.encrypt(padded), iv

    def decrypt_bytes(self, ciphertext: bytes, iv: bytes) -> bytes:
        """Decrypt ciphertext with the given IV.

        Args:
            ciphertext: Encrypted data.
            iv:         The 16-byte IV used during encryption.

        Returns:
            Original plaintext bytes.
        """
        if len(iv) != AES_BLOCK_SIZE:
            raise AESError(
                f"IV must be exactly {AES_BLOCK_SIZE} bytes "
                f"(got {len(iv)})."
            )
        try:
            cipher = AES.new(self._key, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            return unpad(decrypted_padded, AES_BLOCK_SIZE, style="pkcs7")
        except (ValueError, TypeError, KeyError) as exc:
            raise AESError(
                f"AES decryption failed: {exc}"
            ) from exc
