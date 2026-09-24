# CAC & Driver's License Barcode Scanner (`cacbarcode`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Lint: Ruff](https://img.shields.io/badge/lint-ruff-brightgreen.svg)](https://github.com/astral-sh/ruff)
[![Tests: Passing](https://img.shields.io/badge/tests-11%2F11%20passing-brightgreen.svg)](test_cacbarcode.py)
[![Dependencies: Zero](https://img.shields.io/badge/dependencies-0%20(stdlib%20only)-success.svg)](requirements.txt)

A lightweight, zero-dependency Python library, interactive Tkinter graphical scanner/logger, and CLI utility for auto-detecting, decoding, and parsing:
- **DoD Common Access Cards (CAC)** — both Front PDF417 (Versions 1, N, and M) and Back Code 39
- **North American Driver's Licenses & State IDs** — AAMVA PDF417 across US and Canada
- **Generic 1D/2D Barcodes** — Fallback for visitor badges, guest passes, and custom IDs

> **Note on Project Scope:** This repository is a standalone, decoupled barcode scanning and logging engine designed as an open-source building block for access control, registration, and attendance systems. It operates independently with zero external runtime dependencies.

---

## Table of Contents

- [Supported Barcode Formats](#supported-barcode-formats)
- [Requirements & Dependencies](#requirements--dependencies)
- [Installation & Setup](#installation--setup)
- [Hardware Scanner Configuration](#hardware-scanner-configuration)
- [Usage Guide](#usage-guide)
  - [1. Graphical Scanner App (`CAC_Scanner.py`)](#1-graphical-scanner-app-cac_scannerpy)
  - [2. Command-Line Interface (`barcodecmd.py`)](#2-command-line-interface-barcodecmdpy)
  - [3. Python Library API (`cacbarcode.py`)](#3-python-library-api-cacbarcodepy)
- [Field Reference & Decoded Attributes](#field-reference--decoded-attributes)
- [Testing & Code Quality](#testing--code-quality)
- [Privacy & Security Notice](#privacy--security-notice)
- [References](#references)
- [License](#license)

---

## Supported Barcode Formats

### 1. DoD CAC PDF417 (Front of Military ID)
Fully decodes Department of Defense Common Access Cards per the DoD ID Bar Code SDK:
- **Version 1 (88 characters):** DoD ID Bar Code SDK v7.5 (Sep 2012), Table 3.
- **Version N (89 characters):** DoD ID Bar Code SDK v7.5 (Sep 2012), Table 4 (includes trailing Middle Initial).
- **Version M (99 characters):** Modern field cards currently in active circulation.
- **Decoded Fields:** DoD EDIPI, First Name, Middle Initial / Name, Last Name, Date of Birth (and calculated Age), Expiration Date, Issue Date, Branch of Service (Army, Navy, USAF, USMC, USCG, NOAA, USPHS, etc.), Personnel Category (Active Duty, Contractor, Civil Service, Retired, etc.), Rank, Pay Plan Code, Pay Grade Code, Card Instance ID (CII), and Person Designator Identifier (PDI).

### 2. DoD CAC Code 39 (Back of Military ID)
Strict decoding of the 18-character linear barcode on the reverse side of CACs per DoD SDK Table 2:
- **Strict Validation:** Requires exact 18-character length and valid Base-32 character set (`0-9`, `A-V`). Eliminates false-positive cross-talk when scanning driver's licenses or generic barcodes.
- **Decoded Fields:** DoD EDIPI, Branch of Service, Personnel Category, and Card Instance Identifier (CII).

### 3. AAMVA Driver's Licenses & State IDs (PDF417)
Decodes standard North American jurisdiction identification barcodes:
- **Comprehensive Standard Support:** Handles subfiles `DL` and `ID` across AAMVA standard revisions (v1 through modern).
- **Dual Ingestion Modes:** Reliably decodes both standard delimiter-intact records (`\n`, `\r`, `\x1e`, `\x1c`) and stripped single-line keyboard-wedge streams.
- **Robust Multi-Jurisdiction Dates:** Parses ISO (`YYYY-MM-DD`), US standard (`MMDDCCYY`), and Canadian standard (`CCYYMMDD`) formats.
- **Decoded Fields:** License / ID Number (`DAQ`), Full Name (`DAC`, `DAD`, `DCS`, `DAA`, `DCT`), Full Residential Address (Street `DAG`, City `DAI`, State/Jurisdiction `DAJ`, ZIP/Postal Code `DAK`), Date of Birth, Age, Expiration Date, Issue Date, Sex / Gender (`DBC`), License Class (`DCA`), Restrictions (`DCB`), Endorsements (`DCD`), and REAL ID compliance flag (`DDA`).

### 4. Generic 1D / 2D Barcodes
Fallback parser for membership cards, guest badges, visitor passes, and QR/Code 128 barcodes.

---

## Requirements & Dependencies

### Runtime Dependencies
- **Python 3.8+** (Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13 tested).
- **Zero third-party pip dependencies:** Uses Python's standard library exclusively (`datetime`, `re`, `csv`, `time`, `sys`, `unittest`).
- **Tkinter (GUI):**
  - **Windows & macOS:** Included by default with the standard Python installer from [python.org](https://www.python.org/downloads/).
  - **Debian / Ubuntu Linux:** Install via package manager:
    ```bash
    sudo apt update && sudo apt install python3-tk
    ```
  - **Fedora / RHEL Linux:** Install via `dnf`:
    ```bash
    sudo dnf install python3-tkinter
    ```

### Development Dependencies
- **Ruff:** Fast Python linter used for code quality checks:
  ```bash
  pip install -r requirements-dev.txt
  ```

---

## Installation & Setup

### 1. Clone or Download the Repository
```bash
git clone https://github.com/ColinTrachte/CACBarcode.git
cd CACBarcode
```

### 2. (Optional) Create a Virtual Environment
While runtime dependencies are built into Python, using a virtual environment is recommended for development:

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Verify Installation
Run the test suite to confirm everything is operational:
```bash
python -m unittest test_cacbarcode.py -v
```
All 11 tests should execute and report `OK` in a few milliseconds.

---

## Hardware Scanner Configuration

Any standard 2D barcode scanner capable of reading **PDF417** and **Code 39** will work with this project (e.g., Honeywell Xenon, Zebra DS2208 / DS4608, Eyoyo, Inateck, Symcode).

### Scanner Configuration Checklist:
1. **Operating Mode:** Set the scanner to **USB HID Keyboard Wedge** (the default factory mode for almost all USB scanners). In this mode, scanned barcodes type characters directly into whatever window has focus.
2. **Enable PDF417 & Code 39:** Ensure the PDF417 symbology is enabled. (Some scanners have PDF417 disabled out of the box; scan the "Enable PDF417" programming barcode in the scanner manufacturer's quick-start card).
3. **Suffix Carriage Return (CR / Enter):** Ensure the scanner is configured to send a **Carriage Return (`\r` / Enter)** or **CR+LF** suffix after every scan.
4. **Keyboard-Wedge Quiet Window Buffering:**
   - Multi-line 2D barcodes (such as AAMVA Driver's Licenses) contain internal newline characters between fields.
   - Traditional text entry fields would trigger a submit on the very first internal newline, truncating the scan.
   - `CAC_Scanner.py` includes built-in quiet-window debouncing: when it detects high-speed keyboard input characteristic of an AAMVA header, it buffers incoming keystrokes until a brief quiet window passes, ensuring the complete payload is captured.

---

## Usage Guide

### 1. Graphical Scanner App (`CAC_Scanner.py`)

Launch the GUI application:
```bash
python CAC_Scanner.py
```

#### Key Features:
- **Scan Entry Field:** Centered barcode entry box. Plug in your USB scanner, click the entry field (focused automatically), and scan a card.
- **Unified Table View:** Displays decoded cards in a clean, resizable table:
  - `Type`: Card type badge (`CAC PDF417`, `CAC Code 39`, `Driver's License`, `Generic Barcode`).
  - `ID / EDIPI`: DoD EDIPI or Driver's License Number.
  - `Full Name`: Parsed full name.
  - `DOB (Age)`: Date of birth with current calculated age (e.g., `1990-07-04 (36)`).
  - `Expiration`: Card expiration date.
  - `State / Branch`: State jurisdiction or Military branch (e.g., `USA`, `USAF`, `USN`, `AR`, `CA`).
  - `Category / Class`: Personnel category (e.g., `Active Duty`, `DoD contractor`) or Driver's license class (`C`, `D`).
  - `Rank / Sex`: Military rank or gender (`Male`, `Female`).
  - `Details / Address`: Residential street address or pay plan/grade details.
  - `Scan Time`: Timestamp when the card was scanned.
- **Visual Status & Expired Card Highlighting:**
  - Cards that have expired are highlighted with a soft red background (`#ffe6e6`) and flagged `[EXPIRED]`.
  - Duplicate scans are recognized and reported in the status bar.
  - Scanning a CAC Front (PDF417) after scanning its Back (Code 39) automatically enriches the existing row with complete name, rank, and date details.
- **Live Search / Filter:** Type in the `Filter / Search:` box to instantly highlight matching rows in green across any field (ID, name, branch, state, rank).
- **Double-Click Card Details Inspector:** Double-click any row to open an inspection dialog showing all decoded metadata, full multiline address, raw barcode data, and a "Copy Raw Data" clipboard button.
- **CSV Logging & Export:**
  - Every scan is automatically logged locally to `scanned_data.csv`.
  - Click **Export CSV** to export the current filtered table to a custom CSV file.

---

### 2. Command-Line Interface (`barcodecmd.py`)

The CLI utility provides quick auto-detection and pretty-printed terminal summaries:

```bash
# Option A: Pass raw barcode data directly as an argument
python barcodecmd.py "1TONPASX1G9R3EKEAH"

# Option B: Run interactively and scan/paste when prompted
python barcodecmd.py

# Option C: Pipe raw barcode data from stdin or a file
# On Windows (PowerShell):
Get-Content scan.txt | python barcodecmd.py

# On Linux / macOS:
cat scan.txt | python barcodecmd.py
```

**Example CLI Output (DoD CAC):**
```text
============================================================
  Barcode Type : CAC PDF417 [PDF417]
------------------------------------------------------------
  EDIPI         : 1620938196
  Name          : Colin G Trachte
  Date of Birth : 1991-05-22 (Age: 35)
  Expiration    : 2027-08-31 [ACTIVE]
  State         : DoD
  Branch        : USA
  Rank          : EA00
  Category      : DoD contract employee
============================================================
```

**Example CLI Output (AAMVA Driver's License):**
```text
============================================================
  Barcode Type : Driver's License [AAMVA_DL]
------------------------------------------------------------
  ID / License #: S99999999
  Name          : JANE Q SAMPLE
  Date of Birth : 1990-07-04 (Age: 36)
  Expiration    : 2032-07-04 [ACTIVE]
  State         : AR
  Category      : Driver License
  Sex           : Female
  Address       : 123 MAIN ST, ANYTOWN, AR, 720000000
  REAL ID       : Yes (Compliant)
============================================================
```

---

### 3. Python Library API (`cacbarcode.py`)

You can import `cacbarcode` into any Python project, backend service, or kiosk:

#### Automatic Auto-Detection (Recommended)
`decode_barcode(raw_data)` inspects headers, character sets, and payload lengths to instantiate and return the correct barcode object:

```python
from cacbarcode import decode_barcode

raw_payload = "... scanned barcode string from hardware or camera ..."

# Returns: (barcode_instance, type_string)
barcode, barcode_type = decode_barcode(raw_payload)

print(f"Type: {barcode.barcode_type_label} ({barcode_type})")
print(f"ID / EDIPI: {barcode.id_number}")
print(f"Full Name: {barcode.name}")
print(f"Date of Birth: {barcode.dob} (Age: {barcode.age})")
print(f"Expiration: {barcode.expiration_date} (Expired: {barcode.is_expired})")
print(f"State / Branch: {barcode.state or barcode.branch}")

# Pretty-print all fields
print(barcode)
```

#### Direct Class Instantiation
You can also instantiate specific barcode parsers directly:

```python
from cacbarcode import PDF417Barcode, Code39Barcode, DriversLicenseBarcode

# Parse CAC Front PDF417 (88, 89, or 99 characters)
cac_front = PDF417Barcode(raw_cac_pdf417_string)
print(cac_front.edipi)
print(cac_front.first_name, cac_front.last_name)
print(cac_front.branch)    # e.g., "USA", "USAF", "USN"
print(cac_front.category)  # e.g., "Active Duty member"

# Parse CAC Back Code 39 (exact 18 characters)
cac_back = Code39Barcode(raw_code39_string)
print(cac_back.edipi)
print(cac_back.branch)

# Parse AAMVA Driver's License / State ID
dl = DriversLicenseBarcode(raw_aamva_string)
print(dl.id_number)        # DAQ field (License #)
print(dl.name)             # DCS, DAC, DAD fields (Full Name)
print(dl.dob)              # datetime.date object
print(dl.address_street)   # DAG field
print(dl.address_city)     # DAI field
print(dl.state)            # DAJ field
print(dl.address_postal)   # DAK field
print(dl.real_id)          # Boolean
```

---

## Field Reference & Decoded Attributes

All barcode objects inherit from `BaseBarcode` and expose standard attributes:

| Attribute | Type | Description | Supported Formats |
| :--- | :--- | :--- | :--- |
| `id_number` | `str` | Primary ID (DoD EDIPI or Driver's License Number) | All |
| `name` | `str` | Full formatted name | CAC PDF417, AAMVA DL |
| `first_name` | `str` | First name | CAC PDF417, AAMVA DL |
| `middle_name` | `str` | Middle name or middle initial | CAC PDF417, AAMVA DL |
| `last_name` | `str` | Last / family name | CAC PDF417, AAMVA DL |
| `dob` | `datetime.date` | Date of birth | CAC PDF417, AAMVA DL |
| `age` | `int` | Calculated current age in years | CAC PDF417, AAMVA DL |
| `expiration_date` | `datetime.date` | Expiration date | CAC PDF417, AAMVA DL |
| `is_expired` | `bool` | True if card expiration date is before today | CAC PDF417, AAMVA DL |
| `issue_date` | `datetime.date` | Card issue date (when available) | CAC PDF417, AAMVA DL |
| `branch` | `str` | Military branch of service (USA, USN, USAF, etc.) | CAC PDF417, CAC Code 39 |
| `category` | `str` | Personnel category / DL Class | All |
| `rank` | `str` | Military rank code (e.g., `EA00`, `TSGT`) | CAC PDF417 |
| `sex` | `str` | Sex / Gender (`Male`, `Female`, `Not specified`) | AAMVA DL |
| `state` | `str` | State jurisdiction code or `"DoD"` | All |
| `address_street` | `str` | Residential street address | AAMVA DL |
| `address_city` | `str` | City | AAMVA DL |
| `address_postal` | `str` | ZIP / Postal code | AAMVA DL |
| `real_id` | `bool` | True if card indicates REAL ID compliance | AAMVA DL |
| `raw_data` | `str` | Original raw barcode string | All |
| `barcode_type` | `str` | Identifier code (`PDF417`, `Code39`, `AAMVA_DL`, `GENERIC`) | All |
| `barcode_type_label`| `str` | User-friendly label (e.g., `"CAC PDF417"`, `"Driver's License"`) | All |

*Note: For backward compatibility with older versions of `cacbarcode`, legacy property names such as `edipi`, `firstname`, `lastname`, `initial`, `expdate`, `issuedate`, `instanceid`, `pdtname`, `pectdesc`, and `cii` remain fully supported.*

---

## Testing & Code Quality

### Running the Test Suite
The repository includes automated unit tests covering all barcode formats and edge cases:
- Clean and wedge-stripped AAMVA driver's licenses
- DoD CAC PDF417 Version 1 (88-char), Version N (89-char), and Version M (99-char)
- DoD CAC Code 39 (18-char) with Base-32 validation
- Cross-talk prevention (verifying AAMVA strings never falsely decode as Code 39)
- String representation formatting and invalid input handling

Run the tests using Python's built-in `unittest` runner:
```bash
python -m unittest test_cacbarcode.py -v
```

### Running the Linter
The project is configured with [Ruff](https://github.com/astral-sh/ruff) via `pyproject.toml` (rules: `E`, `W`, `F`, `I`, `B`, `UP`, `RUF`):
```bash
python -m ruff check .
```

### Code Style Standard
- **Naming Conventions:** All variables and functions follow strict `snake_case` (with backward compatibility aliases preserved).
- **Allman Block Formatting:** Braces, block definitions, and multiline argument blocks follow readable Allman-style formatting.

---

## Privacy & Security Notice

> [!WARNING]
> Barcode payloads scanned from government and state identification cards contain **Personally Identifiable Information (PII)**, including full names, dates of birth, driver's license numbers, DoD EDIP numbers, and residential addresses.

- Never commit scanned barcode data, logs, or test scans containing real individuals' data to source control.
- This repository includes a preconfigured [`.gitignore`](.gitignore) that automatically excludes `*.csv` files, preventing accidental commits of `scanned_data.csv` or test logs.
- If you build an application using this library, ensure compliant storage and transmission of PII according to applicable federal, state, and organizational data privacy standards.

---

## References

- **DoD ID Bar Code SDK Formats v7.5.0 (Sep 2012):** Department of Defense Defense Manpower Data Center (DMDC). A reference copy is included in this repository as [`DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf`](DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf).
- **AAMVA DL/ID Card Design Standard (Annex D):** American Association of Motor Vehicle Administrators standard for PDF417 two-dimensional barcodes on driver licenses and identification cards.

---

## License

This project is licensed under the terms of the [MIT License](LICENSE). You are free to use, modify, and integrate this software into open-source or commercial applications.
