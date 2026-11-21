
import re, csv, json
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

class Invoice(BaseModel):
    invoice_number: str
    vendor: str
    invoice_date: str
    total_due: float = Field(gt=0)

    @field_validator("invoice_date")
    @classmethod
    def validate_date(cls, value):
        from datetime import date
        date.fromisoformat(value)
        return value

class Lead(BaseModel):
    company: str
    email: str = ""
    website: str = ""
    industry: str = ""
    employees: int = 0
    annual_budget: float = 0
    lead_score: int = 0
    lead_category: str = "Low"

def extract_invoice(text):
    patterns = {
        "invoice_number": r"Invoice Number:\s*(.+)",
        "vendor": r"Vendor:\s*(.+)",
        "invoice_date": r"Invoice Date:\s*(\d{4}-\d{2}-\d{2})",
        "total_due": r"Total Due:\s*\$?([\d,]+(?:\.\d{2})?)"
    }
    values = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        if not match:
            raise ValueError(f"Missing invoice field: {key}")
        values[key] = match.group(1).strip()

    values["total_due"] = float(values["total_due"].replace(",", ""))
    return Invoice(**values)

def score_lead(lead):
    score = 0
    if lead.email and "@" in lead.email:
        score += 20
    if lead.website.startswith("http"):
        score += 20
    if lead.annual_budget >= 50000:
        score += 35
    elif lead.annual_budget >= 20000:
        score += 20
    if lead.employees >= 50:
        score += 25
    elif lead.employees >= 10:
        score += 15

    lead.lead_score = min(score, 100)
    lead.lead_category = (
        "High" if score >= 70 else
        "Medium" if score >= 40 else "Low"
    )
    return lead

def run_pipeline(root):
    root = Path(root)
    data = root / "data"
    output = root / "outputs"
    output.mkdir(exist_ok=True)

    # Invoice extraction and validation
    raw = (data / "invoices.txt").read_text(encoding="utf-8")
    invoice_records = [
        extract_invoice(item)
        for item in raw.split("\n\n") if item.strip()
    ]

    # Duplicate detection
    unique = {}
    for invoice in invoice_records:
        unique[invoice.invoice_number] = invoice

    invoices = list(unique.values())

    with open(output / "invoices.json", "w", encoding="utf-8") as f:
        json.dump(
            [x.model_dump() for x in invoices],
            f, indent=2, ensure_ascii=False
        )

    # Lead enrichment and scoring
    enriched = []
    with open(data / "leads.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lead = Lead(
                company=row["company"],
                email=row["email"],
                website=row["website"],
                industry=row["industry"],
                employees=int(row["employees"]),
                annual_budget=float(row["annual_budget"])
            )
            enriched.append(score_lead(lead))

    with open(output / "enriched_leads.csv", "w",
              newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(enriched[0].model_dump().keys())
        )
        writer.writeheader()
        writer.writerows([x.model_dump() for x in enriched])

    # Processing state persistence
    state = {
        "processed_invoice_ids": [x.invoice_number for x in invoices],
        "total_processed": len(invoices)
    }
    (output / "processing_state.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )

    # Execution report
    report = {
        "status": "SUCCESS",
        "invoice_count": len(invoices),
        "lead_count": len(enriched),
        "high_priority_leads": sum(
            x.lead_category == "High" for x in enriched
        ),
        "total_invoice_value": round(
            sum(x.total_due for x in invoices), 2
        ),
        "validation": "Pydantic validation enabled"
    }

    (output / "execution_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report

if __name__ == "__main__":
    print(run_pipeline(Path(__file__).resolve().parent.parent))
