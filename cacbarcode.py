__author__ = 'John Kusner, Colin Trachte'
import datetime

_1_jan_1000 = datetime.datetime(1000, 1, 1)

class CACBarcode:
    """
    Generic barcode class, constructing this will do nothing
    """
    def __init__(self):
        pass
    
    def read(self, data, start, count):
        # Read `count` characters from `data` starting at `start` and return the read part
        return data[start:start + count]
    
    def readnum(self, data, start, count, base=32):
        print(data[start:start + count])
        # Read `count` characters from `data` starting at `start`, convert to integer with the given `base`
        return int(data[start:start + count], base)

    def readdate(self, data, start):
        # Read 4 characters from `data` starting at `start`, interpret them as the number of days since 1 Jan 1000
        days = self.readnum(data, start, 4)
        date = _1_jan_1000 + datetime.timedelta(days=days)
        return date
    
    def validate_data(self, data):
        if not isinstance(data, str) or not data:
            raise ValueError("Data must be a non-empty string")

    """
    functions below this point, starting with underscore _, are called by constructor, don't call these methods directly
    http://www.cac.mil/docs/DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf, page 50-53
    """
    branch_mapping = {
        "A": "USA", "C": "USCG", "D": "DOD", "F": "USAF",
        "H": "USPHS", "M": "USMC", "N": "USN", "O": "NOAA",
        "1": "Foreign Army", "2": "Foreign Navy", "3": "Foreign Marine Corps",
        "4": "Foreign Air Force", "X": "Other"
    }
    
    #SSN and pdt was dropped from the contents of newer barcodes for obvious reasons.
    """
    pdt_mapping = {
        "S": "Social Security Number (SSN)", "N": "9 digits, not valid SSN",
        "P": "Special code before SSNs", "D": "Temporary Identifier Number (TIN)",
        "F": "Foreign Identifier Number (FIN)", "T": "Test (858 series)",
        "I": "Individual Taxpayer Identification Number"
    }
    """
    category_mapping = {
        "A": "Active Duty member", "B": "Presidential Appointee", "C": "DoD civil service employee",
        "D": "100% disabled American veteran", "E": "DoD contract employee", "F": "Former member",
        "N": "National Guard member", "G": "National Guard member", "H": "Medal of Honor recipient",
        "I": "Non-DoD Civil Service Employee", "J": "Academy student", "K": "non-appropriated fund (NAF) DoD employee",
        "L": "Lighthouse service", "M": "Non-Government agency personnel", "O": "Non-DoD contract employee",
        "Q": "Reserve retiree not yet eligible for retired pay", "R": "Retired Uniformed Service member eligible for retired pay",
        "V": "Reserve member", "S": "Reserve", "T": "Foreign military member", "U": "Foreign national employee",
        "W": "DoD Beneficiary", "Y": "Retired DoD Civil Service Employees"
    }

    def _getbranch(self, code):
        return self.branch_mapping.get(code, "N/A")
    """
    def _getpdt(self, code):
        return self.pdt_mapping.get(code, "N/A")
    """
    def _getcategory(self, code):
        return self.category_mapping.get(code, "N/A")

class PDF417Barcode(CACBarcode):
    """
    Reads a PDF417 2D Barcode on the front of CACs
    See http://www.cac.mil/docs/DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf, pp. 13-14
    """

    def __init__(self, data):
        self.validate_data(data)
        self.data = data
        self.indices = {
            'barcode_version': (0, 1),
            'pdi': (94, 6),
            'edipi': (1, 7),
            'firstname': (16, 20),
            'initial': (36, 1),
            'lastname': (37, 25),
            'dob': (63, 4),
            'pcc': (65, 1),
            'category': (70, 1),
            'branch': (71, 1),
            'rank': (69, 6),
            'ppc': (75, 2),
            'ppgc': (77, 2)
        }
        self.barcode_version = self.read(self.data, *self.indices['barcode_version'])
        self.pdi = self.read(self.data, *self.indices['pdi'])
        self.edipi = self.readnum(self.data, *self.indices['edipi'])
        self.firstname = self.read(self.data, *self.indices['firstname']).strip()
        self.initial = self.read(self.data, *self.indices['initial']).strip()
        self.lastname = self.read(self.data, *self.indices['lastname']).strip()
        self.name = f"{self.firstname} {self.initial} {self.lastname}"
        self.dob = self.readdate(self.data, self.indices['dob'][0])
        self.pcc = self.read(self.data, *self.indices['pcc'])
        self.category = self._getcategory(self.read(self.data, *self.indices['category']))
        self.branch = self._getbranch(self.read(self.data, *self.indices['branch']))
        self.rank = self.read(self.data, *self.indices['rank']).strip()
        self.ppc = self.read(self.data, *self.indices['ppc'])
        self.ppgc = self.read(self.data, *self.indices['ppgc'])

class Code39Barcode(CACBarcode):
    """
    Reads a Code 39 Barcode on the back of CACs
    See http://www.cac.mil/docs/DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf, pp. 15-18
    """
    def __init__(self, data):
        self.data = data
        self.indices = {
            'barcode_version': (0, 1),
            'pdi':(1,6),
            'edipi': (8, 7),
        }
        self.edipi = self.readnum(self.data, *self.indices['edipi'])
