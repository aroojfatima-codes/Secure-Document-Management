"""Command-Line Interface entry point for the SDMS.

Provides a menu-driven interface with separate unauthenticated and
authenticated menus.  Currently supports registration, login, and
logout; document management will be added in later milestones.
"""

from __future__ import annotations

from typing import Any, Callable

from controllers.auth_controller import AuthController
from controllers.audit_controller import AuditController
from controllers.document_controller import DocumentController
from controllers.face_controller import FaceController
from logger.logging_config import get_logger

logger = get_logger(__name__)

# ANSI color codes for improved CLI UX
class _C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"{_C.GREEN}✓ {msg}{_C.RESET}"


def _err(msg: str) -> str:
    return f"{_C.RED}✗ {msg}{_C.RESET}"


def _info(msg: str) -> str:
    return f"{_C.CYAN}{msg}{_C.RESET}"


def _bold(msg: str) -> str:
    return f"{_C.BOLD}{msg}{_C.RESET}"


def _show_result(
    result: dict[str, Any],
    on_success: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    """Display a success or error banner from an operation result dict."""
    print()
    if result.get("success"):
        print(f"  {_ok(result['message'])}")
        if on_success:
            on_success(result)
    else:
        print(f"  {_err(result['error'])}")


def _paginate_documents(
    title: str,
    empty_msg: str,
    fetch_fn: Callable[[int], dict[str, Any]],
) -> None:
    """Display a paginated document list with next/quit navigation."""
    print()
    print(f"  {_bold(f'--- {title} ---')}")
    print()

    page: int = 1
    while True:
        result = fetch_fn(page)

        if not result.get("success"):
            print(f"  {_err(result['error'])}")
            return

        documents = result.get("documents", [])
        pagination = result.get("pagination", {})

        if not documents:
            if page == 1:
                print(f"  {_info(empty_msg)}")
            else:
                print(f"  {_info('No more documents.')}")
            return

        total = pagination.get("total", 0)
        print(
            f"  {_bold(f'Page {pagination['page']}/{pagination['total_pages']}')}"
            f"  ({total} document{'s' if total != 1 else ''})"
        )
        print()

        for i, doc in enumerate(documents, start=1):
            _print_document_summary(doc, index=i)

        print()
        if pagination.get("has_next"):
            choice: str = input(
                f"  {_info('[N]ext page, [Q]uit to menu: ')}"
            ).strip().lower()
            if choice == "n":
                page += 1
                continue
        break


def _format_audit_log_row(log: dict[str, Any]) -> str:
    """Format a single audit log entry as a fixed-width table row."""
    ts: str = log.get("timestamp", "")
    if hasattr(ts, "strftime"):
        ts = ts.strftime("%Y-%m-%d %H:%M")
    else:
        ts = str(ts)[:16]
    username: str = log.get("username", "-")[:12]
    action: str = log.get("action", "")[:22]
    severity: str = log.get("severity", "")[:10]
    status: str = log.get("status", "")[:10]
    resource: str = log.get("resource_name", log.get("resource_id", ""))[:30]
    return (
        f"  {ts:<20} {username:<12} {action:<22} "
        f"{severity:<10} {status:<10} {resource}"
    )


def _print_audit_table_header() -> None:
    """Print the column header for the audit log table."""
    print(
        f"  {_C.DIM}{'TIMESTAMP':<20} {'USER':<12} {'ACTION':<22} "
        f"{'SEVERITY':<10} {'STATUS':<10} RESOURCE{_C.RESET}"
    )
    print(f"  {_C.DIM}{'-'*80}{_C.RESET}")


def _print_audit_search_entry(log: dict[str, Any]) -> None:
    """Print a single audit log entry in the compact search format."""
    print(f"  {_C.DIM}[{log.get('timestamp', '')}]{_C.RESET} "
          f"{log.get('username', '-')} | "
          f"{log.get('action', '')} | "
          f"{log.get('severity', '')} | "
          f"{log.get('status', '')} | "
          f"{log.get('message', '')}")


WELCOME_ART = rf"""
{_C.CYAN}{_C.BOLD}   +==================================================+
   |       Secure Document Management System  v1.0.0       |
   |                Information Security                    |
   +==================================================+{_C.RESET}
"""


def display_welcome() -> None:
    """Print the welcome banner."""
    print(WELCOME_ART)


def _is_admin(controller: AuthController) -> bool:
    """Check whether the current user has the admin role."""
    user = controller.get_current_user()
    return user is not None and user.get("role") == "admin"


def run_cli() -> None:
    """Run the interactive CLI menu loop.

    Displays different options depending on whether a user is
    currently authenticated.
    """
    logger.info("CLI started — interactive mode.")
    controller = AuthController()
    doc_controller = DocumentController()
    audit_controller = AuditController()
    face_controller = FaceController()

    while True:
        print()
        _print_menu(controller)
        print()

        choice: str = input("  Enter your choice: ").strip()

        if choice in ("0", "exit", "quit"):
            if controller.is_authenticated():
                controller.logout()
            print(f"  {_ok('Goodbye.')}")
            logger.info("CLI session ended by user.")
            break

        if choice == "3" and not controller.is_authenticated():
            _handle_face_login(face_controller)
            continue

        dispatch: dict[str, tuple[bool, bool, Callable[[], None]]] = {
            "1":  (False, False, lambda: _handle_registration(controller, face_controller)),
            "2":  (False, False, lambda: _handle_login(controller)),
            "3":  (True,  False, lambda: _handle_logout(controller)),
            "4":  (True,  False, lambda: _handle_upload(doc_controller)),
            "5":  (True,  False, lambda: _handle_list_documents(doc_controller)),
            "6":  (True,  False, lambda: _handle_document_detail(doc_controller)),
            "7":  (True,  False, lambda: _handle_search_documents(doc_controller)),
            "8":  (True,  False, lambda: _handle_download(doc_controller)),
            "9":  (True,  False, lambda: _handle_share(doc_controller)),
            "10": (True,  False, lambda: _handle_shared_documents(doc_controller)),
            "11": (True,  True,  lambda: _handle_audit_logs(audit_controller)),
            "12": (True,  True,  lambda: _handle_audit_search(audit_controller)),
            "13": (True,  False, lambda: _handle_face_settings(face_controller, controller)),
        }

        entry = dispatch.get(choice)
        if entry is None:
            print("  Invalid choice. Please try again.")
            continue

        needs_auth, needs_admin, handler = entry
        if needs_auth and not controller.is_authenticated():
            print("  Invalid choice. Please try again.")
        elif needs_admin and not _is_admin(controller):
            print("  Invalid choice. Please try again.")
        else:
            handler()


def _print_menu(controller: AuthController) -> None:
    """Print the appropriate menu based on authentication state."""
    sep: str = f"  {_C.DIM}+{'-'*37}+{_C.RESET}"
    title_sep: str = f"  {_C.CYAN}+{'-'*37}+{_C.RESET}"
    print(sep)
    if controller.is_authenticated():
        user = controller.get_current_user()
        is_admin: bool = user is not None and user.get("role") == "admin"
        status_line = (
            f"  |  {_C.GREEN}Logged in as {user['username']:<18}{_C.RESET}|"
            if user
            else f"  |  Logged in                              |"
        )
        print(status_line)
        print(title_sep)
        print(f"  |  {_C.BOLD}[3]{_C.RESET} Logout                           |")
        print(f"  |  {_C.BOLD}[4]{_C.RESET} Upload Document                  |")
        print(f"  |  {_C.BOLD}[5]{_C.RESET} My Documents                     |")
        print(f"  |  {_C.BOLD}[6]{_C.RESET} Document Details                 |")
        print(f"  |  {_C.BOLD}[7]{_C.RESET} Search Documents                 |")
        print(f"  |  {_C.BOLD}[8]{_C.RESET} Download Document                |")
        print(f"  |  {_C.BOLD}[9]{_C.RESET} Share Document                    |")
        print(f"  |  {_C.BOLD}[10]{_C.RESET} Shared With Me                   |")
        if is_admin:
            print(title_sep)
            print(f"  |  {_C.BOLD}[11]{_C.RESET} View Audit Logs                 |")
            print(f"  |  {_C.BOLD}[12]{_C.RESET} Search Audit Logs               |")
        print(title_sep)
        print(f"  |  {_C.BOLD}[13]{_C.RESET} Face Settings                    |")
    else:
        print(f"  |  {_C.CYAN}Main Menu{_C.RESET}                         |")
        print(title_sep)
        print(f"  |  {_C.BOLD}[1]{_C.RESET} Register                         |")
        print(f"  |  {_C.BOLD}[2]{_C.RESET} Login (Password)                  |")
        print(f"  |  {_C.BOLD}[3]{_C.RESET} Login (Face Recognition)          |")
    print(f"  |  {_C.BOLD}[0]{_C.RESET} Exit                              |")
    print(sep)


def _handle_registration(
    controller: AuthController,
    face_controller: FaceController,
) -> None:
    """Prompt for registration details and process them."""
    print()
    print(f"  {_bold('--- User Registration ---')}")
    print()

    if controller.is_authenticated():
        print(f"  {_err('You are already logged in.')}")
        return

    print(f"  {_info('Username may contain spaces (automatically converted to underscores).')}")
    username: str = input("  Username        : ").strip()
    if not username:
        print(f"  {_err('Registration cancelled — username is required.')}")
        return

    password: str = input("  Password        : ")

    print()
    print(f"  {_info('Available roles: admin, editor, viewer')}")
    role: str = input("  Role            : ").strip().lower()
    if not role:
        print(f"  {_err('Registration cancelled — role is required.')}")
        return

    print()
    print(f"  {_info('Processing registration ...')}")
    result: dict[str, Any] = controller.register(
        username=username, password=password, role=role
    )

    print()
    if result.get("success"):
        print(f"  {_ok(result['message'])}")
        print(f"    {_bold('User ID')}   : {result['user_id']}")
        print(f"    {_bold('Username')}  : {result['username']}")
        print(f"    {_bold('Role')}      : {result['role']}")

        print()
        print(f"  {_bold('--- Optional Face Recognition ---')}")
        if not face_controller.is_available():
            print(f"  {_err('Face recognition is not available.')}")
            print(f"  {_info('OpenCV face detection could not be initialised.')}")
        else:
            choice: str = input(
                f"  {_info('Enable Face Recognition Authentication? (y/n): ')}"
            ).strip().lower()
            if choice == "y":
                _handle_face_enrollment(
                    face_controller,
                    result["user_id"],
                    result["username"],
                )
            else:
                print(
                    f"  {_info('Face recognition not enabled.')} "
                    f"{_info('You can enable it later via [13] Face Settings.')}"
                )
    else:
        print(f"  {_err(result['error'])}")


def _handle_login(controller: AuthController) -> None:
    """Prompt for login credentials and authenticate."""
    print()
    print(f"  {_bold('--- User Login ---')}")
    print()

    username: str = input("  Username  : ").strip()
    if not username:
        print(f"  {_err('Login cancelled — username is required.')}")
        return

    password: str = input("  Password  : ")

    print()
    print(f"  {_info('Authenticating ...')}")
    result: dict[str, Any] = controller.login(
        username=username, password=password
    )

    _show_result(result)


def _handle_face_login(face_controller: FaceController) -> None:
    """Prompt for face recognition login."""
    print()
    print(f"  {_bold('--- Face Recognition Login ---')}")
    print()

    if not face_controller.is_available():
        print(f"  {_err('Face recognition is not available.')}")
        print(f"  {_info('Use [2] Login (Password) instead.')}")
        return

    print(f"  {_info('Looking at camera...')}")
    result: dict[str, Any] = face_controller.login_face()

    _show_result(result)


def _handle_face_enrollment(
    face_controller: FaceController,
    user_id: str,
    username: str,
) -> None:
    """Run the face enrollment workflow."""
    print()
    print(f"  {_bold('--- Face Enrollment ---')}")
    print()

    if not face_controller.is_available():
        print(f"  {_err('Face recognition is not available.')}")
        return

    print(f"  {_info('You will be asked to capture several facial images.')}")
    print(f"  {_info('Ensure good lighting and look directly at the camera.')}")
    print()

    input(f"  {_bold('Press Enter')} to start enrollment...")

    result: dict[str, Any] = face_controller.enroll(user_id, username)

    _show_result(result)


def _handle_face_settings(
    face_controller: FaceController,
    controller: AuthController,
) -> None:
    """Manage face recognition settings for the current user."""
    print()
    print(f"  {_bold('--- Face Recognition Settings ---')}")
    print()

    if not face_controller.is_available():
        print(f"  {_err('Face recognition is not available.')}")
        return

    user = controller.get_current_user()
    if not user:
        print(f"  {_err('Could not retrieve user information.')}")
        return

    user_id: str = user["user_id"]
    username: str = user["username"]
    enrolled: bool = face_controller.is_enrolled(user_id)

    if enrolled:
        print(f"  {_ok('Status: Face recognition is ENABLED')} for '{username}'.")
        print()
        print(f"  {_bold('[1]')} Re-enroll Face Data")
        print(f"  {_bold('[2]')} Remove Face Enrollment")
        print(f"  {_bold('[0]')} Back to Main Menu")
        print()

        choice: str = input("  Enter your choice: ").strip()

        if choice == "1":
            _handle_face_enrollment(face_controller, user_id, username)
        elif choice == "2":
            confirm: str = input(
                f"  {_err('Are you sure?')} This will remove your facial data. (y/n): "
            ).strip().lower()
            if confirm == "y":
                result = face_controller.remove_enrollment(user_id, username)
                _show_result(result)
            else:
                print(f"  {_info('Removal cancelled.')}")
    else:
        print(f"  Status: Face recognition is {_err('DISABLED')} for '{username}'.")
        print()
        choice = input(
            f"  {_info('Enable Face Recognition Authentication? (y/n): ')}"
        ).strip().lower()
        if choice == "y":
            _handle_face_enrollment(face_controller, user_id, username)
        else:
            print(f"  {_info('Face recognition not enabled.')}")


def _handle_logout(controller: AuthController) -> None:
    """Log the current user out."""
    result: dict[str, Any] = controller.logout()
    _show_result(result)


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
    _paginate_documents(
        title="My Documents",
        empty_msg="No documents found. Upload your first document using [4].",
        fetch_fn=lambda p: doc_controller.list_my_documents(page=p),
    )


def _handle_document_detail(doc_controller: DocumentController) -> None:
    """Show full metadata for a single document."""
    print()
    print(f"  {_bold('--- Document Details ---')}")
    print()

    doc_id: str = input("  Document ID  : ").strip()
    if not doc_id:
        print(f"  {_err('Cancelled — document ID is required.')}")
        return

    print()
    print(f"  {_info('Fetching details ...')}")
    result = doc_controller.get_document_detail(doc_id)

    print()
    if not result.get("success"):
        print(f"  {_err(result['error'])}")
        return

    doc = result["document"]
    print(f"  {_bold('Document ID')}      : {doc['document_id']}")
    print(f"  {_bold('Filename')}         : {doc['original_filename']}")
    print(f"  {_bold('Type')}             : {doc['mime_type']}")
    print(f"  {_bold('Size')}             : {doc['file_size_display']} ({doc['file_size']:,} bytes)")
    print(f"  {_bold('SHA-256')}          : {doc['sha256_hash']}")
    print(f"  {_bold('Owner ID')}         : {doc['owner_id']}")
    print(f"  {_bold('Status')}           : {doc['status']}")
    print(f"  {_bold('Shared with')}      : {doc['shared_with_count']} user(s)")
    print(f"  {_bold('Created')}          : {doc['created_at']}")
    print(f"  {_bold('Updated')}          : {doc['updated_at']}")


def _handle_search_documents(doc_controller: DocumentController) -> None:
    """Search and filter documents owned by the current user."""
    print()
    print(f"  {_bold('--- Search Documents ---')}")
    print()
    print(f"  {_info('Leave fields empty to skip filters.')}")
    print()

    query: str = input("  Search term  : ").strip()
    mime_type: str = input("  MIME type    : ").strip()

    print()
    print(f"  {_info('Searching ...')}")
    result = doc_controller.search_my_documents(
        query=query,
        mime_type=mime_type if mime_type else None,
    )

    print()
    if not result.get("success"):
        print(f"  {_err(result['error'])}")
        return

    documents = result.get("documents", [])
    pagination = result.get("pagination", {})

    if not documents:
        print(f"  {_info('No documents match your search.')}")
        return

    total = pagination.get("total", 0)
    print(
        f"  {_ok(f'Found {total} document{'s' if total != 1 else ''}')}"
        f" (page {pagination['page']}/{pagination['total_pages']})"
    )
    print()

    for i, doc in enumerate(documents, start=1):
        _print_document_summary(doc, index=i)


def _handle_download(doc_controller: DocumentController) -> None:
    """Prompt for document ID and output directory, then download."""
    print()
    print(f"  {_bold('--- Download Document ---')}")
    print()

    doc_id: str = input("  Document ID  : ").strip()
    if not doc_id:
        print(f"  {_err('Download cancelled — document ID is required.')}")
        return

    output_dir: str = input("  Output dir   : ").strip()
    if not output_dir:
        print(f"  {_err('Download cancelled — output directory is required.')}")
        return

    print()
    print(f"  {_info('Downloading, decrypting, and verifying integrity ...')}")
    result = doc_controller.download(
        document_id=doc_id, output_dir=output_dir
    )

    def _download_details(r: dict[str, Any]) -> None:
        print(f"    {_bold('Document ID')}      : {r['document_id']}")
        print(f"    {_bold('File name')}        : {r['original_filename']}")
        print(f"    {_bold('Size')}             : {r['file_size']:,} bytes")
        print(f"    {_bold('Output path')}      : {r['output_path']}")
        print(f"    {_bold('Integrity')}        : {_ok('Verified (SHA-256)')}")

    _show_result(result, _download_details)


def _handle_share(doc_controller: DocumentController) -> None:
    """Prompt for document ID and recipient username, then share."""
    print()
    print(f"  {_bold('--- Share Document ---')}")
    print()

    doc_id: str = input("  Document ID       : ").strip()
    if not doc_id:
        print(f"  {_err('Share cancelled — document ID is required.')}")
        return

    recipient: str = input("  Recipient username : ").strip()
    if not recipient:
        print(f"  {_err('Share cancelled — recipient username is required.')}")
        return

    print()
    print(f"  {_info('Sharing document ...')}")
    result = doc_controller.share_document(
        document_id=doc_id, recipient_username=recipient
    )

    def _share_details(r: dict[str, Any]) -> None:
        print(f"    {_bold('Document ID')}       : {r['document_id']}")
        print(f"    {_bold('Recipient')}         : {r['recipient_username']}")
        print(f"    {_bold('Permission')}        : {r['permission']}")

    _show_result(result, _share_details)


def _handle_audit_logs(audit_controller: AuditController) -> None:
    """View recent audit logs."""
    print()
    print(f"  {_bold('--- Audit Logs ---')}")
    print()

    page: int = 1
    per_page: int = 20

    while True:
        result = audit_controller.view_audit_logs(page=page, per_page=per_page)

        if not result.get("success"):
            print(f"  {_err(result['error'])}")
            return

        logs = result.get("logs", [])

        if not logs:
            print(f"  {_info('No audit logs found.')}")
            return

        current_page: int = result.get("page", 1)
        total_pages: int = result.get("total_pages", 1)
        total: int = result.get("total", 0)
        has_next: bool = result.get("has_next", False)
        print(
            f"  {_bold(f'Page {current_page}/{total_pages}')}"
            f"  ({total} log{'s' if total != 1 else ''})"
        )
        print()
        _print_audit_table_header()

        for log in logs:
            print(_format_audit_log_row(log))

        print()
        if has_next:
            choice: str = input(
                f"  {_info('[N]ext page, [Q]uit to menu: ')}"
            ).strip().lower()
            if choice == "n":
                page += 1
                continue
        break


def _handle_audit_search(audit_controller: AuditController) -> None:
    """Search audit logs with filters."""
    print()
    print(f"  {_bold('--- Search Audit Logs ---')}")
    print(f"  {_info('Leave fields empty to skip filters.')}")
    print()

    username: str = input("  Username    : ").strip()
    action: str = input("  Action      : ").strip().upper()
    severity: str = input(
        "  Severity (INFO, WARNING, SECURITY_ALERT, CRITICAL): "
    ).strip().upper()
    resource_type: str = input(
        "  Resource type (USER, DOCUMENT, SESSION, SHARING, SYSTEM, AUDIT_LOG): "
    ).strip().upper()
    status: str = input(
        "  Status (SUCCESS, FAILURE, DENIED, ERROR): "
    ).strip().upper()
    date_from: str = input("  Date from (YYYY-MM-DD): ").strip()
    date_to: str = input("  Date to (YYYY-MM-DD): ").strip()

    print()
    print(f"  {_info('Searching audit logs ...')}")
    result = audit_controller.view_audit_logs(
        username=username if username else None,
        action=action if action else None,
        severity=severity if severity else None,
        resource_type=resource_type if resource_type else None,
        status=status if status else None,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None,
        page=1,
        per_page=50,
    )

    print()
    if not result.get("success"):
        print(f"  {_err(result['error'])}")
        return

    logs = result.get("logs", [])

    if not logs:
        print(f"  {_info('No audit logs match your search.')}")
        return

    current_page: int = result.get("page", 1)
    total_pages: int = result.get("total_pages", 1)
    total: int = result.get("total", 0)
    print(
        f"  {_ok(f'Found {total} log{'s' if total != 1 else ''}')}"
        f" (page {current_page}/{total_pages})"
    )
    print()
    for log in logs:
        _print_audit_search_entry(log)


def _handle_shared_documents(doc_controller: DocumentController) -> None:
    """List documents shared with the current user."""
    _paginate_documents(
        title="Shared With Me",
        empty_msg="No documents have been shared with you yet.",
        fetch_fn=lambda p: doc_controller.list_shared_with_me(page=p),
    )


def _handle_upload(doc_controller: DocumentController) -> None:
    """Prompt for file path and upload the document."""
    print()
    print(f"  {_bold('--- Upload Document ---')}")
    print()

    file_path: str = input("  File path  : ").strip().strip("\"'")
    if not file_path:
        print(f"  {_err('Upload cancelled — file path is required.')}")
        return

    print()
    print(f"  {_info('Uploading and encrypting ...')}")
    result: dict[str, Any] = doc_controller.upload(file_path)

    def _upload_details(r: dict[str, Any]) -> None:
        print(f"    {_bold('Document ID')}  : {r['document_id']}")
        print(f"    {_bold('File name')}    : {r['original_filename']}")
        print(f"    {_bold('Size')}         : {r['file_size']:,} bytes")
        print(f"    {_bold('MIME type')}    : {r['mime_type']}")
        print(f"    {_bold('SHA-256')}      : {r['sha256_hash']}")

    _show_result(result, _upload_details)
