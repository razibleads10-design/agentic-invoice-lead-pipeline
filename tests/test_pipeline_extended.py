import csv
import json
import tempfile
import unittest
from pathlib import Path

from pipeline import Invoice, Lead, extract_invoice, score_lead, run_pipeline
from pydantic import ValidationError


class ExtendedPipelineTests(unittest.TestCase):

    def test_missing_invoice_field(self):
        with self.assertRaises(ValueError):
            extract_invoice("Invoice Number: INV-1\nVendor: Test")

    def test_invalid_invoice_date(self):
        text = """Invoice Number: INV-1
Vendor: Test
Invoice Date: 2026-99-99
Total Due: $100.00"""
        with self.assertRaises(ValidationError):
            extract_invoice(text)

    def test_non_positive_invoice_amount(self):
        with self.assertRaises(ValidationError):
            Invoice(
                invoice_number="INV-2",
                vendor="Test",
                invoice_date="2026-11-10",
                total_due=0
            )

    def test_amount_with_commas(self):
        text = """Invoice Number: INV-3
Vendor: Test Company
Invoice Date: 2026-11-10
Total Due: $1,250.50"""
        invoice = extract_invoice(text)
        self.assertEqual(invoice.total_due, 1250.50)

    def test_lead_scoring_categories(self):
        low = score_lead(Lead(company="Low"))
        medium = score_lead(Lead(
            company="Medium",
            email="test@example.com",
            website="https://example.com"
        ))
        high = score_lead(Lead(
            company="High",
            email="high@example.com",
            website="https://example.com",
            employees=100,
            annual_budget=100000
        ))

        self.assertEqual(low.lead_category, "Low")
        self.assertEqual(medium.lead_category, "Medium")
        self.assertEqual(high.lead_category, "High")

    def test_pipeline_creates_output_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()

            (data / "invoices.txt").write_text(
                """Invoice Number: INV-1
Vendor: Test Company
Invoice Date: 2026-11-10
Total Due: $100.00""",
                encoding="utf-8"
            )

            with (data / "leads.csv").open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "company", "email", "website",
                        "industry", "employees", "annual_budget"
                    ]
                )
                writer.writeheader()
                writer.writerow({
                    "company": "Test",
                    "email": "test@example.com",
                    "website": "https://example.com",
                    "industry": "Technology",
                    "employees": "50",
                    "annual_budget": "60000"
                })

            report = run_pipeline(root)

            self.assertEqual(report["status"], "SUCCESS")
            self.assertTrue((root / "outputs/invoices.json").exists())
            self.assertTrue((root / "outputs/enriched_leads.csv").exists())
            self.assertTrue((root / "outputs/execution_report.json").exists())

    def test_duplicate_invoice_ids_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data"
            data.mkdir()

            invoice = """Invoice Number: INV-DUP
Vendor: Test Company
Invoice Date: 2026-11-10
Total Due: $100.00"""

            (data / "invoices.txt").write_text(
                invoice + "\n\n" + invoice.replace("$100.00", "$200.00"),
                encoding="utf-8"
            )

            with (data / "leads.csv").open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "company", "email", "website",
                        "industry", "employees", "annual_budget"
                    ]
                )
                writer.writeheader()
                writer.writerow({
                    "company": "Test",
                    "email": "",
                    "website": "",
                    "industry": "Other",
                    "employees": "0",
                    "annual_budget": "0"
                })

            report = run_pipeline(root)
            self.assertEqual(report["invoice_count"], 1)

            saved = json.loads(
                (root / "outputs/invoices.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(saved), 1)


if __name__ == "__main__":
    unittest.main()
