"""Public re-exports for gui.pages."""

from gui.pages.login_page import LoginPage
from gui.pages.register_page import RegisterPage
from gui.pages.dashboard_page import DashboardPage
from gui.pages.documents_page import DocumentsPage
from gui.pages.document_detail_page import DocumentDetailPage
from gui.pages.upload_page import UploadPage
from gui.pages.download_page import DownloadPage
from gui.pages.share_page import SharePage
from gui.pages.shared_page import SharedPage
from gui.pages.search_page import SearchPage
from gui.pages.face_page import FacePage
from gui.pages.audit_page import AuditPage
from gui.pages.settings_page import SettingsPage
from gui.pages.profile_page import ProfilePage

__all__ = [
    "LoginPage", "RegisterPage", "DashboardPage",
    "DocumentsPage", "DocumentDetailPage",
    "UploadPage", "DownloadPage",
    "SharePage", "SharedPage", "SearchPage",
    "FacePage", "AuditPage",
    "SettingsPage", "ProfilePage",
]
