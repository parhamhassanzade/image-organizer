from pathlib import Path
import zipfile

from services.naming_service import generate_new_filename

def create_archive_path(base_folder: str, category: str, subcategories: list[str]) -> Path:
    if not subcategories:
        raise ValueError("حداقل یک ساب‌کتگوری لازم است")

    target = Path(base_folder) / category
    for subcategory in subcategories[:-1]:
        target /= subcategory

    target.mkdir(parents=True, exist_ok=True)
    return target / f"{subcategories[-1]}.zip"

def create_zip_archive(base_folder: str, category: str, subcategories: list[str], files: list[str]) -> str:
    archive_path = create_archive_path(base_folder, category, subcategories)
    leaf_subcategory = subcategories[-1]

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, file_path in enumerate(files, start=1):
            new_name = generate_new_filename(leaf_subcategory, index, file_path)
            archive.write(file_path, arcname=new_name)

    return str(archive_path)
