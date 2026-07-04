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
    """Manages multiple Google Sheets with different schemas."""

    def __init__(self, spreadsheet_name, worksheet_name, headers):
        self.spreadsheet = gc.open(spreadsheet_name)
        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols=str(len(headers)))
            self.worksheet.append_row(headers)
        self.headers = headers
        self._col_map = {h: i for i, h in enumerate(headers)}

    def find_empty_row(self):
        return len(self.worksheet.col_values(1)) + 1

    def append_row(self, values_dict):
        row = [values_dict.get(h, "") for h in self.headers]
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


# Spreadsheet definitions

SPREADSHEETS = {
    "keuangan": {
        "name": "keuangan v4",
        "sheets": {
            "Transaksi": ["Akun", "Tanggal", "Num", "Payee", "Memo", "Tag", "Category", "Clr", "PAYMENT", "DEPOSIT"],
            "Budget": ["Kategori", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"],
        }
    },
    "investasi": {
        "name": "Investasi Zee",
        "sheets": {
            "Portfolio": ["Tanggal", "Jenis", "Nama", "Jumlah Lot", "Harga Beli", "Total", "Broker", "Keterangan"],
            "Dividen": ["Tanggal", "Nama Saham", "Jumlah Dividen", "Broker", "Keterangan"],
            "Realisasi": ["Tanggal", "Jenis", "Nama", "Jumlah Lot", "Harga Beli", "Harga Jual", "Profit/Loss", "Broker"],
        }
    },
    "utang_piutang": {
        "name": "Utang & Piutang",
        "sheets": {
            "Utang": ["Tanggal", "Nama", "Jumlah", "Status", "Jatuh Tempo", "Keterangan"],
            "Piutang": ["Tanggal", "Nama", "Jumlah", "Status", "Jatuh Tempo", "Keterangan"],
        }
    },
    "target_tabungan": {
        "name": "Target Tabungan",
        "sheets": {
            "Goals": ["Nama Goal", "Target Jumlah", "Terkumpul", "Deadline", "Status", "Keterangan"],
            "Progress": ["Tanggal", "Nama Goal", "Jumlah Masuk", "Saldo Goal"],
        }
    },
    "aset": {
        "name": "Aset & Properti",
        "sheets": {
            "Aset": ["Nama Aset", "Jenis", "Nilai Beli", "Nilai Sekarang", "Tanggal Beli", "Keterangan"],
        }
    },
}

# Active manager instances
_managers = {}


def get_manager(spreadsheet_key, sheet_key):
    """Get or create a SheetManager for a specific spreadsheet and sheet."""
    cache_key = f"{spreadsheet_key}:{sheet_key}"
    if cache_key not in _managers:
        spec = SPREADSHEETS[spreadsheet_key]
        mgr = SheetManager(spec["name"], sheet_key, spec["sheets"][sheet_key])
        _managers[cache_key] = mgr
    return _managers[cache_key]


def list_spreadsheets():
    """Return list of all configured spreadsheet keys and specs."""
    return list(SPREADSHEETS.items())


def list_sheets(spreadsheet_key):
    """Return list of sheet names inside a spreadsheet."""
    return list(SPREADSHEETS[spreadsheet_key]["sheets"].keys())
