"""Run from project root: python -m unittest discover -s tests -v"""
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3, csv, sys, unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fixed_pipeline import parse_money, normalize_date, run_pipeline

class PipelineTests(unittest.TestCase):
    def test_parse_currency(self):
        self.assertEqual(parse_money('$1,249.00'),1249.0)
        with self.assertRaises(ValueError): parse_money('invalid')

    def test_date_normalization(self):
        self.assertEqual(normalize_date('2025/02/08'),'2025-02-08')
        with self.assertRaises(ValueError): normalize_date('02-99-2025')

    def test_import_dedup_and_sql_revenue(self):
        with TemporaryDirectory() as temp:
            temp=Path(temp)
            audit=run_pipeline(temp/'sales.db', temp/'revenue.csv', temp/'audit.json')
            with sqlite3.connect(temp/'sales.db') as conn:
                row_count=conn.execute('SELECT COUNT(*) FROM order_items').fetchone()[0]
                unique_count=conn.execute('SELECT COUNT(DISTINCT item_id) FROM order_items').fetchone()[0]
            self.assertEqual(row_count,unique_count)
            self.assertEqual(audit['duplicate_item_rows_removed'],4)
            self.assertGreater(audit['wrong_query_revenue_cad'],audit['fixed_revenue_cad'])
            with (temp/'revenue.csv').open(newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),audit['report_rows'])
            self.assertAlmostEqual(sum(float(x['revenue_cad']) for x in rows),audit['fixed_revenue_cad'],places=2)

if __name__ == '__main__': unittest.main()
