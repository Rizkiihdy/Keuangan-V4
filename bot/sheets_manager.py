import os
import re
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# GOOGLE SHEETS AUTH

_sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
if not _sa_json:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set.")
if _sa_json.startswith(("'", '"')) and _sa_json.endswith(("'", '"')):
    _sa_json = _sa_json[1:-1]
_sa_json = re.sub(r',\s*}', '}', _sa_json)
_sa_json = re.sub(r',\s*]', ']', _sa_json)
_sa_json = re.sub(
    r'("private_key"\s*:\s*")(.*?)"',
    lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + '"',
    _sa_json,
    flags=re.DOTALL,
)
try:
    KUNCI_GOOGLE = json.loads(_sa_json)
except json.JSONDecodeError as e:
    raise RuntimeError(f"GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(KUNCI_GOOGLE, scopes=SCOPE)
gc = gspread.authorize(creds)


class SheetManager:
    """Manages a single worksheet inside a Google Spreadsheet."""

    def __init__(self, spreadsheet_id, worksheet_name, headers=None):
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet = gc.open_by_key(spreadsheet_id)
        self.headers = headers
        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            if headers:
                self.worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols=str(len(headers)))
                self.worksheet.append_row(headers)
            else:
                raise
        if headers:
            self._col_map = {h: i for i, h in enumerate(headers)}

    def find_empty_row(self):
        return len(self.worksheet.col_values(1)) + 1

    def append_row(self, values_dict):
        if self.headers:
            row = [values_dict.get(h, "") for h in self.headers]
        else:
            row = list(values_dict.values())
        self.worksheet.append_row(row, value_input_option="USER_ENTERED")

    def get_all_rows(self):
        raw = self.worksheet.get_all_values()
        if not raw:
            return []
        headers = raw[0]
        rows = []
        for r in raw[1:]:
            if not any(r):
                continue
            rows.append({h: v for h, v in zip(headers, r)})
        return rows

    def get_row_count(self):
        return len(self.worksheet.get_all_values())


# ALL SPREADSHEETS
# The user shared these 6 existing spreadsheets plus the original one

SPREADSHEETS = {
    "keuangan": {
        "id": os.environ.get("GOOGLE_SHEET_ID", "1nbDsBmrQ74g-yC1k8_XVbh8kIP6wfC9ewjAxG6FaCtw"),
        "name": "keuangan v4",
        "sheets": {
            "Transaksi": ["Akun", "Tanggal", "Num", "Payee", "Memo", "Tag", "Category", "Clr", "PAYMENT", "DEPOSIT"],
            "Budget": ["Kategori", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"],
            "Goals": ["Nama Goal", "Target Jumlah", "Terkumpul", "Deadline", "Status", "Keterangan"],
            "Progress": ["Tanggal", "Nama Goal", "Jumlah Masuk", "Saldo Goal"],
            "Aset": ["Nama Aset", "Jenis", "Nilai Beli", "Nilai Sekarang", "Tanggal Beli", "Keterangan"],
        }
    },
    "home_affordability": {
        "id": "1-9aEDT1oGcucnQPTdI_QaikKD3F73pD5xcPY5WAchaQ",
        "name": "Home Affordability",
        "sheets": {
            "Sheet1": None,
        }
    },
    "pensiun": {
        "id": "1WB9EUyYChvxb2cV6vNe9_7qDjYpz6vvjQgvF-iRd4Gg",
        "name": "Kalkulator Pensiun",
        "sheets": {
            "Sheet1": None,
        }
    },
    "simulasi_kredit": {
        "id": "1kvXfV57eAxDx7Tlm-H0HwpVHHd1lXTEAXDJ8qvm0bEw",
        "name": "Simulasi Kredit Motor/Mobil",
        "sheets": {
            "Sheet1": None,
        }
    },
    "tabungan_pensiun": {
        "id": "1YrvpTJsLE1MORB5i79EJYCuJIjti7f2wdP0M5v8lLjg",
        "name": "Kalkulator Tabungan Dana Pensiun",
        "sheets": {
            "Sheet1": None,
        }
    },
    "investasi": {
        "id": "1XjhlnGvlgsaxl3ZB9iaxUCfVvKdhATXw3yWk-fJeq2U",
        "name": "Pelacak Investasi",
        "sheets": {
            "Account1": ["Tanggal", "Jenis", "Nama", "Jumlah Lot", "Harga Beli", "Total", "Broker", "Keterangan"],
            "Account2": ["Tanggal", "Jenis", "Nama", "Jumlah Lot", "Harga Beli", "Total", "Broker", "Keterangan"],
            "Account3": ["Tanggal", "Jenis", "Nama", "Jumlah Lot", "Harga Beli", "Total", "Broker", "Keterangan"],
            "Summary": ["Nama", "Total Lot", "Avg Harga", "Total Value", "Profit/Loss"],
        }
    },
    "utang": {
        "id": "1pjxANUen_K-4Onvf2XENb1XnvdkI5_FOV2LjIA_wrq0",
        "name": "Kalkulator Utang",
        "sheets": {
            "Sheet1": None,
        }
    },
}

# Active manager instances
_managers = {}


def get_manager(spreadsheet_key, sheet_key, headers=None):
    """Get or create a SheetManager for a specific spreadsheet and sheet."""
    cache_key = f"{spreadsheet_key}:{sheet_key}"
    if cache_key not in _managers:
        spec = SPREADSHEETS[spreadsheet_key]
        h = headers if headers else spec["sheets"].get(sheet_key)
        mgr = SheetManager(spec["id"], sheet_key, h)
        _managers[cache_key] = mgr
    return _managers[cache_key]


def get_spreadsheet_id(key):
    return SPREADSHEETS[key]["id"]


def list_spreadsheets():
    """Return list of all configured spreadsheet keys and specs."""
    return list(SPREADSHEETS.items())


def list_sheets(spreadsheet_key):
    """Return list of sheet names inside a spreadsheet."""
    return list(SPREADSHEETS[spreadsheet_key]["sheets"].keys())


def read_sheet_raw(spreadsheet_key, sheet_key):
    """Read all raw values from a sheet (no headers required)."""
    spec = SPREADSHEETS[spreadsheet_key]
    spreadsheet = gc.open_by_key(spec["id"])
    ws = spreadsheet.worksheet(sheet_key)
    return ws.get_all_values()
