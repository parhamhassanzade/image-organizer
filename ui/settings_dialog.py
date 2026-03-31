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

from services.category_service import (
    add_category_entry,
    load_category_settings,
    move_category,
    move_subcategory,
    rename_category,
    remove_category_entry,
    update_category_entry,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تنظیمات")
        self.resize(760, 560)
        self.setMinimumSize(560, 460)
        self.editing_category: str | None = None
        self.editing_entry: tuple[str, str] | None = None

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

        header_title = QLabel("مدیریت کتگوری‌ها")
        header_title.setObjectName("sectionTitle")
        header_subtitle = QLabel("تعریف کتگوری و ساب‌کتگوری")
        header_subtitle.setObjectName("sectionSubtitle")
        header_subtitle.setWordWrap(True)

        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)

        form_card = QFrame()
        form_card.setObjectName("surfaceCard")
        form_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(22, 22, 22, 22)
        form_layout.setSpacing(14)

        self.form_title = QLabel("افزودن مورد")
        self.form_title.setObjectName("sectionTitle")
        self.form_hint = QLabel("هر سطر یک ساب‌کتگوری است.")
        self.form_hint.setObjectName("sectionSubtitle")
        self.form_hint.setWordWrap(True)

        category_label = QLabel("کتگوری")
        category_label.setObjectName("fieldLabel")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("مثال: shoes")

        subcategory_label = QLabel("ساب‌کتگوری")
        subcategory_label.setObjectName("fieldLabel")
        self.subcategory_input = QLineEdit()
        self.subcategory_input.setPlaceholderText("مثال: sneakers/running")

        limit_label = QLabel("حداکثر فایل")
        limit_label.setObjectName("fieldLabel")
        self.limit_input = QSpinBox()
        self.limit_input.setMinimum(1)
        self.limit_input.setMaximum(9999)
        self.limit_input.setValue(20)
        self.limit_input.setSuffix(" فایل")

        output_name_label = QLabel("نام خروجی")
        output_name_label.setObjectName("fieldLabel")
        self.output_name_input = QLineEdit()
        self.output_name_input.setPlaceholderText("اختیاری")

        self.add_button = QPushButton("ذخیره")
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self.save_entry)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.cancel_edit_button = QPushButton("لغو ویرایش")
        self.cancel_edit_button.setObjectName("ghostButton")
        self.cancel_edit_button.clicked.connect(lambda: self.reset_form())
        self.cancel_edit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cancel_edit_button.hide()

        form_actions = QHBoxLayout()
        form_actions.setSpacing(12)
        form_actions.addWidget(self.add_button)
        form_actions.addWidget(self.cancel_edit_button)

        form_layout.addWidget(self.form_title)
        form_layout.addWidget(self.form_hint)
        form_layout.addSpacing(4)
        form_layout.addWidget(category_label)
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(subcategory_label)
        form_layout.addWidget(self.subcategory_input)
        form_layout.addWidget(limit_label)
        form_layout.addWidget(self.limit_input)
        form_layout.addWidget(output_name_label)
        form_layout.addWidget(self.output_name_input)
        form_layout.addLayout(form_actions)

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

        list_title = QLabel("لیست")
        list_title.setObjectName("sectionTitle")
        list_hint = QLabel("برای ویرایش یا تغییر ترتیب، کتگوری یا ساب‌کتگوری را انتخاب کن.")
        list_hint.setObjectName("sectionSubtitle")
        list_hint.setWordWrap(True)

        list_text.addWidget(list_title)
        list_text.addWidget(list_hint)

        self.count_badge = QLabel()
        self.count_badge.setObjectName("statusBadge")
        self.count_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        self.list_top.addLayout(list_text, 1)
        self.list_top.addWidget(self.count_badge, 0, Qt.AlignTop)

        self.entries_list = QListWidget()
        self.entries_list.setWordWrap(True)
        self.entries_list.itemSelectionChanged.connect(self.handle_entry_selection_changed)

        self.actions_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.actions_layout.setSpacing(12)

        self.move_up_button = QPushButton("بالا")
        self.move_up_button.setObjectName("ghostButton")
        self.move_up_button.clicked.connect(lambda: self.move_selected_item(-1))
        self.move_up_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.move_down_button = QPushButton("پایین")
        self.move_down_button.setObjectName("ghostButton")
        self.move_down_button.clicked.connect(lambda: self.move_selected_item(1))
        self.move_down_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.delete_button = QPushButton("حذف")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_selected_entry)
        self.delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.close_button = QPushButton("بستن")
        self.close_button.setObjectName("ghostButton")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.actions_layout.addWidget(self.move_up_button)
        self.actions_layout.addWidget(self.move_down_button)
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

    def refresh_entries(self, selected_entry: tuple[str, str] | None = None):
        self.entries_list.blockSignals(True)
        self.entries_list.clear()
        categories = load_category_settings()
        entry_count = 0
        selected_item = None

        for category in categories:
            header_item = QListWidgetItem(
                f"{category}\n{len(categories[category])} ساب‌کتگوری"
            )
            header_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            header_item.setData(
                Qt.UserRole,
                {
                    "mode": "category",
                    "category": category,
                },
            )
            header_item.setToolTip(category)
            self.entries_list.addItem(header_item)
            if selected_entry == (category, ""):
                selected_item = header_item

            for entry in categories[category]:
                subcategory = str(entry["subcategory"])
                max_files = int(entry["max_files"])
                output_name = str(entry.get("output_name", "")).strip()
                name_preview = output_name or subcategory.split("/")[-1]
                item = QListWidgetItem(
                    f"• {subcategory}\n{max_files} فایل | {name_preview}"
                )
                item.setData(
                    Qt.UserRole,
                    {
                        "mode": "entry",
                        "category": category,
                        "subcategory": subcategory,
                        "max_files": max_files,
                        "output_name": output_name,
                    },
                )
                item.setToolTip(
                    f"{category} / {subcategory} / {max_files} فایل / {name_preview}"
                )
                self.entries_list.addItem(item)
                if selected_entry == (category, subcategory):
                    selected_item = item
                entry_count += 1

        self.count_badge.setText(f"{entry_count} مسیر")
        if selected_item is not None:
            self.entries_list.setCurrentItem(selected_item)
        self.entries_list.blockSignals(False)
        if selected_item is not None:
            self.handle_entry_selection_changed()
        else:
            self.update_action_buttons()

    def handle_entry_selection_changed(self):
        item = self.entries_list.currentItem()
        if item is None:
            self.update_action_buttons()
            return

        item_data = item.data(Qt.UserRole)
        if not item_data:
            self.update_action_buttons()
            return

        if item_data["mode"] == "category":
            self.editing_category = item_data["category"]
            self.editing_entry = None
            self.form_title.setText("ویرایش کتگوری")
            self.form_hint.setText("نام کتگوری را تغییر بده.")
            self.add_button.setText("ذخیره تغییرات")
            self.cancel_edit_button.show()
            self.category_input.setText(item_data["category"])
            self.subcategory_input.clear()
            self.limit_input.setValue(20)
            self.output_name_input.clear()
            self.subcategory_input.setEnabled(False)
            self.limit_input.setEnabled(False)
            self.output_name_input.setEnabled(False)
            self.update_action_buttons(item_data)
            return

        self.editing_category = None
        self.editing_entry = (item_data["category"], item_data["subcategory"])
        self.form_title.setText("ویرایش ساب‌کتگوری")
        self.form_hint.setText("نام کتگوری و ساب‌کتگوری را تغییر بده.")
        self.add_button.setText("ذخیره تغییرات")
        self.cancel_edit_button.show()
        self.subcategory_input.setEnabled(True)
        self.limit_input.setEnabled(True)
        self.output_name_input.setEnabled(True)
        self.category_input.setText(item_data["category"])
        self.subcategory_input.setText(item_data["subcategory"])
        self.limit_input.setValue(int(item_data["max_files"]))
        self.output_name_input.setText(item_data["output_name"])
        self.update_action_buttons(item_data)

    def update_action_buttons(self, item_data=None):
        can_move_up = False
        can_move_down = False
        can_delete = False

        if item_data:
            categories = load_category_settings()
            if item_data["mode"] == "category":
                category_names = list(categories)
                if item_data["category"] in category_names:
                    index = category_names.index(item_data["category"])
                    can_move_up = index > 0
                    can_move_down = index < len(category_names) - 1
            elif item_data["mode"] == "entry":
                entries = categories.get(item_data["category"], [])
                subcategories = [str(entry["subcategory"]) for entry in entries]
                if item_data["subcategory"] in subcategories:
                    index = subcategories.index(item_data["subcategory"])
                    can_move_up = index > 0
                    can_move_down = index < len(subcategories) - 1
                    can_delete = True

        self.move_up_button.setEnabled(can_move_up)
        self.move_down_button.setEnabled(can_move_down)
        self.delete_button.setEnabled(can_delete)

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

    def save_entry(self):
        category = self.category_input.text()
        subcategory = self.subcategory_input.text()
        max_files = self.limit_input.value()
        output_name = self.output_name_input.text()

        try:
            if self.editing_category is not None:
                rename_category(
                    self.editing_category,
                    category,
                )
            elif self.editing_entry is None:
                add_category_entry(
                    category,
                    subcategory,
                    max_files,
                    output_name,
                    "",
                )
            else:
                old_category, old_subcategory = self.editing_entry
                update_category_entry(
                    old_category,
                    old_subcategory,
                    category,
                    subcategory,
                    max_files,
                    output_name,
                    "",
                )
        except ValueError as error:
            QMessageBox.warning(self, "خطا", str(error))
            return
        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
            return

        self.reset_form(category.strip())
        self.refresh_entries()

    def reset_form(self, category_text: str = ""):
        self.editing_category = None
        self.editing_entry = None
        self.form_title.setText("افزودن مورد")
        self.form_hint.setText("هر سطر یک ساب‌کتگوری است.")
        self.add_button.setText("ذخیره")
        self.cancel_edit_button.hide()
        self.entries_list.blockSignals(True)
        self.entries_list.clearSelection()
        self.entries_list.setCurrentItem(None)
        self.entries_list.blockSignals(False)
        self.subcategory_input.setEnabled(True)
        self.limit_input.setEnabled(True)
        self.output_name_input.setEnabled(True)
        self.category_input.setText(category_text)
        self.subcategory_input.clear()
        self.limit_input.setValue(20)
        self.output_name_input.clear()
        self.subcategory_input.setFocus()
        self.update_action_buttons()

    def move_selected_item(self, direction: int):
        item = self.entries_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "خطا", "یک مورد را انتخاب کن")
            return

        item_data = item.data(Qt.UserRole)
        if not item_data:
            return

        try:
            if item_data["mode"] == "category":
                move_category(item_data["category"], direction)
                selected_entry = (item_data["category"], "")
            else:
                move_subcategory(
                    item_data["category"],
                    item_data["subcategory"],
                    direction,
                )
                selected_entry = (
                    item_data["category"],
                    item_data["subcategory"],
                )
        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
            return

        self.refresh_entries(selected_entry)

    def delete_selected_entry(self):
        item = self.entries_list.currentItem()
        if item is None:
            QMessageBox.warning(self, "خطا", "یک مورد را انتخاب کن")
            return

        item_data = item.data(Qt.UserRole)
        if not item_data:
            QMessageBox.warning(
                self,
                "خطا",
                "یک ساب‌کتگوری را انتخاب کن"
            )
            return

        if item_data["mode"] != "entry":
            QMessageBox.warning(self, "خطا", "برای حذف، یک ساب‌کتگوری را انتخاب کن")
            return

        category = item_data["category"]
        subcategory = item_data["subcategory"]

        try:
            remove_category_entry(category, subcategory)
        except Exception as error:
            QMessageBox.critical(self, "خطا", str(error))
            return

        if self.editing_entry == (category, subcategory):
            self.reset_form()
        self.refresh_entries()
