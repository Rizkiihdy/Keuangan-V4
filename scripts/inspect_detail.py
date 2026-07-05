import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../bot"))
from sheets_manager import gc

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1nbDsBmrQ74g-yC1k8_XVbh8kIP6wfC9ewjAxG6FaCtw")
sh = gc.open_by_key(SHEET_ID)

print("=== AKUN ===")
w = sh.worksheet("Akun")
rows = w.get_all_values()
for r in rows[7:14]:
    print(r)

print("\n=== GOALS ===")
w = sh.worksheet("Goals")
rows = w.get_all_values()
for r in rows[4:12]:
    print(r)

print("\n=== TRANSKASI TERAKHIR (5 rows) ===")
w = sh.worksheet("Transaksi")
rows = w.get_all_values()
print("Headers:", rows[3])
for r in rows[-5:]:
    print(r)

print("\n=== BUDGET (first 20 rows) ===")
w = sh.worksheet("Budget")
rows = w.get_all_values()
for r in rows[:20]:
    print(r)

print("\n=== INSIGHT (first 15 rows) ===")
w = sh.worksheet("Insight")
rows = w.get_all_values()
for r in rows[:15]:
    print(r)
