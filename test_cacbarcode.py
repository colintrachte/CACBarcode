"""
Unit tests for cacbarcode.py
Validates:
- AAMVA Driver's Licenses (both clean delimiters and wedge-stripped)
- DoD CAC PDF417 Version 1 (88 chars), Version N (89 chars), and Version M (99 chars)
- DoD CAC Code 39 (18 chars)
- Generic 1D/2D barcodes
- Prevention of cross-talk (AAMVA DLs falsely decoding as Code 39)
"""

import datetime
import unittest

from cacbarcode import (
    AAMVABarcode,
    Code39Barcode,
    DriversLicenseBarcode,
    PDF417Barcode,
    decode_barcode,
)


class TestCACBarcode(unittest.TestCase):

    def setUp(self):
        # Primary test vectors
        self.aamva_clean = (
            "@\n\x1e\rANSI 636021100001DL00310170DLDAQS99999999\n"
            "DCSSAMPLE\nDACJANE\nDADQ\nDBD01152024\nDBB07041990\n"
            "DBA07042032\nDBC2\nDAU066 IN\nDAYBRO\nDAG123 MAIN ST\n"
            "DAIANYTOWN\nDAJAR\nDAK720000000\nDCFSYNTHETIC0001\n"
            "DCGUSA\nDDAF\r"
        )
        self.aamva_stripped = (
            "@ANSI 636021100001DL00310170DLDAQS99999999DCSSAMPLEDACJANEDADQ"
            "DBD01152024DBB07041990DBA07042032DBC2DAU066 INDAYBRODAG123 MAIN ST"
            "DAIANYTOWNDAJARDAK720000000DCFSYNTHETIC0001DCGUSADDAF"
        )
        self.cac_pdf_vn = (
            "N000000N14PC0MIJOHN                SMITH                     "
            "B4LQAF01TSGT  ME06BD7OBFC8KM"
        )
        self.cac_pdf_v1 = (
            "1000000N96B05NAALEX                EXAMPLE                   "
            "AVM0CD00      GS12BD1GBF607"
        )
        self.cac_pdf_vm = (
            "M1G9R3EK01UK5NCKColin               GTrachte                   "
            "B1JGUS EA00      ZZNSHBD8VBE39TONPAS"
        )
        self.cac_code39_synth = "1000000N14PC0MIAFK"
        self.cac_code39_colin = "1TONPASX1G9R3EKEAH"

    def test_aamva_clean_delimiters(self):
        barcode, barcode_type = decode_barcode(self.aamva_clean)
        self.assertEqual(barcode_type, "AAMVA_DL")
        self.assertEqual(barcode.id_number, "S99999999")
        self.assertEqual(barcode.last_name, "SAMPLE")
        self.assertEqual(barcode.first_name, "JANE")
        self.assertEqual(barcode.middle_name, "Q")
        self.assertEqual(barcode.state, "AR")
        self.assertEqual(barcode.dob, datetime.date(1990, 7, 4))
        self.assertEqual(barcode.expiration_date, datetime.date(2032, 7, 4))
        self.assertEqual(barcode.sex, "Female")
        self.assertTrue(barcode.real_id)

    def test_aamva_wedge_stripped(self):
        barcode, barcode_type = decode_barcode(self.aamva_stripped)
        self.assertEqual(barcode_type, "AAMVA_DL")
        self.assertEqual(barcode.id_number, "S99999999")
        self.assertEqual(barcode.last_name, "SAMPLE")
        self.assertEqual(barcode.first_name, "JANE")
        self.assertEqual(barcode.middle_name, "Q")
        self.assertEqual(barcode.state, "AR")
        self.assertEqual(barcode.dob, datetime.date(1990, 7, 4))
        self.assertEqual(barcode.expiration_date, datetime.date(2032, 7, 4))
        self.assertEqual(barcode.sex, "Female")

    def test_cac_pdf417_version_n(self):
        barcode, barcode_type = decode_barcode(self.cac_pdf_vn)
        self.assertEqual(barcode_type, "PDF417")
        self.assertEqual(barcode.edipi, 1234567890)
        self.assertEqual(barcode.first_name, "JOHN")
        self.assertEqual(barcode.middle_name, "M")
        self.assertEqual(barcode.last_name, "SMITH")
        self.assertEqual(barcode.name, "JOHN M SMITH")
        self.assertEqual(barcode.dob.date(), datetime.date(2000, 1, 1))

    def test_cac_pdf417_version_1(self):
        barcode, barcode_type = decode_barcode(self.cac_pdf_v1)
        self.assertEqual(barcode_type, "PDF417")
        self.assertEqual(barcode.edipi, 9876543210)
        self.assertEqual(barcode.last_name, "EXAMPLE")
        self.assertEqual(barcode.dob.date(), datetime.date(1985, 12, 31))

    def test_cac_pdf417_version_m(self):
        barcode, barcode_type = decode_barcode(self.cac_pdf_vm)
        self.assertEqual(barcode_type, "PDF417")
        self.assertEqual(barcode.edipi, 1620938196)
        self.assertEqual(barcode.name, "Colin G Trachte")
        self.assertEqual(barcode.dob.date(), datetime.date(1991, 5, 22))
        self.assertEqual(barcode.branch, "USA")
        self.assertEqual(barcode.category, "DoD contract employee")
        self.assertEqual(barcode.rank, "EA00")
        self.assertEqual(barcode.issue_date.date(), datetime.date(2024, 2, 9))
        self.assertEqual(barcode.expiration_date.date(), datetime.date(2026, 5, 31))
        self.assertEqual(barcode.card_instance_id, "H")
        self.assertEqual(barcode.pdi, "TONPAS")

    def test_cac_code39(self):
        barcode, barcode_type = decode_barcode(self.cac_code39_synth)
        self.assertEqual(barcode_type, "Code39")
        self.assertEqual(barcode.edipi, 1234567890)

        barcode_colin, barcode_type_colin = decode_barcode(self.cac_code39_colin)
        self.assertEqual(barcode_type_colin, "Code39")
        self.assertEqual(barcode_colin.edipi, 1620938196)
        self.assertEqual(barcode_colin.category, "DoD contract employee")
        self.assertEqual(barcode_colin.branch, "USA")

    def test_generic_barcode(self):
        barcode, barcode_type = decode_barcode("VISITOR-998877")
        self.assertEqual(barcode_type, "GENERIC")
        self.assertEqual(barcode.id_number, "VISITOR-998877")

    def test_no_false_positive_cross_decoding(self):
        # AAMVA DL must NEVER parse as Code 39
        with self.assertRaises(ValueError):
            Code39Barcode(self.aamva_clean)

        with self.assertRaises(ValueError):
            Code39Barcode(self.aamva_stripped)

        # Invalid length for PDF417 must raise ValueError
        with self.assertRaises(ValueError):
            PDF417Barcode(self.cac_code39_synth)

    def test_direct_class_instantiation(self):
        # Backward compatibility with existing code
        barcode_pdf = PDF417Barcode(self.cac_pdf_vm)
        self.assertEqual(barcode_pdf.edipi, 1620938196)
        self.assertEqual(barcode_pdf.firstname, "Colin")
        self.assertEqual(barcode_pdf.lastname, "Trachte")

        barcode_c39 = Code39Barcode(self.cac_code39_synth)
        self.assertEqual(barcode_c39.edipi, 1234567890)

        barcode_dl = AAMVABarcode(self.aamva_clean)
        self.assertEqual(barcode_dl.id_number, "S99999999")
        self.assertEqual(barcode_dl.first_name, "JANE")

    def test_str_formatting(self):
        barcode_pdf = PDF417Barcode(self.cac_pdf_vm)
        str_pdf = str(barcode_pdf)
        self.assertIn("CAC PDF417", str_pdf)
        self.assertIn("1620938196", str_pdf)
        self.assertIn("Colin G Trachte", str_pdf)

        barcode_dl = DriversLicenseBarcode(self.aamva_clean)
        str_dl = str(barcode_dl)
        self.assertIn("Driver's License", str_dl)
        self.assertIn("S99999999", str_dl)
        self.assertIn("JANE", str_dl)

    def test_invalid_data_handling(self):
        with self.assertRaises(ValueError):
            decode_barcode("")
        with self.assertRaises(ValueError):
            decode_barcode("   ")
        with self.assertRaises(ValueError):
            decode_barcode("xyz")  # Too short for anything
        with self.assertRaises(ValueError):
            # Invalid Base-32 in CAC Code 39 (Z is not base 32, EDIPI is at 8:15)
            Code39Barcode("1000000NZ4PC0MIAFK")


if __name__ == "__main__":
    unittest.main()
