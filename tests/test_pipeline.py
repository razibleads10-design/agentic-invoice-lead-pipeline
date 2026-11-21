
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pipeline import extract_invoice, score_lead, Lead

class PipelineTests(unittest.TestCase):
    def test_invoice_extraction(self):
        text = """Invoice Number: INV-TEST
Vendor: Test Company
Invoice Date: 2026-11-10
Total Due: $100.00"""
        invoice = extract_invoice(text)
        self.assertEqual(invoice.invoice_number, "INV-TEST")
        self.assertEqual(invoice.total_due, 100.0)

    def test_lead_scoring(self):
        lead = Lead(
            company="Test", email="test@example.com",
            website="https://example.com",
            employees=100, annual_budget=100000
        )
        result = score_lead(lead)
        self.assertEqual(result.lead_score, 100)
        self.assertEqual(result.lead_category, "High")

if __name__ == "__main__":
    unittest.main()
