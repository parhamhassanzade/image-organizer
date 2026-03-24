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
    for category in sorted(categories):
        clean_category = category.strip()
        if not clean_category:
            continue

        normalized_entries = normalize_category_entries(categories[clean_category])
        if normalized_entries:
            normalized_data[clean_category] = normalized_entries

    with SETTINGS_FILE.open("w", encoding="utf-8") as file:
        json.dump({"categories": normalized_data}, file, ensure_ascii=False, indent=2)


def add_category_entry(
    category: str,
    subcategory: str,
    max_files: int,
) -> dict[str, list[dict[str, int | str]]]:
    clean_category = category.strip()
    clean_subcategory = normalize_subcategory_path(subcategory)
    clean_max_files = normalize_max_files(max_files)

    if not clean_category:
        raise ValueError("نام کتگوری نمی‌تواند خالی باشد")

    if not clean_subcategory:
        raise ValueError("نام ساب‌کتگوری نمی‌تواند خالی باشد")

    categories = load_category_settings()
    category_items = categories.setdefault(clean_category, [])

    existing_entry = find_subcategory_entry(category_items, clean_subcategory)
    if existing_entry is None:
        category_items.append(
            {"subcategory": clean_subcategory, "max_files": clean_max_files}
        )
    else:
        existing_entry["max_files"] = clean_max_files

    category_items.sort(key=lambda item: str(item["subcategory"]))
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

    normalized_entries.sort(key=lambda item: str(item["subcategory"]))
    return normalized_entries


def normalize_category_entry(entry) -> dict[str, int | str] | None:
    if isinstance(entry, str):
        clean_subcategory = normalize_subcategory_path(entry)
        if not clean_subcategory:
            return None

        return {"subcategory": clean_subcategory, "max_files": 9999}

    if not isinstance(entry, dict):
        return None

    clean_subcategory = normalize_subcategory_path(str(entry.get("subcategory", "")))
    if not clean_subcategory:
        return None

    return {
        "subcategory": clean_subcategory,
        "max_files": normalize_max_files(entry.get("max_files", 9999)),
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
