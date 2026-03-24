from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFontMetrics
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.category_service import load_category_settings
from services.file_service import create_zip_archive
from ui.settings_dialog import SettingsDialog

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


class FileDropListWidget(QListWidget):
    def __init__(self, drop_handler, parent=None):
        super().__init__(parent)
        self.drop_handler = drop_handler
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._extract_paths(event):
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent):
        if self._extract_paths(event):
            self._set_drag_active(True)
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        paths = self._extract_paths(event)
        self._set_drag_active(False)
        if paths:
            self.drop_handler(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    @staticmethod
    def _extract_paths(event) -> list[str]:
        if not event.mimeData().hasUrls():
            return []

        return [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

    def _set_drag_active(self, is_active: bool):
        self.setProperty("dragActive", is_active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Organizer")
        self.resize(1080, 720)
        self.setMinimumSize(640, 540)
        self.setAcceptDrops(True)

        self.selected_files = []
        self.base_folder = ""
        self.category_settings = {}
        self.last_output_path = ""
        self.subcategory_limit_label = None

        self.setup_ui()
        self.refresh_category_settings()
        self.refresh_file_list()
        self.update_selection_summary()
        self.update_output_summary()
        self.apply_responsive_layout()

    def setup_ui(self):
        self.setObjectName("mainWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.root_layout = QVBoxLayout(content_widget)
        self.root_layout.setContentsMargins(28, 24, 28, 24)
        self.root_layout.setSpacing(18)

        hero_card = QFrame()
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(12)

        hero_title = QLabel("Image Organizer")
        hero_title.setObjectName("heroTitle")

        hero_subtitle = QLabel(
            "مرتب‌سازی، نام‌گذاری استاندارد و خروجی ZIP برای عکس‌ها در یک جریان ساده."
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setWordWrap(True)

        self.hero_badges = QBoxLayout(QBoxLayout.LeftToRight)
        self.hero_badges.setSpacing(8)

        self.selection_badge = QLabel()
        self.selection_badge.setObjectName("statusBadge")
        self.selection_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        output_badge = QLabel("ZIP Export")
        output_badge.setObjectName("accentBadge")
        output_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.hero_badges.addWidget(self.selection_badge)
        self.hero_badges.addWidget(output_badge)
        self.hero_badges.addStretch()

        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)
        hero_layout.addLayout(self.hero_badges)

        self.content_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.content_layout.setSpacing(18)

        controls_card = QFrame()
        controls_card.setObjectName("surfaceCard")
        controls_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(22, 22, 22, 22)
        controls_layout.setSpacing(16)

        controls_eyebrow = QLabel("تنظیمات")
        controls_eyebrow.setObjectName("sectionEyebrow")
        controls_title = QLabel("مسیر خروجی و دسته‌بندی")
        controls_title.setObjectName("sectionTitle")
        controls_subtitle = QLabel(
            "اول مقصد را انتخاب کن، بعد کتگوری و ساب‌کتگوری را برای ساخت فایل zip مشخص کن."
        )
        controls_subtitle.setObjectName("sectionSubtitle")
        controls_subtitle.setWordWrap(True)

        controls_layout.addWidget(controls_eyebrow)
        controls_layout.addWidget(controls_title)
        controls_layout.addWidget(controls_subtitle)

        folder_label = QLabel("پوشه مقصد")
        folder_label.setObjectName("fieldLabel")
        self.folder_label = QLabel("هنوز پوشه‌ای انتخاب نشده")
        self.folder_label.setObjectName("valueLabel")
        self.folder_label.setWordWrap(True)

        self.folder_button = QPushButton("انتخاب پوشه اصلی")
        self.folder_button.setObjectName("ghostButton")
        self.folder_button.clicked.connect(self.select_base_folder)

        folder_hint = QLabel("خروجی نهایی به صورت zip داخل همین مسیر ذخیره می‌شود.")
        folder_hint.setObjectName("mutedText")
        folder_hint.setWordWrap(True)

        self.settings_header = QBoxLayout(QBoxLayout.LeftToRight)
        self.settings_header.setSpacing(12)

        settings_text_layout = QVBoxLayout()
        settings_text_layout.setSpacing(4)

        settings_label = QLabel("دسته‌بندی‌های ثابت")
        settings_label.setObjectName("fieldLabel")
        settings_hint = QLabel("لیست کتگوری‌ها و ساب‌کتگوری‌ها را از این بخش مدیریت کن.")
        settings_hint.setObjectName("mutedText")
        settings_hint.setWordWrap(True)

        settings_text_layout.addWidget(settings_label)
        settings_text_layout.addWidget(settings_hint)

        self.settings_button = QPushButton("تنظیمات")
        self.settings_button.setObjectName("ghostButton")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.settings_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.settings_header.addLayout(settings_text_layout, 1)
        self.settings_header.addWidget(self.settings_button, 0, Qt.AlignTop)

        category_label = QLabel("Category")
        category_label.setObjectName("fieldLabel")
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.update_subcategory_options)

        subcategory_label = QLabel("Subcategory")
        subcategory_label.setObjectName("fieldLabel")
        self.subcategory_combo = QComboBox()
        self.subcategory_combo.currentIndexChanged.connect(self.update_subcategory_limit_label)

        self.subcategory_limit_label = QLabel("برای این ساب‌کتگوری هنوز محدودیتی نمایش داده نشده است.")
        self.subcategory_limit_label.setObjectName("mutedText")
        self.subcategory_limit_label.setWordWrap(True)

        output_note = QLabel("آخرین خروجی")
        output_note.setObjectName("fieldLabel")
        self.output_label = QLabel("هنوز آرشیوی ساخته نشده است.")
        self.output_label.setObjectName("outputLabel")
        self.output_label.setWordWrap(True)

        controls_layout.addWidget(folder_label)
        controls_layout.addWidget(self.folder_label)
        controls_layout.addWidget(self.folder_button)
        controls_layout.addWidget(folder_hint)
        controls_layout.addSpacing(6)
        controls_layout.addLayout(self.settings_header)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(category_label)
        controls_layout.addWidget(self.category_combo)
        controls_layout.addWidget(subcategory_label)
        controls_layout.addWidget(self.subcategory_combo)
        controls_layout.addWidget(self.subcategory_limit_label)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(output_note)
        controls_layout.addWidget(self.output_label)
        controls_layout.addStretch()

        files_card = QFrame()
        files_card.setObjectName("surfaceCard")
        files_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        files_layout = QVBoxLayout(files_card)
        files_layout.setContentsMargins(22, 22, 22, 22)
        files_layout.setSpacing(16)

        self.files_top = QBoxLayout(QBoxLayout.LeftToRight)
        self.files_top.setSpacing(12)

        files_text_layout = QVBoxLayout()
        files_text_layout.setSpacing(4)

        files_eyebrow = QLabel("ورودی")
        files_eyebrow.setObjectName("sectionEyebrow")
        files_title = QLabel("تصاویر انتخاب‌شده")
        files_title.setObjectName("sectionTitle")
        files_subtitle = QLabel(
            "فایل یا پوشه را روی لیست رها کن یا از دکمه انتخاب استفاده کن. فقط فرمت‌های تصویری پذیرفته می‌شوند."
        )
        files_subtitle.setObjectName("sectionSubtitle")
        files_subtitle.setWordWrap(True)

        files_text_layout.addWidget(files_eyebrow)
        files_text_layout.addWidget(files_title)
        files_text_layout.addWidget(files_subtitle)

        self.file_count_badge = QLabel()
        self.file_count_badge.setObjectName("statusBadge")
        self.file_count_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.files_top.addLayout(files_text_layout, 1)
        self.files_top.addWidget(self.file_count_badge, 0, Qt.AlignTop)

        self.file_list = FileDropListWidget(self.handle_dropped_paths)
        self.file_list.setObjectName("fileDropList")
        self.file_list.setToolTip("فایل یا پوشه را اینجا رها کن")
        self.file_list.setSpacing(6)
        self.file_list.setAlternatingRowColors(False)
        self.file_list.setWordWrap(True)

        self.file_actions = QBoxLayout(QBoxLayout.LeftToRight)
        self.file_actions.setSpacing(12)

        self.select_files_button = QPushButton("انتخاب عکس‌ها")
        self.select_files_button.setObjectName("ghostButton")
        self.select_files_button.clicked.connect(self.select_files)
        self.select_files_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.clear_files_button = QPushButton("پاک کردن لیست")
        self.clear_files_button.setObjectName("ghostButton")
        self.clear_files_button.clicked.connect(self.clear_selected_files)
        self.clear_files_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.file_actions.addWidget(self.select_files_button)
        self.file_actions.addWidget(self.clear_files_button)
        self.file_actions.addStretch()

        files_layout.addLayout(self.files_top)
        files_layout.addWidget(self.file_list, 1)
        files_layout.addLayout(self.file_actions)

        self.content_layout.addWidget(controls_card, 5)
        self.content_layout.addWidget(files_card, 7)

        self.footer_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.footer_layout.addStretch()

        self.process_button = QPushButton("ساخت فایل ZIP")
        self.process_button.setObjectName("primaryButton")
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setMinimumHeight(52)
        self.process_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.footer_layout.addWidget(self.process_button)

        self.root_layout.addWidget(hero_card)
        self.root_layout.addLayout(self.content_layout, 1)
        self.root_layout.addLayout(self.footer_layout)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def select_base_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه اصلی")
        if folder:
            self.base_folder = folder
            self.folder_label.setText(folder)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "انتخاب عکس‌ها",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.update_selected_files(files, append=False)

    def clear_selected_files(self):
        self.selected_files = []
        self.refresh_file_list()
        self.update_selection_summary()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self._extract_drop_paths(event):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent):
        if self._extract_drop_paths(event):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        paths = self._extract_drop_paths(event)
        if paths:
            self.handle_dropped_paths(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def handle_dropped_paths(self, paths: list[str]):
        files = self.collect_image_files(paths)
        if not files:
            QMessageBox.warning(
                self,
                "فایل نامعتبر",
                "فقط فایل‌های تصویری یا پوشه‌های شامل تصویر قابل اضافه شدن هستند"
            )
            return

        self.update_selected_files(files, append=True)

    def update_selected_files(self, files: list[str], append: bool):
        combined_files = self.selected_files + files if append else files
        self.selected_files = list(dict.fromkeys(combined_files))
        self.refresh_file_list()
        self.update_selection_summary()

    def refresh_file_list(self):
        self.file_list.clear()

        if not self.selected_files:
            empty_item = QListWidgetItem(
                "فایلی انتخاب نشده است.\nفایل یا پوشه را اینجا رها کن یا از دکمه انتخاب استفاده کن."
            )
            empty_item.setFlags(Qt.NoItemFlags)
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.file_list.addItem(empty_item)
            return

        for file_path in self.selected_files:
            path = Path(file_path)
            item = QListWidgetItem(self._format_file_item_text(path))
            item.setToolTip(str(path))
            self.file_list.addItem(item)

    def update_selection_summary(self):
        count = len(self.selected_files)
        file_label = "فایل" if count <= 1 else "فایل"
        self.selection_badge.setText(f"{count} {file_label} آماده")
        self.file_count_badge.setText(f"{count} تصویر")
        self.clear_files_button.setEnabled(count > 0)

    def update_output_summary(self):
        if not self.last_output_path:
            self.output_label.setText("هنوز آرشیوی ساخته نشده است.")
            return

        self.output_label.setText(self.last_output_path)

    def update_subcategory_limit_label(self):
        selected_entry = self.get_selected_subcategory_entry()
        if selected_entry is None:
            self.subcategory_limit_label.setText(
                "برای این ساب‌کتگوری هنوز محدودیتی نمایش داده نشده است."
            )
            return

        max_files = int(selected_entry["max_files"])
        self.subcategory_limit_label.setText(
            f"حداکثر تعداد فایل برای این ساب‌کتگوری: {max_files}"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_responsive_layout()
        if self.selected_files:
            self.refresh_file_list()

    def apply_responsive_layout(self):
        window_width = self.width()
        compact_layout = window_width < 980
        stacked_actions = window_width < 720

        self.content_layout.setDirection(
            QBoxLayout.TopToBottom if compact_layout else QBoxLayout.LeftToRight
        )
        self.hero_badges.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.settings_header.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.files_top.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.file_actions.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.footer_layout.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )

        root_margin = 18 if stacked_actions else 28
        root_spacing = 14 if stacked_actions else 18
        self.root_layout.setContentsMargins(root_margin, 20, root_margin, 20)
        self.root_layout.setSpacing(root_spacing)
        self.content_layout.setSpacing(14 if compact_layout else 18)

        button_policy = QSizePolicy.Expanding if stacked_actions else QSizePolicy.Maximum
        self.selection_badge.setSizePolicy(button_policy, QSizePolicy.Fixed)
        self.file_count_badge.setSizePolicy(button_policy, QSizePolicy.Fixed)
        self.settings_button.setSizePolicy(button_policy, QSizePolicy.Fixed)

        if stacked_actions:
            self.hero_badges.setAlignment(Qt.AlignLeft)
            self.files_top.setAlignment(Qt.AlignLeft)
            self.settings_header.setAlignment(Qt.AlignLeft)
            self.file_actions.setStretch(2, 0)
            self.footer_layout.setStretch(0, 0)
            self.process_button.setMinimumWidth(0)
        else:
            self.hero_badges.setAlignment(Qt.AlignVCenter)
            self.files_top.setAlignment(Qt.AlignTop)
            self.settings_header.setAlignment(Qt.AlignTop)
            self.file_actions.setStretch(2, 1)
            self.footer_layout.setStretch(0, 1)
            self.process_button.setMinimumWidth(260)

    def _format_file_item_text(self, path: Path) -> str:
        metrics = QFontMetrics(self.file_list.font())
        available_width = max(self.file_list.viewport().width() - 48, 220)
        parent_text = metrics.elidedText(str(path.parent), Qt.ElideMiddle, available_width)
        return f"{path.name}\n{parent_text}"

    def collect_image_files(self, paths: list[str]) -> list[str]:
        collected_files = []

        for raw_path in paths:
            path = Path(raw_path)
            if path.is_file() and self.is_supported_image(path):
                collected_files.append(str(path))
                continue

            if path.is_dir():
                for child in sorted(path.rglob("*")):
                    if child.is_file() and self.is_supported_image(child):
                        collected_files.append(str(child))

        return collected_files

    @staticmethod
    def is_supported_image(path: Path) -> bool:
        return path.suffix.lower() in IMAGE_EXTENSIONS

    @staticmethod
    def _extract_drop_paths(event) -> list[str]:
        if not event.mimeData().hasUrls():
            return []

        return [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.isLocalFile()
        ]

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        self.refresh_category_settings()

    def refresh_category_settings(self):
        self.category_settings = load_category_settings()

        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("انتخاب کتگوری")

        for category in sorted(self.category_settings):
            self.category_combo.addItem(category)

        self.category_combo.blockSignals(False)
        self.update_subcategory_options()

    def update_subcategory_options(self):
        self.subcategory_combo.blockSignals(True)
        self.subcategory_combo.clear()
        self.subcategory_combo.addItem("انتخاب ساب‌کتگوری")

        category = self.category_combo.currentText()
        if category not in self.category_settings:
            self.subcategory_combo.blockSignals(False)
            self.update_subcategory_limit_label()
            return

        for entry in self.category_settings[category]:
            subcategory = str(entry["subcategory"])
            max_files = int(entry["max_files"])
            self.subcategory_combo.addItem(subcategory, entry)
            index = self.subcategory_combo.count() - 1
            self.subcategory_combo.setItemData(
                index,
                f"حداکثر {max_files} فایل",
                Qt.ToolTipRole,
            )

        self.subcategory_combo.blockSignals(False)
        self.update_subcategory_limit_label()

    def get_selected_subcategory_entry(self) -> dict[str, int | str] | None:
        entry = self.subcategory_combo.currentData()
        if isinstance(entry, dict):
            return entry

        category = self.category_combo.currentText()
        subcategory = self.subcategory_combo.currentText().strip()
        if category not in self.category_settings or not subcategory:
            return None

        for item in self.category_settings[category]:
            if item["subcategory"] == subcategory:
                return item

        return None

    def process_files(self):
        category = self.category_combo.currentText().strip()
        subcategory_path = self.subcategory_combo.currentText().strip()
        subcategories = [part.strip() for part in subcategory_path.split("/") if part.strip()]
        selected_entry = self.get_selected_subcategory_entry()

        if not self.base_folder:
            QMessageBox.warning(self, "خطا", "اول پوشه اصلی را انتخاب کن")
            return

        if category not in self.category_settings:
            QMessageBox.warning(self, "خطا", "اول یک کتگوری ذخیره‌شده انتخاب کن")
            return

        if not subcategories:
            QMessageBox.warning(
                self,
                "خطا",
                "اول یک ساب‌کتگوری ذخیره‌شده انتخاب کن"
            )
            return

        if selected_entry is None:
            QMessageBox.warning(self, "خطا", "اطلاعات ساب‌کتگوری پیدا نشد")
            return

        if not self.selected_files:
            QMessageBox.warning(self, "خطا", "هیچ عکسی انتخاب نشده")
            return

        max_files = int(selected_entry["max_files"])
        if len(self.selected_files) > max_files:
            QMessageBox.warning(
                self,
                "تعداد بیش از حد مجاز",
                f"برای این ساب‌کتگوری فقط {max_files} فایل مجاز است."
            )
            return

        try:
            archive_path = create_zip_archive(
                self.base_folder,
                category,
                subcategories,
                self.selected_files
            )

            self.last_output_path = archive_path
            self.update_output_summary()

            QMessageBox.information(
                self,
                "موفق",
                f"خروجی zip با موفقیت ساخته شد:\n{archive_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))
