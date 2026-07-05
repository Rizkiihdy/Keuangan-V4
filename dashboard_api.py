import os
import sys
import re
import time
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__, static_folder="dashboard/dist", static_url_path="")
CORS(app)

_gc = None
try:
    sys.path.insert(0, os.path.join(os.getcwd(), "bot"))
    from sheets_manager import gc
    _gc = gc
except Exception as _e:
    print(f"[WARN] Google Sheets not loaded: {_e}")

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
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

def get_sheet(name):
    if not _gc:
        raise RuntimeError("Google Sheets not connected")
    ss = _gc.open_by_key(SHEET_ID)
    return ss.worksheet(name).get_all_values()

def parse_rp(text):
    if not text or not isinstance(text, str):
        return 0
    cleaned = re.sub(r"[Rp\s\.]", "", str(text)).replace(",", ".")
    try:
        return int(float(cleaned))
    except:
        return 0

def parse_date(text):
    if not text:
        return None
    for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"]:
        try:
            return datetime.strptime(text.strip(), fmt)
        except:
            pass
    return None

def fmt_rp(n):
    return f"Rp{abs(int(n)):,}".replace(",", ".")

# ─── HEALTH ──────────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"ok": True})

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True, "ts": time.time()})

@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    _cache.clear()
    return jsonify({"ok": True})

# ─── OVERVIEW (Hero + Financial Health) ──────────────────────────────────────
@app.route("/api/overview")
@cached("overview", ttl=30)
def overview():
    rows = get_sheet("Transaksi")
    now = datetime.now()
    bulan_ini = now.strftime("%Y-%m")
    tahun_ini = now.year
    this_week = now.isocalendar()[1]

    pemasukan_bulan = 0
    pengeluaran_bulan = 0
    pemasukan_tahun = 0
    pengeluaran_tahun = 0
    pemasukan_minggu = 0
    pengeluaran_minggu = 0
    spending_cat = {}

    # Monthly cash flow (12 months)
    monthly = {}
    for i in range(12):
        d = (now.replace(day=1) - timedelta(days=i*28)).replace(day=1)
        key = d.strftime("%Y-%m")
        monthly[key] = {"income": 0, "expense": 0, "label": d.strftime("%b")}

    for r in rows[4:]:
        if not r or not r[0]:
            continue
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        cat = r[6].strip() if len(r) > 6 else ""
        mk = dt.strftime("%Y-%m")
        is_b = mk == bulan_ini
        is_t = dt.year == tahun_ini
        is_w = dt.isocalendar()[1] == this_week and dt.year == now.year

        if deposit > 0:
            if is_b: pemasukan_bulan += deposit
            if is_t: pemasukan_tahun += deposit
            if is_w: pemasukan_minggu += deposit
            if mk in monthly: monthly[mk]["income"] += deposit
        elif payment > 0 and cat != "[Transfer]":
            if is_b:
                pengeluaran_bulan += payment
                spending_cat[cat] = spending_cat.get(cat, 0) + payment
            if is_t: pengeluaran_tahun += payment
            if is_w: pengeluaran_minggu += payment
            if mk in monthly: monthly[mk]["expense"] += payment

    # Accounts
    akun_rows = get_sheet("Akun")
    total_saldo = 0
    akun_list = []
    for r in akun_rows[7:]:
        if not r or not r[0] or r[0].strip() in ("", "[42]"):
            continue
        bal = parse_rp(r[5]) if len(r) > 5 else 0
        total_saldo += bal
        akun_list.append({"nama": r[0].strip(), "balance": bal})

    # Goals
    goals_rows = get_sheet("Goals")
    total_tabungan = 0
    for r in goals_rows[4:]:
        if not r or len(r) < 9 or not r[4] or r[4].strip() in ("", "[42]"):
            continue
        total_tabungan += parse_rp(r[8])

    # Financial Health Score
    saving_rate = (pemasukan_bulan - pengeluaran_bulan) / pemasukan_bulan * 100 if pemasukan_bulan > 0 else 0
    expense_ratio = pengeluaran_bulan / pemasukan_bulan * 100 if pemasukan_bulan > 0 else 100
    cashflow = pemasukan_bulan - pengeluaran_bulan
    score = max(0, min(100, int(
        (saving_rate * 0.35) +
        (max(0, 100 - expense_ratio) * 0.35) +
        (50 if cashflow >= 0 else 20) * 0.30
    )))

    monthly_arr = sorted(monthly.items())
    return jsonify({
        "total_saldo": total_saldo,
        "total_tabungan": total_tabungan,
        "pemasukan_bulan": pemasukan_bulan,
        "pengeluaran_bulan": pengeluaran_bulan,
        "cashflow_bulan": cashflow,
        "pemasukan_tahun": pemasukan_tahun,
        "pengeluaran_tahun": pengeluaran_tahun,
        "pemasukan_minggu": pemasukan_minggu,
        "pengeluaran_minggu": pengeluaran_minggu,
        "saving_rate": round(saving_rate, 1),
        "expense_ratio": round(expense_ratio, 1),
        "financial_score": score,
        "spending_by_cat": sorted(spending_cat.items(), key=lambda x: x[1], reverse=True)[:8],
        "monthly_cashflow": [{"month": v["label"], "income": v["income"], "expense": v["expense"]} for _, v in monthly_arr],
        "bulan_ini": now.strftime("%B %Y"),
        "akun_list": akun_list[:5],
    })

# ─── AKUN ────────────────────────────────────────────────────────────────────
@app.route("/api/akun")
@cached("akun", ttl=60)
def akun():
    rows = get_sheet("Akun")
    transaksi_rows = get_sheet("Transaksi")
    now = datetime.now()
    bulan_ini = now.strftime("%Y-%m")

    # Build per-account monthly change
    akun_changes = {}
    for r in transaksi_rows[4:]:
        if not r or not r[0]:
            continue
        nama_akun = r[0].strip()
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt or dt.strftime("%Y-%m") != bulan_ini:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        if nama_akun not in akun_changes:
            akun_changes[nama_akun] = 0
        akun_changes[nama_akun] += deposit - payment

    data = []
    for r in rows[7:]:
        if not r or not r[0] or r[0].strip() in ("", "[42]"):
            continue
        nama = r[0].strip()
        bal = parse_rp(r[5]) if len(r) > 5 else 0
        data.append({
            "nama": nama,
            "balance": bal,
            "cleared": parse_rp(r[4]) if len(r) > 4 else 0,
            "perubahan_bulan": akun_changes.get(nama, 0),
        })
    return jsonify({"data": data})

# ─── TRANSAKSI ───────────────────────────────────────────────────────────────
@app.route("/api/transaksi")
@cached("transaksi", ttl=30)
def transaksi():
    rows = get_sheet("Transaksi")
    data = []
    for r in rows[4:]:
        if not r or not r[0]:
            continue
        akun = r[0].strip()
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt:
            continue
        memo = r[4].strip() if len(r) > 4 else ""
        cat = r[6].strip() if len(r) > 6 else ""
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        if cat == "[Transfer]":
            tipe = "Transfer"
        elif deposit > 0:
            tipe = "Pemasukan"
        else:
            tipe = "Pengeluaran"
        jumlah = deposit if deposit > 0 else payment
        data.append({
            "akun": akun,
            "tanggal": dt.strftime("%Y-%m-%d"),
            "tanggal_fmt": dt.strftime("%d %b %Y"),
            "memo": memo,
            "kategori": cat,
            "tipe": tipe,
            "jumlah": jumlah,
            "payment": payment,
            "deposit": deposit,
        })
    data.reverse()
    return jsonify({"data": data[:200], "total": len(data)})

# ─── BUDGET ──────────────────────────────────────────────────────────────────
@app.route("/api/budget")
@cached("budget", ttl=60)
def budget():
    rows = get_sheet("Budget")
    transaksi_rows = get_sheet("Transaksi")
    now = datetime.now()
    bulan_ini = now.strftime("%Y-%m")
    month_idx = now.month - 1  # 0-based

    # Actual spending this month per category
    actual = {}
    for r in transaksi_rows[4:]:
        if not r or not r[0]:
            continue
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt or dt.strftime("%Y-%m") != bulan_ini:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        cat = r[6].strip() if len(r) > 6 else ""
        if payment > 0 and cat and cat != "[Transfer]":
            actual[cat] = actual.get(cat, 0) + payment

    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    income = []
    expense = []
    in_income = False
    in_expense = False

    for r in rows:
        if not r:
            continue
        label = r[0].strip()
        if label == "INCOME CATEGORIES":
            in_income, in_expense = True, False
            continue
        if label == "EXPENSE CATEGORIES":
            in_income, in_expense = False, True
            continue
        if not label or label.startswith("[") or "TOTAL" in label or "NET" in label:
            continue
        budget_val = parse_rp(r[2 + month_idx]) if len(r) > 2 + month_idx else 0
        total = parse_rp(r[14]) if len(r) > 14 else 0
        item = {
            "nama": label,
            "budget_bulan": budget_val,
            "aktual": actual.get(label, 0),
            "sisa": budget_val - actual.get(label, 0),
            "total_tahun": total,
        }
        if in_income:
            income.append(item)
        elif in_expense:
            expense.append(item)

    return jsonify({"income": income, "expense": expense, "months": months, "bulan": months[month_idx]})

# ─── GOALS ───────────────────────────────────────────────────────────────────
@app.route("/api/goals")
@cached("goals", ttl=60)
def goals():
    rows = get_sheet("Goals")
    data = []
    for r in rows[4:]:
        if not r or len(r) < 9 or not r[4] or r[4].strip() in ("", "[42]"):
            continue
        nama = r[4].strip()
        target = parse_rp(r[6]) if len(r) > 6 else 0
        balance = parse_rp(r[8]) if len(r) > 8 else 0
        pct_str = r[7].strip() if len(r) > 7 else "0%"
        try:
            pct = float(pct_str.replace(",", ".").replace("%", "").strip())
        except:
            pct = (balance / target * 100) if target > 0 else 0
        data.append({
            "nama": nama,
            "target": target,
            "balance": balance,
            "persen": round(min(pct, 100), 1),
        })
    return jsonify({"data": data})

# ─── CASHFLOW CHART ──────────────────────────────────────────────────────────
@app.route("/api/cashflow")
@cached("cashflow", ttl=60)
def cashflow():
    rows = get_sheet("Transaksi")
    now = datetime.now()
    # Last 6 months
    months = {}
    for i in range(5, -1, -1):
        d = now.replace(day=1)
        for _ in range(i):
            d = (d - timedelta(days=1)).replace(day=1)
        mk = d.strftime("%Y-%m")
        months[mk] = {"label": d.strftime("%b '%y"), "income": 0, "expense": 0}

    daily_7 = {}
    for i in range(6, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_7[d] = {"label": (now - timedelta(days=i)).strftime("%d %b"), "total": 0}

    running_saldo = []
    saldo = 0

    for r in rows[4:]:
        if not r or not r[0]:
            continue
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        cat = r[6].strip() if len(r) > 6 else ""
        mk = dt.strftime("%Y-%m")
        dk = dt.strftime("%Y-%m-%d")

        if mk in months:
            if deposit > 0:
                months[mk]["income"] += deposit
            elif payment > 0 and cat != "[Transfer]":
                months[mk]["expense"] += payment

        if dk in daily_7 and payment > 0 and cat != "[Transfer]":
            daily_7[dk]["total"] += payment

        saldo += deposit - payment
        running_saldo.append({"tanggal": dk, "saldo": saldo})

    return jsonify({
        "monthly": list(months.values()),
        "daily_7": list(daily_7.values()),
        "running_saldo": running_saldo[-30:],
    })

# ─── WEEKLY REPORT ───────────────────────────────────────────────────────────
@app.route("/api/weekly")
@cached("weekly", ttl=120)
def weekly():
    rows = get_sheet("Weekly")
    data = {"header": {}, "summary": {}, "rows": []}
    for r in rows:
        if not r:
            continue
        if r[0] == "Week Begins":
            data["header"]["week_start"] = r[1]
        if r[0] == "BUDGET SUMMARY":
            continue
        if len(r) > 5 and r[4] and r[5]:
            data["rows"].append({"label": r[4], "value": r[5]})
    return jsonify(data)

# ─── LAPORAN BULANAN ─────────────────────────────────────────────────────────
@app.route("/api/laporan")
@cached("laporan", ttl=120)
def laporan():
    rows = get_sheet("Laporan")
    data = []
    for r in rows:
        if not r or not any(r):
            continue
        data.append(r)
    return jsonify({"rows": data[:50]})

# ─── INSIGHT (Sheets data) ────────────────────────────────────────────────────
@app.route("/api/insight")
@cached("insight", ttl=300)
def insight():
    rows = get_sheet("Insight")
    memo, payee, stats, top_w = [], [], {}, []
    section = None
    for r in rows[3:]:
        if not any(r):
            continue
        if r[0] == "Memo":
            section = "memo"
            continue
        if len(r) > 7 and r[7] == "Payee":
            section = "payee"
        if len(r) > 14 and r[14] == "Keterangan":
            section = "stats"
        if "TOP PENGELUARAN MINGGU INI" in str(r[0]):
            section = "top"
            continue
        if section == "memo" and r[0] and r[0] not in ("Memo",):
            memo.append({"nama": r[0], "total": parse_rp(r[1]), "frekuensi": r[2] if len(r) > 2 else "0"})
        if section in ("payee", "stats", "top") and len(r) > 7 and r[7] and r[7] not in ("Payee",):
            payee.append({"nama": r[7], "total": parse_rp(r[8]), "frekuensi": r[9] if len(r) > 9 else "0"})
        if len(r) > 15 and r[14] and r[15]:
            stats[r[14]] = r[15]
    return jsonify({"memo": memo[:10], "payee": payee[:10], "stats": stats})

# ─── AI INSIGHT (Gemini) ─────────────────────────────────────────────────────
@app.route("/api/ai-insight")
@cached("ai_insight", ttl=600)
def ai_insight():
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

        # Gather summary data
        rows = get_sheet("Transaksi")
        now = datetime.now()
        bulan_ini = now.strftime("%Y-%m")
        pemasukan = 0
        pengeluaran = 0
        spending_cat = {}
        for r in rows[4:]:
            if not r or not r[0]:
                continue
            dt = parse_date(r[1]) if len(r) > 1 else None
            if not dt or dt.strftime("%Y-%m") != bulan_ini:
                continue
            payment = parse_rp(r[8]) if len(r) > 8 else 0
            deposit = parse_rp(r[9]) if len(r) > 9 else 0
            cat = r[6].strip() if len(r) > 6 else ""
            if deposit > 0:
                pemasukan += deposit
            elif payment > 0 and cat != "[Transfer]":
                pengeluaran += payment
                spending_cat[cat] = spending_cat.get(cat, 0) + payment

        saving_rate = ((pemasukan - pengeluaran) / pemasukan * 100) if pemasukan > 0 else 0
        top_cats = sorted(spending_cat.items(), key=lambda x: x[1], reverse=True)[:5]

        prompt = f"""Kamu adalah Oliv, asisten keuangan pribadi yang cerdas dan ramah. Analisis kondisi keuangan bulan {now.strftime('%B %Y')} berikut dan berikan 5 insight singkat dalam Bahasa Indonesia yang actionable dan motivatif:

Data keuangan:
- Total Pemasukan: {fmt_rp(pemasukan)}
- Total Pengeluaran: {fmt_rp(pengeluaran)}
- Saving Rate: {saving_rate:.1f}%
- Top pengeluaran: {', '.join([f"{k}: {fmt_rp(v)}" for k, v in top_cats])}

Format: Berikan tepat 5 bullet point singkat (1-2 kalimat), mulai dengan emoji yang relevan. Fokus pada kondisi positif dan rekomendasi yang helpful. Jangan gunakan markdown bold/italic."""

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        insights_text = response.text.strip()
        lines = [l.strip() for l in insights_text.split("\n") if l.strip()]

        return jsonify({"insights": lines, "generated_at": now.isoformat()})
    except Exception as e:
        return jsonify({
            "insights": [
                "💡 Pantau pengeluaran harianmu untuk mencapai target tabungan lebih cepat.",
                "📊 Saving rate yang baik adalah minimal 20% dari pemasukan.",
                "🎯 Setiap transaksi yang dicatat membawa kamu lebih dekat ke financial freedom.",
                "💪 Konsistensi lebih penting dari jumlah — terus catat keuanganmu!",
                "🌱 Investasi terbaik dimulai dari memahami ke mana uangmu pergi.",
            ],
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        })

# ─── ACTIVITY FEED ────────────────────────────────────────────────────────────
@app.route("/api/activity")
@cached("activity", ttl=30)
def activity():
    rows = get_sheet("Transaksi")
    data = []
    for r in rows[4:]:
        if not r or not r[0]:
            continue
        dt = parse_date(r[1]) if len(r) > 1 else None
        if not dt:
            continue
        payment = parse_rp(r[8]) if len(r) > 8 else 0
        deposit = parse_rp(r[9]) if len(r) > 9 else 0
        memo = r[4].strip() if len(r) > 4 else ""
        cat = r[6].strip() if len(r) > 6 else ""
        akun = r[0].strip()
        if cat == "[Transfer]":
            tipe = "transfer"
            emoji = "🔄"
        elif deposit > 0:
            tipe = "income"
            emoji = "🟢"
        else:
            tipe = "expense"
            emoji = "🔴"
        data.append({
            "emoji": emoji,
            "tipe": tipe,
            "memo": memo or cat,
            "jumlah": deposit if deposit > 0 else payment,
            "akun": akun,
            "tanggal": dt.strftime("%Y-%m-%d"),
            "tanggal_fmt": dt.strftime("%d %b"),
        })
    data.reverse()
    return jsonify({"data": data[:20]})

# ─── SPA ─────────────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    dist = os.path.join(os.getcwd(), "dashboard", "dist")
    if path and os.path.exists(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    if os.path.exists(os.path.join(dist, "index.html")):
        return send_from_directory(dist, "index.html")
    return jsonify({"message": "Build dashboard dulu: cd dashboard && npm run build"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Oliv Dashboard API — port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
