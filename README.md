# Image Organizer

اپلیکیشن دسکتاپ ساده برای:

- انتخاب عکس‌ها با دکمه یا drag & drop
- دسته‌بندی بر اساس `Category` و `Subcategory`
- محدود کردن تعداد فایل برای هر ساب‌کتگوری
- خروجی گرفتن به صورت فایل `ZIP`

## پیش‌نیازها

- ویندوز 10 یا 11
- Python 3.11 یا 3.12
- `pip`

## اجرای پروژه روی ویندوز

### 1. ساخت virtual environment

در PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

اگر از `cmd` استفاده می‌کنی:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 2. نصب dependencyها

```powershell
pip install PySide6 pyinstaller
```

### 3. اجرای برنامه

```powershell
python main.py
```

## ساخت فایل اجرایی روی ویندوز

نکته مهم:

- برای گرفتن خروجی ویندوز، build را باید روی خود ویندوز انجام بدهی.
- ساخت فایل `exe` روی macOS یا Linux با PyInstaller به صورت مستقیم برای ویندوز پشتیبانی نمی‌شود.

### روش پیشنهادی: `onedir`

این روش برای این پروژه پایدارتر است، چون فایل `data/categories.json` هم کنار برنامه در دسترس می‌ماند.

```powershell
pyinstaller --noconfirm --windowed --onedir --add-data "data;data" main.py
```

خروجی معمولا اینجا ساخته می‌شود:

```text
dist\main\
```

و فایل اجرایی داخل این مسیر است:

```text
dist\main\main.exe
```

### روش تک‌فایل: `onefile`

اگر حتما فقط یک فایل `exe` می‌خواهی:

```powershell
pyinstaller --noconfirm --windowed --onefile --add-data "data;data" main.py
```

خروجی:

```text
dist\main.exe
```

توجه:

- در حالت `onefile`، رفتار فایل‌های داده و تنظیمات ممکن است از `onedir` حساس‌تر باشد.
- اگر دیدی تنظیمات کتگوری‌ها یا فایل `categories.json` درست persist نمی‌شوند، از `onedir` استفاده کن.

## پاک کردن خروجی‌های build

اگر خواستی دوباره از اول build بگیری:

```powershell
rmdir /s /q build
rmdir /s /q dist
del main.spec
```

اگر در PowerShell بودی:

```powershell
Remove-Item -Recurse -Force build, dist
Remove-Item -Force main.spec
```

فقط اگر واقعا می‌خواهی build قبلی پاک شود این دستورها را اجرا کن.

## ساختار مهم پروژه

```text
main.py
ui/
services/
data/categories.json
```

## نکات استفاده

- تنظیمات کتگوری‌ها از داخل خود برنامه و از بخش `تنظیمات` مدیریت می‌شوند.
- برای هر ساب‌کتگوری می‌توانی `Upload limit` تعریف کنی.
- اگر تعداد فایل‌های انتخاب‌شده از limit بیشتر باشد، برنامه اجازه ساخت ZIP نمی‌دهد.

## عیب‌یابی

### برنامه اجرا نمی‌شود

این دستور را تست کن:

```powershell
python --version
pip --version
```

### ماژول `PySide6` پیدا نمی‌شود

```powershell
pip install PySide6
```

### فایل اجرایی ساخته شد ولی اجرا نمی‌شود

- build را روی خود ویندوز انجام بده
- یک بار پوشه‌های `build` و `dist` را پاک کن و دوباره build بگیر
- روش `onedir` را به جای `onefile` تست کن
