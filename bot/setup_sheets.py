"""
setup_sheets.py — Run once to build the full Indonesian finance system.
Tabs: Transaksi · Anggaran · Laporan Bulanan · Laporan Tahunan · Target Tabungan
"""

import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))

import gspread
from google.oauth2.service_account import Credentials
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, ALL_CATEGORIES,
    TRANSAKSI_HEADERS, TRANSAKSI_MAX_ROWS,
    TIPE_PEMASUKAN, TIPE_PENGELUARAN,
    OLD_TO_NEW_CATEGORY, OLD_TO_NEW_TYPE,
)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

R = TRANSAKSI_MAX_ROWS
MONTHS_ID = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des"]

# ── colours ───────────────────────────────────────────────────────────────────
def _c(r, g, b):
    return {"red": round(r/255,4), "green": round(g/255,4), "blue": round(b/255,4)}

WHITE        = _c(255,255,255);  NAVY    = _c( 26, 35,126)
INDIGO       = _c( 57, 73,171);  L_INDIGO= _c(232,234,246)
INC_DARK     = _c( 27, 94, 32);  INC_LIGHT=_c(232,245,233)
EXP_DARK     = _c(183, 28, 28);  EXP_LIGHT=_c(255,235,238)
AMAN_BG      = _c(200,230,201);  RAWAN_BG =_c(255,249,196);  OVER_BG=_c(255,205,210)
AMBER        = _c(245,127, 23);  GRAY_100 =_c(245,245,245);  GRAY_400=_c(189,189,189)
TEAL         = _c(  0,121,107);  TEAL_LIGHT=_c(178,223,219)
GRAY_700     = _c( 97, 97, 97)

IDR_FMT = {"type":"NUMBER","pattern":'"Rp "#,##0'}
PCT_FMT = {"type":"NUMBER","pattern":'0.0"%"'}

# ── API helpers ───────────────────────────────────────────────────────────────
def get_client():
    raw = os.environ.get("GOOGLE_CREDENTIALS_JSON","")
    if not raw: raise ValueError("GOOGLE_CREDENTIALS_JSON not set")
    creds = Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    return gspread.authorize(creds)

def send(sh, reqs):
    if reqs: sh.batch_update({"requests": reqs})

def gr(sid, r1, c1, r2, c2):
    return {"sheetId":sid,"startRowIndex":r1,"endRowIndex":r2,
            "startColumnIndex":c1,"endColumnIndex":c2}

def fmt(sid, r1, c1, r2, c2, **kw):
    cell = {}
    if "bg"     in kw: cell["backgroundColor"] = kw["bg"]
    tf = {}
    if "fg"     in kw: tf["foregroundColor"]   = kw["fg"]
    if "bold"   in kw: tf["bold"]              = kw["bold"]
    if "size"   in kw: tf["fontSize"]          = kw["size"]
    if "italic" in kw: tf["italic"]            = kw["italic"]
    if tf:             cell["textFormat"]      = tf
    if "halign" in kw: cell["horizontalAlignment"] = kw["halign"]
    if "valign" in kw: cell["verticalAlignment"]   = kw["valign"]
    if "numfmt" in kw: cell["numberFormat"]    = kw["numfmt"]
    if "wrap"   in kw: cell["wrapStrategy"]    = kw["wrap"]
    fields = ",".join(f for f in [
        "backgroundColor" if "bg" in kw else "",
        "textFormat" if tf else "",
        "horizontalAlignment" if "halign" in kw else "",
        "verticalAlignment"   if "valign" in kw else "",
        "numberFormat"        if "numfmt" in kw else "",
        "wrapStrategy"        if "wrap"   in kw else "",
    ] if f)
    return {"repeatCell":{"range":gr(sid,r1,c1,r2,c2),
                          "cell":{"userEnteredFormat":cell},
                          "fields":f"userEnteredFormat({fields})"}}

def merge(sid, r1, c1, r2, c2):
    return {"mergeCells":{"range":gr(sid,r1,c1,r2,c2),"mergeType":"MERGE_ALL"}}

def col_w(sid, col, px):
    return {"updateDimensionProperties":{
        "range":{"sheetId":sid,"dimension":"COLUMNS","startIndex":col,"endIndex":col+1},
        "properties":{"pixelSize":px},"fields":"pixelSize"}}

def row_h(sid, row, px):
    return {"updateDimensionProperties":{
        "range":{"sheetId":sid,"dimension":"ROWS","startIndex":row,"endIndex":row+1},
        "properties":{"pixelSize":px},"fields":"pixelSize"}}

def border(sid, r1, c1, r2, c2, color=None, style="SOLID"):
    color = color or GRAY_400
    b = {"style":style,"colorStyle":{"rgbColor":color}}
    return {"updateBorders":{"range":gr(sid,r1,c1,r2,c2),
        "top":b,"bottom":b,"left":b,"right":b,"innerHorizontal":b,"innerVertical":b}}

def freeze(sid, rows=0, cols=0):
    return {"updateSheetProperties":{
        "properties":{"sheetId":sid,"gridProperties":{
            "frozenRowCount":rows,"frozenColumnCount":cols}},
        "fields":"gridProperties.frozenRowCount,gridProperties.frozenColumnCount"}}

def dropdown(sid, r1, c1, r2, c2, values):
    return {"setDataValidation":{"range":gr(sid,r1,c1,r2,c2),
        "rule":{"condition":{"type":"ONE_OF_LIST",
                             "values":[{"userEnteredValue":v} for v in values]},
                "showCustomUi":True,"strict":True}}}

def cf_text(sid, r1, c1, r2, c2, text, bg):
    return {"addConditionalFormatRule":{
        "rule":{"ranges":[gr(sid,r1,c1,r2,c2)],
                "booleanRule":{
                    "condition":{"type":"TEXT_EQ","values":[{"userEnteredValue":text}]},
                    "format":{"backgroundColor":bg}}},
        "index":0}}

def get_or_create(sh, title, rows=1000, cols=20):
    for ws in sh.worksheets():
        if ws.title.lower() == title.lower():
            sh.del_worksheet(ws)
            print(f"    Deleted: '{ws.title}'")
            break
    return sh.add_worksheet(title=title, rows=rows, cols=cols)

# ── SUMPRODUCT formula builders ───────────────────────────────────────────────

def sp(cat_ref: str, month: int, tipe: str, year_expr: str) -> str:
    """SUMPRODUCT for Transaksi filtered by cat, month, type, year."""
    return (
        f"=SUMPRODUCT("
        f"(MONTH(Transaksi!$A$2:$A${R})={month})"
        f"*(YEAR(Transaksi!$A$2:$A${R})={year_expr})"
        f'*(Transaksi!$B$2:$B${R}="{tipe}")'
        f"*(Transaksi!$D$2:$D${R}={cat_ref})"
        f"*Transaksi!$C$2:$C${R})"
    )

def sp_all(month: int, tipe: str, year_expr: str) -> str:
    """SUMPRODUCT all rows of type in month/year."""
    return (
        f"=SUMPRODUCT("
        f"(MONTH(Transaksi!$A$2:$A${R})={month})"
        f"*(YEAR(Transaksi!$A$2:$A${R})={year_expr})"
        f'*(Transaksi!$B$2:$B${R}="{tipe}")'
        f"*Transaksi!$C$2:$C${R})"
    )

def sp_dyn(cat_ref: str, tipe: str) -> str:
    """SUMPRODUCT for Laporan Bulanan — month=$C$2, year=$E$2."""
    return (
        f"=SUMPRODUCT("
        f"(MONTH(Transaksi!$A$2:$A${R})=$C$2)"
        f"*(YEAR(Transaksi!$A$2:$A${R})=$E$2)"
        f'*(Transaksi!$B$2:$B${R}="{tipe}")'
        f"*(Transaksi!$D$2:$D${R}={cat_ref})"
        f"*Transaksi!$C$2:$C${R})"
    )

def sp_dyn_all(tipe: str) -> str:
    """SUMPRODUCT all rows of type — month=$C$2, year=$E$2."""
    return (
        f"=SUMPRODUCT("
        f"(MONTH(Transaksi!$A$2:$A${R})=$C$2)"
        f"*(YEAR(Transaksi!$A$2:$A${R})=$E$2)"
        f'*(Transaksi!$B$2:$B${R}="{tipe}")'
        f"*Transaksi!$C$2:$C${R})"
    )

# ── MIGRATION ─────────────────────────────────────────────────────────────────

OLD_H7 = ["Date","Time","Type","Amount","Category","Description","User"]

def _migrate(rows: list[list]) -> list[list]:
    result = []
    for r in rows:
        if not r or not any(r):
            continue
        try:
            # Detect 7-col old format (has Time column as HH:MM:SS)
            if len(r) >= 7 and ":" in str(r[1]):
                tanggal, tipe_old, jumlah_raw = r[0], r[2], r[3]
                kategori_old, keterangan = str(r[4]).strip(), str(r[5]).strip()
            elif len(r) >= 5:
                tanggal, tipe_old, jumlah_raw = r[0], r[1], r[2]
                kategori_old = str(r[3]).strip()
                keterangan   = str(r[4]).strip() if len(r) > 4 else ""
            else:
                continue

            tipe = OLD_TO_NEW_TYPE.get(str(tipe_old).strip())
            if not tipe:
                continue

            try:
                jumlah = float(str(jumlah_raw).replace(",","").replace(".","").strip())
                if jumlah <= 0:
                    continue
            except ValueError:
                continue

            kategori = OLD_TO_NEW_CATEGORY.get(kategori_old, "Lainnya")
            result.append([tanggal, tipe, jumlah, kategori, keterangan])
        except Exception:
            continue
    return result

# ── 1. TRANSAKSI ──────────────────────────────────────────────────────────────

def setup_transaksi(sh):
    print("  Setting up Transaksi...")
    saved_data: list[list] = []

    for ws in sh.worksheets():
        if ws.title.lower() == "transaksi":
            all_vals = ws.get_all_values()
            if len(all_vals) > 1:
                header, rows = all_vals[0], all_vals[1:]
                if header == TRANSAKSI_HEADERS:
                    saved_data = [r for r in rows if any(r)]
                    print(f"    Preserving {len(saved_data)} rows (current format).")
                elif header == OLD_H7 or (header and header[0] == "Date"):
                    saved_data = _migrate(rows)
                    print(f"    Migrated {len(saved_data)} rows from old format.")
            break

    ws  = get_or_create(sh, "Transaksi", rows=R, cols=6)
    sid = ws.id
    ws.update(values=[TRANSAKSI_HEADERS] + saved_data,
              range_name="A1", value_input_option="USER_ENTERED")

    reqs = [
        col_w(sid,0,110), col_w(sid,1,130), col_w(sid,2,145),
        col_w(sid,3,200), col_w(sid,4,360),
        fmt(sid,0,0,1,5, bg=NAVY, fg=WHITE, bold=True, size=10,
            halign="CENTER", valign="MIDDLE"),
        row_h(sid,0,36),
        fmt(sid,1,2,R,3, numfmt=IDR_FMT, halign="RIGHT"),
        freeze(sid, rows=1),
        dropdown(sid,1,1,R,2, [TIPE_PEMASUKAN, TIPE_PENGELUARAN]),
        dropdown(sid,1,3,R,4, ALL_CATEGORIES),
    ]
    send(sh, reqs)
    print("  ✓ Transaksi done.")
    return ws

# ── 2. ANGGARAN ───────────────────────────────────────────────────────────────

def _read_existing_budgets(sh) -> dict[str, float]:
    budgets: dict[str, float] = {}
    for ws in sh.worksheets():
        if ws.title == "Anggaran":
            for row in ws.get_all_values():
                if row and row[0] in EXPENSE_CATEGORIES and len(row) > 1:
                    try:
                        raw = str(row[1]).strip().replace(".","").replace(",","")
                        budgets[row[0]] = float(raw) if raw else 0.0
                    except ValueError:
                        pass
            break
    return budgets

def setup_anggaran(sh, existing_budgets: dict[str, float]):
    print("  Setting up Anggaran...")
    ws  = get_or_create(sh, "Anggaran", rows=50, cols=18)
    sid = ws.id

    # Layout (1-based rows):
    # 1=Title  2=Note  3=spacer  4=PENGELUARAN header  5=col-headers
    # 6-17=12 expense categories  18=TOTAL  19=spacer
    # 20=PEMASUKAN header  21=col-headers  22-24=3 income categories
    # 25=TOTAL PEMASUKAN  26=spacer  27=NET SAVINGS
    MONTH_HDRS = ["Kategori","Anggaran Bulanan"] + MONTHS_ID + ["Total Anggaran","Total Aktual","Selisih"]

    EXP_START = 6
    EXP_END   = EXP_START + len(EXPENSE_CATEGORIES) - 1   # 17
    EXP_TOTAL = EXP_END + 1                                # 18

    INC_START = 22
    INC_END   = INC_START + len(INCOME_CATEGORIES) - 1    # 24
    INC_TOTAL = INC_END + 1                                # 25

    # Rebuild expense rows
    exp_rows = []
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        r = EXP_START + i
        budget = existing_budgets.get(cat, 0)
        mf = [sp(f"$A{r}", m+1, TIPE_PENGELUARAN, "YEAR(TODAY())") for m in range(12)]
        exp_rows.append([cat, budget] + mf + [f"=B{r}*12", f"=SUM(C{r}:N{r})", f"=O{r}-P{r}"])

    exp_total_row = (
        ["TOTAL PENGELUARAN", f"=SUM(B{EXP_START}:B{EXP_END})"] +
        [f"=SUM({chr(67+m)}{EXP_START}:{chr(67+m)}{EXP_END})" for m in range(12)] +
        [f"=SUM(O{EXP_START}:O{EXP_END})",
         f"=SUM(P{EXP_START}:P{EXP_END})",
         f"=SUM(Q{EXP_START}:Q{EXP_END})"]
    )

    inc_rows = []
    for i, cat in enumerate(INCOME_CATEGORIES):
        r = INC_START + i
        mf = [sp(f"$A{r}", m+1, TIPE_PEMASUKAN, "YEAR(TODAY())") for m in range(12)]
        inc_rows.append([cat, ""] + mf + ["", f"=SUM(C{r}:N{r})", ""])

    inc_total_row = (
        ["TOTAL PEMASUKAN", ""] +
        [f"=SUM({chr(67+m)}{INC_START}:{chr(67+m)}{INC_END})" for m in range(12)] +
        ["", f"=SUM(P{INC_START}:P{INC_END})", ""]
    )

    net_savings_row = ["💙 NET SAVINGS (Pemasukan − Pengeluaran)", ""] + [""]*12 + [
        "", f"=P{INC_TOTAL}-P{EXP_TOTAL}", ""
    ]

    sheet_data = (
        [["📋 ANGGARAN TAHUNAN"]]                                          +  # 1
        [["ℹ️  Isi kolom B (Anggaran Bulanan) per kategori. Aktual otomatis."]] +  # 2
        [[""]]                                                              +  # 3
        [["📉 PENGELUARAN"]]                                                +  # 4
        [MONTH_HDRS]                                                        +  # 5
        exp_rows                                                            +  # 6-17
        [exp_total_row]                                                     +  # 18
        [[""]]                                                              +  # 19
        [["📈 PEMASUKAN"]]                                                  +  # 20
        [["Kategori","","Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des","","Total Aktual",""]]  +  # 21
        inc_rows                                                            +  # 22-24
        [inc_total_row]                                                     +  # 25
        [[""]]                                                              +  # 26
        [net_savings_row]                                                      # 27
    )

    ws.update(values=sheet_data, range_name="A1", value_input_option="USER_ENTERED")

    # ── formatting ──────────────────────────────────────────────────────────
    ncols = 17  # A-Q
    reqs  = []

    # Column widths
    reqs += [col_w(sid,0,180)]   # A: Kategori
    reqs += [col_w(sid,1,145)]   # B: Anggaran Bulanan
    reqs += [col_w(sid,c,80) for c in range(2,14)]  # C-N: months
    reqs += [col_w(sid,14,130), col_w(sid,15,130), col_w(sid,16,110)]  # O,P,Q

    # Title
    reqs += [merge(sid,0,0,1,ncols),
             fmt(sid,0,0,1,ncols, bg=NAVY, fg=WHITE, bold=True, size=14,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,0,48)]

    # Note
    reqs += [merge(sid,1,0,2,ncols),
             fmt(sid,1,0,2,ncols, bg=L_INDIGO, fg=INDIGO, italic=True, size=9)]

    # Section headers
    for row_i, bg in [(3, EXP_DARK), (19, INC_DARK)]:
        reqs += [merge(sid,row_i,0,row_i+1,ncols),
                 fmt(sid,row_i,0,row_i+1,ncols, bg=bg, fg=WHITE, bold=True, size=11,
                     halign="LEFT", valign="MIDDLE"),
                 row_h(sid,row_i,36)]

    # Column header rows (row 5 = index 4, row 21 = index 20)
    for hi in [4, 20]:
        reqs += [fmt(sid,hi,0,hi+1,ncols, bg=INDIGO, fg=WHITE, bold=True, size=9,
                     halign="CENTER", valign="MIDDLE"),
                 row_h(sid,hi,32)]

    # Expense data rows
    for i in range(len(EXPENSE_CATEGORIES)):
        ri = 5 + i  # 0-indexed row
        bg = GRAY_100 if i % 2 == 0 else WHITE
        reqs += [fmt(sid,ri,0,ri+1,1, bg=bg, bold=True, size=10),
                 fmt(sid,ri,1,ri+1,15, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=9),
                 fmt(sid,ri,15,ri+1,17, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=9)]

    # Totals rows
    for ti in [EXP_TOTAL-1, INC_TOTAL-1]:  # 0-indexed
        reqs += [fmt(sid,ti,0,ti+1,ncols, bg=NAVY, fg=WHITE, bold=True, size=10,
                     numfmt=IDR_FMT, halign="RIGHT")]

    # Income data rows
    for i in range(len(INCOME_CATEGORIES)):
        ri = 21 + i
        bg = INC_LIGHT if i % 2 == 0 else WHITE
        reqs += [fmt(sid,ri,0,ri+1,1, bg=bg, bold=True, size=10),
                 fmt(sid,ri,2,ri+1,14, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=9),
                 fmt(sid,ri,15,ri+1,16, bg=bg, numfmt=IDR_FMT, halign="RIGHT", bold=True, size=9)]

    # Net savings row
    reqs += [fmt(sid,26,0,27,ncols, bg=TEAL, fg=WHITE, bold=True, size=11,
                 numfmt=IDR_FMT, halign="RIGHT")]

    # Anggaran Bulanan editable column: light yellow bg to signal user input
    reqs += [fmt(sid,5,1,5+len(EXPENSE_CATEGORIES),2, bg={"red":1,"green":0.98,"blue":0.8})]

    # Borders around expense table
    reqs += [border(sid,4,0,EXP_TOTAL,ncols),
             border(sid,20,0,INC_TOTAL,ncols)]

    # Conditional formatting for Q column (selisih): green=positive, red=negative
    reqs += [
        cf_text(sid,5,16,EXP_TOTAL-1,17,"", GRAY_100),  # placeholder
    ]

    reqs += [freeze(sid, rows=5)]

    send(sh, reqs)
    print("  ✓ Anggaran done.")
    return ws

# ── 3. LAPORAN BULANAN ────────────────────────────────────────────────────────

def setup_laporan_bulanan(sh):
    print("  Setting up Laporan Bulanan...")
    ws  = get_or_create(sh, "Laporan Bulanan", rows=50, cols=8)
    sid = ws.id

    # Layout (1-based row numbers):
    # 1: Title
    # 2: Month/year selectors
    # 3: spacer
    # 4: RINGKASAN header
    # 5: Pemasukan bulan ini
    # 6: Pengeluaran bulan ini
    # 7: Saldo
    # 8: spacer
    # 9: Table headers
    # 10-21: 12 expense categories
    # 22: TOTAL
    # 23: spacer
    # 24: note

    CAT_START = 10
    CAT_END   = CAT_START + len(EXPENSE_CATEGORIES) - 1  # 21
    TOTAL_ROW = CAT_END + 1                               # 22

    INCOME_F = sp_dyn_all(TIPE_PEMASUKAN)
    EXPENSE_F = f"=SUM(D{CAT_START}:D{CAT_END})"
    SALDO_F   = "=D5-D6"

    # Category rows
    cat_rows = []
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        r = CAT_START + i
        cat_rows.append([
            cat,
            f"=IFERROR(VLOOKUP(B{r};Anggaran!$A:$B;2;0);0)",
            sp_dyn(f"$B{r}", TIPE_PENGELUARAN),
            f"=IF(C{r}=0;0;C{r}-D{r})",
            f"=IF(C{r}=0;0;D{r}/C{r}*100)",
            f'=IF(C{r}=0;"Aman";IF(F{r}>=100;"Over";IF(F{r}>=85;"Rawan";"Aman")))',
        ])

    total_row = [
        "TOTAL",
        f"=SUM(C{CAT_START}:C{CAT_END})",
        f"=SUM(D{CAT_START}:D{CAT_END})",
        f"=SUM(E{CAT_START}:E{CAT_END})",
        f"=IF(C{TOTAL_ROW}=0;0;D{TOTAL_ROW}/C{TOTAL_ROW}*100)",
        "",
    ]

    sheet_data = (
        [["📅 LAPORAN BULANAN"]]                             +  # 1
        [["Bulan:", "", "=MONTH(TODAY())", "Tahun:", "=YEAR(TODAY())"]] +  # 2
        [[""]]                                               +  # 3
        [["📊 RINGKASAN BULAN INI"]]                         +  # 4
        [["💚 Pemasukan:", "", "", INCOME_F]]                +  # 5
        [["❤️  Pengeluaran:", "", "", EXPENSE_F]]            +  # 6
        [["💙 Saldo:", "", "", SALDO_F]]                     +  # 7
        [[""]]                                               +  # 8
        [["Kategori","Anggaran Bulanan","Aktual","Selisih","% Terpakai","Status"]] +  # 9
        cat_rows                                             +  # 10-21
        [total_row]                                          +  # 22
        [[""]]                                               +  # 23
        [["💡 Ganti Bulan: ubah angka di C2. Atur anggaran di tab 'Anggaran'."]]  # 24
    )

    ws.update(values=sheet_data, range_name="B1", value_input_option="USER_ENTERED")

    # ── formatting ──────────────────────────────────────────────────────────
    reqs = []

    # Column widths: A=margin, B=cat, C=anggaran, D=aktual, E=selisih, F=pct, G=status
    widths = [18, 185, 145, 145, 120, 100, 100]
    reqs += [col_w(sid,i,w) for i,w in enumerate(widths)]

    # Title (row 1, index 0)
    reqs += [merge(sid,0,1,1,7),
             fmt(sid,0,1,1,7, bg=NAVY, fg=WHITE, bold=True, size=14,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,0,48)]

    # Selector row (row 2, index 1)
    reqs += [fmt(sid,1,1,2,7, bg=L_INDIGO, fg=INDIGO, bold=True, size=10),
             row_h(sid,1,34)]

    # Dropdown for month selector: C2 = column index 2, row index 1
    reqs += [dropdown(sid,1,2,2,3, [str(i) for i in range(1,13)])]

    # Ringkasan header (row 4, index 3)
    reqs += [merge(sid,3,1,4,7),
             fmt(sid,3,1,4,7, bg=INDIGO, fg=WHITE, bold=True, size=10,
                 halign="LEFT", valign="MIDDLE"),
             row_h(sid,3,32)]

    # Summary value rows (5-7, index 4-6): values in D (index 3)
    reqs += [fmt(sid,4,1,7,4, bg=INC_LIGHT, fg=INC_DARK, bold=True, size=10),
             fmt(sid,4,3,5,4, bg=INC_LIGHT, fg=INC_DARK, bold=True, size=13,
                 numfmt=IDR_FMT, halign="RIGHT"),
             fmt(sid,5,3,6,4, bg=EXP_LIGHT, fg=EXP_DARK, bold=True, size=13,
                 numfmt=IDR_FMT, halign="RIGHT"),
             fmt(sid,6,3,7,4, bg=TEAL_LIGHT, fg=TEAL, bold=True, size=13,
                 numfmt=IDR_FMT, halign="RIGHT"),
             fmt(sid,5,1,6,4, bg=EXP_LIGHT, fg=EXP_DARK, bold=True, size=10),
             fmt(sid,6,1,7,4, bg=TEAL_LIGHT, fg=TEAL, bold=True, size=10)]

    # Table header row (9, index 8)
    reqs += [fmt(sid,8,1,9,7, bg=NAVY, fg=WHITE, bold=True, size=10,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,8,34)]

    # Category data rows (10-21, index 9-20)
    for i in range(len(EXPENSE_CATEGORIES)):
        ri = 9 + i
        bg = GRAY_100 if i % 2 == 0 else WHITE
        reqs += [
            fmt(sid,ri,1,ri+1,2, bg=bg, bold=True, size=10),
            fmt(sid,ri,2,ri+1,5, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=10),
            fmt(sid,ri,5,ri+1,6, bg=bg, numfmt=PCT_FMT, halign="CENTER", size=10),
            fmt(sid,ri,6,ri+1,7, bg=bg, bold=True, halign="CENTER", size=10),
        ]

    # Total row (22, index 21)
    reqs += [fmt(sid,21,1,22,7, bg=NAVY, fg=WHITE, bold=True, size=10,
                 numfmt=IDR_FMT, halign="RIGHT")]

    # Note row (24, index 23)
    reqs += [merge(sid,23,1,24,7),
             fmt(sid,23,1,24,7, bg=L_INDIGO, fg=INDIGO, italic=True, size=9)]

    # Borders
    reqs += [border(sid,8,1,TOTAL_ROW,7)]

    # Conditional formatting for Status column (G = index 6)
    CF_ROWS_START = 9  # 0-indexed
    CF_ROWS_END   = 21
    reqs += [
        cf_text(sid,CF_ROWS_START,6,CF_ROWS_END,7,"Aman",  AMAN_BG),
        cf_text(sid,CF_ROWS_START,6,CF_ROWS_END,7,"Rawan", RAWAN_BG),
        cf_text(sid,CF_ROWS_START,6,CF_ROWS_END,7,"Over",  OVER_BG),
    ]

    reqs += [freeze(sid, rows=9)]
    send(sh, reqs)
    print("  ✓ Laporan Bulanan done.")
    return ws

# ── 4. LAPORAN TAHUNAN ────────────────────────────────────────────────────────

def setup_laporan_tahunan(sh):
    print("  Setting up Laporan Tahunan...")
    ws  = get_or_create(sh, "Laporan Tahunan", rows=50, cols=16)
    sid = ws.id

    # Layout (1-based):
    # 1: Title
    # 2: "Tahun:" [C2=YEAR(TODAY())]
    # 3: spacer
    # 4: "📉 PENGELUARAN"
    # 5: headers: Kategori | Jan | ... | Des | Total
    # 6-17: 12 expense categories
    # 18: TOTAL PENGELUARAN
    # 19: spacer
    # 20: "📈 PEMASUKAN"
    # 21: headers
    # 22-24: 3 income categories
    # 25: TOTAL PEMASUKAN
    # 26: spacer
    # 27: NET SAVINGS

    EXP_START = 6; EXP_END = EXP_START + len(EXPENSE_CATEGORIES) - 1  # 17
    EXP_TOTAL = EXP_END + 1  # 18
    INC_START = 22; INC_END = INC_START + len(INCOME_CATEGORIES) - 1  # 24
    INC_TOTAL = INC_END + 1  # 25
    NET_ROW   = 27

    HDR = ["Kategori"] + MONTHS_ID + ["Total"]

    # Expense rows: category | Jan-Dec SUMPRODUCT | SUM
    exp_rows = []
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        r = EXP_START + i
        mf = [sp(f"$B{r}", m+1, TIPE_PENGELUARAN, "$C$2") for m in range(12)]
        exp_rows.append([cat] + mf + [f"=SUM(C{r}:N{r})"])

    # Expense total row
    exp_total_row = (
        ["TOTAL PENGELUARAN"] +
        [f"=SUM({chr(67+m)}{EXP_START}:{chr(67+m)}{EXP_END})" for m in range(12)] +
        [f"=SUM(O{EXP_START}:O{EXP_END})"]
    )

    # Income rows
    inc_rows = []
    for i, cat in enumerate(INCOME_CATEGORIES):
        r = INC_START + i
        mf = [sp(f"$B{r}", m+1, TIPE_PEMASUKAN, "$C$2") for m in range(12)]
        inc_rows.append([cat] + mf + [f"=SUM(C{r}:N{r})"])

    # Income total row
    inc_total_row = (
        ["TOTAL PEMASUKAN"] +
        [f"=SUM({chr(67+m)}{INC_START}:{chr(67+m)}{INC_END})" for m in range(12)] +
        [f"=SUM(O{INC_START}:O{INC_END})"]
    )

    net_row = ["💙 SALDO BERSIH TAHUNAN"] + [""]*12 + [f"=O{INC_TOTAL}-O{EXP_TOTAL}"]

    sheet_data = (
        [["📊 LAPORAN TAHUNAN"]]                               +  # 1
        [["Tahun:", "=YEAR(TODAY())"]]                         +  # 2
        [[""]]                                                 +  # 3
        [["📉 PENGELUARAN"]]                                   +  # 4
        [HDR]                                                  +  # 5
        exp_rows                                               +  # 6-17
        [exp_total_row]                                        +  # 18
        [[""]]                                                 +  # 19
        [["📈 PEMASUKAN"]]                                     +  # 20
        [HDR]                                                  +  # 21
        inc_rows                                               +  # 22-24
        [inc_total_row]                                        +  # 25
        [[""]]                                                 +  # 26
        [net_row]                                              +  # 27
        [["💡 Ganti Tahun: ubah angka di C2."]]               +  # 28
        [[""]]                                                    # 29
    )

    # Data starts at column B (index 1) for all rows
    ws.update(values=sheet_data, range_name="B1", value_input_option="USER_ENTERED")

    # ── formatting ──────────────────────────────────────────────────────────
    reqs = []
    NCOLS = 15  # B-P (indices 1-15)

    reqs += [col_w(sid,0,18), col_w(sid,1,185)]  # margin + Kategori
    reqs += [col_w(sid,c,72) for c in range(2,14)]  # months
    reqs += [col_w(sid,14,110)]  # Total

    # Title
    reqs += [merge(sid,0,1,1,15),
             fmt(sid,0,1,1,15, bg=NAVY, fg=WHITE, bold=True, size=14,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,0,48)]

    # Year selector row
    reqs += [fmt(sid,1,1,2,4, bg=L_INDIGO, fg=INDIGO, bold=True, size=11),
             row_h(sid,1,34)]

    # Section headers (rows 4, 20 — index 3, 19)
    for ri, bg in [(3, EXP_DARK), (19, INC_DARK)]:
        reqs += [merge(sid,ri,1,ri+1,15),
                 fmt(sid,ri,1,ri+1,15, bg=bg, fg=WHITE, bold=True, size=11,
                     halign="LEFT", valign="MIDDLE"),
                 row_h(sid,ri,34)]

    # Column header rows (5, 21 — index 4, 20)
    for hi in [4, 20]:
        reqs += [fmt(sid,hi,1,hi+1,15, bg=INDIGO, fg=WHITE, bold=True, size=9,
                     halign="CENTER", valign="MIDDLE"),
                 row_h(sid,hi,30)]

    # Expense data rows
    for i in range(len(EXPENSE_CATEGORIES)):
        ri = 5 + i
        bg = GRAY_100 if i % 2 == 0 else WHITE
        reqs += [fmt(sid,ri,1,ri+1,2, bg=bg, bold=True, size=9),
                 fmt(sid,ri,2,ri+1,15, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=9)]

    # Income data rows
    for i in range(len(INCOME_CATEGORIES)):
        ri = 21 + i
        bg = INC_LIGHT if i % 2 == 0 else WHITE
        reqs += [fmt(sid,ri,1,ri+1,2, bg=bg, bold=True, size=9),
                 fmt(sid,ri,2,ri+1,15, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=9)]

    # Totals rows
    for ti in [EXP_TOTAL-1, INC_TOTAL-1]:
        reqs += [fmt(sid,ti,1,ti+1,15, bg=NAVY, fg=WHITE, bold=True,
                     numfmt=IDR_FMT, halign="RIGHT", size=10)]

    # Net savings row
    reqs += [fmt(sid,NET_ROW-1,1,NET_ROW,15, bg=TEAL, fg=WHITE, bold=True,
                 numfmt=IDR_FMT, halign="RIGHT", size=11)]

    # Borders
    reqs += [border(sid,4,1,EXP_TOTAL,15),
             border(sid,20,1,INC_TOTAL,15)]

    reqs += [freeze(sid, rows=5)]
    send(sh, reqs)
    print("  ✓ Laporan Tahunan done.")
    return ws

# ── 5. TARGET TABUNGAN ────────────────────────────────────────────────────────

def setup_target_tabungan(sh):
    print("  Setting up Target Tabungan...")
    ws  = get_or_create(sh, "Target Tabungan", rows=50, cols=8)
    sid = ws.id

    CAT_START = 5  # 1-based first goal row

    GOALS = [
        ("Rumah",         500_000_000),
        ("Umroh",          30_000_000),
        ("Mobil",         200_000_000),
        ("Dana Darurat",   50_000_000),
        ("Liburan",        10_000_000),
        ("Laptop/Gadget",  15_000_000),
        ("Nikah",          80_000_000),
        ("Investasi",     100_000_000),
        ("Pendidikan",     50_000_000),
        ("Lainnya",        20_000_000),
    ]

    goal_rows = []
    for i, (name, target) in enumerate(GOALS):
        r = CAT_START + i
        goal_rows.append([
            name, target, 0,
            f"=IF(C{r}=0;0;IFERROR(D{r}/C{r}*100;0))",
            f'=IF(D{r}=0;"Belum Mulai";IF(D{r}>=C{r};"Tercapai! 🎉";IF(D{r}/C{r}>=0.75;"Hampir Sampai 💪";IF(D{r}/C{r}>=0.5;"Setengah Jalan 🚀";"Baru Mulai ✨"))))',
        ])

    CAT_END = CAT_START + len(GOALS) - 1

    sheet_data = (
        [["🎯 TARGET TABUNGAN"]]                                               +  # 1
        [["💡 Isi kolom 'Terkumpul' secara manual. Target & Progress otomatis."]] +  # 2
        [[""]]                                                                  +  # 3
        [["Item Tabungan","Target (Rp)","Terkumpul (Rp)","% Progress","Status"]] +  # 4
        goal_rows                                                               +  # 5-14
        [[""]]                                                                  +  # 15
        [["💡 Tambahkan baris baru di bawah untuk goal tambahan."]]               # 16
    )

    ws.update(values=sheet_data, range_name="B1", value_input_option="USER_ENTERED")

    reqs = []
    NCOLS_T = 6  # B-G

    reqs += [col_w(sid,0,18), col_w(sid,1,185), col_w(sid,2,155),
             col_w(sid,3,155), col_w(sid,4,110), col_w(sid,5,170)]

    # Title
    reqs += [merge(sid,0,1,1,6),
             fmt(sid,0,1,1,6, bg=NAVY, fg=WHITE, bold=True, size=14,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,0,48)]

    # Note
    reqs += [merge(sid,1,1,2,6),
             fmt(sid,1,1,2,6, bg=L_INDIGO, fg=INDIGO, italic=True, size=9)]

    # Header row (row 4, index 3)
    reqs += [fmt(sid,3,1,4,6, bg=INDIGO, fg=WHITE, bold=True, size=10,
                 halign="CENTER", valign="MIDDLE"),
             row_h(sid,3,34)]

    # Data rows
    for i in range(len(GOALS)):
        ri = 4 + i
        bg = GRAY_100 if i % 2 == 0 else WHITE
        reqs += [
            fmt(sid,ri,1,ri+1,2, bg=bg, bold=True, size=10),
            fmt(sid,ri,2,ri+1,4, bg=bg, numfmt=IDR_FMT, halign="RIGHT", size=10),
            fmt(sid,ri,4,ri+1,5, bg=bg, numfmt=PCT_FMT, halign="CENTER", size=10),
            fmt(sid,ri,5,ri+1,6, bg=bg, bold=True, halign="CENTER", size=10),
            row_h(sid,ri,32),
        ]

    # Make "Terkumpul" column (D, index 3) editable-looking (light yellow bg)
    reqs += [fmt(sid,4,3,4+len(GOALS),4, bg={"red":1,"green":0.98,"blue":0.8})]

    # Borders
    reqs += [border(sid,3,1,CAT_END,6)]

    # Conditional formatting for Status column (F, index 5)
    S0, S1 = 4, 4 + len(GOALS)
    for text, bg in [("Tercapai! 🎉", AMAN_BG), ("Hampir Sampai 💪", AMAN_BG),
                     ("Setengah Jalan 🚀", RAWAN_BG), ("Baru Mulai ✨", RAWAN_BG),
                     ("Belum Mulai", {"red":0.9,"green":0.9,"blue":0.9})]:
        reqs += [cf_text(sid, S0, 5, S1, 6, text, bg)]

    reqs += [freeze(sid, rows=4)]
    send(sh, reqs)
    print("  ✓ Target Tabungan done.")
    return ws

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to Google Sheets...")
    gc = get_client()
    sh = gc.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    print(f"Opened: {sh.title}\n")

    # Remove deprecated tabs
    stale = {"dashboard","kalkulator budgeting bulanan","ref_budget"}
    for ws in sh.worksheets():
        if ws.title.lower() in stale:
            sh.del_worksheet(ws)
            print(f"  Removed deprecated tab: '{ws.title}'")

    # Preserve existing Anggaran budget values before recreating tabs
    existing_budgets = _read_existing_budgets(sh)
    if existing_budgets:
        print(f"  Preserved {len(existing_budgets)} existing budget values from Anggaran.")

    setup_transaksi(sh)
    setup_anggaran(sh, existing_budgets)
    setup_laporan_bulanan(sh)
    setup_laporan_tahunan(sh)
    setup_target_tabungan(sh)

    print("\n✅ All sheets rebuilt successfully!")
    print("Open your Google Sheet to start using the system.")

if __name__ == "__main__":
    main()
