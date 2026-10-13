<div align="center">

# FinTrack

### Your finances. Your device. Your data.

An offline-first desktop finance manager for tracking accounts, spending, budgets, goals, and recurring payments without sending financial data to the cloud.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## Why FinTrack?

FinTrack brings everyday money management into one clean desktop application. It works entirely offline, stores data locally, and gives you practical tools for understanding where your money goes without requiring an account, subscription, or bank connection.

## Highlights

| Area | Capabilities |
| --- | --- |
| Accounts | Multiple accounts, opening balances, archiving, and same-currency transfers |
| Transactions | Income and expense tracking, categories, notes, editing, search, and filtering |
| Imports | CSV/XLSX statement import, flexible column mapping, preview, and duplicate detection |
| Planning | Monthly category budgets, savings goals, and recurring payments |
| Insights | Monthly cash flow, category spending, trends, and recurring merchant detection |
| Reports | Monthly PDF/XLSX reports and CSV transaction exports |
| Experience | Light/dark themes, calendar-based month selection, and demo data |
| Data safety | Local SQLite storage, backups, and database integrity checks |

## Quick start

### Windows

Double-click `RUN_WINDOWS.bat`, or run the setup manually in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

### macOS

Run `./RUN_MACOS.sh`, or use the manual setup below:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

FinTrack requires Python 3.10 or newer. Python 3.11 through 3.13 is recommended.

## Getting started

1. Open **Accounts** and create your first account.
2. Add entries under **Transactions**, or import a CSV/XLSX bank statement.
3. Categorize transactions so reports and spending insights remain accurate.
4. Set monthly category limits under **Budgets**.
5. Use **Goals** and **Recurring** to plan ahead.
6. Export reports or create a database backup from **Settings**.

Want to explore first? Select **Settings > Load demo data** before creating an account.

## Importing statements

FinTrack accepts `.csv` and `.xlsx` statements. The import workflow lets you:

- Select the destination account
- Map date, description, amount, debit, credit, and reference columns
- Review converted transactions before saving them
- Skip duplicates when the same statement rows are imported again

Supported dates include ISO (`YYYY-MM-DD`) and common slash, dash, and dot formats. Ambiguous slash-formatted dates default to day-first, so always review the preview before confirming.

> PDF statements, OCR, and direct bank connections are not currently supported.

## How data is handled

FinTrack makes no network calls and does not connect to a bank. The application database is stored in the standard application-data location for your operating system:

| Platform | Default location |
| --- | --- |
| Windows | `%LOCALAPPDATA%\FinTrack\fintrack.db` |
| macOS | `~/Library/Application Support/FinTrack/fintrack.db` |
| Linux | `~/.local/share/FinTrack/fintrack.db` |

Money is stored as integer hundredths rather than floating-point values. Reports are currency-specific, and FinTrack never silently combines or converts currencies.

> [!WARNING]
> FinTrack is a personal project, not an audited financial or banking product. The SQLite database, backups, and exported reports are not encrypted. Never store online-banking credentials in FinTrack, and protect files containing personal financial information.

## Testing

Install the dependencies from `requirements.txt`, then run:

```bash
python -m pytest -q
python -m compileall -q fintrack main.py
```

The current test suite contains 14 automated tests covering core finance operations, imports, reports, budgets, goals, recurring transactions, insights, and database migration behavior.

## Project structure

```text
FinTrack/
|-- fintrack/
|   |-- db.py          # SQLite persistence and finance operations
|   |-- importer.py    # CSV/XLSX parsing and validation
|   |-- reports.py     # PDF/XLSX report generation
|   |-- theme.py       # Light and dark application themes
|   `-- ui.py          # PySide6 desktop interface
|-- samples/           # Example bank statement
|-- tests/             # Automated test suite
|-- main.py            # Application entry point
|-- pyproject.toml     # Project metadata
`-- requirements.txt   # Runtime and test dependencies
```

## Current limitations

- Cross-currency conversion and transfers are not supported.
- Database files and backups are not encrypted.
- Statement importing supports CSV/XLSX only.
- Duplicate detection is based on imported row data and source details; renamed or reordered statements should be reviewed carefully.
- Full credit-card liability accounting, reconciliation, transaction splits, and investment tracking are not yet implemented.

## Roadmap

- Encrypted local storage and optional application lock
- Rules for automatic merchant categorization
- Transaction splitting and account reconciliation
- Persisted exchange rates and cross-currency transfers
- Reusable bank import templates
- Improved accessibility and advanced filtering
- Signed desktop installers for Windows and macOS

## Packaging

To create a distributable application, install `pyside6-deploy` in the active environment and run:

```bash
pyside6-deploy main.py
```

Builds should be created and tested on each target operating system. Public releases may require code signing and, on macOS, notarization.

## Contributing

Contributions are welcome. Fork the repository, create a focused branch, add or update tests where appropriate, and open a pull request describing the change.

## License

FinTrack is available under the [MIT License](LICENSE).
