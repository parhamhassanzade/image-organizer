from pathlib import Path
import zipfile

from services.naming_service import generate_new_filename


def create_archive_path(base_folder: str, category: str) -> Path:
    target = Path(base_folder)
    target.mkdir(parents=True, exist_ok=True)
    return target / f"{category}.zip"


def create_zip_archive(
    base_folder: str,
    category: str,
    files_by_subcategory: dict[str, list[str]],
    output_names_by_subcategory: dict[str, str],
) -> str:
    archive_path = create_archive_path(base_folder, category)
    has_files = False

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for subcategory_path in sorted(files_by_subcategory):
            file_entries = files_by_subcategory[subcategory_path]
            if not file_entries:
                continue

            has_files = True
            leaf_subcategory = subcategory_path.split("/")[-1]
            output_name = output_names_by_subcategory.get(subcategory_path, "")

            for index, file_path in enumerate(file_entries, start=1):
                new_name = generate_new_filename(
                    leaf_subcategory,
                    index,
                    file_path,
                    output_name,
                )
                archive_name = f"{subcategory_path}/{new_name}"
                archive.write(file_path, arcname=archive_name)

    if not has_files:
        raise ValueError("هیچ فایلی برای ساخت zip انتخاب نشده است")

    return str(archive_path)
