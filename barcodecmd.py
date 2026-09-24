#!/usr/bin/env python3
"""
Command-line interface for the CAC and Driver's License Barcode Scanner.
Auto-detects and decodes:
  - DoD CAC PDF417 (v1, vN, vM)
  - DoD CAC Code 39
  - AAMVA Driver's Licenses / State IDs
  - Generic 1D / 2D barcodes
"""

import sys

from cacbarcode import decode_barcode


def format_barcode_summary(barcode_obj, barcode_type):
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append(
        f"  Barcode Type : {barcode_obj.barcode_type_label} [{barcode_type}]"
    )
    summary_lines.append("-" * 60)

    if barcode_obj.id_number:
        id_label = (
            "EDIPI"
            if barcode_type in ("PDF417", "Code39")
            else "ID / License #"
        )
        summary_lines.append(f"  {id_label:<14}: {barcode_obj.id_number}")

    if barcode_obj.name:
        summary_lines.append(f"  {'Name':<14}: {barcode_obj.name}")

    if barcode_obj.dob:
        dob_str = (
            barcode_obj.dob.strftime("%Y-%m-%d")
            if hasattr(barcode_obj.dob, "strftime")
            else str(barcode_obj.dob)
        )
        age_str = (
            f" (Age: {barcode_obj.age})" if barcode_obj.age is not None else ""
        )
        summary_lines.append(f"  {'Date of Birth':<14}: {dob_str}{age_str}")

    if barcode_obj.expiration_date:
        exp_str = (
            barcode_obj.expiration_date.strftime("%Y-%m-%d")
            if hasattr(barcode_obj.expiration_date, "strftime")
            else str(barcode_obj.expiration_date)
        )
        status_tag = " [EXPIRED]" if barcode_obj.is_expired else " [ACTIVE]"
        summary_lines.append(f"  {'Expiration':<14}: {exp_str}{status_tag}")

    if barcode_obj.state:
        summary_lines.append(f"  {'State':<14}: {barcode_obj.state}")

    if barcode_obj.branch:
        summary_lines.append(f"  {'Branch':<14}: {barcode_obj.branch}")

    if barcode_obj.rank:
        summary_lines.append(f"  {'Rank':<14}: {barcode_obj.rank}")

    if barcode_obj.category:
        summary_lines.append(f"  {'Category':<14}: {barcode_obj.category}")

    if barcode_obj.sex:
        summary_lines.append(f"  {'Sex':<14}: {barcode_obj.sex}")

    if hasattr(barcode_obj, "address_street") and (
        barcode_obj.address_street or barcode_obj.address_city
    ):
        address_parts = filter(
            None,
            [
                getattr(barcode_obj, "address_street", ""),
                getattr(barcode_obj, "address_city", ""),
                getattr(barcode_obj, "state", ""),
                getattr(barcode_obj, "address_postal", ""),
            ],
        )
        summary_lines.append(f"  {'Address':<14}: {', '.join(address_parts)}")

    if getattr(barcode_obj, "real_id", False):
        summary_lines.append(f"  {'REAL ID':<14}: Yes (Compliant)")

    summary_lines.append("=" * 60)
    return "\n".join(summary_lines)


def main():
    if len(sys.argv) > 1:
        raw_barcode_data = " ".join(sys.argv[1:]).strip()
    elif not sys.stdin.isatty():
        raw_barcode_data = sys.stdin.read().strip()
    else:
        print("CAC & Driver's License Barcode Reader")
        print("-" * 40)
        try:
            raw_barcode_data = input(
                "Scan or enter barcode data string: "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not raw_barcode_data:
        print("Error: No barcode data provided.", file=sys.stderr)
        sys.exit(1)

    try:
        barcode_obj, barcode_type = decode_barcode(raw_barcode_data)
    except Exception as parse_error:
        print(
            f"Error: Failed to parse barcode data ({parse_error})",
            file=sys.stderr,
        )
        sys.exit(1)

    print(format_barcode_summary(barcode_obj, barcode_type))


if __name__ == "__main__":
    main()
