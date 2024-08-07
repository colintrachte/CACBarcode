# CACBarcode
A simple one class library under the MIT license designed to help python programmers who need to parse CAC barcodes (PDF417 and Code39) into Python objects with all data parsed. Updated to work with cards that are in circulation as of 2024. A full blown tkinter GUI with .csv export is now included.

The original document for the barcode structure was located at http://www.cac.mil/docs/DoD-ID-Bar-Code_SDK-Formats_v7-5-0_Sep2012.pdf
Since the link appears to be broken, I have uploaded a copy of the pdf to this repo.

# Usage
```python
from cacbarcode import PDF417Barcode, Code39Barcode

# To parse a barcode, simply do
barcode = PDF417Barcode("data here")

# or the other kind
barcode = Code39Barcode("data here")

# If you want an EDIPI, but aren't sure which barcode is being scanned, do this:
edipi = None
barcode_data = "BARCODE DATA HERE"

try:
  barcode = PDF417Barcode(barcode_data)
  # if this was the wrong type, an exception will be thrown
  # otherwise, this was the correct type, so set the edipi
  edipi = barcode.edipi
except:
  # Try the other barcode type
  try:
    barcode = Code39Barcode(barcode_data)
    
    edipi = barcode.edipi
  except:
    # Neither barcode was correct
    print("Neither barcode worked!")
    
print("EDIPI =", edipi)
```

The easiest way to use this library is with a barcode scanner connected to a computer.
The barcode scanner emulates keyboard input, so doing
```python
barcode = PDF417Barcode(input(">"))
```
will be a very easy way to parse barcodes.

To easily see the contents of the barcode, simply print the object
```python
print(barcode)
```
