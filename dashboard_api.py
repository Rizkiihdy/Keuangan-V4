import os
import sys
import re
import time
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder="dashboard/dist", static_url_path="")
CORS(app)

# Try to load sheets module; if it fails, still serve SPA but APIs will error gracefully
_gc = None
try:
    sys.path.insert(0, os.path.join(os.getcwd(), "bot"))
    from sheets_manager import gc
    _gc = gc
except Exception as _e:
    print(f"[WARN] Google Sheets not loaded: {_e}")

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")

def get_sheet(worksheet_name):
    if not _gc:
        raise RuntimeError("Google Sheets not connected")
    ss = _gc.open_by_key(SHEET_ID)
    return ss.worksheet(worksheet_name).get_all_values()

_cache = {}
CACHE_TTL = 60

def cached(key, ttl=CACHE_TTL):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = time.time()
            if key in _cache and now - _cache[key]["ts"] < ttl:
                return _cache[key]["data"]
            result = fn(*args, **kwargs)
            _cache[key] = {"data": result, "ts": now}
            return result
        return wrapper
    return decorator


def parse_rp(text):
    if not text or not isinstance(text, str):
        return 0
    cleaned = re.sub(r"[Rp\s]", "", text).replace(".", "").replace(",", ".")
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def parse_date(text):
    """Parse MM/DD/YYYY to YYYY-MM-DD"""
    if not text:
        return ""
    try:
        dt = datetime.strptime(text.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return text.strip()


# ─── HEALTH ───────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "oliv-dashboard"})


@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok", "ts": time.time()})


# ─── TRANSAKSI ──────────────────────────────────────────

@app.route("/api/transaksi")
@cached("transaksi", ttl=30)
def transaksi():
    rows = get_sheet("Transaksi")
    # Header is at row index 3 (4th row)
    # Akun, Tanggal, Num, Payee, Memo, Tag, Category, Clr, PAYMENT, DEPOSIT, Account Balance, Cleared Balance, BALANCE
    data = []
    for r in rows[4:]:
        if not any(r) or not r[0]:
            continue
        akun = r[0].strip()
        tanggal = parse_date(r[1].strip()) if len(r) > 1 else ""
        memo = r[4].strip() if len(r) > 4 else ""
        kategori = r[6].strip() if len(r) > 6 else ""
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0

        if not tanggal:
            continue

        tipe = "Transfer" if kategori == "[Transfer]" else ("Pemasukan" if deposit > 0 else "Pengeluaran")
        jumlah = deposit if deposit > 0 else payment

        data.append({
            "akun": akun,
            "tanggal": tanggal,
            "tanggal_raw": r[1].strip() if len(r) > 1 else "",
            "tipe": tipe,
            "jumlah": jumlah,
            "kategori": kategori,
            "memo": memo,
            "payment": payment,
            "deposit": deposit,
        })
    return jsonify({"data": data[-100:][::-1], "total": len(data)})


# ─── AKUN ─────────────────────────────────────────────

@app.route("/api/akun")
@cached("akun", ttl=60)
def akun():
    rows = get_sheet("Akun")
    data = []
    # Header at row 6 (0-indexed): ['Akun', '', 'Goal', '%', 'Cleared', 'Balance', '', '']
    for r in rows[7:]:
        if not r or not r[0]:
            continue
        nama = r[0].strip()
        if not nama or nama == "[42]":
            continue
        balance = parse_rp(r[5]) if len(r) > 5 else 0
        cleared = parse_rp(r[4]) if len(r) > 4 else 0
        goal = r[2].strip() if len(r) > 2 else ""
        data.append({
            "nama": nama,
            "balance": balance,
            "cleared": cleared,
            "goal": goal,
        })
    return jsonify({"data": data})


# ─── GOALS ────────────────────────────────────────────

@app.route("/api/goals")
@cached("goals", ttl=60)
def goals():
    rows = get_sheet("Goals")
    data = []
    # Data starts at row index 4
    # cols: empty(0-3), Fund(4), Location(5), Goal(6), %(7), Balance(8)
    for r in rows[4:]:
        if not r or len(r) < 9 or not r[4]:
            continue
        nama = r[4].strip()
        if not nama or nama == "[42]":
            continue
        target = parse_rp(r[6]) if len(r) > 6 else 0
        balance = parse_rp(r[8]) if len(r) > 8 else 0
        pct = r[7].strip() if len(r) > 7 else "0%"
        data.append({
            "nama": nama,
            "target": target,
            "balance": balance,
            "persen": pct,
        })
    return jsonify({"data": data})


# ─── BUDGET ───────────────────────────────────────────

@app.route("/api/budget")
@cached("budget", ttl=60)
def budget():
    rows = get_sheet("Budget")
    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    income = []
    expense = []

    in_income = False
    in_expense = False
    for r in rows:
        if not r:
            continue
        label = r[0].strip() if r else ""
        if label == "INCOME CATEGORIES":
            in_income = True
            in_expense = False
            continue
        if label == "EXPENSE CATEGORIES":
            in_income = False
            in_expense = True
            continue
        if not label or label.startswith("[") or "TOTAL" in label or "NET" in label:
            continue
        vals = []
        for i in range(12):
            val = parse_rp(r[2 + i]) if len(r) > 2 + i else 0
            vals.append(val)
        total = parse_rp(r[14]) if len(r) > 14 else sum(vals)
        item = {"nama": label, "total": total, "bulanan": vals}
        if in_income:
            income.append(item)
        elif in_expense:
            expense.append(item)

    return jsonify({"income": income, "expense": expense, "months": months})


# ─── INSIGHT ──────────────────────────────────────────

@app.route("/api/insight")
@cached("insight", ttl=300)
def insight():
    rows = get_sheet("Insight")
    memo_analysis = []
    payee_analysis = []
    stats = {}
    top_weekly = []

    section = None
    for r in rows:
        if not any(r):
            continue
        if "ANALISIS BERDASARKAN MEMO" in r[0]:
            section = "memo"
            continue
        if "ANALISIS BERDASARKAN PAYEE" in r[0]:
            section = "payee"
            continue
        if "STATISTIK KEBIASAAN" in r[0]:
            section = "stats"
            continue
        if "TOP PENGELUARAN MINGGU INI" in r[0] or "#1 Memo" in r[0]:
            section = "top_weekly"

        if r[0] == "Memo" or r[7] == "Payee" or r[14] == "Keterangan":
            continue

        if section == "memo" and r[0]:
            memo_analysis.append({
                "nama": r[0].strip(),
                "total": parse_rp(r[1]),
                "frekuensi": r[2].strip() if len(r) > 2 else "0",
            })
        if section == "payee" and len(r) > 7 and r[7]:
            payee_analysis.append({
                "nama": r[7].strip(),
                "total": parse_rp(r[8]),
                "frekuensi": r[9].strip() if len(r) > 9 else "0",
            })
        if section == "stats" and len(r) > 14 and r[14] and r[15]:
            stats[r[14].strip()] = r[15].strip()
        if section == "top_weekly" and r[14] and r[15]:
            top_weekly.append({
                "label": r[14].strip(),
                "nilai": r[15].strip(),
            })

    return jsonify({
        "memo_analysis": memo_analysis[:10],
        "payee_analysis": payee_analysis[:10],
        "stats": stats,
        "top_weekly": top_weekly[:5],
    })


# ─── OVERVIEW ─────────────────────────────────────────

@app.route("/api/overview")
@cached("overview", ttl=30)
def overview():
    rows = get_sheet("Transaksi")
    now = datetime.now()
    bulan_ini = now.strftime("%Y-%m")
    minggu_ini = now.isocalendar()[1]
    tahun_ini = now.strftime("%Y")

    total_pemasukan_bulan = 0
    total_pengeluaran_bulan = 0
    total_pemasukan_tahun = 0
    total_pengeluaran_tahun = 0
    total_pemasukan_minggu = 0
    total_pengeluaran_minggu = 0

    spending_by_cat = {}
    income_by_cat = {}

    for r in rows[4:]:
        if not any(r) or not r[0]:
            continue
        tanggal = parse_date(r[1].strip()) if len(r) > 1 else ""
        if not tanggal:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        kategori = r[6].strip() if len(r) > 6 else "Lainnya"

        dt = None
        try:
            dt = datetime.strptime(tanggal, "%Y-%m-%d")
        except:
            continue

        is_bulan = dt.strftime("%Y-%m") == bulan_ini
        is_tahun = dt.strftime("%Y") == tahun_ini
        is_minggu = dt.isocalendar()[1] == minggu_ini and dt.year == now.year

        if deposit > 0:
            if is_bulan:
                total_pemasukan_bulan += deposit
            if is_tahun:
                total_pemasukan_tahun += deposit
            if is_minggu:
                total_pemasukan_minggu += deposit
            income_by_cat[kategori] = income_by_cat.get(kategori, 0) + deposit
        elif payment > 0:
            if is_bulan:
                total_pengeluaran_bulan += payment
                spending_by_cat[kategori] = spending_by_cat.get(kategori, 0) + payment
            if is_tahun:
                total_pengeluaran_tahun += payment
            if is_minggu:
                total_pengeluaran_minggu += payment

    akun_rows = get_sheet("Akun")
    total_saldo = 0
    for r in akun_rows[7:]:
        if not r or not r[0]:
            continue
        if r[0].strip() == "[42]" or not r[0].strip():
            continue
        total_saldo += parse_rp(r[5]) if len(r) > 5 else 0

    goals_rows = get_sheet("Goals")
    total_goals = 0
    for r in goals_rows[4:]:
        if not r or len(r) < 9 or not r[4]:
            continue
        if r[4].strip() == "[42]" or not r[4].strip():
            continue
        total_goals += parse_rp(r[8]) if len(r) > 8 else 0

    cat_data = [{"kategori": k, "jumlah": v} for k, v in
                sorted(spending_by_cat.items(), key=lambda x: x[1], reverse=True)[:8]]

    return jsonify({
        "saldo_total": total_saldo,
        "tabungan_total": total_goals,
        "pemasukan_bulan": total_pemasukan_bulan,
        "pengeluaran_bulan": total_pengeluaran_bulan,
        "selisih_bulan": total_pemasukan_bulan - total_pengeluaran_bulan,
        "pemasukan_minggu": total_pemasukan_minggu,
        "pengeluaran_minggu": total_pengeluaran_minggu,
        "pemasukan_tahun": total_pemasukan_tahun,
        "pengeluaran_tahun": total_pengeluaran_tahun,
        "spending_by_kategori": cat_data,
        "income_by_kategori": [{"kategori": k, "jumlah": v} for k, v in income_by_cat.items()],
        "bulan_ini": now.strftime("%B %Y"),
    })


# ─── SPA ──────────────────────────────────────────────

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    dist = os.path.join(os.getcwd(), "dashboard", "dist")
    if path and os.path.exists(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    if os.path.exists(os.path.join(dist, "index.html")):
        return send_from_directory(dist, "index.html")
    return jsonify({"message": "Dashboard belum di-build. Jalankan: cd dashboard && npm run build"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Dashboard API running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
