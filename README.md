
# Finance Tracker (Tkinter)

A simple, desktop **personal finance tracker** built with Python and Tkinter. It lets you record incomes and expenses, manage categories, view your running balance, and persist data locally in CSV files—no database required. Designed with an accessible green-themed UI inspired by "wealth/wellness" palettes.

> Course project (2024) by **Bagay, Axel Drake M.**

---

## ✨ Features
- **Add income/expense** transactions with category and timestamp (auto-filled).
- **Edit or soft-delete** transactions (deleted rows are hidden but retained in storage).
- **Running balance** shown prominently and updated live.
- **Category management**: add or remove income/expense categories on the fly.
- **Currency selector** (USD, PHP, EUR, JPY) stored per user.
- **Exit confirmation** dialog with "Don't ask again" preference.
- **Local persistence** using portable CSV files (no external DB).
- **Clean, card-style UI** using Tkinter `ttk` widgets and custom styles.

---

## 🖼️ UI at a Glance
- **Title bar**: App name
- **Balance card**: Running balance and currency combobox
- **Add transaction card**: Amount, type (Income/Expense), category with inline category tools
- **Transactions list**: Treeview with color-coded rows (green = income, red = expense)
- **Action buttons**: Edit / Delete below the list

---

## 📁 Project Structure
```
.
├── Finance tracker.py        # Main Tkinter application
└── data/                     # Created automatically on first run
    ├── categories.csv        # Income & expense category lists
    ├── config.csv            # UI/behavior preferences (ask_on_exit)
    ├── currency.csv          # Selected currency
    └── transactions.csv      # All transactions (with type & soft-delete flag)
```

> The `data/` folder is created automatically next to the script on first launch.

---

## ⚙️ Requirements
- **Python 3.8+** (tested with 3.10+)
- **Tkinter** (bundled with most Python distributions)

No third‑party packages are required.

### Verify Tkinter is available
```bash
python -m tkinter
```
This should open a small Tk window. If it fails, install Tk for your OS (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu).

---

## 🚀 Run Locally
1. **Clone or download** this repository / source file.
2. Ensure Python is available on your PATH.
3. From the project directory, run:
   ```bash
   python "Finance tracker.py"
   ```

On first run, the app will create the `data/` directory and seed default categories.

---

## 🧠 How It Works (Architecture)
- **Models**
  - `Transaction` (abstract) + `IncomeTransaction` and `ExpenseTransaction` subclasses.
  - `TransactionManager`: in-memory list + CSV persistence (`transactions.csv`), sorting by timestamp, soft-delete support.
  - `CategoryManager`: loads/saves `categories.csv` with separate income/expense lists; seeds defaults when missing.
  - `CurrencyManager`: stores the selected currency in `currency.csv`.
  - `ConfigManager`: stores UI preference `ask_on_exit` in `config.csv`.
- **Views/Controllers**
  - `FinanceTracker` (Tkinter): builds styled UI using `ttk.Style` and manages interactions.
  - `EditTransactionDialog` and `ExitConfirmDialog` (modal dialogs).

---

## 📚 Data Format
- **`transactions.csv`** columns: `amount,category,timestamp,deleted,type`
  - `type`: `Income` or `Expense`
  - `deleted`: `True`/`False` (soft delete)
  - `timestamp` format: `%Y-%m-%d %H:%M:%S`
- **`categories.csv`** columns: `type,category` where `type` is `income` or `expense`.
- **`currency.csv`**: single row `currency,<CODE>`
- **`config.csv`**: single row `ask_on_exit,True|False`

---

## 🕹️ Usage Notes
- **Adding a transaction**: Enter an amount, pick `Income`/`Expense`, choose a category. Timestamp is auto-set to now.
- **Categories**: After choosing a type, the category box enables; use **Add Category** or **Delete Category** as needed.
- **Editing**: Select a row → **Edit** → adjust amount, type, category, or timestamp (must match `%Y-%m-%d %H:%M:%S`).
- **Deleting**: Select a row → **Delete** (soft delete; can no longer see it in the list, but it remains in storage).
- **Currency**: Change via the balance card dropdown; the choice is remembered.
- **Exit**: You can disable the confirmation dialog via "Don't ask me again".

---

## 🧩 Extensibility Ideas
- Export summaries (weekly/monthly) and charts.
- Budget targets and alerts per category.
- Import/export CSV wizard.
- Multi-currency with FX rates and conversions.
- Password/PIN lock and simple encryption for CSV files.
- Dark mode / theming presets.

---

## 🛠️ Troubleshooting
- **Numbers rejected** when adding: ensure `Amount` is a valid number (`123.45`).
- **Invalid timestamp** on edit: must match `%Y-%m-%d %H:%M:%S` (e.g., `2024-03-15 14:05:00`).
- **Tkinter not found**: install system Tk libraries (Linux) or ensure Python from python.org is used (Windows/macOS typically bundle Tk).
- **CSV locked** on Windows: close other apps (Excel) that might have opened the file.

---

## 🙌 Attribution
- Author: **Bagay, Axel Drake M.**  
- Year: **2024**

