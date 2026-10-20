"""Reproducible Python + SQLite data-pipeline repair, standard library only.
Run: python fixed_pipeline.py    (outputs reports/sales.db and revenue_by_month.csv)
"""
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime
import csv
import sqlite3
import json

ROOT = Path(__file__).resolve().parent

def parse_money(raw: str) -> float:
    """Accept '$1,249.00' or '1249.00', reject blank/bad values."""
    value = str(raw).strip().replace('$', '').replace(',', '')
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary amount: {raw!r}") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"Invalid non-finite or negative amount: {raw!r}")
    return float(amount)

def normalize_date(raw: str) -> str:
    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Invalid order date: {raw!r}")

def load_csv(name: str):
    with (ROOT / 'data' / name).open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))

def run_pipeline(db_path=None, report_path=None, audit_path=None):
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    db_path = Path(db_path) if db_path else reports / 'sales.db'
    report_path = Path(report_path) if report_path else reports / 'revenue_by_month.csv'
    audit_path = Path(audit_path) if audit_path else reports / 'audit.json'
    # Each run refreshes this demo database; production use would use migrations.
    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""CREATE TABLE orders (order_id TEXT PRIMARY KEY, order_date TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE order_items (item_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0), unit_price REAL NOT NULL CHECK(unit_price>=0));
CREATE TABLE payments (payment_id TEXT PRIMARY KEY, order_id TEXT NOT NULL, status TEXT NOT NULL);""")
        dates_standardized=0
        for row in load_csv('orders.csv'):
            ds=normalize_date(row['order_date'])
            dates_standardized += ds != row['order_date']
            conn.execute('INSERT INTO orders VALUES (?,?,?)', (row['order_id'],ds,row['status'].lower().strip()))
        seen=set(); repeated=0
        for row in load_csv('order_items.csv'):
            if row['item_id'] in seen:
                repeated+=1; continue
            seen.add(row['item_id'])
            qty=int(row['quantity'])
            if qty<=0: raise ValueError('Invalid quantity')
            conn.execute('INSERT INTO order_items VALUES (?,?,?,?,?)', (row['item_id'],row['order_id'],row['sku'],qty,parse_money(row['unit_price'])))
        for row in load_csv('payments.csv'):
            conn.execute('INSERT INTO payments VALUES (?,?,?)', (row['payment_id'],row['order_id'],row['status'].lower().strip()))
        conn.commit()
        query=(ROOT/'sql'/'fixed_query.sql').read_text(encoding='utf-8')
        result=conn.execute(query).fetchall()
        with report_path.open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f)
            writer.writerow(['month','revenue_cad','paid_order_count'])
            writer.writerows(result)
        bad_query=(ROOT/'sql'/'broken_query.sql').read_text(encoding='utf-8')
        wrong=conn.execute(bad_query).fetchall()
        fixed_total=round(sum(row[1] for row in result),2)
        wrong_total=round(sum(row[1] for row in wrong),2)
        audit={'orders_imported':len(load_csv('orders.csv')),'unique_items_imported':len(seen),
          'duplicate_item_rows_removed':repeated,'dates_standardized':dates_standardized,
          'fixed_revenue_cad':fixed_total,'wrong_query_revenue_cad':wrong_total,
          'overstatement_cad':round(wrong_total-fixed_total,2),'report_rows':len(result)}
        audit_path.write_text(json.dumps(audit,indent=2),encoding='utf-8')
        return audit
    finally:
        conn.close()

if __name__ == '__main__':
    print(json.dumps(run_pipeline(),indent=2))
