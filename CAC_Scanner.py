import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, simpledialog
import csv
from datetime import datetime
from cacbarcode import PDF417Barcode, Code39Barcode

class BarcodeScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Barcode Scanner App")
        self.root.state('zoomed')# Maximize the window at startup

        self.colors = {
            'background': '#f5f5f5',
            'text': '#000000',
            'status': '#ff9900',
            'error': '#ff3333',
            'warning': '#ffcc00',
            'success': '#33cc33'
        }

        self.logo = self.load_logo("logo.png")
        self.previous_barcode_edipi = None
        self.previous_barcode_type = None
        self.scanned_edipi = {}
        self.create_widgets()

    def load_logo(self, logo_path):
        try:
            logo = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(False, logo)
            return logo
        except Exception as e:
            print(f"Warning: {e} - Logo not loaded. Continuing without logo.")
            return None

    def create_widgets(self):
        self.setup_input_frame()
        self.setup_status_bar()
        self.setup_result_frame()
        self.apply_styles()

    def setup_input_frame(self):
        self.input_frame = ttk.Frame(self.root, padding="10", style="Input.TFrame")
        self.input_frame.pack(pady=10)

        self.input_label = ttk.Label(self.input_frame, text="Scan Barcode:", style="Label.TLabel")
        self.input_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.input_entry = ttk.Entry(self.input_frame, width=50, style="Input.TEntry")
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_entry.bind("<Return>", self.scan_barcode)

        self.filter_label = ttk.Label(self.input_frame, text="Filter:", style="Label.TLabel")
        self.filter_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.filter_entry = ttk.Entry(self.input_frame, width=20, style="Input.TEntry")
        self.filter_entry.grid(row=0, column=3, padx=5, pady=5)
        self.filter_entry.bind("<KeyRelease>", self.apply_filter)

        self.export_button = ttk.Button(self.input_frame, text="Export Data", command=self.export_csv, style="Button.TButton")
        self.export_button.grid(row=0, column=4, padx=5, pady=5)

    def setup_status_bar(self):
        self.status_bar = tk.Label(self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("TkDefaultFont", 12, "bold"), background=self.colors['status'])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_result_frame(self):
        self.result_frame = ttk.Frame(self.root, padding="10", style="Result.TFrame")
        self.result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.treeview = ttk.Treeview(self.result_frame, columns=("data", "edipi", "name", "branch", "category", "rank", "dob", "pcc", "ppc", "ppgc", "datetime"))
        self.treeview.heading("#0", text="Type")
        for col in self.treeview["columns"]:
            self.treeview.heading(col, text=col.capitalize())

        self.treeview.bind("<Double-1>", self.on_treeview_double_click)

        self.treeview.pack(fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.treeview.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.treeview.configure(yscrollcommand=self.scrollbar.set)

    def apply_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background=self.colors['background'])
        style.configure("Label.TLabel", background=self.colors['background'], foreground=self.colors['text'])
        style.configure("Input.TEntry", foreground=self.colors['text'])
        style.configure("Button.TButton", background=self.colors['success'])
        style.configure("Result.TFrame", background=self.colors['background'])

    def parse_barcode(self, barcode_data):
        for barcode_class, barcode_type in [(PDF417Barcode, "PDF417"), (Code39Barcode, "Code39")]:
            try:
                return barcode_class(barcode_data), barcode_type
            except Exception:
                continue
        self.show_status("Error: Failed to parse barcode data.", message_type='error')
        return None, None

    def scan_barcode(self, event=None):
        barcode_data = self.input_entry.get().strip()

        if not barcode_data:
            return

        barcode, barcode_type = self.parse_barcode(barcode_data)
        if not barcode:
            return

        barcode_edipi = barcode.edipi if hasattr(barcode, 'edipi') else ''
        if barcode_edipi in self.scanned_edipi:
            if self.previous_barcode_type == "Code39" and barcode_type == "PDF417":
                self.update_existing_entry(barcode)
            else:
                self.show_status("Error: Duplicate EDIPI detected.", message_type='error')
                return
        else:
            self.scanned_edipi[barcode_edipi] = barcode_type

        self.show_status("Barcode scanned successfully.", debug=f"Scanned data: {barcode_data}", message_type='success')

        self.input_entry.delete(0, tk.END)

        scan_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.treeview.insert("", tk.END, text=barcode_type, values=(
            getattr(barcode, 'data', ''), barcode_edipi, getattr(barcode, 'name', ''),
            getattr(barcode, 'branch', ''), getattr(barcode, 'category', ''),
            getattr(barcode, 'rank', ''), getattr(barcode, 'dob', '').strftime("%x") if hasattr(barcode, 'dob') else '',
            getattr(barcode, 'pcc', ''), getattr(barcode, 'ppc', ''),
            getattr(barcode, 'ppgc', ''), scan_datetime
        ))

        self.resize_columns()
        self.save_to_csv(barcode)
        self.previous_barcode_edipi = barcode_edipi
        self.previous_barcode_type = barcode_type

    def update_existing_entry(self, barcode):
        for child in self.treeview.get_children():
            values = self.treeview.item(child, 'values')
            if values[1] == barcode.edipi:
                self.treeview.item(child, values=(
                    getattr(barcode, 'data', ''), barcode.edipi, getattr(barcode, 'name', ''),
                    getattr(barcode, 'branch', ''), getattr(barcode, 'category', ''),
                    getattr(barcode, 'rank', ''), getattr(barcode, 'dob', '').strftime("%x") if hasattr(barcode, 'dob') else '',
                    getattr(barcode, 'pcc', ''), getattr(barcode, 'ppc', ''),
                    getattr(barcode, 'ppgc', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                break

    def resize_columns(self):
        min_width = 80   # Set a minimum width in pixels
        max_width = 300  # Set a maximum width in pixels
        
        for col in self.treeview["columns"]:
            max_text_width = max(len(str(item)) * 10 for item in [self.treeview.item(row_id)['values'][self.treeview["columns"].index(col)] for row_id in self.treeview.get_children()])
            # Constrain the column width within the min and max bounds
            adjusted_width = min(max(max_text_width, min_width), max_width)
            self.treeview.column(col, width=adjusted_width)

    def save_to_csv(self, barcode):
        with open("scanned_data.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                self.write_csv_header(writer)
            writer.writerow(self.get_csv_row(barcode))

    def write_csv_header(self, writer):
        writer.writerow([
            "Type", "Data", "EDIPI", "Name", "Branch", "Category", "Rank", "DOB", "PCC", "PPC", "PPGC", "DateTime"
        ])

    def get_csv_row(self, barcode):
        return [
            type(barcode).__name__, getattr(barcode, 'data', ''),
            getattr(barcode, 'edipi', ''), getattr(barcode, 'name', ''),
            getattr(barcode, 'branch', ''), getattr(barcode, 'category', ''),
            getattr(barcode, 'rank', ''), getattr(barcode, 'dob', '').strftime("%x") if hasattr(barcode, 'dob') else '',
            getattr(barcode, 'pcc', ''), getattr(barcode, 'ppc', ''),
            getattr(barcode, 'ppgc', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.save_to_csv_file(file_path)
            open("scanned_data.csv", 'w').close()
            self.show_status("Data exported and new CSV file created.", message_type='success')

    def save_to_csv_file(self, file_path):
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            self.write_csv_header(writer)
            for child in self.treeview.get_children():
                writer.writerow(self.treeview.item(child, 'values'))

    def show_status(self, message, debug="", message_type='info'):
        color = self.colors.get(message_type, self.colors['text'])
        self.status_bar.config(text=message, bg=color)
        if debug:
            print(f"DEBUG: {debug}")

    def apply_filter(self, event=None):
        filter_text = self.filter_entry.get().lower()
        for child in self.treeview.get_children():
            item = self.treeview.item(child)
            if filter_text in str(item['values']).lower():
                self.treeview.item(child, tags=("match",))
            else:
                self.treeview.item(child, tags=("nomatch",))
        self.treeview.tag_configure("match", background="lightgreen")
        self.treeview.tag_configure("nomatch", background="white")

    def on_treeview_double_click(self, event):
        # Identify the row and column under the cursor
        region = self.treeview.identify('region', event.x, event.y)
        if region == 'cell':
            column = self.treeview.identify_column(event.x)
            row = self.treeview.identify_row(event.y)

            # Get the bounding box of the cell
            x, y, width, height = self.treeview.bbox(row, column)
            value = self.treeview.item(row, "values")[int(column[1:]) - 1]

            # Create a new entry widget for editing
            self.editing_entry = ttk.Entry(self.treeview)
            self.editing_entry.place(x=x, y=y, width=width, height=height)
            self.editing_entry.insert(0, value)
            self.editing_entry.focus()

            # Bind the Entry widget to handle editing completion
            self.editing_entry.bind("<Return>", lambda e: self.save_editing(row, column))
            self.editing_entry.bind("<FocusOut>", lambda e: self.save_editing(row, column))

    def save_editing(self, row, column):
        new_value = self.editing_entry.get()
        values = list(self.treeview.item(row, "values"))
        values[int(column[1:]) - 1] = new_value
        self.treeview.item(row, values=values)
        self.editing_entry.destroy()


def main():
    root = tk.Tk()
    app = BarcodeScannerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
