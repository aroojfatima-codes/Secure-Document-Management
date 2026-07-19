"""Main application controller -- navigation, theming, sidebar toggle, page routing."""

from __future__ import annotations

import traceback

import customtkinter as ctk

from gui.animations import fade_in
from gui.components.dialogs import Toast
from gui.components.sidebar import Sidebar
from gui.components.topbar import TopBar
from gui.pages.audit_page import AuditPage
from gui.pages.dashboard_page import DashboardPage
from gui.pages.document_detail_page import DocumentDetailPage
from gui.pages.documents_page import DocumentsPage
from gui.pages.download_page import DownloadPage
from gui.pages.face_page import FacePage
from gui.pages.login_page import LoginPage
from gui.pages.profile_page import ProfilePage
from gui.pages.register_page import RegisterPage
from gui.pages.search_page import SearchPage
from gui.pages.settings_page import SettingsPage
from gui.pages.share_page import SharePage
from gui.pages.shared_page import SharedPage
from gui.pages.upload_page import UploadPage
from gui.theme import Dim, ThemeManager

tm = ThemeManager()
C = tm.C


class App(ctk.CTk):

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.title("Secure Document Management System")
        self.minsize(Dim.MIN_W, Dim.MIN_H)
        self.configure(fg_color=C.bg_main)

        self.after(50, self._maximize_window)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._current_user = None
        self._page_cache: dict[str, ctk.CTkFrame] = {}
        self._active_page_name = ""
        self._sidebar_expanded = True

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(
            self, width=Dim.SIDEBAR_W,
            on_navigate=self._navigate,
            on_toggle=self._toggle_sidebar,
            on_logout=self._logout,
            on_login=self._show_login,
            on_register=self._show_register,
        )
        self._sidebar.grid(row=0, column=0, sticky="ns")

        right = ctk.CTkFrame(self, fg_color=C.bg_main)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        self._right = right

        self._topbar = TopBar(right)
        self._topbar.grid(row=0, column=0, sticky="ew")
        self._topbar.set_theme_change_callback(self._change_theme)
        self._topbar.set_logout_callback(self._logout)

        self._page_container = ctk.CTkFrame(right, fg_color=C.bg_main)
        self._page_container.grid(row=1, column=0, sticky="nsew")
        self._page_container.grid_columnconfigure(0, weight=1)
        self._page_container.grid_rowconfigure(0, weight=1)

        self._show_login()

    def _maximize_window(self):
        try:
            self.state("zoomed")
        except Exception:
            try:
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
            except Exception:
                pass

    def _show_login(self):
        self._clear_pages(destroy=True)
        try:
            self._sidebar.build_unauth_menu()
        except Exception:
            pass
        self._topbar.set_logged_in(False)
        try:
            page = LoginPage(
                self._page_container,
                on_login=self._handle_login,
                on_switch_register=lambda: self._show_register(),
                on_face_login=self._handle_face_login,
            )
            page.grid(row=0, column=0, sticky="nsew")
            self._page_cache["login"] = page
            self._active_page_name = "login"
            self._topbar.set_breadcrumb("Login")
            fade_in(page)
        except Exception as e:
            traceback.print_exc()
            Toast(self, f"Error loading login page: {e}", "error")

    def _show_register(self):
        self._clear_pages(destroy=True)
        try:
            page = RegisterPage(
                self._page_container,
                on_register=self._handle_register,
                on_switch_login=lambda: self._show_login(),
            )
            page.grid(row=0, column=0, sticky="nsew")
            self._page_cache["register"] = page
            self._active_page_name = "register"
            self._topbar.set_breadcrumb("Register")
            fade_in(page)
        except Exception as e:
            traceback.print_exc()
            Toast(self, f"Error loading register page: {e}", "error")

    def _build_current_user(self, result: dict, fallback_username: str = "") -> dict:
        """Extract user info dict from a login/face-login result."""
        username = result.get("username", fallback_username)
        return {
            "user_id": result.get("user_id", ""),
            "username": username,
            "full_name": result.get("full_name", username.title()),
            "role": result.get("role", "viewer"),
            "email": result.get("email", ""),
        }

    def _handle_login(self, username: str, password: str):
        if self.controller:
            try:
                result = self.controller["auth"].login(username, password)
                if result and result.get("success"):
                    self._current_user = self._build_current_user(result, username)
                    try:
                        self._on_auth_success()
                    except Exception as e:
                        traceback.print_exc()
                        Toast(self, f"Dashboard failed to load: {e}", "error")
                    return
                else:
                    error_msg = result.get("error", "Login failed") if result else "Login failed"
                    Toast(self, error_msg, "error")
                    return
            except Exception as e:
                Toast(self, f"Login error: {e}", "error")
                return
        self._current_user = {
            "username": username,
            "full_name": username.title(),
            "role": "admin",
            "email": f"{username}@example.com",
        }
        try:
            self._on_auth_success()
        except Exception as e:
            traceback.print_exc()
            Toast(self, f"Dashboard failed to load: {e}", "error")

    def _handle_face_login(self):
        if self.controller:
            try:
                result = self.controller["face"].login_face()
                if result and result.get("success"):
                    self._current_user = self._build_current_user(result)
                    try:
                        self._on_auth_success()
                    except Exception as e:
                        traceback.print_exc()
                        Toast(self, f"Dashboard failed to load: {e}", "error")
                    return
                else:
                    error_msg = result.get("error", "Face login failed") if result else "Face login failed"
                    Toast(self, error_msg, "error")
                    return
            except Exception as e:
                Toast(self, f"Face login error: {e}", "error")
                return
        Toast(self, "No controller available for face login", "error")

    def _handle_register(self, username, fullname, email, role, password):
        if self.controller:
            try:
                result = self.controller["auth"].register(username, password, role)
                if result and result.get("success"):
                    Toast(self, f"Account created for {username}!", "success")
                else:
                    error_msg = result.get("error", "Registration failed") if result else "Registration failed"
                    Toast(self, error_msg, "error")
                    return
            except Exception as e:
                Toast(self, f"Registration error: {e}", "error")
                return
        else:
            Toast(self, f"Account created for {username}!", "success")
        self._show_login()

    def _on_auth_success(self):
        Toast(self, f"Welcome, {self._current_user.get('full_name', self._current_user['username'])}!", "success")
        try:
            self._sidebar.build_auth_menu(self._current_user)
        except Exception:
            pass
        self._topbar.set_logged_in(True)
        self._page_cache.clear()
        self._navigate("dashboard")

    def _logout(self):
        if self.controller:
            try:
                self.controller["auth"].logout()
            except Exception:
                pass
        self._current_user = None
        self._page_cache.clear()
        self._show_login()
        Toast(self, "Logged out successfully", "info")

    def _navigate(self, page_name: str):
        try:
            if page_name == "login":
                self._show_login()
                return
            if page_name == "register":
                self._show_register()
                return
            if page_name == self._active_page_name and page_name in self._page_cache:
                return
            if page_name in self._page_cache:
                self._show_cached_page(page_name)
                return
            page = self._create_page(page_name)
            if page:
                self._page_cache[page_name] = page
                self._show_cached_page(page_name)
            else:
                Toast(self, f"Failed to create page '{page_name}'. Check logs for details.", "error")
        except Exception as e:
            traceback.print_exc()
            Toast(self, f"Navigation error: {e}", "error")

    def _show_cached_page(self, name: str):
        self._clear_pages()
        try:
            page = self._page_cache.get(name)
            if page is None or not page.winfo_exists():
                self._page_cache.pop(name, None)
                self._navigate(name)
                return
            page.grid(row=0, column=0, sticky="nsew")
            self._active_page_name = name
            self._topbar.set_breadcrumb(self._breadcrumb_for(name))
            u = self._current_user or {}
            self._topbar.set_user(
                u.get("full_name", u.get("username", "User")),
                u.get("role", ""),
            )
            fade_in(page)
        except Exception as e:
            traceback.print_exc()
            Toast(self, f"Error showing page '{name}': {e}", "error")

    def _create_page(self, name: str):
        u = self._current_user or {}
        ctrl = self.controller

        def _load_docs_for_page(page, method="list_my_documents"):
            """Load documents into a page that has a load_documents method."""
            if ctrl:
                try:
                    result = getattr(ctrl["document"], method)(1, 50)
                    docs = result.get("documents", []) if result and result.get("success") else []
                    page.load_documents(docs)
                except Exception:
                    pass

        def _make_dashboard():
            return DashboardPage(self._page_container, user=u)

        def _make_documents():
            page = DocumentsPage(self._page_container)
            page._app = self
            _load_docs_for_page(page)
            return page

        def _make_document_detail():
            return DocumentDetailPage(self._page_container, app=self)

        def _make_upload():
            page = UploadPage(self._page_container)
            page._app = self
            return page

        def _make_download():
            page = DownloadPage(self._page_container)
            page._app = self
            _load_docs_for_page(page)
            return page

        def _make_share():
            page = SharePage(self._page_container)
            page._app = self
            _load_docs_for_page(page)
            return page

        def _make_shared():
            page = SharedPage(self._page_container)
            page._app = self
            _load_docs_for_page(page, "list_shared_with_me")
            return page

        def _make_search():
            page = SearchPage(self._page_container)
            page._app = self
            _load_docs_for_page(page)
            return page

        def _make_face():
            def on_enroll(username):
                if ctrl and u.get("user_id"):
                    try:
                        return ctrl["face"].enroll(u["user_id"], username)
                    except Exception:
                        return {"success": False, "error": "Enrollment failed"}
                return {"success": True, "message": f"Face enrolled for '{username}'"}

            def on_verify():
                if ctrl:
                    try:
                        return ctrl["face"].login_face()
                    except Exception:
                        return {"success": False, "error": "Verification failed"}
                return {"success": True, "message": "Face verification successful!"}

            return FacePage(self._page_container, on_enroll=on_enroll, on_verify=on_verify)

        def _make_audit():
            page = AuditPage(self._page_container)
            if ctrl:
                try:
                    result = ctrl["audit"].view_audit_logs()
                    logs = result.get("logs", []) if result and result.get("success") else []
                    page.load_logs(logs)
                except Exception:
                    pass
            return page

        def _make_settings():
            return SettingsPage(self._page_container, on_theme_change=self._change_theme)

        def _make_profile():
            return ProfilePage(self._page_container, user=u)

        pages = {
            "dashboard": _make_dashboard,
            "documents": _make_documents,
            "document_detail": _make_document_detail,
            "upload": _make_upload,
            "download": _make_download,
            "share": _make_share,
            "shared": _make_shared,
            "search": _make_search,
            "face": _make_face,
            "audit": _make_audit,
            "settings": _make_settings,
            "profile": _make_profile,
        }
        factory = pages.get(name)
        if factory:
            try:
                return factory()
            except Exception as e:
                traceback.print_exc()
                Toast(self, f"Error creating page '{name}': {e}", "error")
                return None
        return None

    def _breadcrumb_for(self, name: str) -> str:
        titles = {
            "dashboard": "Dashboard",
            "documents": "Documents",
            "document_detail": "Documents / Detail",
            "upload": "Documents / Upload",
            "download": "Documents / Download",
            "share": "Documents / Share",
            "shared": "Documents / Shared",
            "search": "Search",
            "face": "Face Recognition",
            "audit": "Audit Logs",
            "settings": "Settings",
            "profile": "Profile",
        }
        return titles.get(name, name.title())

    def _toggle_sidebar(self):
        try:
            self._sidebar_expanded = not self._sidebar_expanded
            target = Dim.SIDEBAR_W if self._sidebar_expanded else Dim.SIDEBAR_COLLAPSED_W
            self._sidebar.animate_width(target)
        except Exception:
            self._sidebar_expanded = True

    def _change_theme(self, mode: str):
        try:
            tm.set_mode(mode)
            self.configure(fg_color=C.bg_main)
            self._apply_theme_recursive(self)
        except Exception:
            pass

    def _apply_theme_recursive(self, widget):
        try:
            if hasattr(widget, "apply_theme"):
                widget.apply_theme()
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._apply_theme_recursive(child)
        except Exception:
            pass

    def _clear_pages(self, destroy: bool = False):
        """Hide page widgets in the page container.

        If destroy=True, also destroy them and clear the cache.
        """
        for child in self._page_container.winfo_children():
            try:
                child.grid_forget()
                if destroy:
                    child.destroy()
            except Exception:
                pass
        if destroy:
            self._page_cache.clear()
            self._active_page_name = ""

    def _on_close(self):
        if self.controller:
            try:
                self.controller["auth"].logout()
            except Exception:
                pass
        self.destroy()


SDMSApp = App
