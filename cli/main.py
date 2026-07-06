"""Command-Line Interface entry point for the SDMS.

Provides a menu-driven interface with separate unauthenticated and
authenticated menus.  Currently supports registration, login, and
logout; document management will be added in later milestones.
"""

from __future__ import annotations

from typing import Any

from controllers.auth_controller import AuthController
from controllers.document_controller import DocumentController
from logger.logging_config import get_logger

logger = get_logger(__name__)

WELCOME_ART = r"""
   ======================================================
        Secure Document Management System  v1.0.0
                 Information Security
   ======================================================
"""


def display_welcome() -> None:
    """Print the welcome banner."""
    print(WELCOME_ART)


def run_cli() -> None:
    """Run the interactive CLI menu loop.

    Displays different options depending on whether a user is
    currently authenticated.
    """
    logger.info("CLI started — interactive mode.")
    controller = AuthController()
    doc_controller = DocumentController()

    while True:
        print()
        _print_menu(controller)
        print()

        choice: str = input("  Enter your choice: ").strip()

        if choice in ("0", "exit", "quit"):
            if controller.is_authenticated():
                controller.logout()
            print("  Goodbye.")
            logger.info("CLI session ended by user.")
            break
        elif choice == "1":
            _handle_registration(controller)
        elif choice == "2":
            _handle_login(controller)
        elif choice == "3" and controller.is_authenticated():
            _handle_logout(controller)
        elif choice == "4" and controller.is_authenticated():
            _handle_upload(doc_controller)
        elif choice == "5" and controller.is_authenticated():
            _handle_list_documents(doc_controller)
        elif choice == "6" and controller.is_authenticated():
            _handle_document_detail(doc_controller)
        elif choice == "7" and controller.is_authenticated():
            _handle_search_documents(doc_controller)
        elif choice == "8" and controller.is_authenticated():
            _handle_download(doc_controller)
        elif choice == "9" and controller.is_authenticated():
            _handle_share(doc_controller)
        elif choice == "10" and controller.is_authenticated():
            _handle_shared_documents(doc_controller)
        else:
            print("  Invalid choice. Please try again.")


def _print_menu(controller: AuthController) -> None:
    """Print the appropriate menu based on authentication state."""
    print("  ┌─────────────────────────────────────┐")
    if controller.is_authenticated():
        user = controller.get_current_user()
        print(
            f"  │  Logged in as {user['username']:<20}│"
            if user
            else "  │  Logged in                              │"
        )
        print("  ├─────────────────────────────────────┤")
        print("  │  [3] Logout                           │")
        print("  │  [4] Upload Document                  │")
        print("  │  [5] My Documents                     │")
        print("  │  [6] Document Details                 │")
        print("  │  [7] Search Documents                 │")
        print("  │  [8] Download Document                │")
        print("  │  [9] Share Document                    │")
        print("  │  [10] Shared With Me                   │")
    else:
        print("  │  Main Menu                            │")
        print("  ├─────────────────────────────────────┤")
        print("  │  [1] Register                         │")
        print("  │  [2] Login                            │")
    print("  │  [0] Exit                              │")
    print("  └─────────────────────────────────────┘")


def _handle_registration(controller: AuthController) -> None:
    """Prompt for registration details and process them."""
    print()
    print("  --- User Registration ---")
    print()

    if controller.is_authenticated():
        print("  You are already logged in.")
        return

    username: str = input("  Username        : ").strip()
    if not username:
        print("  Registration cancelled — username is required.")
        return

    password: str = input("  Password        : ")

    print()
    print("  Available roles: admin, editor, viewer")
    role: str = input("  Role            : ").strip().lower()
    if not role:
        print("  Registration cancelled — role is required.")
        return

    print()
    print("  Processing registration ...")
    result: dict[str, Any] = controller.register(
        username=username, password=password, role=role
    )

    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
        print(f"    User ID   : {result['user_id']}")
        print(f"    Username  : {result['username']}")
        print(f"    Role      : {result['role']}")
    else:
        print(f"  ✗ {result['error']}")


def _handle_login(controller: AuthController) -> None:
    """Prompt for login credentials and authenticate."""
    print()
    print("  --- User Login ---")
    print()

    username: str = input("  Username  : ").strip()
    if not username:
        print("  Login cancelled — username is required.")
        return

    password: str = input("  Password  : ")

    print()
    print("  Authenticating ...")
    result: dict[str, Any] = controller.login(
        username=username, password=password
    )

    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
    else:
        print(f"  ✗ {result['error']}")


def _handle_logout(controller: AuthController) -> None:
    """Log the current user out."""
    result: dict[str, Any] = controller.logout()
    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
    else:
        print(f"  ✗ {result['error']}")


def _print_document_summary(doc: dict[str, Any], index: int | None = None) -> None:
    """Print a compact one-line document summary."""
    prefix: str = f"  [{index}] " if index is not None else "  "
    ext: str = doc.get("file_extension", "")
    size: str = doc.get("file_size_display", "")
    status: str = doc.get("status", "")
    print(
        f"{prefix}{doc['document_id'][:8]}... | "
        f"{doc['original_filename']}{' ' + ext if ext else ''} | "
        f"{size:>8} | "
        f"{status}"
    )


def _handle_list_documents(doc_controller: DocumentController) -> None:
    """List all documents owned by the current user."""
    print()
    print("  --- My Documents ---")
    print()

    page: int = 1
    while True:
        result = doc_controller.list_my_documents(page=page)

        if not result.get("success"):
            print(f"  ✗ {result['error']}")
            return

        documents = result.get("documents", [])
        pagination = result.get("pagination", {})

        if not documents:
            if page == 1:
                print("  No documents found. Upload your first document using [4].")
            else:
                print("  No more documents.")
            return

        total = pagination.get("total", 0)
        print(
            f"  Page {pagination['page']}/{pagination['total_pages']}"
            f"  ({total} document{'s' if total != 1 else ''})"
        )
        print()

        for i, doc in enumerate(documents, start=1):
            _print_document_summary(doc, index=i)

        print()
        if pagination.get("has_next"):
            choice: str = input(
                "  [N]ext page, [Q]uit to menu: "
            ).strip().lower()
            if choice == "n":
                page += 1
                continue
        break


def _handle_document_detail(doc_controller: DocumentController) -> None:
    """Show full metadata for a single document."""
    print()
    print("  --- Document Details ---")
    print()

    doc_id: str = input("  Document ID  : ").strip()
    if not doc_id:
        print("  Cancelled — document ID is required.")
        return

    print()
    print("  Fetching details ...")
    result = doc_controller.get_document_detail(doc_id)

    print()
    if not result.get("success"):
        print(f"  ✗ {result['error']}")
        return

    doc = result["document"]
    print(f"  Document ID      : {doc['document_id']}")
    print(f"  Filename         : {doc['original_filename']}")
    print(f"  Type             : {doc['mime_type']}")
    print(f"  Size             : {doc['file_size_display']} ({doc['file_size']:,} bytes)")
    print(f"  SHA-256          : {doc['sha256_hash']}")
    print(f"  Owner ID         : {doc['owner_id']}")
    print(f"  Status           : {doc['status']}")
    print(f"  Shared with      : {doc['shared_with_count']} user(s)")
    print(f"  Created          : {doc['created_at']}")
    print(f"  Updated          : {doc['updated_at']}")


def _handle_search_documents(doc_controller: DocumentController) -> None:
    """Search and filter documents owned by the current user."""
    print()
    print("  --- Search Documents ---")
    print()
    print("  Leave fields empty to skip filters.")
    print()

    query: str = input("  Search term  : ").strip()
    mime_type: str = input("  MIME type    : ").strip()

    print()
    print("  Searching ...")
    result = doc_controller.search_my_documents(
        query=query,
        mime_type=mime_type if mime_type else None,
    )

    print()
    if not result.get("success"):
        print(f"  ✗ {result['error']}")
        return

    documents = result.get("documents", [])
    pagination = result.get("pagination", {})

    if not documents:
        print("  No documents match your search.")
        return

    total = pagination.get("total", 0)
    print(
        f"  Found {total} document{'s' if total != 1 else ''}"
        f" (page {pagination['page']}/{pagination['total_pages']})"
    )
    print()

    for i, doc in enumerate(documents, start=1):
        _print_document_summary(doc, index=i)


def _handle_download(doc_controller: DocumentController) -> None:
    """Prompt for document ID and output directory, then download."""
    print()
    print("  --- Download Document ---")
    print()

    doc_id: str = input("  Document ID  : ").strip()
    if not doc_id:
        print("  Download cancelled — document ID is required.")
        return

    output_dir: str = input("  Output dir   : ").strip()
    if not output_dir:
        print("  Download cancelled — output directory is required.")
        return

    print()
    print("  Downloading, decrypting, and verifying integrity ...")
    result = doc_controller.download(
        document_id=doc_id, output_dir=output_dir
    )

    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
        print(f"    Document ID      : {result['document_id']}")
        print(f"    File name        : {result['original_filename']}")
        print(f"    Size             : {result['file_size']:,} bytes")
        print(f"    Output path      : {result['output_path']}")
        print("    Integrity        : Verified (SHA-256)")
    else:
        print(f"  ✗ {result['error']}")


def _handle_share(doc_controller: DocumentController) -> None:
    """Prompt for document ID and recipient username, then share."""
    print()
    print("  --- Share Document ---")
    print()

    doc_id: str = input("  Document ID       : ").strip()
    if not doc_id:
        print("  Share cancelled — document ID is required.")
        return

    recipient: str = input("  Recipient username : ").strip()
    if not recipient:
        print("  Share cancelled — recipient username is required.")
        return

    print()
    print("  Sharing document ...")
    result = doc_controller.share_document(
        document_id=doc_id, recipient_username=recipient
    )

    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
        print(f"    Document ID       : {result['document_id']}")
        print(f"    Recipient         : {result['recipient_username']}")
        print(f"    Permission        : {result['permission']}")
    else:
        print(f"  ✗ {result['error']}")


def _handle_shared_documents(doc_controller: DocumentController) -> None:
    """List documents shared with the current user."""
    print()
    print("  --- Shared With Me ---")
    print()

    page: int = 1
    while True:
        result = doc_controller.list_shared_with_me(page=page)

        if not result.get("success"):
            print(f"  ✗ {result['error']}")
            return

        documents = result.get("documents", [])
        pagination = result.get("pagination", {})

        if not documents:
            if page == 1:
                print("  No documents have been shared with you yet.")
            else:
                print("  No more documents.")
            return

        total = pagination.get("total", 0)
        print(
            f"  Page {pagination['page']}/{pagination['total_pages']}"
            f"  ({total} document{'s' if total != 1 else ''})"
        )
        print()

        for i, doc in enumerate(documents, start=1):
            _print_document_summary(doc, index=i)

        print()
        if pagination.get("has_next"):
            choice: str = input(
                "  [N]ext page, [Q]uit to menu: "
            ).strip().lower()
            if choice == "n":
                page += 1
                continue
        break


def _handle_upload(doc_controller: DocumentController) -> None:
    """Prompt for file path and upload the document."""
    print()
    print("  --- Upload Document ---")
    print()

    file_path: str = input("  File path  : ").strip()
    if not file_path:
        print("  Upload cancelled — file path is required.")
        return

    print()
    print("  Uploading and encrypting ...")
    result: dict[str, Any] = doc_controller.upload(file_path)

    print()
    if result.get("success"):
        print(f"  ✓ {result['message']}")
        print(f"    Document ID  : {result['document_id']}")
        print(f"    File name    : {result['original_filename']}")
        print(f"    Size         : {result['file_size']:,} bytes")
        print(f"    MIME type    : {result['mime_type']}")
        print(f"    SHA-256      : {result['sha256_hash']}")
    else:
        print(f"  ✗ {result['error']}")
