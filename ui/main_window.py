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
from services.naming_service import generate_new_filename
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


class SubcategoryUploadWidget(QFrame):
    def __init__(
        self,
        subcategory,
        max_files,
        output_name,
        file_collector,
        on_files_changed,
        parent=None,
    ):
        super().__init__(parent)
        self.subcategory = subcategory
        self.max_files = max_files
        self.output_name = output_name
        self.file_collector = file_collector
        self.on_files_changed = on_files_changed
        self.selected_files = []

        self.setup_ui()
        self.refresh_file_list()
        self.refresh_status()

    def setup_ui(self):
        self.setObjectName("uploadCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title_label = QLabel(self.subcategory)
        title_label.setObjectName("uploadTitle")
        title_label.setWordWrap(True)

        self.meta_label = QLabel()
        self.meta_label.setObjectName("uploadMeta")
        self.meta_label.setWordWrap(True)

        title_layout.addWidget(title_label)
        title_layout.addWidget(self.meta_label)

        self.count_badge = QLabel()
        self.count_badge.setObjectName("statusBadge")
        self.count_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        header_layout.addLayout(title_layout, 1)
        header_layout.addWidget(self.count_badge, 0, Qt.AlignTop)

        self.file_list = FileDropListWidget(self.handle_dropped_paths)
        self.file_list.setObjectName("fileDropList")
        self.file_list.setToolTip("فایل یا پوشه را روی این ساب‌کتگوری رها کن")
        self.file_list.setSpacing(6)
        self.file_list.setWordWrap(True)
        self.file_list.setMinimumHeight(190)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.select_button = QPushButton("انتخاب عکس")
        self.select_button.setObjectName("ghostButton")
        self.select_button.clicked.connect(self.select_files)

        self.clear_button = QPushButton("پاک کردن")
        self.clear_button.setObjectName("ghostButton")
        self.clear_button.clicked.connect(self.clear_files)

        actions_layout.addWidget(self.select_button)
        actions_layout.addWidget(self.clear_button)
        actions_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addWidget(self.file_list)
        layout.addLayout(actions_layout)

    def set_files(self, files):
        self.selected_files = self.normalize_file_paths(files)
        self.refresh_file_list()
        self.refresh_status()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"انتخاب عکس برای {self.subcategory}",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if files:
            self.update_selected_files(files, append=True)

    def clear_files(self):
        self.selected_files = []
        self.refresh_file_list()
        self.refresh_status()
        self.on_files_changed(self.subcategory, self.selected_files)

    def handle_dropped_paths(self, paths: list[str]):
        files = self.file_collector(paths)
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
        unique_files = self.normalize_file_paths(combined_files)
        accepted_files = unique_files[:self.max_files]

        if len(unique_files) > self.max_files:
            QMessageBox.warning(
                self,
                "بیش از حد مجاز",
                f"برای {self.subcategory} فقط {self.max_files} فایل ذخیره شد."
            )

        self.selected_files = accepted_files
        self.refresh_file_list()
        self.refresh_status()
        self.on_files_changed(self.subcategory, self.selected_files)

    def refresh_file_list(self):
        self.file_list.clear()

        if not self.selected_files:
            empty_item = QListWidgetItem(
                "هنوز فایلی برای این ساب‌کتگوری انتخاب نشده است.\nفایل را اینجا رها کن یا از دکمه انتخاب استفاده کن."
            )
            empty_item.setFlags(Qt.NoItemFlags)
            empty_item.setTextAlignment(Qt.AlignCenter)
            self.file_list.addItem(empty_item)
            return

        metrics = QFontMetrics(self.file_list.font())
        leaf_subcategory = self.subcategory.split("/")[-1]

        for index, file_path in enumerate(self.selected_files, start=1):
            path = Path(file_path)
            target_name = generate_new_filename(
                leaf_subcategory,
                index,
                file_path,
                self.output_name,
            )
            parent_path = metrics.elidedText(str(path.parent), Qt.ElideMiddle, 280)
            item = QListWidgetItem(
                f"{path.name}\nنام خروجی: {target_name}\n{parent_path}"
            )
            item.setToolTip(
                f"فایل اصلی: {file_path}\nنام خروجی: {target_name}"
            )
            self.file_list.addItem(item)

    def refresh_status(self):
        count = len(self.selected_files)
        self.count_badge.setText(f"{count}/{self.max_files}")
        self.clear_button.setEnabled(count > 0)
        output_preview = self.output_name.strip() or self.subcategory.split("/")[-1]
        self.meta_label.setText(
            f"حداکثر {self.max_files} فایل • نام خروجی: {output_preview}"
        )

    @staticmethod
    def normalize_file_paths(files) -> list[str]:
        normalized_files = []
        seen_paths = set()

        for item in files:
            file_path = str(item).strip()
            if not file_path or file_path in seen_paths:
                continue

            normalized_files.append(file_path)
            seen_paths.add(file_path)

        return normalized_files


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Organizer")
        self.resize(1120, 760)
        self.setMinimumSize(720, 560)

        self.base_folder = ""
        self.category_settings = {}
        self.selected_files_by_category = {}
        self.upload_widgets = {}
        self.last_output_path = ""

        self.setup_ui()
        self.refresh_category_settings()
        self.update_selection_summary()
        self.update_output_summary()
        self.apply_responsive_layout()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        page_scroll = QScrollArea()
        page_scroll.setWidgetResizable(True)
        page_scroll.setFrameShape(QFrame.NoFrame)
        page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        page_widget = QWidget()
        self.root_layout = QVBoxLayout(page_widget)
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
            "برای هر ساب‌کتگوری عکس‌های جداگانه آپلود کن و در نهایت کل کتگوری را به صورت ZIP تحویل بگیر."
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setWordWrap(True)

        self.hero_badges = QBoxLayout(QBoxLayout.LeftToRight)
        self.hero_badges.setSpacing(8)

        self.selection_badge = QLabel()
        self.selection_badge.setObjectName("statusBadge")

        zip_badge = QLabel("Grouped ZIP Export")
        zip_badge.setObjectName("accentBadge")

        self.hero_badges.addWidget(self.selection_badge)
        self.hero_badges.addWidget(zip_badge)
        self.hero_badges.addStretch()

        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)
        hero_layout.addLayout(self.hero_badges)

        self.content_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.content_layout.setSpacing(18)

        controls_card = QFrame()
        controls_card.setObjectName("surfaceCard")
        controls_layout = QVBoxLayout(controls_card)
        controls_layout.setContentsMargins(22, 22, 22, 22)
        controls_layout.setSpacing(16)

        controls_eyebrow = QLabel("تنظیمات")
        controls_eyebrow.setObjectName("sectionEyebrow")
        controls_title = QLabel("مسیر خروجی و کتگوری")
        controls_title.setObjectName("sectionTitle")
        controls_subtitle = QLabel(
            "کتگوری را انتخاب کن. ساب‌کتگوری‌های آن در پنل سمت راست نمایش داده می‌شوند و هر کدام آپلود جداگانه دارند."
        )
        controls_subtitle.setObjectName("sectionSubtitle")
        controls_subtitle.setWordWrap(True)

        folder_label = QLabel("پوشه مقصد")
        folder_label.setObjectName("fieldLabel")
        self.folder_label = QLabel("هنوز پوشه‌ای انتخاب نشده")
        self.folder_label.setObjectName("valueLabel")
        self.folder_label.setWordWrap(True)

        self.folder_button = QPushButton("انتخاب پوشه اصلی")
        self.folder_button.setObjectName("ghostButton")
        self.folder_button.clicked.connect(self.select_base_folder)

        folder_hint = QLabel("فایل ZIP نهایی با نام کتگوری داخل همین مسیر ذخیره می‌شود.")
        folder_hint.setObjectName("mutedText")
        folder_hint.setWordWrap(True)

        self.settings_header = QBoxLayout(QBoxLayout.LeftToRight)
        self.settings_header.setSpacing(12)

        settings_text_layout = QVBoxLayout()
        settings_text_layout.setSpacing(4)

        settings_label = QLabel("مدیریت کتگوری‌ها")
        settings_label.setObjectName("fieldLabel")
        settings_hint = QLabel(
            "از بخش تنظیمات، کتگوری و ساب‌کتگوری‌ها را همراه با محدودیت تعداد فایل و نام خروجی پیش‌فرض تعریف کن."
        )
        settings_hint.setObjectName("mutedText")
        settings_hint.setWordWrap(True)

        settings_text_layout.addWidget(settings_label)
        settings_text_layout.addWidget(settings_hint)

        self.settings_button = QPushButton("تنظیمات")
        self.settings_button.setObjectName("ghostButton")
        self.settings_button.clicked.connect(self.open_settings_dialog)

        self.settings_header.addLayout(settings_text_layout, 1)
        self.settings_header.addWidget(self.settings_button, 0, Qt.AlignTop)

        category_label = QLabel("Category")
        category_label.setObjectName("fieldLabel")
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.update_category_view)

        self.category_info_label = QLabel(
            "بعد از انتخاب کتگوری، ساب‌کتگوری‌های آن در پنل سمت راست ظاهر می‌شوند."
        )
        self.category_info_label.setObjectName("mutedText")
        self.category_info_label.setWordWrap(True)

        output_note = QLabel("آخرین خروجی")
        output_note.setObjectName("fieldLabel")
        self.output_label = QLabel("هنوز آرشیوی ساخته نشده است.")
        self.output_label.setObjectName("outputLabel")
        self.output_label.setWordWrap(True)

        controls_layout.addWidget(controls_eyebrow)
        controls_layout.addWidget(controls_title)
        controls_layout.addWidget(controls_subtitle)
        controls_layout.addWidget(folder_label)
        controls_layout.addWidget(self.folder_label)
        controls_layout.addWidget(self.folder_button)
        controls_layout.addWidget(folder_hint)
        controls_layout.addSpacing(6)
        controls_layout.addLayout(self.settings_header)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(category_label)
        controls_layout.addWidget(self.category_combo)
        controls_layout.addWidget(self.category_info_label)
        controls_layout.addSpacing(4)
        controls_layout.addWidget(output_note)
        controls_layout.addWidget(self.output_label)
        controls_layout.addStretch()

        uploads_card = QFrame()
        uploads_card.setObjectName("surfaceCard")
        uploads_layout = QVBoxLayout(uploads_card)
        uploads_layout.setContentsMargins(22, 22, 22, 22)
        uploads_layout.setSpacing(16)

        self.uploads_top = QBoxLayout(QBoxLayout.LeftToRight)
        self.uploads_top.setSpacing(12)

        uploads_text_layout = QVBoxLayout()
        uploads_text_layout.setSpacing(4)

        uploads_eyebrow = QLabel("ورودی")
        uploads_eyebrow.setObjectName("sectionEyebrow")
        uploads_title = QLabel("آپلود برای هر ساب‌کتگوری")
        uploads_title.setObjectName("sectionTitle")
        uploads_subtitle = QLabel(
            "هر ساب‌کتگوری یک ناحیه drag & drop مستقل دارد و نام نهایی فایل‌ها از تنظیمات همان ساب‌کتگوری خوانده می‌شود."
        )
        uploads_subtitle.setObjectName("sectionSubtitle")
        uploads_subtitle.setWordWrap(True)

        uploads_text_layout.addWidget(uploads_eyebrow)
        uploads_text_layout.addWidget(uploads_title)
        uploads_text_layout.addWidget(uploads_subtitle)

        self.file_count_badge = QLabel()
        self.file_count_badge.setObjectName("statusBadge")

        self.uploads_top.addLayout(uploads_text_layout, 1)
        self.uploads_top.addWidget(self.file_count_badge, 0, Qt.AlignTop)

        self.uploads_hint = QLabel(
            "بعد از انتخاب کتگوری، کارت‌های آپلود برای ساب‌کتگوری‌ها اینجا ساخته می‌شوند."
        )
        self.uploads_hint.setObjectName("mutedText")
        self.uploads_hint.setWordWrap(True)

        self.uploads_scroll_area = QScrollArea()
        self.uploads_scroll_area.setWidgetResizable(True)
        self.uploads_scroll_area.setFrameShape(QFrame.NoFrame)

        self.uploads_container = QWidget()
        self.uploads_container_layout = QVBoxLayout(self.uploads_container)
        self.uploads_container_layout.setContentsMargins(0, 0, 0, 0)
        self.uploads_container_layout.setSpacing(14)
        self.uploads_scroll_area.setWidget(self.uploads_container)

        uploads_layout.addLayout(self.uploads_top)
        uploads_layout.addWidget(self.uploads_hint)
        uploads_layout.addWidget(self.uploads_scroll_area, 1)

        self.content_layout.addWidget(controls_card, 4)
        self.content_layout.addWidget(uploads_card, 7)

        self.footer_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.footer_layout.addStretch()

        self.clear_category_button = QPushButton("پاک کردن آپلودهای این کتگوری")
        self.clear_category_button.setObjectName("ghostButton")
        self.clear_category_button.clicked.connect(self.clear_current_category_uploads)

        self.process_button = QPushButton("ساخت فایل ZIP")
        self.process_button.setObjectName("primaryButton")
        self.process_button.clicked.connect(self.process_files)
        self.process_button.setMinimumHeight(52)

        self.footer_layout.addWidget(self.clear_category_button)
        self.footer_layout.addWidget(self.process_button)

        self.root_layout.addWidget(hero_card)
        self.root_layout.addLayout(self.content_layout, 1)
        self.root_layout.addLayout(self.footer_layout)

        page_scroll.setWidget(page_widget)
        main_layout.addWidget(page_scroll)

    def select_base_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه اصلی")
        if folder:
            self.base_folder = folder
            self.folder_label.setText(folder)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_responsive_layout()

    def apply_responsive_layout(self):
        window_width = self.width()
        compact_layout = window_width < 980
        stacked_actions = window_width < 760

        self.content_layout.setDirection(
            QBoxLayout.TopToBottom if compact_layout else QBoxLayout.LeftToRight
        )
        self.hero_badges.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.settings_header.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.uploads_top.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )
        self.footer_layout.setDirection(
            QBoxLayout.TopToBottom if stacked_actions else QBoxLayout.LeftToRight
        )

        root_margin = 18 if stacked_actions else 28
        self.root_layout.setContentsMargins(root_margin, 20, root_margin, 20)
        self.content_layout.setSpacing(14 if compact_layout else 18)

        if stacked_actions:
            self.process_button.setMinimumWidth(0)
            self.hero_badges.setAlignment(Qt.AlignLeft)
            self.uploads_top.setAlignment(Qt.AlignLeft)
            self.settings_header.setAlignment(Qt.AlignLeft)
        else:
            self.process_button.setMinimumWidth(260)
            self.hero_badges.setAlignment(Qt.AlignVCenter)
            self.uploads_top.setAlignment(Qt.AlignTop)
            self.settings_header.setAlignment(Qt.AlignTop)

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

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        self.refresh_category_settings()

    def refresh_category_settings(self):
        self.category_settings = load_category_settings()

        self.category_combo.blockSignals(True)
        current_category = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("انتخاب کتگوری")

        for category in sorted(self.category_settings):
            self.category_combo.addItem(category)

        if current_category in self.category_settings:
            self.category_combo.setCurrentText(current_category)

        self.category_combo.blockSignals(False)
        self.update_category_view()

    def update_category_view(self):
        category = self.category_combo.currentText()

        if category not in self.category_settings:
            self.category_info_label.setText(
                "بعد از انتخاب کتگوری، ساب‌کتگوری‌های آن در پنل سمت راست ظاهر می‌شوند."
            )
            self.refresh_upload_widgets()
            self.update_selection_summary()
            return

        subcategory_count = len(self.category_settings[category])
        configured_names = sum(
            1
            for entry in self.category_settings[category]
            if str(entry.get("output_name", "")).strip()
        )
        self.category_info_label.setText(
            f"برای کتگوری {category} تعداد {subcategory_count} ساب‌کتگوری تعریف شده است. {configured_names} مورد نام خروجی سفارشی دارند."
        )
        self.refresh_upload_widgets()
        self.update_selection_summary()

    def refresh_upload_widgets(self):
        self.upload_widgets = {}
        self.clear_layout(self.uploads_container_layout)

        category = self.category_combo.currentText()
        if category not in self.category_settings:
            self.uploads_hint.setText("اول یک کتگوری انتخاب کن.")
            self.add_uploads_placeholder("بعد از انتخاب کتگوری، کارت‌های آپلود اینجا ساخته می‌شوند.")
            return

        entries = self.category_settings[category]
        category_uploads = self.selected_files_by_category.setdefault(category, {})

        self.uploads_hint.setText(
            "برای هر ساب‌کتگوری فایل‌ها را جداگانه اضافه کن. اگر نام خروجی در تنظیمات خالی باشد، از نام خود ساب‌کتگوری استفاده می‌شود."
        )

        for entry in entries:
            subcategory = str(entry["subcategory"])
            max_files = int(entry["max_files"])
            output_name = str(entry.get("output_name", "")).strip()
            upload_widget = SubcategoryUploadWidget(
                subcategory=subcategory,
                max_files=max_files,
                output_name=output_name,
                file_collector=self.collect_image_files,
                on_files_changed=self.handle_subcategory_files_changed,
            )
            upload_widget.set_files(category_uploads.get(subcategory, []))
            self.upload_widgets[subcategory] = upload_widget
            self.uploads_container_layout.addWidget(upload_widget)

        self.uploads_container_layout.addStretch()

    def add_uploads_placeholder(self, text: str):
        placeholder = QLabel(text)
        placeholder.setObjectName("outputLabel")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setWordWrap(True)
        placeholder.setMinimumHeight(180)
        self.uploads_container_layout.addWidget(placeholder)
        self.uploads_container_layout.addStretch()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)

    def handle_subcategory_files_changed(self, subcategory: str, files: list[str]):
        category = self.category_combo.currentText()
        if category not in self.category_settings:
            return

        category_uploads = self.selected_files_by_category.setdefault(category, {})
        if files:
            category_uploads[subcategory] = files
        else:
            category_uploads.pop(subcategory, None)

        self.update_selection_summary()

    def clear_current_category_uploads(self):
        category = self.category_combo.currentText()
        if category not in self.category_settings:
            return

        self.selected_files_by_category[category] = {}
        self.refresh_upload_widgets()
        self.update_selection_summary()

    def update_selection_summary(self):
        category = self.category_combo.currentText()
        if category not in self.category_settings:
            self.selection_badge.setText("0 فایل آماده")
            self.file_count_badge.setText("بدون انتخاب")
            self.clear_category_button.setEnabled(False)
            self.process_button.setEnabled(False)
            return

        category_uploads = self.selected_files_by_category.get(category, {})
        total_files = sum(len(files) for files in category_uploads.values())
        active_subcategories = sum(1 for files in category_uploads.values() if files)
        total_subcategories = len(self.category_settings[category])

        self.selection_badge.setText(
            f"{total_files} فایل در {active_subcategories}/{total_subcategories} ساب‌کتگوری"
        )
        self.file_count_badge.setText(f"{total_files} تصویر")
        self.clear_category_button.setEnabled(total_files > 0)
        self.process_button.setEnabled(total_files > 0)

    def update_output_summary(self):
        if not self.last_output_path:
            self.output_label.setText("هنوز آرشیوی ساخته نشده است.")
            return

        self.output_label.setText(self.last_output_path)

    def get_current_category_uploads(self) -> dict[str, list[str]]:
        category = self.category_combo.currentText()
        if category not in self.category_settings:
            return {}
        return self.selected_files_by_category.get(category, {})

    def process_files(self):
        category = self.category_combo.currentText().strip()

        if not self.base_folder:
            QMessageBox.warning(self, "خطا", "اول پوشه اصلی را انتخاب کن")
            return

        if category not in self.category_settings:
            QMessageBox.warning(self, "خطا", "اول یک کتگوری ذخیره‌شده انتخاب کن")
            return

        category_entries = {
            str(entry["subcategory"]): {
                "max_files": int(entry["max_files"]),
                "output_name": str(entry.get("output_name", "")).strip(),
            }
            for entry in self.category_settings[category]
        }
        current_uploads = self.get_current_category_uploads()
        files_by_subcategory = {
            subcategory: files
            for subcategory, files in current_uploads.items()
            if files
        }

        if not files_by_subcategory:
            QMessageBox.warning(
                self,
                "خطا",
                "حداقل برای یکی از ساب‌کتگوری‌ها باید عکس انتخاب شود"
            )
            return

        for subcategory, files in files_by_subcategory.items():
            entry = category_entries.get(subcategory)
            if entry is None:
                continue

            max_files = int(entry["max_files"])
            if len(files) > max_files:
                QMessageBox.warning(
                    self,
                    "تعداد بیش از حد مجاز",
                    f"برای {subcategory} فقط {max_files} فایل مجاز است."
                )
                return

        try:
            output_names_by_subcategory = {
                subcategory: str(entry["output_name"])
                for subcategory, entry in category_entries.items()
            }
            archive_path = create_zip_archive(
                self.base_folder,
                category,
                files_by_subcategory,
                output_names_by_subcategory,
            )

            self.last_output_path = archive_path
            self.update_output_summary()

            QMessageBox.information(
                self,
                "موفق",
                f"خروجی zip با موفقیت ساخته شد:\n{archive_path}"
            )

        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
