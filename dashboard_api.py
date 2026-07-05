import os
import sys
import re
import time
from functools import wraps
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Health check endpoint MUST be first — before any import that might fail
app = Flask(__name__, static_folder="dashboard/dist", static_url_path="")
CORS(app)

@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "oliv-dashboard"})

# Try to load sheets module; if it fails, still serve SPA but APIs will error gracefully
_gc = None
_SPREADSHEETS = None
try:
    sys.path.insert(0, os.path.join(os.getcwd(), "bot"))
    from sheets_manager import gc, SPREADSHEETS
    _gc = gc
    _SPREADSHEETS = SPREADSHEETS
except Exception as _e:
    print(f"[WARN] Google Sheets not loaded: {_e}")

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
        return float(cleaned)
    except Exception:
        return 0


def parse_pct(text):
    if not text:
        return 0
    cleaned = text.replace("%", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except Exception:
        return 0


def parse_date(text):
    from datetime import datetime
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return text


def get_sheet(spreadsheet_key, worksheet_name):
    spec = SPREADSHEETS[spreadsheet_key]
    ss = gc.open_by_key(spec["id"])
    return ss.worksheet(worksheet_name).get_all_values()


@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok", "ts": time.time()})


@app.route("/api/transaksi")
@cached("transaksi", ttl=30)
def transaksi():
    rows = get_sheet("keuangan", "Transaksi")
    data = []
    for r in rows[5:]:
        if not any(r) or not r[0]:
            continue
        tanggal_raw = r[0].strip() if len(r) > 0 else ""
        tipe = r[1].strip() if len(r) > 1 else ""
        jumlah_raw = r[2].strip() if len(r) > 2 else ""
        kategori = r[3].strip() if len(r) > 3 else ""
        keterangan = r[4].strip() if len(r) > 4 else ""
        if not tanggal_raw or not jumlah_raw:
            continue
        data.append({
            "tanggal": parse_date(tanggal_raw),
            "tanggal_raw": tanggal_raw,
            "tipe": tipe,
            "jumlah": parse_rp(jumlah_raw),
            "jumlah_fmt": jumlah_raw,
            "kategori": kategori,
            "keterangan": keterangan,
        })
    return jsonify({"data": data, "total": len(data)})


@app.route("/api/anggaran")
@cached("anggaran", ttl=60)
def anggaran():
    rows = get_sheet("keuangan", "Anggaran")
    pengeluaran = []
    pemasukan = []
    months = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]

    in_pengeluaran = False
    in_pemasukan = False

    for r in rows:
        if not r:
            continue
        label = r[0].strip() if r else ""
        if "PENGELUARAN" in label and "TOTAL" not in label:
            in_pengeluaran = True
            in_pemasukan = False
            continue
        if "PEMASUKAN" in label and "TOTAL" not in label:
            in_pengeluaran = False
            in_pemasukan = True
            continue
        if "TOTAL" in label:
            continue
        if label.startswith("Kategori"):
            continue

        if in_pengeluaran and label and not label.startswith("NET"):
            anggaran_val = parse_rp(r[1]) if len(r) > 1 else 0
            month_vals = []
            for i, m in enumerate(months):
                val = parse_rp(r[2 + i]) if len(r) > 2 + i else 0
                month_vals.append({"bulan": m, "nilai": val})
            total_aktual = parse_rp(r[15]) if len(r) > 15 else 0
            pengeluaran.append({
                "kategori": label,
                "anggaran": anggaran_val,
                "total_aktual": total_aktual,
                "bulanan": month_vals,
            })

        if in_pemasukan and label and not label.startswith("NET"):
            month_vals = []
            for i, m in enumerate(months):
                val = parse_rp(r[2 + i]) if len(r) > 2 + i else 0
                month_vals.append({"bulan": m, "nilai": val})
            total_aktual = parse_rp(r[15]) if len(r) > 15 else 0
            pemasukan.append({
                "kategori": label,
                "total_aktual": total_aktual,
                "bulanan": month_vals,
            })

    return jsonify({"pengeluaran": pengeluaran, "pemasukan": pemasukan})


@app.route("/api/goals")
@cached("goals", ttl=60)
def goals():
    rows = get_sheet("keuangan", "Target Tabungan")
    data = []
    for r in rows[4:]:
        if not any(r):
            continue
        item = r[1].strip() if len(r) > 1 else ""
        if not item or item == "Item Tabungan":
            continue
        target = parse_rp(r[2]) if len(r) > 2 else 0
        terkumpul = parse_rp(r[3]) if len(r) > 3 else 0
        pct_raw = r[4].strip() if len(r) > 4 else "0%"
        status = r[5].strip() if len(r) > 5 else ""
        pct = parse_pct(pct_raw) if "%" in pct_raw else (terkumpul / target * 100 if target > 0 else 0)
        data.append({
            "nama": item,
            "target": target,
            "terkumpul": terkumpul,
            "persen": round(pct, 1),
            "status": status,
        })
    return jsonify({"data": data})


@app.route("/api/investasi")
@cached("investasi", ttl=60)
def investasi():
    rows = get_sheet("investasi", "Summary")
    accounts = []
    headers_found = False
    for r in rows:
        if not r:
            continue
        if r[0].strip() == "Tab Name":
            headers_found = True
            continue
        if headers_found and r[0].strip() and r[0].strip() not in ("", "Summary"):
            name = r[0].strip()
            invested = parse_rp(r[1]) if len(r) > 1 else 0
            value = parse_rp(r[2]) if len(r) > 2 else 0
            gl = parse_rp(r[3]) if len(r) > 3 else 0
            pct = parse_pct(r[4]) if len(r) > 4 else 0
            if invested > 0 or value > 0:
                accounts.append({
                    "nama": name,
                    "invested": invested,
                    "value": value,
                    "gain_loss": gl,
                    "persen": pct,
                })
    total_invested = sum(a["invested"] for a in accounts)
    total_value = sum(a["value"] for a in accounts)
    return jsonify({
        "accounts": accounts,
        "total_invested": total_invested,
        "total_value": total_value,
        "total_gain_loss": total_value - total_invested,
    })


@app.route("/api/kalkulator/rumah")
@cached("kalkulator_rumah", ttl=300)
def kalkulator_rumah():
    rows = get_sheet("home_affordability", "Affordability")
    data = {}
    for i, r in enumerate(rows):
        if not r:
            continue
        label = r[1].strip() if len(r) > 1 else ""
        val_d = r[3].strip() if len(r) > 3 else ""
        val_f = r[5].strip() if len(r) > 5 else ""
        if "Penghasilan Kotor" in label:
            data["penghasilan_tahunan"] = parse_rp(val_d)
            data["harga_rumah_estimasi"] = parse_rp(val_f)
        elif "Maksimum Biaya Rumah" in label or "Persentase" in label:
            data["pct_maks"] = val_d
        elif "Maksimum Cicilan Rumah" in label:
            data["cicilan_maks"] = parse_rp(val_d)
        elif "Cicilan Kendaraan" in label:
            data["cicilan_kendaraan"] = parse_rp(val_d)
        elif "Utang Lainnya" in label:
            data["utang_lain"] = parse_rp(val_d)
        elif "Dana Tersedia" in label or "Down Payment" in label or "Uang Muka" in label:
            data["dana_uang_muka"] = parse_rp(val_d)
    return jsonify(data)


@app.route("/api/kalkulator/kredit")
@cached("kalkulator_kredit", ttl=300)
def kalkulator_kredit():
    rows = get_sheet("simulasi_kredit", "Simulasi Kredit")
    data = {}
    for r in rows:
        if not r or len(r) < 2:
            continue
        label = r[0].strip()
        val = r[1].strip() if len(r) > 1 else ""
        val_r = r[5].strip() if len(r) > 5 else ""
        if "Harga Cash" in label:
            data["harga_cash"] = parse_rp(val)
        elif "Uang Muka" in label or "DP" in label:
            data["uang_muka"] = parse_rp(val)
        elif "Pokok Utang" in label:
            data["pokok_utang"] = parse_rp(val)
        elif "Tenor" in label:
            try:
                data["tenor_bulan"] = int(val.split()[0]) if val else 0
            except Exception:
                data["tenor_bulan"] = 0
        elif "Cicilan Bulanan" in label:
            data["cicilan_bulanan"] = parse_rp(val)
        elif "Total Uang Keluar" in label:
            data["total_keluar"] = parse_rp(val_r)
        elif "Total Beban Bunga" in label:
            data["total_bunga"] = parse_rp(val_r)
        elif "Suku Bunga Efektif per Tahun" in label:
            data["bunga_tahunan"] = val_r
    return jsonify(data)


@app.route("/api/kalkulator/pensiun")
@cached("kalkulator_pensiun", ttl=300)
def kalkulator_pensiun():
    rows = get_sheet("pensiun", "Retirement")
    data = {}
    for r in rows:
        if not r:
            continue
        row_str = " ".join(r)
        if "Usia Saat Ini" in row_str:
            for i, cell in enumerate(r):
                if "Usia Saat Ini" in cell and i + 1 < len(r):
                    try:
                        data["usia_sekarang"] = int(r[i + 1].strip())
                    except Exception:
                        pass
        if "Usia Pensiun" in row_str:
            for i, cell in enumerate(r):
                if "Usia Pensiun" in cell and i + 1 < len(r):
                    try:
                        data["usia_pensiun"] = int(r[i + 1].strip())
                    except Exception:
                        pass
        if "Gaji Saat Pensiun" in row_str or "Gaji Saat Ini" in row_str:
            for i, cell in enumerate(r):
                if ("Gaji Saat Pensiun" in cell or "Gaji Saat Ini" in cell) and i + 1 < len(r):
                    data["gaji_pensiun"] = parse_rp(r[i + 1])
        if "Dana Pensiun" in row_str and "Target" in row_str:
            for i, cell in enumerate(r):
                if "Dana Pensiun" in cell and i + 1 < len(r):
                    data["target_dana"] = parse_rp(r[i + 1])
        if "Tabungan" in row_str and "Saat Ini" in row_str:
            for i, cell in enumerate(r):
                if "Tabungan" in cell and "Saat Ini" in cell and i + 1 < len(r):
                    data["tabungan_sekarang"] = parse_rp(r[i + 1])
    return jsonify(data)


@app.route("/api/kalkulator/tabungan-pensiun")
@cached("kalkulator_tabungan_pensiun", ttl=300)
def kalkulator_tabungan_pensiun():
    rows = get_sheet("tabungan_pensiun", "401k")
    data = {}
    for r in rows:
        if not r:
            continue
        row_str = " ".join(r)
        if "Usia Saat Ini" in row_str:
            for i, cell in enumerate(r):
                if "Usia Saat Ini" in cell and i + 1 < len(r):
                    try:
                        data["usia_sekarang"] = int(r[i + 1].strip())
                    except Exception:
                        pass
        if "Usia Pensiun" in row_str:
            for i, cell in enumerate(r):
                if "Usia Pensiun" in cell and i + 1 < len(r):
                    try:
                        data["usia_pensiun"] = int(r[i + 1].strip())
                    except Exception:
                        pass
        if "Tahun Berinvestasi" in row_str:
            for i, cell in enumerate(r):
                if "Tahun Berinvestasi" in cell and i + 1 < len(r):
                    try:
                        data["tahun_investasi"] = int(r[i + 1].strip())
                    except Exception:
                        pass
        if "Saldo Tabungan Saat Ini" in row_str:
            for i, cell in enumerate(r):
                if "Saldo Tabungan Saat Ini" in cell and i + 1 < len(r):
                    data["saldo_sekarang"] = parse_rp(r[i + 1])
        if "Estimated Value" in row_str or "Nilai di Masa Depan" in row_str:
            for i, cell in enumerate(r):
                if ("Estimated Value" in cell or "Nilai di Masa Depan" in cell) and i + 1 < len(r):
                    data["nilai_masa_depan"] = parse_rp(r[i + 1])
        if "Kontribusi Bulanan" in row_str or "Iuran Bulanan" in row_str:
            for i, cell in enumerate(r):
                if ("Kontribusi" in cell or "Iuran" in cell) and i + 1 < len(r):
                    data["kontribusi_bulanan"] = parse_rp(r[i + 1])
        if "Return Tahunan" in row_str or "Expected Return" in row_str:
            for i, cell in enumerate(r):
                if "Return" in cell and i + 1 < len(r):
                    data["return_tahunan"] = r[i + 1].strip()
    return jsonify(data)


@app.route("/api/kalkulator/utang")
@cached("kalkulator_utang", ttl=30)
def kalkulator_utang():
    rows = get_sheet("utang", "Calculator")
    debts = []
    headers_row = -1
    for i, r in enumerate(rows):
        if r and r[0].strip() == "Baris":
            headers_row = i
            break

    if headers_row >= 0:
        for r in rows[headers_row + 1:]:
            if not r or not r[0].strip().isdigit():
                continue
            kreditur = r[1].strip() if len(r) > 1 else ""
            if not kreditur:
                continue
            sisa = parse_rp(r[2]) if len(r) > 2 else 0
            bunga = r[3].strip() if len(r) > 3 else "0%"
            min_pay = parse_rp(r[4]) if len(r) > 4 else 0
            if sisa > 0:
                debts.append({
                    "kreditur": kreditur,
                    "sisa_hutang": sisa,
                    "bunga_tahunan": bunga,
                    "min_pembayaran": min_pay,
                })

    total_hutang = sum(d["sisa_hutang"] for d in debts)
    total_min = sum(d["min_pembayaran"] for d in debts)
    return jsonify({
        "debts": debts,
        "total_hutang": total_hutang,
        "total_min_pembayaran": total_min,
    })


@app.route("/api/overview")
@cached("overview", ttl=30)
def overview():
    from datetime import datetime
    rows = get_sheet("keuangan", "Transaksi")
    total_pemasukan = 0
    total_pengeluaran = 0
    bulan_ini = datetime.now().strftime("%Y-%m")
    spending_by_cat = {}

    for r in rows[5:]:
        if not any(r) or not r[0]:
            continue
        tanggal = parse_date(r[0].strip() if r[0] else "")
        tipe = r[1].strip() if len(r) > 1 else ""
        jumlah = parse_rp(r[2]) if len(r) > 2 else 0
        kategori = r[3].strip() if len(r) > 3 else "Lainnya"
        if not tanggal:
            continue
        if tipe == "Pemasukan":
            total_pemasukan += jumlah
        elif tipe == "Pengeluaran":
            total_pengeluaran += jumlah
            if tanggal and tanggal.startswith(bulan_ini):
                spending_by_cat[kategori] = spending_by_cat.get(kategori, 0) + jumlah

    saldo = total_pemasukan - total_pengeluaran

    inv_rows = get_sheet("investasi", "Summary")
    total_investasi = 0
    headers_found = False
    for r in inv_rows:
        if not r:
            continue
        if r[0].strip() == "Tab Name":
            headers_found = True
            continue
        if headers_found and r[0].strip() and r[0].strip() not in ("", "Summary"):
            total_investasi += parse_rp(r[2]) if len(r) > 2 else 0

    cat_data = [{"kategori": k, "jumlah": v} for k, v in
                sorted(spending_by_cat.items(), key=lambda x: x[1], reverse=True)]

    return jsonify({
        "total_pemasukan": total_pemasukan,
        "total_pengeluaran": total_pengeluaran,
        "saldo_bersih": saldo,
        "total_investasi": total_investasi,
        "spending_by_kategori": cat_data,
    })


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    dist = os.path.join(os.getcwd(), "dashboard", "dist")
    if path and os.path.exists(os.path.join(dist, path)):
        return send_from_directory(dist, path)
    if os.path.exists(os.path.join(dist, "index.html")):
        return send_from_directory(dist, "index.html")
    return jsonify({"message": "Dashboard belum di-build. Jalankan: cd dashboard && pnpm build"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_PORT", 3001))
    print(f"Dashboard API running on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
