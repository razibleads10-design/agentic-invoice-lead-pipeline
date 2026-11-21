# Agentic Invoice & B2B Lead Pipeline

A reproducible Python data automation project demonstrating
deterministic invoice extraction, Pydantic validation,
B2B lead scoring, duplicate detection and processing state persistence.

## Features
- Regex-based invoice field extraction
- Pydantic data validation
- B2B lead scoring and categorization
- Duplicate invoice detection
- JSON and CSV output generation
- Processing state persistence
- Execution report
- Automated unit tests

## Technology
Python, Pydantic, Regex, CSV, JSON

## Run
```bash
pip install -r requirements.txt
python src/pipeline.py
python -m unittest discover -s tests -v
```

## Project Structure
- src/: Pipeline source code
- data/: Fictional sample invoice and lead data
- outputs/: Generated results and execution report
- tests/: Automated tests

## Demo Data
All included company and contact information is fictional.
The example uses deterministic rule-based processing.
No external API or paid API key is required.

## Scope
This version implements the deterministic Python pipeline.
CrewAI orchestration and Gemini-based fallback are not
included in this implementation.
