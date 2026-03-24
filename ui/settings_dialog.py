from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from services.category_service import add_category_entry, load_category_settings, remove_category_entry


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات کتگوری‌ها")
        self.resize(760, 560)
        self.setMinimumSize(560, 460)

        self.setup_ui()
        self.refresh_entries()
        self.apply_responsive_layout()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        self.root_layout = QVBoxLayout(content_widget)
        self.root_layout.setContentsMargins(24, 24, 24, 24)
        self.root_layout.setSpacing(16)

        header_card = QFrame()
        header_card.setObjectName("heroCard")
        header_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(22, 20, 22, 20)
        header_layout.setSpacing(8)

        header_eyebrow = QLabel("Library")
        header_eyebrow.setObjectName("sectionEyebrow")
        header_title = QLabel("مدیریت کتگوری‌ها")
        header_title.setObjectName("sectionTitle")
        header_subtitle = QLabel(
            "برای هر کتگوری می‌توانی چند مسیر ساب‌کتگوری تعریف کنی. نمونه: shoes/sneakers"
        )
        header_subtitle.setObjectName("sectionSubtitle")
        header_subtitle.setWordWrap(True)

        header_layout.addWidget(header_eyebrow)
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)

        form_card = QFrame()
        form_card.setObjectName("surfaceCard")
        form_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(22, 22, 22, 22)
        form_layout.setSpacing(14)

        form_eyebrow = QLabel("ورودی جدید")
        form_eyebrow.setObjectName("sectionEyebrow")
        form_title = QLabel("افزودن دسته‌بندی")
        form_title.setObjectName("sectionTitle")
        form_hint = QLabel(
            "یک کتگوری را یک بار وارد کن و بعد برای همان، چند ساب‌کتگوری مختلف اضافه کن."
        )
        form_hint.setObjectName("sectionSubtitle")
        form_hint.setWordWrap(True)

        category_label = QLabel("Category")
        category_label.setObjectName("fieldLabel")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("مثال: shoes")

        subcategory_label = QLabel("Subcategory path")
        subcategory_label.setObjectName("fieldLabel")
        self.subcategory_input = QLineEdit()
        self.subcategory_input.setPlaceholderText("مثال: sneakers/running")

        limit_label = QLabel("Upload limit")
        limit_label.setObjectName("fieldLabel")
        self.limit_input = QSpinBox()
        self.limit_input.setMinimum(1)
        self.limit_input.setMaximum(9999)
        self.limit_input.setValue(20)
        self.limit_input.setSuffix(" فایل")

        output_name_label = QLabel("New photo name")
        output_name_label.setObjectName("fieldLabel")
        self.output_name_input = QLineEdit()
        self.output_name_input.setPlaceholderText(
            "اختیاری؛ اگر خالی باشد از نام ساب‌کتگوری استفاده می‌شود"
        )

        self.add_button = QPushButton("ذخیره")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.add_entry)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        form_layout.addWidget(form_eyebrow)
        form_layout.addWidget(form_title)
        form_layout.addWidget(form_hint)
        form_layout.addSpacing(4)
        form_layout.addWidget(category_label)
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(subcategory_label)
        form_layout.addWidget(self.subcategory_input)
        form_layout.addWidget(limit_label)
        form_layout.addWidget(self.limit_input)
        form_layout.addWidget(output_name_label)
        form_layout.addWidget(self.output_name_input)
        form_layout.addWidget(self.add_button)

        list_card = QFrame()
        list_card.setObjectName("surfaceCard")
        list_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(22, 22, 22, 22)
        list_layout.setSpacing(14)

        self.list_top = QBoxLayout(QBoxLayout.LeftToRight)
        self.list_top.setSpacing(12)

        list_text = QVBoxLayout()
        list_text.setSpacing(4)

        list_eyebrow = QLabel("موارد ذخیره‌شده")
        list_eyebrow.setObjectName("sectionEyebrow")
        list_title = QLabel("کتگوری‌ها و مسیرها")
        list_title.setObjectName("sectionTitle")
        list_hint = QLabel("برای حذف، یکی از موارد لیست را انتخاب کن.")
        list_hint.setObjectName("sectionSubtitle")
        list_hint.setWordWrap(True)

        list_text.addWidget(list_eyebrow)
        list_text.addWidget(list_title)
        list_text.addWidget(list_hint)

        self.count_badge = QLabel()
        self.count_badge.setObjectName("statusBadge")
        self.count_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.list_top.addLayout(list_text, 1)
        self.list_top.addWidget(self.count_badge, 0, Qt.AlignTop)

        self.entries_list = QListWidget()
        self.entries_list.setWordWrap(True)

        self.actions_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.actions_layout.setSpacing(12)

        self.delete_button = QPushButton("حذف مورد انتخاب‌شده")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_selected_entry)
        self.delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.close_button = QPushButton("بستن")
        self.close_button.setObjectName("ghostButton")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.actions_layout.addWidget(self.delete_button)
        self.actions_layout.addStretch()
        self.actions_layout.addWidget(self.close_button)

        list_layout.addLayout(self.list_top)
        list_layout.addWidget(self.entries_list, 1)
        list_layout.addLayout(self.actions_layout)

        self.root_layout.addWidget(header_card)
        self.root_layout.addWidget(form_card)
        self.root_layout.addWidget(list_card, 1)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def refresh_entries(self):
        self.entries_list.clear()
        categories = load_category_settings()
        entry_count = 0

        for category in sorted(categories):
            header_item = QListWidgetItem(
                f"{category}\n{len(categories[category])} ساب‌کتگوری"
            )
            header_item.setFlags(Qt.NoItemFlags)
            header_item.setToolTip(category)
            self.entries_list.addItem(header_item)

            for entry in categories[category]:
                subcategory = str(entry["subcategory"])
                max_files = int(entry["max_files"])
                output_name = str(entry.get("output_name", "")).strip()
                name_preview = output_name or subcategory.split("/")[-1]
                item = QListWidgetItem(
                    f"  • {subcategory}\n    حداکثر {max_files} فایل\n    نام خروجی: {name_preview}"
                )
                item.setData(Qt.UserRole, (category, subcategory))
                item.setToolTip(
                    f"{category} / {subcategory} / {max_files} فایل / نام خروجی: {name_preview}"
                )
                self.entries_list.addItem(item)
                entry_count += 1

        self.count_badge.setText(f"{entry_count} مسیر")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.apply_responsive_layout()

    def apply_responsive_layout(self):
        dialog_width = self.width()
        stacked_layout = dialog_width < 720

        self.list_top.setDirection(
            QBoxLayout.TopToBottom if stacked_layout else QBoxLayout.LeftToRight
        )
        self.actions_layout.setDirection(
            QBoxLayout.TopToBottom if stacked_layout else QBoxLayout.LeftToRight
        )

        root_margin = 18 if stacked_layout else 24
        root_spacing = 14 if stacked_layout else 16
        self.root_layout.setContentsMargins(root_margin, 18, root_margin, 18)
        self.root_layout.setSpacing(root_spacing)

        policy = QSizePolicy.Expanding if stacked_layout else QSizePolicy.Maximum
        self.count_badge.setSizePolicy(policy, QSizePolicy.Fixed)

        if stacked_layout:
            self.list_top.setAlignment(Qt.AlignLeft)
            self.actions_layout.setStretch(1, 0)
        else:
            self.list_top.setAlignment(Qt.AlignTop)
            self.actions_layout.setStretch(1, 1)

    def add_entry(self):
        category = self.category_input.text()
        subcategory = self.subcategory_input.text()
        max_files = self.limit_input.value()
        output_name = self.output_name_input.text()

        try:
            add_category_entry(category, subcategory, max_files, output_name)
        except ValueError as error:
            QMessageBox.warning(self, "خطا", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
            return

        self.category_input.setText(category.strip())
        self.subcategory_input.clear()
        self.output_name_input.clear()
        self.subcategory_input.setFocus()
        self.refresh_entries()

    def delete_selected_entry(self):
        item = self.entries_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "خطا", "اول یک مورد را انتخاب کن")
            return

        item_data = item.data(Qt.UserRole)
        if not item_data:
            QMessageBox.warning(
                self,
                "خطا",
                "برای حذف، یکی از ساب‌کتگوری‌ها را انتخاب کن"
            )
            return

        category, subcategory = item_data

        try:
            remove_category_entry(category, subcategory)
        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
            return

        self.refresh_entries()
