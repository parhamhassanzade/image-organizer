from pathlib import Path
import zipfile


def create_archive_path(base_folder: str, archive_stem: str) -> Path:
    target = Path(base_folder)
    target.mkdir(parents=True, exist_ok=True)
    return target / f"{archive_stem}.zip"


def create_zip_archive(
    base_folder: str,
    archive_stem: str,
    archive_items: list[tuple[str, str]],
) -> str:
    archive_path = create_archive_path(base_folder, archive_stem)
    used_names: set[str] = set()

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path, archive_name in archive_items:
            if archive_name in used_names:
                raise ValueError(
                    f"نام خروجی تکراری است و نمی‌تواند در آرشیو نهایی استفاده شود: {archive_name}"
                )

            archive.write(file_path, arcname=archive_name)
            used_names.add(archive_name)

    if not archive_items:
        raise ValueError("هیچ فایلی برای ساخت zip انتخاب نشده است")

    return str(archive_path)
