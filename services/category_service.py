from __future__ import annotations

import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "categories.json"


def load_category_settings() -> dict[str, list[dict[str, int | str]]]:
    if not SETTINGS_FILE.exists():
        return {}

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except json.JSONDecodeError:
        return {}

    categories = raw_data.get("categories", {})
    normalized_data: dict[str, list[dict[str, int | str]]] = {}

    for category, entries in categories.items():
        clean_category = category.strip()
        if not clean_category:
            continue

        normalized_entries = normalize_category_entries(entries)
        if normalized_entries:
            normalized_data[clean_category] = normalized_entries

    return normalized_data


def save_category_settings(categories: dict[str, list[dict[str, int | str]]]) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_data: dict[str, list[dict[str, int | str]]] = {}
    for category, entries in categories.items():
        clean_category = category.strip()
        if not clean_category:
            continue

        normalized_entries = normalize_category_entries(entries)
        if normalized_entries:
            normalized_data[clean_category] = normalized_entries

    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump({"categories": normalized_data}, file, ensure_ascii=False, indent=2)


def add_category_entry(
    category: str,
    subcategory: str,
    max_files: int,
    output_name: str,
    archive_name: str,
) -> dict[str, list[dict[str, int | str]]]:
    clean_category = category.strip()
    clean_subcategory = normalize_subcategory_path(subcategory)
    clean_max_files = normalize_max_files(max_files)
    clean_output_name = normalize_output_name(output_name)
    clean_archive_name = normalize_archive_name(archive_name)

    if not clean_category:
        raise ValueError("نام کتگوری نمی‌تواند خالی باشد")

    if not clean_subcategory:
        raise ValueError("نام ساب‌کتگوری نمی‌تواند خالی باشد")

    categories = load_category_settings()
    category_items = categories.setdefault(clean_category, [])

    if not clean_archive_name and category_items:
        clean_archive_name = normalize_archive_name(category_items[0].get("archive_name", ""))

    for item in category_items:
        item["archive_name"] = clean_archive_name

    existing_entry = find_subcategory_entry(category_items, clean_subcategory)
    if existing_entry is None:
        category_items.append(
            {
                "subcategory": clean_subcategory,
                "max_files": clean_max_files,
                "output_name": clean_output_name,
                "archive_name": clean_archive_name,
            }
        )
    else:
        existing_entry["max_files"] = clean_max_files
        existing_entry["output_name"] = clean_output_name
        existing_entry["archive_name"] = clean_archive_name

    save_category_settings(categories)
    return categories


def remove_category_entry(
    category: str,
    subcategory: str,
) -> dict[str, list[dict[str, int | str]]]:
    categories = load_category_settings()
    clean_category = category.strip()
    clean_subcategory = normalize_subcategory_path(subcategory)

    if clean_category not in categories:
        return categories

    categories[clean_category] = [
        item for item in categories[clean_category]
        if item["subcategory"] != clean_subcategory
    ]

    if not categories[clean_category]:
        del categories[clean_category]

    save_category_settings(categories)
    return categories


def update_category_entry(
    old_category: str,
    old_subcategory: str,
    new_category: str,
    new_subcategory: str,
    max_files: int,
    output_name: str,
    archive_name: str,
) -> dict[str, list[dict[str, int | str]]]:
    categories = load_category_settings()
    clean_old_category = old_category.strip()
    clean_old_subcategory = normalize_subcategory_path(old_subcategory)
    clean_new_category = new_category.strip()
    clean_new_subcategory = normalize_subcategory_path(new_subcategory)
    clean_max_files = normalize_max_files(max_files)
    clean_output_name = normalize_output_name(output_name)
    clean_archive_name = normalize_archive_name(archive_name)

    if not clean_new_category:
        raise ValueError("نام کتگوری نمی‌تواند خالی باشد")

    if not clean_new_subcategory:
        raise ValueError("نام ساب‌کتگوری نمی‌تواند خالی باشد")

    source_items = categories.get(clean_old_category)
    if not source_items:
        raise ValueError("کتگوری انتخاب‌شده پیدا نشد")

    existing_entry = find_subcategory_entry(source_items, clean_old_subcategory)
    if existing_entry is None:
        raise ValueError("ساب‌کتگوری انتخاب‌شده پیدا نشد")

    if not clean_archive_name:
        clean_archive_name = normalize_archive_name(existing_entry.get("archive_name", ""))

    if clean_old_category == clean_new_category and clean_old_subcategory == clean_new_subcategory:
        existing_entry["max_files"] = clean_max_files
        existing_entry["output_name"] = clean_output_name
        existing_entry["archive_name"] = clean_archive_name
        save_category_settings(categories)
        return categories

    target_items = categories.setdefault(clean_new_category, [])
    duplicate_entry = find_subcategory_entry(target_items, clean_new_subcategory)
    if duplicate_entry is not None:
        raise ValueError("این ساب‌کتگوری قبلا ثبت شده است")

    if clean_old_category == clean_new_category:
        existing_entry["subcategory"] = clean_new_subcategory
        existing_entry["max_files"] = clean_max_files
        existing_entry["output_name"] = clean_output_name
        existing_entry["archive_name"] = clean_archive_name
        save_category_settings(categories)
        return categories

    categories[clean_old_category] = [
        item for item in source_items
        if item["subcategory"] != clean_old_subcategory
    ]
    if not categories[clean_old_category]:
        del categories[clean_old_category]

    if target_items:
        clean_archive_name = normalize_archive_name(target_items[0].get("archive_name", clean_archive_name))

    for item in target_items:
        item["archive_name"] = clean_archive_name

    target_items.append(
        {
            "subcategory": clean_new_subcategory,
            "max_files": clean_max_files,
            "output_name": clean_output_name,
            "archive_name": clean_archive_name,
        }
    )

    save_category_settings(categories)
    return categories


def rename_category(
    old_category: str,
    new_category: str,
) -> dict[str, list[dict[str, int | str]]]:
    categories = load_category_settings()
    clean_old_category = old_category.strip()
    clean_new_category = new_category.strip()

    if not clean_new_category:
        raise ValueError("نام کتگوری نمی‌تواند خالی باشد")

    if clean_old_category not in categories:
        raise ValueError("کتگوری انتخاب‌شده پیدا نشد")

    if clean_old_category == clean_new_category:
        return categories

    source_items = categories[clean_old_category]
    target_items = categories.get(clean_new_category)
    if target_items is not None:
        target_subcategories = {
            str(item["subcategory"]) for item in target_items
        }
        duplicate_subcategories = [
            str(item["subcategory"])
            for item in source_items
            if str(item["subcategory"]) in target_subcategories
        ]
        if duplicate_subcategories:
            raise ValueError("در کتگوری مقصد ساب‌کتگوری تکراری وجود دارد")

        target_items.extend(source_items)
        del categories[clean_old_category]
    else:
        reordered_categories: dict[str, list[dict[str, int | str]]] = {}
        for category, entries in categories.items():
            if category == clean_old_category:
                reordered_categories[clean_new_category] = entries
            elif category != clean_new_category:
                reordered_categories[category] = entries
        categories = reordered_categories

    save_category_settings(categories)
    return categories


def move_category(
    category: str,
    direction: int,
) -> dict[str, list[dict[str, int | str]]]:
    categories = load_category_settings()
    clean_category = category.strip()
    category_names = list(categories)

    if clean_category not in categories:
        return categories

    current_index = category_names.index(clean_category)
    target_index = current_index + direction
    if target_index < 0 or target_index >= len(category_names):
        return categories

    category_names[current_index], category_names[target_index] = (
        category_names[target_index],
        category_names[current_index],
    )

    reordered_categories = {
        category_name: categories[category_name]
        for category_name in category_names
    }
    save_category_settings(reordered_categories)
    return reordered_categories


def move_subcategory(
    category: str,
    subcategory: str,
    direction: int,
) -> dict[str, list[dict[str, int | str]]]:
    categories = load_category_settings()
    clean_category = category.strip()
    clean_subcategory = normalize_subcategory_path(subcategory)
    entries = categories.get(clean_category)
    if not entries:
        return categories

    current_index = next(
        (
            index
            for index, entry in enumerate(entries)
            if str(entry["subcategory"]) == clean_subcategory
        ),
        -1,
    )
    if current_index < 0:
        return categories

    target_index = current_index + direction
    if target_index < 0 or target_index >= len(entries):
        return categories

    entries[current_index], entries[target_index] = (
        entries[target_index],
        entries[current_index],
    )

    save_category_settings(categories)
    return categories


def normalize_category_entries(entries) -> list[dict[str, int | str]]:
    normalized_entries: list[dict[str, int | str]] = []
    seen_subcategories: set[str] = set()

    for entry in entries:
        normalized_entry = normalize_category_entry(entry)
        if normalized_entry is None:
            continue

        subcategory = str(normalized_entry["subcategory"])
        if subcategory in seen_subcategories:
            continue

        normalized_entries.append(normalized_entry)
        seen_subcategories.add(subcategory)

    return normalized_entries


def normalize_category_entry(entry) -> dict[str, int | str] | None:
    if isinstance(entry, str):
        clean_subcategory = normalize_subcategory_path(entry)
        if not clean_subcategory:
            return None

        return {
            "subcategory": clean_subcategory,
            "max_files": 9999,
            "output_name": "",
            "archive_name": "",
        }

    if not isinstance(entry, dict):
        return None

    clean_subcategory = normalize_subcategory_path(str(entry.get("subcategory", "")))
    if not clean_subcategory:
        return None

    return {
        "subcategory": clean_subcategory,
        "max_files": normalize_max_files(entry.get("max_files", 9999)),
        "output_name": normalize_output_name(entry.get("output_name", "")),
        "archive_name": normalize_archive_name(entry.get("archive_name", "")),
    }


def find_subcategory_entry(
    entries: list[dict[str, int | str]],
    subcategory: str,
) -> dict[str, int | str] | None:
    for entry in entries:
        if entry["subcategory"] == subcategory:
            return entry
    return None


def normalize_max_files(value) -> int:
    try:
        max_files = int(value)
    except (TypeError, ValueError):
        raise ValueError("حداکثر تعداد فایل باید یک عدد صحیح باشد")

    if max_files < 1:
        raise ValueError("حداکثر تعداد فایل باید حداقل 1 باشد")

    return max_files


def normalize_subcategory_path(value: str) -> str:
    normalized_value = value.strip().replace("\\", "/").replace(">", "/")
    parts = [part.strip() for part in normalized_value.split("/") if part.strip()]
    return "/".join(parts)


def normalize_output_name(value) -> str:
    return str(value).strip()


def normalize_archive_name(value) -> str:
    return str(value).strip()
