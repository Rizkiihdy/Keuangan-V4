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

KUNCI_GOOGLE = {
    "type": "service_account",
    "project_id": "project-keuangan-v4",
    "private_key_id": "349ce386732c2f8371c88532d986576b3958f9b6",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC04AVi9UGu2Xhd\nx835Azd8WDMyy80nI+SLDxHmphRn4MIPkixZgCU/TyTF52R9q+XofavCcgj5jlro\nMizrmP6RF/3qbI+dKmM6hVVnHqxHEUJ4W0BShBBpKNOKtvyEgn6ifELgiCo+o4h1\n0ckLvvNsEJbuxWYXSI/mJPnCdb/v8mulYV+RRMLsVezppzHgoD7/x84TEh8HaRNO\nxLI3jV9t1IOZs3FVPYC6spBuLKKOBFCFnUDirPJjdrnym+Kq1JHjpyDQLogxRbGn\n2Wp4gVnhG33sgyVQjqUYUJVzCgtMzPuKStAvfjiF5PPP5aCOhfMR6s4q1XV/lQuM\n46XisQzDAgMBAAECggEAHL96Zlxq1c/qH1BcKWwxy8lM9zwzMuReinJDuxrB0DIw\nmz71Xj2i2JQgrnUfoLsgmI+DgYKUcJhdVIhyYU542jYrp7ByMbMEqyQkCyFx6lMQ\n8zDgYVJs3/nwMsebYl2co6tdCcjlRf1so/qgRLCoieV9HR2HeMM8s9dD/HywnAHx\nuNXJyVQhOYlVrR0Ui/aowZ5Z0+JezlHX/XlYR3XOIDcS7sAL8SPzzw3EMj9KgX5b\nQ9fAnJ1s5VB4FCbKLyZvTaKXBjP6KL1u27qhKzxRa9vo+oHRQ+VTin2l+sp/z6zq\nuMwyuAS6wENvZigKXpplfJccrICEhAHYfaBBtXK0cQKBgQDX0F0cQkOk+KCLMy8/\nn+nSXzqr+AgRBOOUA9riKDZOSgLFXOZBsixIitEP5gJWiDqvZerk0/QMZLN9OEKI\nIaFXWDBRDRWb+bM5Lham8/1SgE5QRzlOFNATeQMb1OuSjdeQ9npmXM5YcNhvCwaL\nOUZ7b55KnAevEpdyImnM9q8SiQKBgQDWjihNQmPtOXOuxkkcfbLsx7MRnfR3sIA/\nH36Kh179qIEk3cWTKQFRzdioDylm4dO0H/3AAJTdT0A3huelHqkxvpxsJB5Hne2Y\nRiVPm8+Ns8oFJBwTgLE8y7/LcpLWDS9gAADK2MmUgj9HKkGZRzQ1fW90ogBztkLz\nb/JIIYSB6wKBgQCfyWMXCCzjWT4ssjH6bqEFpIJhTxxR1YfWUGBgcBt9LakNjbHh\n1FSbRURy+/6hKO4ibVhUImYgQvLt9Ji2CAhYDjB/4isst90tqeUVqbLWwa66G3Hf\nUOOad0+I7MWaVbDUYNnRLkeNDcgBt20Z6cc4nzTY0tuRkTdWRwqEueR32QKBgFjV\nrUwn4/Xx5rsDsHvSc8Xj/Xma3AC+nKsGID+9QxBlt2sLQ+XlgX1cbItRE8RcVmpr\nIIZh90EWsjELc1gDtOw6zstbvQnMEvcMfCBVE//I5ClyxQkyLLBOcFANVUy5Utc9\nyRYz4mrR7t9JWLXdLHnFQOOau/MtENV4kWlaL2IXAoGALGFKCTn+RzIBe3wWyoH8\nta+iBuchAwXaxRQcpQsmefDGPaUulT82pdLK6c4UneZ5cPnkko2wRjogRMVmE0O9\nl0Owjb0lNYjRkbUwalyrKRahi8gC4MKsd/kyEk8tmzuV4IguxktWHKKI3SnkmuUL\n97pETIBFFFsfxyQ0m8bl3tw=\n-----END PRIVATE KEY-----\n",
    "client_email": "iki-bot-v4@project-keuangan-v4.iam.gserviceaccount.com",
    "client_id": "112117775587929019607",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/iki-bot-v4%40project-keuangan-v4.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

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

def excel_serial_to_iso(serial_str):
    """Convert Excel serial date number to YYYY-MM-DD string"""
    try:
        serial = float(serial_str)
        base = datetime(1899, 12, 30)
        dt = base + timedelta(days=serial)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        serial_str = str(serial_str).strip()
        if len(serial_str) == 10 and serial_str[4] == '-' and serial_str[7] == '-':
            return serial_str
        return serial_str

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
    for b in semua[1:]:
        if len(b) < 10:
            continue
        try:
            payment = int(float(b[8])) if b[8].strip() else 0
        except ValueError:
            payment = 0
        try:
            deposit = int(float(b[9])) if b[9].strip() else 0
        except ValueError:
            deposit = 0
        
        tgl_iso = excel_serial_to_iso(b[1])
        
        hasil.append({
            "akun": b[0].strip(), 
            "tgl": tgl_iso, 
            "jam": b[2].strip(), 
            "payee": b[3].strip(), 
            "memo": b[4].strip(), 
            "tag": b[5].strip(),
            "kategori": b[6].strip(), 
            "clr": b[7].strip(),
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
    """Baca anggaran dari sheet Budget, kolom sesuai bulan"""
    try:
        sheet_budget = sheet_utama.worksheet("Budget")
        data = sheet_budget.get_all_values()
        
        bulan_ini = now_wib().month
        col_index = bulan_ini
        
        for i, row in enumerate(data):
            if len(row) > col_index and row[0].strip() == kategori:
                val = row[col_index].strip()
                if val:
                    val_clean = val.replace(".", "").replace(",", ".")
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
    