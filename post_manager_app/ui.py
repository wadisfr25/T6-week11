from __future__ import annotations

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from post_manager_app.api import ApiResponse, extract_data
from post_manager_app.workers import ApiWorker


class PostManagerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Post Manager - Threading & REST API")
        self.resize(1360, 780)

        self.thread_pool = QThreadPool.globalInstance()
        self.pending_requests = 0
        self.selected_post_id: int | None = None
        self.current_details: dict = {}

        self._build_ui()
        self._connect_events()
        self.load_posts()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(12)

        header = QLabel("Post Manager")
        header.setStyleSheet("font-size: 26px; font-weight: 700; color: #17324d;")

        subtitle = QLabel("CRUD post via REST API dengan multi-threading agar UI tetap responsif.")
        subtitle.setStyleSheet("font-size: 13px; color: #516579;")

        header_box = QVBoxLayout()
        header_box.setSpacing(4)
        header_box.addWidget(header)
        header_box.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([780, 520])

        outer_layout.addLayout(header_box)
        outer_layout.addWidget(splitter)
        self.setCentralWidget(central_widget)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_label = QLabel("Siap")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        status_bar.addWidget(self.status_label, 1)
        status_bar.addPermanentWidget(self.progress_bar)

        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f4f8fb;
                color: #1f2933;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #dbe5ee;
                border-radius: 12px;
                margin-top: 10px;
                background: white;
                font-weight: 700;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px;
                color: #17324d;
            }
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
                border: 1px solid #cad7e1;
                border-radius: 8px;
                padding: 8px;
                background: #fbfdff;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 14px;
                font-weight: 600;
                background: #dfe9f2;
            }
            QPushButton:hover {
                background: #cfdeeb;
            }
            QPushButton:disabled {
                background: #ecf1f5;
                color: #98a5b3;
            }
            QTableWidget {
                border: 1px solid #dbe5ee;
                border-radius: 10px;
                background: white;
                gridline-color: #ecf1f5;
                selection-background-color: #dceeff;
                selection-color: #17324d;
            }
            QHeaderView::section {
                background: #eef5fa;
                border: none;
                border-bottom: 1px solid #dbe5ee;
                padding: 8px;
                font-weight: 700;
                color: #17324d;
            }
            """
        )

    def _build_left_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        top_actions = QHBoxLayout()
        top_actions.setSpacing(8)
        self.refresh_button = QPushButton("Refresh")
        self.reset_button = QPushButton("Reset Form")
        self.edit_button = QPushButton("Update Post")
        self.delete_button = QPushButton("Hapus Post")
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.refresh_button.setStyleSheet("background: #1f7a8c; color: white;")
        self.edit_button.setStyleSheet("background: #2d6a4f; color: white;")
        self.delete_button.setStyleSheet("background: #bc4749; color: white;")
        top_actions.addWidget(self.refresh_button)
        top_actions.addWidget(self.reset_button)
        top_actions.addStretch(1)
        top_actions.addWidget(self.edit_button)
        top_actions.addWidget(self.delete_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Title", "Author", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 280)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 110)

        table_box = QGroupBox("Daftar Posts")
        table_layout = QVBoxLayout(table_box)
        table_layout.addWidget(self.table)

        form_box = QGroupBox("Form Post")
        form_layout = QGridLayout(form_box)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)

        self.title_input = QLineEdit()
        self.author_input = QLineEdit()
        self.slug_input = QLineEdit()
        self.status_input = QComboBox()
        self.status_input.addItems(["published", "draft"])
        self.body_input = QTextEdit()
        self.body_input.setMinimumHeight(140)

        form_layout.addWidget(QLabel("Title"), 0, 0)
        form_layout.addWidget(self.title_input, 0, 1)
        form_layout.addWidget(QLabel("Author"), 1, 0)
        form_layout.addWidget(self.author_input, 1, 1)
        form_layout.addWidget(QLabel("Slug"), 2, 0)
        form_layout.addWidget(self.slug_input, 2, 1)
        form_layout.addWidget(QLabel("Status"), 3, 0)
        form_layout.addWidget(self.status_input, 3, 1)
        form_layout.addWidget(QLabel("Body"), 4, 0, Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(self.body_input, 4, 1)

        bottom_actions = QHBoxLayout()
        bottom_actions.setSpacing(8)
        self.create_button = QPushButton("Tambah Post")
        self.create_button.setStyleSheet("background: #15616d; color: white;")
        self.fill_selected_button = QPushButton("Muat ke Form")
        self.fill_selected_button.setEnabled(False)
        bottom_actions.addWidget(self.create_button)
        bottom_actions.addWidget(self.fill_selected_button)
        bottom_actions.addStretch(1)

        layout.addLayout(top_actions)
        layout.addWidget(table_box, 3)
        layout.addWidget(form_box, 2)
        layout.addLayout(bottom_actions)
        return wrapper

    def _build_right_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        detail_box = QGroupBox("Detail Post")
        detail_layout = QFormLayout(detail_box)
        detail_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop)
        detail_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)

        self.detail_id = QLabel("-")
        self.detail_title = QLabel("-")
        self.detail_author = QLabel("-")
        self.detail_slug = QLabel("-")
        self.detail_status = QLabel("-")
        self.detail_body = QPlainTextEdit()
        self.detail_body.setReadOnly(True)
        self.detail_body.setMinimumHeight(180)
        self.detail_comments = QPlainTextEdit()
        self.detail_comments.setReadOnly(True)
        self.detail_comments.setMinimumHeight(220)

        detail_layout.addRow("ID", self.detail_id)
        detail_layout.addRow("Title", self.detail_title)
        detail_layout.addRow("Author", self.detail_author)
        detail_layout.addRow("Slug", self.detail_slug)
        detail_layout.addRow("Status", self.detail_status)
        detail_layout.addRow("Body", self.detail_body)
        detail_layout.addRow("Comments", self.detail_comments)

        info_box = QGroupBox("Catatan")
        info_layout = QVBoxLayout(info_box)
        note = QLabel(
            "• Klik baris tabel untuk mengambil detail post.\n"
            "• Semua request API dijalankan di thread terpisah.\n"
            "• Error timeout, koneksi, dan validasi slug unik akan ditampilkan ke user."
        )
        note.setStyleSheet("color: #516579; line-height: 1.5;")
        note.setWordWrap(True)
        info_layout.addWidget(note)

        layout.addWidget(detail_box, 5)
        layout.addWidget(info_box, 1)
        return wrapper

    def _connect_events(self) -> None:
        self.refresh_button.clicked.connect(self.load_posts)
        self.reset_button.clicked.connect(self.reset_form)
        self.create_button.clicked.connect(self.create_post)
        self.edit_button.clicked.connect(self.update_post)
        self.delete_button.clicked.connect(self.delete_post)
        self.fill_selected_button.clicked.connect(self.fill_form_with_current_details)
        self.table.itemSelectionChanged.connect(self.handle_table_selection)

    def run_api_worker(
        self,
        operation_name: str,
        method: str,
        endpoint: str = "",
        payload: dict | None = None,
    ) -> None:
        worker = ApiWorker(operation_name, method, endpoint, payload)
        worker.signals.started.connect(self.handle_worker_started)
        worker.signals.finished.connect(self.handle_worker_finished)
        worker.signals.failed.connect(self.handle_worker_failed)
        self.thread_pool.start(worker)

    def handle_worker_started(self, operation_name: str) -> None:
        self.pending_requests += 1
        self.progress_bar.show()
        self.refresh_controls_state()
        self.status_label.setText(f"Loading: {operation_name}...")

    def handle_worker_finished(self, operation_name: str, response: ApiResponse) -> None:
        self.pending_requests = max(0, self.pending_requests - 1)
        self.refresh_controls_state()
        if self.pending_requests == 0:
            self.progress_bar.hide()
        self.status_label.setText(f"Selesai: {operation_name}")

        handler = getattr(self, f"on_{operation_name}", None)
        if handler is not None:
            handler(response)

    def handle_worker_failed(self, operation_name: str, message: str, status_code: int, errors: object) -> None:
        self.pending_requests = max(0, self.pending_requests - 1)
        self.refresh_controls_state()
        if self.pending_requests == 0:
            self.progress_bar.hide()
        self.status_label.setText(f"Gagal: {operation_name}")

        title = "Validasi gagal" if status_code == 422 else f"Request gagal ({operation_name})"
        QMessageBox.critical(self, title, message)

    def refresh_controls_state(self) -> None:
        enabled = self.pending_requests == 0
        self.refresh_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.create_button.setEnabled(enabled)
        has_selection = self.selected_post_id is not None
        self.edit_button.setEnabled(enabled and has_selection)
        self.delete_button.setEnabled(enabled and has_selection)
        self.fill_selected_button.setEnabled(enabled and has_selection)

    def validate_form(self) -> dict | None:
        payload = {
            "title": self.title_input.text().strip(),
            "body": self.body_input.toPlainText().strip(),
            "author": self.author_input.text().strip(),
            "slug": self.slug_input.text().strip(),
            "status": self.status_input.currentText().strip(),
        }
        missing_fields = [key for key, value in payload.items() if not value]
        if missing_fields:
            QMessageBox.warning(
                self,
                "Input belum lengkap",
                "Field berikut wajib diisi: " + ", ".join(missing_fields),
            )
            return None
        return payload

    def load_posts(self) -> None:
        self.run_api_worker("load_posts", "GET")

    def create_post(self) -> None:
        payload = self.validate_form()
        if payload is not None:
            self.run_api_worker("create_post", "POST", payload=payload)

    def update_post(self) -> None:
        if self.selected_post_id is None:
            QMessageBox.information(self, "Tidak ada pilihan", "Pilih post dari tabel terlebih dahulu.")
            return

        payload = self.validate_form()
        if payload is not None:
            self.run_api_worker("update_post", "PUT", endpoint=str(self.selected_post_id), payload=payload)

    def delete_post(self) -> None:
        if self.selected_post_id is None:
            QMessageBox.information(self, "Tidak ada pilihan", "Pilih post dari tabel terlebih dahulu.")
            return

        answer = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            f"Hapus post ID {self.selected_post_id}?\n\nSemua comments yang terkait juga akan ikut terhapus.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.run_api_worker("delete_post", "DELETE", endpoint=str(self.selected_post_id))

    def handle_table_selection(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_post_id = None
            self.current_details = {}
            self.refresh_controls_state()
            self.clear_detail_panel()
            return

        post_id_item = self.table.item(selected_items[0].row(), 0)
        if post_id_item is None:
            return

        self.selected_post_id = int(post_id_item.text())
        self.refresh_controls_state()
        self.run_api_worker("load_detail", "GET", endpoint=str(self.selected_post_id))

    def clear_detail_panel(self) -> None:
        self.detail_id.setText("-")
        self.detail_title.setText("-")
        self.detail_author.setText("-")
        self.detail_slug.setText("-")
        self.detail_status.setText("-")
        self.detail_body.setPlainText("")
        self.detail_comments.setPlainText("")

    def fill_form_with_current_details(self) -> None:
        if not self.current_details:
            QMessageBox.information(self, "Detail belum siap", "Tunggu sampai detail post selesai dimuat.")
            return

        self.title_input.setText(str(self.current_details.get("title", "")))
        self.author_input.setText(str(self.current_details.get("author", "")))
        self.slug_input.setText(str(self.current_details.get("slug", "")))
        self.body_input.setPlainText(str(self.current_details.get("body", "")))

        status_value = str(self.current_details.get("status", "draft"))
        index = self.status_input.findText(status_value)
        if index >= 0:
            self.status_input.setCurrentIndex(index)

    def reset_form(self) -> None:
        self.title_input.clear()
        self.author_input.clear()
        self.slug_input.clear()
        self.body_input.clear()
        self.status_input.setCurrentIndex(0)

    def on_load_posts(self, response: ApiResponse) -> None:
        posts = extract_data(response.payload)
        posts = posts if isinstance(posts, list) else []
        self.table.setRowCount(len(posts))

        for row_index, post in enumerate(posts):
            values = [
                str(post.get("id", "")),
                str(post.get("title", "")),
                str(post.get("author", "")),
                str(post.get("status", "")),
            ]
            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_index == 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col_index == 3:
                    item.setForeground(QColor("#13505b") if value == "published" else QColor("#7c5c00"))
                self.table.setItem(row_index, col_index, item)

        self.status_label.setText(f"Berhasil memuat {len(posts)} posts.")
        if not posts:
            self.clear_detail_panel()

    def on_load_detail(self, response: ApiResponse) -> None:
        detail = extract_data(response.payload)
        detail = detail if isinstance(detail, dict) else {}
        if self.selected_post_id is not None and detail.get("id") != self.selected_post_id:
            return

        self.current_details = detail
        self.detail_id.setText(str(detail.get("id", "-")))
        self.detail_title.setText(str(detail.get("title", "-")))
        self.detail_author.setText(str(detail.get("author", "-")))
        self.detail_slug.setText(str(detail.get("slug", "-")))
        self.detail_status.setText(str(detail.get("status", "-")))
        self.detail_body.setPlainText(str(detail.get("body", "")))
        self.detail_comments.setPlainText(self.format_comments(detail.get("comments", [])))
        self.fill_form_with_current_details()

    def on_create_post(self, response: ApiResponse) -> None:
        payload = response.payload if isinstance(response.payload, dict) else {}
        data = extract_data(payload)
        post_id = str(data.get("id", "")) if isinstance(data, dict) else ""
        message = payload.get("message", "Post berhasil ditambahkan.") if isinstance(payload, dict) else "Post berhasil ditambahkan."
        if post_id:
            message = f"{message}\nID baru: {post_id}"

        QMessageBox.information(self, "Tambah Post", message)
        self.load_posts()

    def on_update_post(self, response: ApiResponse) -> None:
        payload = response.payload if isinstance(response.payload, dict) else {}
        message = payload.get("message", "Post berhasil diperbarui.") if isinstance(payload, dict) else "Post berhasil diperbarui."
        QMessageBox.information(self, "Update Berhasil", message)
        self.load_posts()
        if self.selected_post_id is not None:
            self.run_api_worker("load_detail", "GET", endpoint=str(self.selected_post_id))

    def on_delete_post(self, response: ApiResponse) -> None:
        payload = response.payload if isinstance(response.payload, dict) else {}
        message = payload.get("message", "Post berhasil dihapus.") if isinstance(payload, dict) else "Post berhasil dihapus."
        QMessageBox.information(self, "Hapus Berhasil", message)
        self.selected_post_id = None
        self.current_details = {}
        self.clear_detail_panel()
        self.table.clearSelection()
        self.reset_form()
        self.load_posts()

    def format_comments(self, comments: object) -> str:
        if not isinstance(comments, list) or not comments:
            return "Belum ada komentar."

        lines: list[str] = []
        for index, comment in enumerate(comments, start=1):
            if not isinstance(comment, dict):
                lines.append(f"{index}. {comment}")
                continue
            author = comment.get("author") or comment.get("name") or "Anonim"
            message = comment.get("body") or comment.get("content") or comment.get("comment") or "-"
            lines.append(f"{index}. {author}: {message}")
        return "\n".join(lines)
