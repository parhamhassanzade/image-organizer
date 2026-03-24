from pathlib import Path

INVALID_FILENAME_CHARS = '\\/:*?"<>|'


def sanitize_filename_part(value: str) -> str:
    clean_value = value.strip()
    for char in INVALID_FILENAME_CHARS:
        clean_value = clean_value.replace(char, "-")
    return clean_value.strip().strip(".")


def get_output_basename(subcategory_name: str, output_name: str = "") -> str:
    clean_output_name = sanitize_filename_part(output_name)
    if clean_output_name:
        return clean_output_name
    return sanitize_filename_part(subcategory_name) or "image"


def generate_new_filename(
    subcategory_name: str,
    index: int,
    original_file: str,
    output_name: str = "",
) -> str:
    extension = Path(original_file).suffix.lower()
    base_name = get_output_basename(subcategory_name, output_name)
    return f"{base_name}{extension}"
