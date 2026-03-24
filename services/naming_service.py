from pathlib import Path

def generate_new_filename(subcategory_name: str, index: int, original_file: str) -> str:
    extension = Path(original_file).suffix.lower()
    return f"{subcategory_name}_{index:03d}{extension}"