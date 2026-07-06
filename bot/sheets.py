import os
import re
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

from config import (
    DAFTAR_AKUN, EXPENSE_CATEGORIES, INCOME_CATEGORIES,
    NON_BUDGET_CATEGORIES, TRANSAKSI_HEADERS
)

# GOOGLE SHEETS AUTH

_sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
if not _sa_json:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is not set.")
# Strip surrounding quotes if the value was stored with them
if _sa_json.startswith(("'", '"')) and _sa_json.endswith(("'", '"')):
    _sa_json = _sa_json[1:-1]
# Fix common issues when JSON is pasted from Google Cloud Console:
# 1. Trailing commas before closing brace (invalid JSON)
_sa_json = re.sub(r',\s*}', '}', _sa_json)
_sa_json = re.sub(r',\s*]', ']', _sa_json)
# 2. Literal newlines inside private_key string value
_sa_json = re.sub(
    r'("private_key"\s*:\s*")(.*?)(")',
    lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + m.group(3),
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

try:
    sheet_utama = gc.open("keuangan v4")
    sheet_transaksi = sheet_utama.worksheet("Transaksi")
    print("Google Sheets terhubung.")
except Exception as e:
    print(f"Error koneksi Google Sheets: {e}")
    raise


# TIMEZONE & EXCEL DATE FIX (WIB = UTC+7)

WIB_OFFSET = timedelta(hours=7)

def now_wib():
    """Return current datetime in WIB (UTC+7)"""
    return datetime.utcnow() + WIB_OFFSET

def jam_sekarang_excel():
    """Return fraction of day for WIB time (kolom C / Num)"""
    now = now_wib()
    return (now.hour / 24) + (now.minute / 1440) + (now.second / 86400)

def tanggal_sekarang_excel():
    """Return Excel serial date for today in WIB"""
    dt = now_wib()
    base = datetime(1899, 12, 30)
    delta = dt - base
    return delta.days + (delta.seconds / 86400)

def parse_rp(val_str):
    """Parse nilai rupiah: 'Rp3.700.000' → 3700000, '3700000' → 3700000"""
    if not val_str:
        return 0
    s = str(val_str).strip()
    if not s:
        return 0
    # Hapus Rp, spasi, titik (thousand separator Indonesia), lalu ganti koma→titik
    s = re.sub(r"[Rp\s]", "", s)
    s = s.replace(".", "").replace(",", ".")
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0

def excel_serial_to_iso(serial_str):
    """Convert Excel serial date number atau string tanggal ke YYYY-MM-DD.
    
    Sheet keuangan V4 menyimpan tanggal sebagai string DD/MM/YYYY
    (misal: '08/06/2026' = 8 Juni 2026).
    """
    s = str(serial_str).strip()
    if not s:
        return ""
    # Coba parse sebagai Excel serial number (angka)
    try:
        serial = float(s)
        base = datetime(1899, 12, 30)
        dt = base + timedelta(days=serial)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass
    # Coba berbagai format string tanggal
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s

def iso_to_excel_serial(iso_date_str):
    """Convert YYYY-MM-DD to Excel serial date number"""
    dt = datetime.strptime(iso_date_str, "%Y-%m-%d")
    base = datetime(1899, 12, 30)
    delta = dt - base
    return delta.days


# HELPERS

def cari_baris_kosong(sheet):
    return len(sheet.col_values(1)) + 1


# WRITE

def tulis_transaksi(akun, payee, memo, kategori, payment, deposit):
    baris = cari_baris_kosong(sheet_transaksi)
    tgl_excel = tanggal_sekarang_excel()
    jam_excel = jam_sekarang_excel()
    
    data = [
        akun,           # A: Akun
        tgl_excel,      # B: Tanggal (Excel serial)
        jam_excel,      # C: Num (fraction of day = WIB time)
        payee,          # D: Payee (keterangan panjang)
        memo,           # E: Memo (nama barang/item)
        "",             # F: Tag
        kategori,       # G: Category
        "c",            # H: Clr
        int(payment) if payment else "",
        int(deposit) if deposit else "",
    ]
    sheet_transaksi.update(
        range_name=f"A{baris}:J{baris}",
        values=[data],
        value_input_option="USER_ENTERED",
    )


def tulis_transfer(dari_akun, ke_akun, nominal, memo="Pindah Saldo"):
    tgl_excel = tanggal_sekarang_excel()
    jam_excel = jam_sekarang_excel()
    b1 = cari_baris_kosong(sheet_transaksi)
    
    sheet_transaksi.update(
        range_name=f"A{b1}:J{b1}",
        values=[[dari_akun, tgl_excel, jam_excel, "-", memo, "", "[Transfer]", "c", int(nominal), ""]],
        value_input_option="USER_ENTERED",
    )
    b2 = b1 + 1
    sheet_transaksi.update(
        range_name=f"A{b2}:J{b2}",
        values=[[ke_akun, tgl_excel, jam_excel, "-", memo, "", "[Transfer]", "c", "", int(nominal)]],
        value_input_option="USER_ENTERED",
    )


# READ

def get_semua_transaksi():
    semua = sheet_transaksi.get_all_values()
    hasil = []
    # Sheet keuangan V4: 4 baris header (row 0-2 = judul/help, row 3 = kolom header)
    # Data mulai dari row index 4
    for b in semua[4:]:
        # Wajib ada akun (kolom A) dan tanggal (kolom B)
        if not b or not b[0].strip() or not (len(b) > 1 and b[1].strip()):
            continue
        # Skip baris formula/summary (akun kosong atau bukan nama akun valid)
        akun = b[0].strip()
        if akun.startswith("[") or len(b) < 9:
            continue

        tgl_iso = excel_serial_to_iso(b[1])
        if not tgl_iso:
            continue

        payment = parse_rp(b[8]) if len(b) > 8 else 0
        deposit = parse_rp(b[9]) if len(b) > 9 else 0

        hasil.append({
            "akun": akun,
            "tgl": tgl_iso,
            "jam": b[2].strip() if len(b) > 2 else "",
            "payee": b[3].strip() if len(b) > 3 else "",
            "memo": b[4].strip() if len(b) > 4 else "",
            "tag": b[5].strip() if len(b) > 5 else "",
            "kategori": b[6].strip() if len(b) > 6 else "",
            "clr": b[7].strip() if len(b) > 7 else "",
            "payment": payment,
            "deposit": deposit,
        })
    return hasil


def filter_operasional(transaksi):
    exclude = set(NON_BUDGET_CATEGORIES + ["[Beginning Balance]", "[Carryover Balance]", "NON-BUDGET CATEGORIES"])
    return [t for t in transaksi if t["kategori"] not in exclude]


def saldo_per_akun(transaksi):
    saldo = {}
    for t in transaksi:
        akun = t["akun"]
        saldo[akun] = saldo.get(akun, 0) + t["deposit"] - t["payment"]
    return saldo


def get_month_expense_for_category(kategori):
    bulan_ini = now_wib().strftime("%Y-%m")
    total = 0
    for t in get_semua_transaksi():
        if t["tgl"].startswith(bulan_ini) and t["kategori"] == kategori:
            total += t["payment"]
    return total


def get_anggaran_for_category(kategori):
    """Baca anggaran dari sheet Budget, kolom sesuai bulan.
    
    Struktur Budget sheet keuangan V4:
    - Row 9: ['', '', 'Jan', 'Feb', 'Mar', ...] → Jan = col index 2
    - Jadi bulan N → col index = N + 1
    """
    try:
        sheet_budget = sheet_utama.worksheet("Budget")
        data = sheet_budget.get_all_values()
        
        bulan_ini = now_wib().month
        col_index = bulan_ini + 1  # Jan(1) → col 2, Feb(2) → col 3, dst
        
        for row in data:
            if len(row) > col_index and row[0].strip() == kategori:
                val = row[col_index].strip()
                if val:
                    val_clean = re.sub(r"[Rp\s\.]", "", val).replace(",", ".")
                    try:
                        return float(val_clean)
                    except ValueError:
                        return 0
        return 0
    except Exception:
        return 0


def get_recent(n=10):
    txns = get_semua_transaksi()
    return txns[-n:][::-1]


def get_summary():
    bulan_ini = now_wib().strftime("%Y-%m")
    total_income = 0
    total_expense = 0
    by_category = {}
    transactions = 0

    for t in get_semua_transaksi():
        if not t["tgl"].startswith(bulan_ini):
            continue
        if t["kategori"] in NON_BUDGET_CATEGORIES:
            continue
        if t["payment"] > 0:
            total_expense += t["payment"]
            by_category[t["kategori"]] = by_category.get(t["kategori"], 0) + t["payment"]
            transactions += 1
        if t["deposit"] > 0:
            total_income += t["deposit"]
            transactions += 1

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "saldo": total_income - total_expense,
        "by_category": by_category,
        "transactions": transactions,
    }


def get_week_transactions():
    hari_ini = now_wib().date()
    tujuh_lalu = hari_ini - timedelta(days=6)
    hasil = []
    for t in get_semua_transaksi():
        try:
            tgl_t = datetime.strptime(t["tgl"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if tujuh_lalu <= tgl_t <= hari_ini:
            hasil.append(t)
    return hasil
    