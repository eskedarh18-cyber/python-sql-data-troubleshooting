# Python & SQL Troubleshooting | Reproducible Demonstration

**Synthetic demonstration: not client work.** Dataset is intentionally fictional. Tools: Python standard library and SQLite; no installation dependencies.

## Business problem
A sales-report pipeline fails because CSV amounts contain dollar symbols (`float('$1,249.00')` errors). When repaired superficially, retry-delivered item rows and a many-to-many SQL join make monthly revenue inaccurate.

## Reproduce / repair
```bash
python broken_pipeline.py                 # expected ValueError (intentional)
python fixed_pipeline.py                  # repairs import, builds reports/sales.db, CSV and audit
python -m unittest discover -s tests -v  # verify three tests
```
Open `sql/broken_query.sql` and `sql/fixed_query.sql` for side-by-side comparisons. The bad query multiplies item rows when an order has multiple payment capture records. The fixed query uses `EXISTS` to test payment eligibility without row multiplication, filters cancelled orders, and relies on deduplicated item keys.

## Root causes and controls
1. **Currency-as-text:** parse the currency safely with `Decimal` and reject invalid values.
2. **Duplicate events:** deduplicate item retry events on stable `item_id` before loading.
3. **Date inconsistency:** normalize mixed ISO/slash dates before SQLite reporting.
4. **Join fan-out:** aggregate `order_items` after an `EXISTS` paid-payment check.
5. **Incorrect statuses:** exclude cancelled orders from recognized sales.

**Limitations:** This is a deliberately narrow example, not a production payment reconciliation system. Captured payment existence is a demo business rule; actual recognition, refunds, tax, and multi-currency handling require specific requirements and controls. SQLite REAL rounding is for illustration, not authoritative financial ledger storage.

## Outputs
- `reports/revenue_by_month.csv`: corrected monthly report.
- `reports/audit.json`: counts and before/after revenue comparison.
- `reports/sales.db`: inspectable SQLite database.
- `tests/test_pipeline.py`: reproducible tests.
