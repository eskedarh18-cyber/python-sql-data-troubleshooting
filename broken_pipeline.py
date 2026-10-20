"""INTENTIONALLY BROKEN - demonstration only. Run to reproduce the error."""
import csv
from pathlib import Path
DATA = Path(__file__).resolve().parent / "data" / "order_items.csv"
with DATA.open(newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    revenue = sum(float(r["unit_price"]) * int(r["quantity"]) for r in reader)
print("Revenue", revenue)
# BUG: float("$46.50") raises ValueError; also no duplicate / status checks.
