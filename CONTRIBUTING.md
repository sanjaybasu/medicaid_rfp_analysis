# contributing

## setup

```bash
git clone https://github.com/sanjaybasu/medicaid_rfp_analysis.git
cd medicaid_rfp_analysis
python -m venv venv
source venv/bin/activate  # windows: venv\Scripts\activate
pip install -r requirements.txt
```

## code style

- follow pep 8
- lowercase comments, no superlatives
- keep functions under 50 lines
- use type hints where possible
- test before committing

## running tests

```bash
pytest tests/
```

## data integrity

- never commit fake/synthetic data
- all analysis must trace to source files
- verify numbers against source csvs
- document data transformations

## pull requests

1. fork the repo
2. create feature branch
3. make changes with tests
4. verify all scripts run
5. submit pr with clear description

## questions

open an issue or contact sanjay@waymarkcare.org
