# FinTrack

FinTrack is an offline-first desktop personal finance manager built with Python, PySide6, and SQLite. It helps you track accounts and transactions, plan monthly budgets, review spending insights, manage savings goals and recurring payments, import bank statements, and export reports—all while keeping your data on your computer.

> [!IMPORTANT]
> FinTrack is a personal project, not an audited banking product. Its local database and backups are not encrypted. Do not store bank credentials in the app, and protect any imported financial data appropriately.

## Features

- Track multiple accounts, balances, income, expenses, and same-currency transfers
- Categorize transactions and search transaction history
- Import CSV and XLSX bank statements with column mapping and a review step
- Set monthly category budgets and compare them with actual spending
- View monthly summaries, spending breakdowns, and cash-flow trends
- Track savings goals and recurring payments
- Export monthly reports to PDF and XLSX, or transactions to CSV
- Switch between light and dark themes
- Back up the local SQLite database and verify its integrity
- Load demonstration data for a quick tour

## Requirements

- Python 3.10 or newer (Python 3.11–3.13 recommended)
- Windows, macOS, or Linux with GUI support

## Quick start

### Windows

The easiest option is to double-click `RUN_WINDOWS.bat`. To set up the app manually in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

### macOS or Linux

On macOS, you can run `./RUN_MACOS.sh`. To set up the app manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## First steps

1. Add an account from **Accounts**.
2. Record income or expenses under **Transactions**, or import a CSV/XLSX statement.
3. Assign categories so dashboards, budgets, and insights are accurate.
4. Set category limits in **Budgets** and review the monthly overview.
5. Export a report from **Reports**, or create a database backup in **Settings**.

To explore without entering your own data, choose **Settings → Load demo data** before creating an account.

## Statement imports

FinTrack supports `.csv` and `.xlsx` files. During import, select an account and map the file's date, description, amount (or debit and credit), and optional reference columns. Always verify the preview before confirming an import.

Supported date formats include ISO (`YYYY-MM-DD`) and common slash/dash formats. Ambiguous slash-formatted dates are treated as day-first. PDF and OCR imports are not currently supported.

## Data and privacy

- Data is stored locally in a SQLite database in the operating system's application-data folder.
- Monetary values are stored as integer hundredths to avoid floating-point rounding errors.
- FinTrack makes no network calls and does not connect directly to banks.
- Accounts and reports are currency-specific; the app does not perform currency conversion.
- Transfers currently require accounts with the same currency.
- Database files, backups, and exported reports are not encrypted.

## Development

Install the dependencies, including pytest, from `requirements.txt`, then run:

```bash
python -m pytest -q
python -m compileall -q fintrack main.py
```

Project structure:

```text
FinTrack/
├── fintrack/
│   ├── db.py          # SQLite persistence and finance operations
│   ├── importer.py    # CSV/XLSX statement parsing
│   ├── reports.py     # PDF/XLSX report generation
│   ├── theme.py       # Light and dark themes
│   └── ui.py          # PySide6 desktop interface
├── samples/           # Example bank statement
├── tests/             # Automated tests
├── main.py            # Application entry point
└── requirements.txt
```

## Packaging

Install `pyside6-deploy` in the active virtual environment and run:

```bash
pyside6-deploy main.py
```

Build and test packages on each target operating system. Public distribution may also require code signing and, on macOS, notarization.

## License

Licensed under the [MIT License](LICENSE).
