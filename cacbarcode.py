__author__ = "John Kusner, Colin Trachte"

import datetime
import re

# Epoch for DoD Julian date calculation (days since 1 Jan 1000)
_epoch_jan_1_1000 = datetime.datetime(1000, 1, 1)
_1_jan_1000 = _epoch_jan_1_1000

# Strict Base-32 character set (0-9, A-V) used in DoD barcodes
_base32_pattern = re.compile(r"^[0-9A-Va-v]+$")


def parse_base_32(raw_str):
    """
    Parse a string as Base-32 (0-9, A-V).
    Raises ValueError if characters outside the Base-32 alphabet are present.
    """
    if not raw_str or not _base32_pattern.match(raw_str):
        raise ValueError(f"Invalid Base-32 string: {raw_str!r}")
    return int(raw_str, 32)


# Backwards compatibility alias
parse_base32 = parse_base_32


class BaseBarcode:
    """
    Base class representing any scanned ID or barcode.
    Provides standard fields and string formatting.
    """

    def __init__(
        self,
        raw_data,
        barcode_type="GENERIC",
        barcode_type_label="Generic",
    ):
        self.raw_data = raw_data
        self.data = raw_data
        self.barcode_type = barcode_type
        self.barcode_type_label = barcode_type_label
        self.barcode_version = ""
        self.id_number = ""
        self.name = ""
        self.first_name = ""
        self.middle_name = ""
        self.last_name = ""
        self.dob = None
        self.age = None
        self.expiration_date = None
        self.is_expired = False
        self.issue_date = None
        self.branch = ""
        self.category = ""
        self.rank = ""
        self.sex = ""
        self.state = ""
        self.details = {}
        self.scan_datetime = datetime.datetime.now()

    def __repr__(self):
        return (
            f"<{self.barcode_type_label} ID={self.id_number!r} "
            f"Name={self.name!r} Exp={self.expiration_date}>"
        )

    def __str__(self):
        summary_lines = [f"{self.barcode_type_label}:"]
        if self.id_number:
            summary_lines.append(f"  ID: {self.id_number}")
        if self.name:
            summary_lines.append(f"  Name: {self.name}")
        if self.dob:
            dob_str = (
                self.dob.strftime("%Y-%m-%d")
                if hasattr(self.dob, "strftime")
                else str(self.dob)
            )
            age_str = f" (Age: {self.age})" if self.age is not None else ""
            summary_lines.append(f"  DOB: {dob_str}{age_str}")
        if self.expiration_date:
            exp_str = (
                self.expiration_date.strftime("%Y-%m-%d")
                if hasattr(self.expiration_date, "strftime")
                else str(self.expiration_date)
            )
            status_tag = " [EXPIRED]" if self.is_expired else " [VALID]"
            summary_lines.append(f"  Expires: {exp_str}{status_tag}")
        if self.state:
            summary_lines.append(f"  State: {self.state}")
        if self.branch:
            summary_lines.append(f"  Branch: {self.branch}")
        if self.rank:
            summary_lines.append(f"  Rank: {self.rank}")
        if self.category:
            summary_lines.append(f"  Category: {self.category}")
        return "\n".join(summary_lines)


class CACBarcode(BaseBarcode):
    """
    Generic military CAC barcode class providing DoD decoding tables and helpers.
    http://www.cac.mil/docs/DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf
    """

    branch_mapping = {
        "A": "USA",
        "C": "USCG",
        "D": "DOD",
        "F": "USAF",
        "H": "USPHS",
        "M": "USMC",
        "N": "USN",
        "O": "NOAA",
        "1": "Foreign Army",
        "2": "Foreign Navy",
        "3": "Foreign Marine Corps",
        "4": "Foreign Air Force",
        "X": "Other",
    }

    category_mapping = {
        "A": "Active Duty member",
        "B": "Presidential Appointee",
        "C": "DoD civil service employee",
        "D": "100% disabled American veteran",
        "E": "DoD contract employee",
        "F": "Former member",
        "N": "National Guard member",
        "G": "National Guard member",
        "H": "Medal of Honor recipient",
        "I": "Non-DoD Civil Service Employee",
        "J": "Academy student",
        "K": "non-appropriated fund (NAF) DoD employee",
        "L": "Lighthouse service",
        "M": "Non-Government agency personnel",
        "O": "Non-DoD contract employee",
        "Q": "Reserve retiree not yet eligible for retired pay",
        "R": "Retired Uniformed Service member eligible for retired pay",
        "V": "Reserve member",
        "S": "Reserve",
        "T": "Foreign military member",
        "U": "Foreign national employee",
        "W": "DoD Beneficiary",
        "Y": "Retired DoD Civil Service Employees",
    }

    def __init__(
        self,
        raw_data,
        barcode_type="CAC_GENERIC",
        barcode_type_label="CAC Barcode",
    ):
        super().__init__(raw_data, barcode_type, barcode_type_label)
        self.state = "DoD"

    def read(self, data, start, count):
        return data[start : start + count]

    def read_num(self, data, start, count, base=32):
        chunk = data[start : start + count]
        if base == 32:
            return parse_base_32(chunk)
        return int(chunk, base)

    # Backwards compatibility alias
    readnum = read_num

    def read_date(self, data, start):
        days = self.read_num(data, start, 4, base=32)
        return _epoch_jan_1_1000 + datetime.timedelta(days=days)

    # Backwards compatibility alias
    readdate = read_date

    def validate_data(self, data):
        if not isinstance(data, str) or not data.strip():
            raise ValueError("Data must be a non-empty string")

    def _get_branch(self, code):
        return self.branch_mapping.get(code, "N/A")

    # Backwards compatibility alias
    _getbranch = _get_branch

    def _get_category(self, code):
        return self.category_mapping.get(code, "N/A")

    # Backwards compatibility alias
    _getcategory = _get_category

    def _get_pdt(self, code):
        pdt_mapping = {
            "S": "Social Security Number (SSN)",
            "N": "9 digits, not valid SSN",
            "P": "Special code before SSNs",
            "D": "Temporary Identifier Number (TIN)",
            "F": "Foreign Identifier Number (FIN)",
            "T": "Test (858 series)",
            "I": "Individual Taxpayer Identification Number",
        }
        return pdt_mapping.get(code, "N/A")

    _getpdt = _get_pdt

    def _get_pect(self, code):
        pect_mapping = {
            "01": "On Active Duty",
            "02": "Mobilization",
            "06": "Separated from Selected Reserve",
            "13": "Granted retired pay",
            "20": "Transitional assistance (TA-30)",
        }
        return pect_mapping.get(code, "")

    _getpect = _get_pect

    @staticmethod
    def calculate_age(dob):
        if not dob:
            return None
        today = datetime.date.today()
        birth_date = dob.date() if isinstance(dob, datetime.datetime) else dob
        age_years = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
        return age_years if 0 <= age_years <= 130 else None


class PDF417Barcode(CACBarcode):
    """
    Reads a PDF417 2D Barcode on the front of CACs.
    Supports:
      - Version 1 (88 chars): DoD SDK Table 3 (Sep 2012)
      - Version N (89 chars): DoD SDK Table 4 (Sep 2012, includes trailing Middle Initial)
      - Version M (99 chars): Modern field cards in active circulation
    """

    def __init__(self, data):
        self.validate_data(data)
        data = data.strip()
        super().__init__(
            data,
            barcode_type="CAC_PDF417",
            barcode_type_label="CAC PDF417",
        )

        char_length = len(data)
        if char_length not in (88, 89, 99):
            raise ValueError(
                f"Invalid CAC PDF417 length: {char_length} (expected 88, 89, or 99 characters)"
            )

        self.barcode_version = data[0]

        if char_length == 99 or self.barcode_version == "M":
            self._parse_version_m(data)
        elif char_length == 89 or self.barcode_version == "N":
            self._parse_version_n(data)
        elif char_length == 88 or self.barcode_version == "1":
            self._parse_version_1(data)
        else:
            raise ValueError(
                f"Unrecognized CAC PDF417 version code: {self.barcode_version!r} (length: {char_length})"
            )

        self.id_number = str(self.edipi)
        self.age = self.calculate_age(self.dob)
        if self.expiration_date:
            today_date = datetime.datetime.now()
            self.is_expired = self.expiration_date < today_date

    def _parse_version_m(self, data):
        """Parse modern 99-character field CAC barcode."""
        self.indices = {
            "barcode_version": (0, 1),
            "edipi": (1, 7),
            "code": (8, 8),
            "first_name": (16, 20),
            "middle_initial": (36, 1),
            "last_name": (37, 26),
            "dob": (63, 4),
            "rank": (69, 6),
            "category": (70, 1),
            "branch": (71, 1),
            "pay_plan_code": (75, 2),
            "pay_grade_code": (77, 2),
            "issue_date": (79, 4),
            "expiration_date": (83, 4),
            "card_instance_id": (87, 1),
            "pdi": (93, 6),
        }
        self.edipi = self.read_num(data, *self.indices["edipi"])
        self.first_name = self.read(data, *self.indices["first_name"]).strip()
        self.middle_name = self.read(data, *self.indices["middle_initial"]).strip()
        self.last_name = self.read(data, *self.indices["last_name"]).strip()
        self.middle_initial = self.middle_name
        self.name = " ".join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )

        self.dob = self.read_date(data, self.indices["dob"][0])
        self.rank = self.read(data, *self.indices["rank"]).strip()
        self.category = self._get_category(self.read(data, *self.indices["category"]))
        self.branch = self._get_branch(self.read(data, *self.indices["branch"]))
        self.pay_plan_code = self.read(data, *self.indices["pay_plan_code"]).strip()
        self.pay_grade_code = self.read(data, *self.indices["pay_grade_code"]).strip()

        try:
            self.expiration_date = self.read_date(
                data, self.indices["expiration_date"][0]
            )
        except Exception:
            self.expiration_date = None

        try:
            self.issue_date = self.read_date(data, self.indices["issue_date"][0])
        except Exception:
            self.issue_date = None

        self.card_instance_id = self.read(data, *self.indices["card_instance_id"])
        self.pdi = self.read(data, *self.indices["pdi"])

        # Backward compatibility aliases
        self.firstname = self.first_name
        self.lastname = self.last_name
        self.initial = self.middle_initial
        self.middleinitial = self.middle_initial
        self.expdate = self.expiration_date
        self.issuedate = self.issue_date
        self.instanceid = self.card_instance_id
        self.ppc = self.pay_plan_code
        self.ppgc = self.pay_grade_code
        self.pcc = self.category

    def _parse_version_1(self, data):
        """Parse DoD SDK Table 3 (88 characters, Version 1)."""
        self.indices = {
            "barcode_version": (0, 1),
            "pdi": (1, 6),
            "pdt": (7, 1),
            "edipi": (8, 7),
            "first_name": (15, 20),
            "last_name": (35, 26),
            "dob": (61, 4),
            "category": (65, 1),
            "branch": (66, 1),
            "pect": (67, 2),
            "rank": (69, 6),
            "pay_plan_code": (75, 2),
            "pay_grade_code": (77, 2),
            "issue_date": (79, 4),
            "expiration_date": (83, 4),
            "card_instance_id": (87, 1),
        }
        self.pdi = self.read(data, *self.indices["pdi"])
        self.pdt = self.read(data, *self.indices["pdt"])
        self.pdt_name = self._get_pdt(self.pdt)
        self.edipi = self.read_num(data, *self.indices["edipi"])
        self.first_name = self.read(data, *self.indices["first_name"]).strip()
        self.middle_name = ""
        self.middle_initial = ""
        self.last_name = self.read(data, *self.indices["last_name"]).strip()
        self.name = f"{self.first_name} {self.last_name}".strip()

        self.dob = self.read_date(data, self.indices["dob"][0])
        category_code = self.read(data, *self.indices["category"])
        self.category = self._get_category(category_code)
        branch_code = self.read(data, *self.indices["branch"])
        self.branch = self._get_branch(branch_code)
        self.pect = self.read(data, *self.indices["pect"])
        self.pect_desc = self._get_pect(self.pect)
        self.rank = self.read(data, *self.indices["rank"]).strip()
        self.pay_plan_code = self.read(data, *self.indices["pay_plan_code"]).strip()
        self.pay_grade_code = self.read(data, *self.indices["pay_grade_code"]).strip()
        self.expiration_date = self.read_date(data, self.indices["expiration_date"][0])
        self.issue_date = self.read_date(data, self.indices["issue_date"][0])
        self.card_instance_id = self.read(data, *self.indices["card_instance_id"])

        # Backward compatibility aliases
        self.firstname = self.first_name
        self.lastname = self.last_name
        self.initial = ""
        self.middleinitial = ""
        self.expdate = self.expiration_date
        self.issuedate = self.issue_date
        self.instanceid = self.card_instance_id
        self.pdtname = self.pdt_name
        self.pectdesc = self.pect_desc
        self.ppc = self.pay_plan_code
        self.ppgc = self.pay_grade_code
        self.pcc = self.category

    def _parse_version_n(self, data):
        """Parse DoD SDK Table 4 (89 characters, Version N with trailing Middle Initial)."""
        self._parse_version_1(data[:88])
        self.middle_initial = data[88:89].strip()
        self.middle_name = self.middle_initial
        self.name = " ".join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )
        self.initial = self.middle_initial
        self.middleinitial = self.middle_initial


class Code39Barcode(CACBarcode):
    """
    Reads a Code 39 Barcode on the back of CACs.
    Layout per DoD SDK Table 2 (18 characters):
      - 0: Version Code (1 char)
      - 1-6: Person Designator Identifier (PDI, 6 chars)
      - 7: Person Designator Type Code (1 char)
      - 8-14: DoD EDIPI (7 chars, Base-32)
      - 15: Personnel Category Code (1 char)
      - 16: Branch / Service Code (1 char)
      - 17: Card Instance Identifier (1 char)
    """

    def __init__(self, data):
        self.validate_data(data)
        data = data.strip()
        super().__init__(
            data,
            barcode_type="CAC_CODE39",
            barcode_type_label="CAC Code 39",
        )

        if len(data) != 18:
            raise ValueError(
                f"Invalid CAC Code 39 length: {len(data)} (expected exactly 18 characters)"
            )

        if not re.match(r"^[0-9A-Za-z]+$", data):
            raise ValueError(f"Invalid characters in CAC Code 39 barcode: {data!r}")

        self.indices = {
            "barcode_version": (0, 1),
            "pdi": (1, 6),
            "pdt": (7, 1),
            "edipi": (8, 7),
            "category": (15, 1),
            "branch": (16, 1),
            "card_instance_id": (17, 1),
        }
        self.barcode_version = self.read(data, *self.indices["barcode_version"])
        self.pdi = self.read(data, *self.indices["pdi"])
        self.pdt = self.read(data, *self.indices["pdt"])
        self.pdt_name = self._get_pdt(self.pdt)
        self.edipi = self.read_num(data, *self.indices["edipi"])
        self.id_number = str(self.edipi)

        category_code = self.read(data, *self.indices["category"])
        branch_code = self.read(data, *self.indices["branch"])
        self.category = self._get_category(category_code)
        self.branch = self._get_branch(branch_code)
        self.card_instance_id = self.read(data, *self.indices["card_instance_id"])
        self.cii = self.card_instance_id
        self.name = f"DoD ID {self.edipi}"


# Element tags recognized in AAMVA Driver's Licenses
aamva_tags = [
    "DAQ",
    "DCS",
    "DAC",
    "DAD",
    "DCU",
    "DBB",
    "DBA",
    "DBD",
    "DBC",
    "DAU",
    "DAY",
    "DAG",
    "DAH",
    "DAI",
    "DAJ",
    "DAK",
    "DCG",
    "DCF",
    "DCK",
    "DDA",
    "DDE",
    "DDF",
    "DDG",
    "DDB",
    "DCJ",
    "DCI",
    "DCH",
    "DCD",
    "DCB",
    "DCA",
    "DBH",
    "DBG",
    "DBE",
    "DAN",
    "DAM",
    "DAL",
    "DAO",
    "DAP",
    "DAR",
    "DAS",
    "DAT",
    "DAW",
    "DAX",
    "DAZ",
    "DDK",
    "DCT",
    "DAA",
]
AAMVA_TAGS = aamva_tags
_aamva_tag_pattern = re.compile("(" + "|".join(aamva_tags) + ")")


def parse_aamva_date(raw_date_str):
    """
    Parse an AAMVA date string into a datetime.date object.
    Supports ISO (YYYY-MM-DD), CCYYMMDD, and MMDDCCYY formats.
    """
    if not raw_date_str:
        return None
    clean_date = raw_date_str.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", clean_date):
        try:
            return datetime.date.fromisoformat(clean_date)
        except ValueError:
            return None

    digits = re.sub(r"\D", "", clean_date)
    if len(digits) != 8:
        return None

    first4 = int(digits[:4])
    if 1900 <= first4 <= 2100:
        year = first4
        month = int(digits[4:6])
        day = int(digits[6:8])
    else:
        month = int(digits[:2])
        day = int(digits[2:4])
        year = int(digits[4:8])

    try:
        return datetime.date(year, month, day)
    except (ValueError, OverflowError):
        return None


class DriversLicenseBarcode(BaseBarcode):
    """
    Reads an AAMVA-compliant PDF417 2D Barcode from US & Canadian Driver's Licenses and State IDs.
    Supports both delimiter-intact and keyboard-wedge stripped payloads.
    """

    def __init__(self, data):
        if not isinstance(data, str) or not data.strip():
            raise ValueError("Data must be a non-empty string")
        raw = data.strip()
        super().__init__(
            raw,
            barcode_type="AAMVA_DL",
            barcode_type_label="Driver's License",
        )

        fields = self._tokenize_and_collect(raw)
        if (
            not fields.get("DAQ")
            and not fields.get("DCS")
            and not fields.get("DAC")
            and not fields.get("DAA")
        ):
            raise ValueError(
                "No AAMVA identity elements (DAQ/DCS/DAC/DAA) found in barcode"
            )

        self.fields = fields
        self.id_number = fields.get("DAQ", "")

        # Name handling (AAMVA v1 used DAA 'LAST,FIRST,MIDDLE'; v2+ uses DCS, DAC, DAD; v2-3 used DCT)
        self.first_name = fields.get("DAC", "")
        self.middle_name = fields.get("DAD", "")
        self.last_name = fields.get("DCS", "")

        if not self.first_name and fields.get("DCT"):
            name_parts = re.split(r"[ ,]+", fields["DCT"].strip())
            if name_parts:
                self.first_name = name_parts[0]
                if not self.middle_name and len(name_parts) > 1:
                    self.middle_name = " ".join(name_parts[1:])

        if not self.last_name and fields.get("DAA"):
            name_parts = [p.strip() for p in fields["DAA"].split(",")]
            if len(name_parts) >= 1:
                self.last_name = name_parts[0]
            if not self.first_name and len(name_parts) >= 2:
                self.first_name = name_parts[1]
            if not self.middle_name and len(name_parts) >= 3:
                self.middle_name = name_parts[2]

        self.name = " ".join(
            filter(None, [self.first_name, self.middle_name, self.last_name])
        )
        self.firstname = self.first_name
        self.lastname = self.last_name
        self.initial = self.middle_name[:1] if self.middle_name else ""

        # Dates
        self.dob = parse_aamva_date(fields.get("DBB", ""))
        self.expiration_date = parse_aamva_date(fields.get("DBA", ""))
        self.issue_date = parse_aamva_date(fields.get("DBD", ""))

        if self.dob:
            today_date = datetime.date.today()
            self.age = (
                today_date.year
                - self.dob.year
                - (
                    (today_date.month, today_date.day)
                    < (self.dob.month, self.dob.day)
                )
            )

        if self.expiration_date:
            self.is_expired = self.expiration_date < datetime.date.today()

        # Sex / Gender
        sex_raw = fields.get("DBC", "").upper()
        if sex_raw in ("1", "M"):
            self.sex = "Male"
        elif sex_raw in ("2", "F"):
            self.sex = "Female"
        elif sex_raw == "9":
            self.sex = "Not specified"
        else:
            self.sex = sex_raw

        # Location / Address
        self.state = fields.get("DAJ", "")
        self.address_street = fields.get("DAG", "")
        self.address_city = fields.get("DAI", "")
        self.address_postal = fields.get("DAK", "")

        # License Class / Endorsements / Restrictions
        self.license_class = fields.get("DCA", "")
        self.restrictions = fields.get("DCB", "")
        self.endorsements = fields.get("DCD", "")
        self.category = self.license_class if self.license_class else "Driver License"
        self.real_id = fields.get("DDA") == "F"

    def _tokenize_and_collect(self, raw):
        """Tokenize either line-delimited or stripped AAMVA payloads."""
        chunks = re.split(r"[\r\n\x1e\x1c]+", raw)
        valid_chunks = [c for c in chunks if c.strip()]

        fields = {}
        if len(valid_chunks) > 3:
            for chunk in valid_chunks:
                clean_chunk = chunk.strip()
                tag_match = _aamva_tag_pattern.search(clean_chunk)
                if tag_match:
                    tag = tag_match.group(1)
                    val = clean_chunk[tag_match.end() :].strip()
                    if tag not in fields:
                        fields[tag] = val
            return fields

        matches = list(_aamva_tag_pattern.finditer(raw))
        for idx, match in enumerate(matches):
            tag = match.group(1)
            start_pos = match.end()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
            val = raw[start_pos:end_pos].strip()
            if idx + 1 == len(matches):
                val = re.split(r"[\r\n\x1e\x1c]|Z[A-Z0-9]{2}", val)[0].strip()
            if val or tag not in fields:
                fields[tag] = val
        return fields


# Backward-compatibility alias
AAMVABarcode = DriversLicenseBarcode


class GenericBarcode(BaseBarcode):
    """Fallback class for standard linear or 2D barcodes."""

    def __init__(self, data):
        clean_code = data.strip().replace("\r", "").replace("\n", "")
        if not clean_code or len(clean_code) < 4:
            raise ValueError("Generic barcode data must be at least 4 characters")
        super().__init__(
            clean_code,
            barcode_type="GENERIC",
            barcode_type_label="Generic Barcode",
        )
        self.id_number = clean_code
        self.name = f"Card #{clean_code}"
        self.category = "Visitor / Pass"


def decode_barcode(raw_data):
    """
    Universal Barcode Dispatcher.
    Inspects structure, headers, length, and character set to accurately
    instantiate and return the appropriate barcode object.

    Returns:
        (barcode_object, type_string)
    """
    if not isinstance(raw_data, str) or not raw_data.strip():
        raise ValueError("Barcode data must be a non-empty string")

    clean_data = raw_data.strip()

    # 1. AAMVA Driver's License check
    if (
        "@" in clean_data
        or "ANSI " in clean_data
        or (
            "DAQ" in clean_data
            and (
                "DCS" in clean_data
                or "DAC" in clean_data
                or "DBB" in clean_data
            )
        )
        or ("DL" in clean_data and len(clean_data) > 60)
    ):
        try:
            dl_obj = DriversLicenseBarcode(clean_data)
            return dl_obj, "AAMVA_DL"
        except Exception:
            pass

    # 2. CAC PDF417 check
    if len(clean_data) in (88, 89, 99) and "@" not in clean_data:
        try:
            cac_obj = PDF417Barcode(clean_data)
            return cac_obj, "PDF417"
        except Exception:
            pass

    # 3. CAC Code 39 check
    if len(clean_data) == 18 and re.match(r"^[0-9A-Za-z]+$", clean_data):
        try:
            code39_obj = Code39Barcode(clean_data)
            return code39_obj, "Code39"
        except Exception:
            pass

    # 4. Fallback AAMVA check
    if "DAQ" in clean_data or "DL" in clean_data:
        try:
            dl_obj = DriversLicenseBarcode(clean_data)
            return dl_obj, "AAMVA_DL"
        except Exception:
            pass

    # 5. Generic barcode fallback
    try:
        gen_obj = GenericBarcode(clean_data)
        return gen_obj, "GENERIC"
    except Exception:
        pass

    raise ValueError("Failed to recognize or parse barcode data")
