import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../bot"))
from sheets_manager import gc

SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1nbDsBmrQ74g-yC1k8_XVbh8kIP6wfC9ewjAxG6FaCtw")
print(f"Opening sheet: {SHEET_ID}")
try:
    sh = gc.open_by_key(SHEET_ID)
    print(f"Title: {sh.title}")
    print(f"Worksheets: {[w.title for w in sh.worksheets()]}")
    for w in sh.worksheets():
        print(f"\n--- {w.title} ---")
        rows = w.get_all_values()
        print(f"Rows: {len(rows)}, Cols: {len(rows[0]) if rows else 0}")
        for i, r in enumerate(rows[:8]):
            print(r)
        if len(rows) > 8:
            print(f"... ({len(rows)-8} more rows)")
except Exception as e:
    print(f"Error: {e}")
