import csv
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from cacbarcode import decode_barcode


class BarcodeScannerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("CAC & Driver's License Barcode Scanner")
        self.root.state("zoomed")  # Maximize the window at startup

        self.colors = {
            "background": "#f5f5f5",
            "text": "#000000",
            "status": "#ff9900",
            "error": "#ff3333",
            "warning": "#ffcc00",
            "success": "#33cc33",
            "expired": "#ffe6e6",
            "valid": "#ffffff",
        }

        self.logo = self.load_logo("logo.png")
        self.previous_card_id = None
        self.previous_barcode_type = None
        self.scanned_cards = {}  # id_number -> barcode_type
        self.card_data_store = {}  # iid -> barcode object

        # Scanner wedge timing buffer
        self._wedge_timer = None
        self._last_keystroke_time = 0

        self.create_widgets()

    def load_logo(self, logo_path):
        try:
            logo = tk.PhotoImage(file=logo_path)
            self.root.iconphoto(False, logo)
            return logo
        except Exception:
            return None

    def create_widgets(self):
        self.setup_input_frame()
        self.setup_status_bar()
        self.setup_result_frame()
        self.apply_styles()

    def setup_input_frame(self):
        self.input_frame = ttk.Frame(
            self.root,
            padding="10",
            style="Input.TFrame",
        )
        self.input_frame.pack(pady=10, fill=tk.X)

        center_frame = ttk.Frame(self.input_frame, style="Input.TFrame")
        center_frame.pack(anchor=tk.CENTER)

        self.input_label = ttk.Label(
            center_frame,
            text="Scan Barcode:",
            style="Label.TLabel",
            font=("TkDefaultFont", 10, "bold"),
        )
        self.input_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.input_entry = ttk.Entry(
            center_frame,
            width=50,
            style="Input.TEntry",
        )
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        self.input_entry.focus()
        self.input_entry.bind("<Return>", self.on_return_pressed)
        self.input_entry.bind("<Key>", self.on_key_pressed)

        self.clear_btn = ttk.Button(
            center_frame,
            text="Clear",
            command=self.clear_input,
            style="Button.TButton",
        )
        self.clear_btn.grid(row=0, column=2, padx=5, pady=5)

        self.filter_label = ttk.Label(
            center_frame,
            text="Filter / Search:",
            style="Label.TLabel",
        )
        self.filter_label.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        self.filter_entry = ttk.Entry(
            center_frame,
            width=20,
            style="Input.TEntry",
        )
        self.filter_entry.grid(row=0, column=4, padx=5, pady=5)
        self.filter_entry.bind("<KeyRelease>", self.apply_filter)

        self.export_button = ttk.Button(
            center_frame,
            text="Export CSV",
            command=self.export_csv,
            style="Button.TButton",
        )
        self.export_button.grid(row=0, column=5, padx=5, pady=5)

    def setup_status_bar(self):
        self.status_bar = tk.Label(
            self.root,
            text="Ready to scan (DoD CAC or State Driver's License)",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=("TkDefaultFont", 11, "bold"),
            background=self.colors["status"],
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_result_frame(self):
        self.result_frame = ttk.Frame(
            self.root,
            padding="10",
            style="Result.TFrame",
        )
        self.result_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        self.columns = (
            "type",
            "id_number",
            "name",
            "dob",
            "exp_date",
            "state_branch",
            "category_class",
            "rank_sex",
            "details",
            "datetime",
        )
        self.column_headers = {
            "type": "Type",
            "id_number": "ID / EDIPI",
            "name": "Full Name",
            "dob": "DOB (Age)",
            "exp_date": "Expiration",
            "state_branch": "State / Branch",
            "category_class": "Category / Class",
            "rank_sex": "Rank / Sex",
            "details": "Details / Address",
            "datetime": "Scan Time",
        }

        self.treeview = ttk.Treeview(
            self.result_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse",
        )
        for col in self.columns:
            self.treeview.heading(col, text=self.column_headers[col])
            self.treeview.column(col, minwidth=60, width=120, anchor=tk.W)

        self.treeview.bind("<Double-1>", self.on_treeview_double_click)

        self.scrollbar_y = ttk.Scrollbar(
            self.result_frame,
            orient="vertical",
            command=self.treeview.yview,
        )
        self.scrollbar_y.pack(side="right", fill="y")

        self.scrollbar_x = ttk.Scrollbar(
            self.result_frame,
            orient="horizontal",
            command=self.treeview.xview,
        )
        self.scrollbar_x.pack(side="bottom", fill="x")

        self.treeview.configure(
            xscrollcommand=self.scrollbar_x.set,
            yscrollcommand=self.scrollbar_y.set,
        )
        self.treeview.pack(fill=tk.BOTH, expand=True)

        self.treeview.tag_configure("expired", background=self.colors["expired"])
        self.treeview.tag_configure("match", background="lightgreen")
        self.treeview.tag_configure("nomatch", background="white")

    def apply_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background=self.colors["background"])
        style.configure(
            "Label.TLabel",
            background=self.colors["background"],
            foreground=self.colors["text"],
        )
        style.configure("Input.TEntry", foreground=self.colors["text"])
        style.configure("Button.TButton", background=self.colors["success"])
        style.configure("Result.TFrame", background=self.colors["background"])
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

    def clear_input(self):
        self.input_entry.delete(0, tk.END)
        self.input_entry.focus()

    def on_key_pressed(self, event=None):
        self._last_keystroke_time = time.time()
        if self._wedge_timer is not None:
            self.root.after_cancel(self._wedge_timer)
            self._wedge_timer = None

    def on_return_pressed(self, event=None):
        text = self.input_entry.get()
        if not text:
            return

        time_since_key = time.time() - self._last_keystroke_time
        if ("@" in text or "ANSI " in text) and time_since_key < 0.08:
            if self._wedge_timer is not None:
                self.root.after_cancel(self._wedge_timer)
            self._wedge_timer = self.root.after(100, self.scan_barcode)
            return

        self.scan_barcode()

    def scan_barcode(self, event=None):
        if self._wedge_timer is not None:
            self.root.after_cancel(self._wedge_timer)
            self._wedge_timer = None

        raw_barcode_data = self.input_entry.get().strip()
        if not raw_barcode_data:
            return

        barcode_obj, barcode_type = self.parse_barcode(raw_barcode_data)
        if not barcode_obj:
            return

        card_id = (
            getattr(barcode_obj, "id_number", "")
            or str(getattr(barcode_obj, "edipi", ""))
        )
        if card_id and card_id in self.scanned_cards:
            if self.previous_barcode_type == "Code39" and barcode_type in (
                "PDF417",
                "AAMVA_DL",
            ):
                self.update_existing_entry(barcode_obj, barcode_type)
            else:
                self.show_status(
                    f"Warning: Duplicate card scanned (ID: {card_id}).",
                    message_type="warning",
                )
        else:
            if card_id:
                self.scanned_cards[card_id] = barcode_type

        self.show_status(
            f"Successfully scanned {barcode_obj.barcode_type_label}: {barcode_obj.name or card_id}",
            debug=f"Type={barcode_type}, ID={card_id}",
            message_type="success",
        )

        self.input_entry.delete(0, tk.END)

        scan_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_values = self.format_row_values(
            barcode_obj, barcode_type, scan_datetime
        )

        row_tags = (
            ("expired",)
            if getattr(barcode_obj, "is_expired", False)
            else ()
        )
        item_id = self.treeview.insert(
            "", tk.END, values=row_values, tags=row_tags
        )
        self.card_data_store[item_id] = barcode_obj

        self.resize_columns()
        self.save_to_csv(barcode_obj, barcode_type, scan_datetime)
        self.previous_card_id = card_id
        self.previous_barcode_type = barcode_type

    def parse_barcode(self, barcode_data):
        try:
            barcode_obj, barcode_type = decode_barcode(barcode_data)
            return barcode_obj, barcode_type
        except Exception as parse_error:
            self.show_status(
                f"Error: Failed to parse barcode data ({parse_error})",
                message_type="error",
            )
            return None, None

    def format_row_values(self, barcode_obj, barcode_type, scan_datetime):
        card_id = (
            getattr(barcode_obj, "id_number", "")
            or str(getattr(barcode_obj, "edipi", ""))
        )

        dob_val = getattr(barcode_obj, "dob", None)
        dob_str = ""
        if dob_val:
            dob_date = (
                dob_val.date() if isinstance(dob_val, datetime) else dob_val
            )
            age = getattr(barcode_obj, "age", None)
            dob_str = f"{dob_date.strftime('%Y-%m-%d')}" + (
                f" ({age})" if age is not None else ""
            )

        exp_val = (
            getattr(barcode_obj, "expiration_date", None)
            or getattr(barcode_obj, "expdate", None)
        )
        exp_str = ""
        if exp_val:
            exp_date = (
                exp_val.date() if isinstance(exp_val, datetime) else exp_val
            )
            exp_str = exp_date.strftime("%Y-%m-%d")
            if getattr(barcode_obj, "is_expired", False):
                exp_str += " [EXPIRED]"

        state_branch = (
            getattr(barcode_obj, "branch", "")
            or getattr(barcode_obj, "state", "")
        )
        category_class = (
            getattr(barcode_obj, "category", "")
            or getattr(barcode_obj, "license_class", "")
        )
        rank_sex = (
            getattr(barcode_obj, "rank", "")
            or getattr(barcode_obj, "sex", "")
        )

        details_list = []
        if (
            hasattr(barcode_obj, "address_street")
            and barcode_obj.address_street
        ):
            details_list.append(barcode_obj.address_street)
        if hasattr(barcode_obj, "address_city") and barcode_obj.address_city:
            details_list.append(barcode_obj.address_city)
        if getattr(barcode_obj, "ppc", ""):
            details_list.append(f"PPC:{barcode_obj.ppc}")
        if getattr(barcode_obj, "ppgc", ""):
            details_list.append(f"Grade:{barcode_obj.ppgc}")
        details_summary = ", ".join(details_list)

        return (
            barcode_obj.barcode_type_label,
            card_id,
            getattr(barcode_obj, "name", ""),
            dob_str,
            exp_str,
            state_branch,
            category_class,
            rank_sex,
            details_summary,
            scan_datetime,
        )

    def update_existing_entry(self, barcode_obj, barcode_type):
        card_id = (
            getattr(barcode_obj, "id_number", "")
            or str(getattr(barcode_obj, "edipi", ""))
        )
        for child in self.treeview.get_children():
            values = self.treeview.item(child, "values")
            if values[1] == card_id:
                scan_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                new_values = self.format_row_values(
                    barcode_obj, barcode_type, scan_datetime
                )
                row_tags = (
                    ("expired",)
                    if getattr(barcode_obj, "is_expired", False)
                    else ()
                )
                self.treeview.item(child, values=new_values, tags=row_tags)
                self.card_data_store[child] = barcode_obj
                break

    def resize_columns(self):
        min_width = 80
        max_width = 280
        for idx, col in enumerate(self.columns):
            header_len = len(self.column_headers.get(col, col)) * 11
            max_len = header_len
            for row_id in self.treeview.get_children():
                val = str(self.treeview.item(row_id)["values"][idx])
                max_len = max(max_len, len(val) * 9)
            adjusted_width = min(max(max_len, min_width), max_width)
            self.treeview.column(col, width=adjusted_width)

    def save_to_csv(self, barcode_obj, barcode_type, scan_datetime):
        with open("scanned_data.csv", mode="a", newline="", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            if file.tell() == 0:
                self.write_csv_header(csv_writer)
            csv_writer.writerow(
                self.get_csv_row(barcode_obj, barcode_type, scan_datetime)
            )

    def write_csv_header(self, csv_writer):
        csv_writer.writerow(
            [
                "Type",
                "ID_Number",
                "Name",
                "First_Name",
                "Middle_Name",
                "Last_Name",
                "DOB",
                "Age",
                "Expiration_Date",
                "Is_Expired",
                "State",
                "Branch",
                "Category",
                "Rank",
                "Sex",
                "Street",
                "City",
                "Postal_Code",
                "Raw_Data",
                "Scan_DateTime",
            ]
        )

    def get_csv_row(self, barcode_obj, barcode_type, scan_datetime):
        card_id = (
            getattr(barcode_obj, "id_number", "")
            or str(getattr(barcode_obj, "edipi", ""))
        )
        dob = getattr(barcode_obj, "dob", "")
        dob_str = (
            dob.strftime("%Y-%m-%d")
            if hasattr(dob, "strftime")
            else str(dob or "")
        )
        exp = (
            getattr(barcode_obj, "expiration_date", "")
            or getattr(barcode_obj, "expdate", "")
        )
        exp_str = (
            exp.strftime("%Y-%m-%d")
            if hasattr(exp, "strftime")
            else str(exp or "")
        )

        return [
            barcode_obj.barcode_type_label,
            card_id,
            getattr(barcode_obj, "name", ""),
            getattr(barcode_obj, "first_name", "")
            or getattr(barcode_obj, "firstname", ""),
            getattr(barcode_obj, "middle_name", "")
            or getattr(barcode_obj, "initial", ""),
            getattr(barcode_obj, "last_name", "")
            or getattr(barcode_obj, "lastname", ""),
            dob_str,
            getattr(barcode_obj, "age", "") or "",
            exp_str,
            getattr(barcode_obj, "is_expired", False),
            getattr(barcode_obj, "state", ""),
            getattr(barcode_obj, "branch", ""),
            getattr(barcode_obj, "category", ""),
            getattr(barcode_obj, "rank", ""),
            getattr(barcode_obj, "sex", ""),
            getattr(barcode_obj, "address_street", ""),
            getattr(barcode_obj, "address_city", ""),
            getattr(barcode_obj, "address_postal", ""),
            getattr(barcode_obj, "raw_data", "")
            or getattr(barcode_obj, "data", ""),
            scan_datetime,
        ]

    def export_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if file_path:
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                csv_writer = csv.writer(file)
                self.write_csv_header(csv_writer)
                for child in self.treeview.get_children():
                    tags = self.treeview.item(child, "tags")
                    if "nomatch" in tags:
                        continue
                    barcode_entry = self.card_data_store.get(child)
                    if barcode_entry:
                        row_vals = self.treeview.item(child, "values")
                        csv_writer.writerow(
                            self.get_csv_row(
                                barcode_entry, row_vals[0], row_vals[9]
                            )
                        )
            self.show_status(
                f"Data exported successfully to {file_path}",
                message_type="success",
            )

    def show_status(self, message, debug="", message_type="info"):
        color = self.colors.get(message_type, self.colors["status"])
        self.status_bar.config(text=message, bg=color)
        if debug:
            print(f"DEBUG: {debug}")

    def apply_filter(self, event=None):
        filter_text = self.filter_entry.get().lower().strip()
        matching_rows = []
        non_matching_rows = []

        for child in self.treeview.get_children():
            item = self.treeview.item(child)
            row_str = " ".join(str(v) for v in item["values"]).lower()
            if not filter_text or filter_text in row_str:
                matching_rows.append((child, item))
            else:
                non_matching_rows.append((child, item))

        for row, _item in matching_rows:
            self.treeview.item(row, tags=("match",))

        for row, _item in non_matching_rows:
            self.treeview.item(row, tags=("nomatch",))

        if not filter_text:
            for child in self.treeview.get_children():
                barcode_entry = self.card_data_store.get(child)
                if barcode_entry and getattr(barcode_entry, "is_expired", False):
                    self.treeview.item(child, tags=("expired",))
                else:
                    self.treeview.item(child, tags=())

    def on_treeview_double_click(self, event):
        """Open detailed card information dialog on row double-click."""
        item_id = self.treeview.focus()
        if not item_id:
            return

        barcode_obj = self.card_data_store.get(item_id)
        if not barcode_obj:
            return

        self.show_detail_dialog(barcode_obj)

    def show_detail_dialog(self, barcode_obj):
        dialog_window = tk.Toplevel(self.root)
        dialog_window.title(
            f"Card Details: {barcode_obj.barcode_type_label} - "
            f"{barcode_obj.name or barcode_obj.id_number}"
        )
        dialog_window.geometry("540x480")
        dialog_window.transient(self.root)
        dialog_window.grab_set()

        content_frame = ttk.Frame(dialog_window, padding="15")
        content_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            content_frame,
            text=barcode_obj.barcode_type_label,
            font=("TkDefaultFont", 13, "bold"),
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        info_frame = ttk.LabelFrame(content_frame, text="Decoded Fields", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        fields_list = [
            (
                "ID / EDIPI",
                getattr(barcode_obj, "id_number", "")
                or str(getattr(barcode_obj, "edipi", "")),
            ),
            ("Full Name", getattr(barcode_obj, "name", "")),
            (
                "First Name",
                getattr(barcode_obj, "first_name", "")
                or getattr(barcode_obj, "firstname", ""),
            ),
            (
                "Middle Name",
                getattr(barcode_obj, "middle_name", "")
                or getattr(barcode_obj, "initial", ""),
            ),
            (
                "Last Name",
                getattr(barcode_obj, "last_name", "")
                or getattr(barcode_obj, "lastname", ""),
            ),
            (
                "Date of Birth",
                f"{barcode_obj.dob} (Age: {getattr(barcode_obj, 'age', 'N/A')})"
                if getattr(barcode_obj, "dob", None)
                else "N/A",
            ),
            (
                "Expiration",
                f"{getattr(barcode_obj, 'expiration_date', '') or getattr(barcode_obj, 'expdate', '')} "
                f"{'[EXPIRED]' if getattr(barcode_obj, 'is_expired', False) else '[ACTIVE]'}",
            ),
            ("State", getattr(barcode_obj, "state", "")),
            ("Branch", getattr(barcode_obj, "branch", "")),
            ("Category", getattr(barcode_obj, "category", "")),
            (
                "Rank / Class",
                getattr(barcode_obj, "rank", "")
                or getattr(barcode_obj, "license_class", ""),
            ),
            ("Sex", getattr(barcode_obj, "sex", "")),
        ]

        if hasattr(barcode_obj, "address_street") and barcode_obj.address_street:
            full_address = (
                f"{barcode_obj.address_street}, "
                f"{getattr(barcode_obj, 'address_city', '')}, "
                f"{getattr(barcode_obj, 'state', '')} "
                f"{getattr(barcode_obj, 'address_postal', '')}"
            ).strip()
            fields_list.append(("Address", full_address))

        for row_idx, (field_label, field_val) in enumerate(fields_list):
            if field_val and field_val != "N/A":
                lbl_widget = ttk.Label(
                    info_frame,
                    text=f"{field_label}:",
                    font=("TkDefaultFont", 9, "bold"),
                )
                lbl_widget.grid(row=row_idx, column=0, sticky="w", padx=5, pady=2)
                val_widget = ttk.Label(info_frame, text=str(field_val))
                val_widget.grid(row=row_idx, column=1, sticky="w", padx=5, pady=2)

        raw_frame = ttk.LabelFrame(content_frame, text="Raw Barcode Data", padding="5")
        raw_frame.pack(fill=tk.X, pady=5)

        raw_text_box = tk.Text(raw_frame, height=4, wrap="char", font=("Courier", 8))
        raw_text_box.insert(
            "1.0",
            getattr(barcode_obj, "raw_data", "") or getattr(barcode_obj, "data", ""),
        )
        raw_text_box.configure(state="disabled")
        raw_text_box.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        def copy_raw_data():
            dialog_window.clipboard_clear()
            dialog_window.clipboard_append(
                getattr(barcode_obj, "raw_data", "") or getattr(barcode_obj, "data", "")
            )
            messagebox.showinfo(
                "Copied",
                "Raw barcode data copied to clipboard!",
                parent=dialog_window,
            )

        copy_btn = ttk.Button(button_frame, text="Copy Raw Data", command=copy_raw_data)
        copy_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(
            button_frame, text="Close", command=dialog_window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)


def main():
    root = tk.Tk()
    BarcodeScannerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
