import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

# ----------------------------------------------------------------------
# Wealth‑Inspired Green Color Palette & Fonts
# ----------------------------------------------------------------------
WINDOW_WIDTH = 650
WINDOW_HEIGHT = 650

# Fonts
TITLE_FONT = ("Inter", 22, "bold")
BALANCE_FONT = ("Inter", 20, "bold")
LABEL_FONT = ("Inter", 11)
BUTTON_FONT = ("Inter", 10, "bold")

# Colors
BG_COLOR = "#F1F8E9"          # soft light green background
CARD_COLOR = "#FFFFFF"         # white for cards
PRIMARY_GREEN = "#2E7D32"      # deep green – primary action color
SECONDARY_GREEN = "#4CAF50"    # lighter green for hover / accents
TEXT_COLOR = "#1B5E20"         # dark green text for headings
LABEL_COLOR = "#2E3B2E"        # dark gray‑green for labels
INCOME_COLOR = "#2E7D32"       # green for income (same as primary)
EXPENSE_COLOR = "#C62828"       # rich red for expense
BORDER_COLOR = "#C8E6C9"        # very light green for borders

# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CATEGORIES_FILE = DATA_DIR / "categories.csv"
CONFIG_FILE = DATA_DIR / "config.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
CURRENCY_FILE = DATA_DIR / "currency.csv"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

# ----------------------------------------------------------------------
# Model Classes (unchanged – robust logic)
# ----------------------------------------------------------------------
class Transaction(ABC):
    def __init__(self, amount: float, category: str, timestamp: str):
        self.amount = amount
        self.category = category
        self.timestamp = timestamp
        self.deleted = False

    @abstractmethod
    def signed_amount(self) -> float:
        pass

    def to_dict(self) -> dict:
        return {
            "amount": str(self.amount),
            "category": self.category,
            "timestamp": self.timestamp,
            "deleted": str(self.deleted),
            "type": self.__class__.__name__.replace("Transaction", "")
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        amount = float(data["amount"])
        category = data["category"]
        timestamp = data["timestamp"]
        deleted = data.get("deleted", "False") == "True"
        t_type = data.get("type", "Income")
        if t_type == "Income":
            trans = IncomeTransaction(amount, category, timestamp)
        elif t_type == "Expense":
            trans = ExpenseTransaction(amount, category, timestamp)
        else:
            raise ValueError(f"Unknown transaction type: {t_type}")
        trans.deleted = deleted
        return trans


class IncomeTransaction(Transaction):
    def signed_amount(self) -> float:
        return self.amount


class ExpenseTransaction(Transaction):
    def signed_amount(self) -> float:
        return -self.amount


class TransactionManager:
    def __init__(self):
        self.transactions: list[Transaction] = []
        self.load()

    @property
    def balance(self) -> float:
        return sum(t.signed_amount() for t in self.transactions if not t.deleted)

    def add(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)
        self._sort()

    def delete(self, index: int) -> None:
        if 0 <= index < len(self.transactions):
            self.transactions[index].deleted = True

    def edit(self, index: int, new_transaction: Transaction) -> None:
        if 0 <= index < len(self.transactions):
            new_transaction.deleted = self.transactions[index].deleted
            self.transactions[index] = new_transaction
            self._sort()

    def _sort(self) -> None:
        self.transactions.sort(
            key=lambda t: datetime.strptime(t.timestamp, TIMESTAMP_FORMAT),
            reverse=True
        )

    def save(self) -> None:
        with open(TRANSACTIONS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["amount", "category", "timestamp", "deleted", "type"])
            writer.writeheader()
            for t in self.transactions:
                writer.writerow(t.to_dict())

    def load(self) -> None:
        self.transactions = []
        if not TRANSACTIONS_FILE.exists():
            return
        try:
            with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.transactions.append(Transaction.from_dict(row))
            self._sort()
        except Exception as e:
            print(f"Error loading transactions: {e}")
            self.transactions = []


class CategoryManager:
    def __init__(self):
        self.income: list[str] = []
        self.expense: list[str] = []
        self.load()

    def load(self) -> None:
        self.income = []
        self.expense = []
        if CATEGORIES_FILE.exists():
            try:
                with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row["type"] == "income":
                            self.income.append(row["category"])
                        elif row["type"] == "expense":
                            self.expense.append(row["category"])
            except Exception:
                pass
        if not self.income:
            self.income = ["Salary", "Bonus", "Freelance"]
        if not self.expense:
            self.expense = ["Food", "Rent", "Transport"]

    def save(self) -> None:
        with open(CATEGORIES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["type", "category"])
            for cat in self.income:
                writer.writerow(["income", cat])
            for cat in self.expense:
                writer.writerow(["expense", cat])

    def add(self, type_: str, category: str) -> None:
        if type_ == "Income" and category not in self.income:
            self.income.append(category)
            self.save()
        elif type_ == "Expense" and category not in self.expense:
            self.expense.append(category)
            self.save()

    def delete(self, type_: str, category: str) -> None:
        if type_ == "Income":
            self.income.remove(category)
        elif type_ == "Expense":
            self.expense.remove(category)
        else:
            raise ValueError("Invalid transaction type")
        self.save()


class CurrencyManager:
    def __init__(self):
        self.currency = self.load()

    def load(self) -> str:
        if CURRENCY_FILE.exists():
            try:
                with open(CURRENCY_FILE, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0] == "currency":
                            return row[1]
            except Exception:
                pass
        return "PHP"

    def save(self, currency: str) -> None:
        with open(CURRENCY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["currency", currency])
        self.currency = currency


class ConfigManager:
    def __init__(self):
        self.ask_on_exit = True
        self.load()

    def load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0] == "ask_on_exit":
                            self.ask_on_exit = row[1] == "True"
                            break
            except Exception:
                pass

    def save(self) -> None:
        with open(CONFIG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ask_on_exit", str(self.ask_on_exit)])


# ----------------------------------------------------------------------
# Custom Dialogs (updated with green theme)
# ----------------------------------------------------------------------
class ExitConfirmDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Confirm Exit")
        self.grab_set()
        self.configure(bg=BG_COLOR)
        self.result = False
        self.dont_ask = False

        ttk.Label(self, text="Do you really want to exit?",
                  font=LABEL_FONT, background=BG_COLOR, foreground=LABEL_COLOR).grid(
            row=0, column=0, columnspan=2, pady=10, padx=10
        )

        self.dont_ask_var = tk.BooleanVar()
        ttk.Checkbutton(self, text="Don't ask me again", variable=self.dont_ask_var,
                        style="Green.TCheckbutton").grid(
            row=1, column=0, columnspan=2, pady=5
        )

        ttk.Button(self, text="Exit", command=self.on_exit,
                   style="Green.TButton", width=10).grid(row=2, column=0, pady=10, padx=5)
        ttk.Button(self, text="Cancel", command=self.on_cancel,
                   style="Green.TButton", width=10).grid(row=2, column=1, pady=10, padx=5)

        self.bind("<Return>", lambda e: self.on_exit())
        self.bind("<Escape>", lambda e: self.on_cancel())

    def on_exit(self):
        self.result = True
        self.dont_ask = self.dont_ask_var.get()
        self.destroy()

    def on_cancel(self):
        self.result = False
        self.destroy()


class EditTransactionDialog(tk.Toplevel):
    def __init__(self, parent, transaction, categories_income, categories_expense):
        super().__init__(parent)
        self.parent = parent
        self.title("Edit Transaction")
        self.grab_set()
        self.configure(bg=BG_COLOR)
        self.transaction = transaction
        self.result = None

        ttk.Label(self, text="Amount:", font=LABEL_FONT,
                  background=BG_COLOR, foreground=LABEL_COLOR).grid(
            row=0, column=0, sticky="w", pady=5, padx=10
        )
        self.amount_entry = ttk.Entry(self, width=20, font=LABEL_FONT)
        self.amount_entry.insert(0, str(transaction.amount))
        self.amount_entry.grid(row=0, column=1, pady=5, padx=10)

        ttk.Label(self, text="Type:", font=LABEL_FONT,
                  background=BG_COLOR, foreground=LABEL_COLOR).grid(
            row=1, column=0, sticky="w", pady=5, padx=10
        )
        self.type_var = tk.StringVar(value="Income" if isinstance(transaction, IncomeTransaction) else "Expense")
        self.type_combo = ttk.Combobox(self, textvariable=self.type_var,
                                       values=["Income", "Expense"],
                                       state="readonly", width=18, font=LABEL_FONT)
        self.type_combo.grid(row=1, column=1, pady=5, padx=10)
        self.type_combo.bind("<<ComboboxSelected>>", self._update_category_list)

        ttk.Label(self, text="Category:", font=LABEL_FONT,
                  background=BG_COLOR, foreground=LABEL_COLOR).grid(
            row=2, column=0, sticky="w", pady=5, padx=10
        )
        self.category_var = tk.StringVar(value=transaction.category)
        self.category_combo = ttk.Combobox(self, textvariable=self.category_var,
                                           state="readonly", width=18, font=LABEL_FONT)
        self.category_combo.grid(row=2, column=1, pady=5, padx=10)

        ttk.Label(self, text="Date/Time:", font=LABEL_FONT,
                  background=BG_COLOR, foreground=LABEL_COLOR).grid(
            row=3, column=0, sticky="w", pady=5, padx=10
        )
        self.timestamp_entry = ttk.Entry(self, width=20, font=LABEL_FONT)
        self.timestamp_entry.insert(0, transaction.timestamp)
        self.timestamp_entry.grid(row=3, column=1, pady=5, padx=10)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="Save", command=self.on_save,
                   style="Green.TButton", width=10).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel,
                   style="Green.TButton", width=10).pack(side="left", padx=5)

        self._update_category_list()

    def _update_category_list(self, event=None):
        if self.type_var.get() == "Income":
            categories = self.parent.category_mgr.income
        else:
            categories = self.parent.category_mgr.expense
        self.category_combo["values"] = categories
        if self.category_var.get() not in categories and categories:
            self.category_var.set(categories[0])

    def on_save(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a valid number.")
            return
        t_type = self.type_var.get()
        category = self.category_var.get()
        timestamp = self.timestamp_entry.get().strip()
        try:
            datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        except ValueError:
            messagebox.showerror("Invalid Date/Time",
                                 f"Please use format: {TIMESTAMP_FORMAT}")
            return
        if not category:
            messagebox.showerror("No Category", "Please select a category.")
            return
        if t_type == "Income":
            new_trans = IncomeTransaction(amount, category, timestamp)
        else:
            new_trans = ExpenseTransaction(amount, category, timestamp)
        self.result = new_trans
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ----------------------------------------------------------------------
# Main Application Class (green theme, card layout)
# ----------------------------------------------------------------------
class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Finance Tracker")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        self.config_mgr = ConfigManager()
        self.currency_mgr = CurrencyManager()
        self.category_mgr = CategoryManager()
        self.transaction_mgr = TransactionManager()

        self.currency_var = tk.StringVar(value=self.currency_mgr.currency)
        self.balance_str = tk.StringVar()
        self._update_balance_str()

        self._setup_styles()
        self._build_ui()
        self._refresh_transaction_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Frames
        style.configure("Card.TFrame", background=CARD_COLOR, relief="solid", borderwidth=1)
        style.map("Card.TFrame", background=[("active", CARD_COLOR)])

        # Labels
        style.configure("Card.TLabel", background=CARD_COLOR, foreground=LABEL_COLOR, font=LABEL_FONT)
        style.configure("Balance.TLabel", background=CARD_COLOR, foreground=PRIMARY_GREEN,
                        font=BALANCE_FONT)

        # Entry & Combobox
        style.configure("Green.TEntry", fieldbackground="white", foreground=TEXT_COLOR,
                        font=LABEL_FONT, borderwidth=1, relief="solid")
        style.configure("Green.TCombobox", fieldbackground="white", foreground=TEXT_COLOR,
                        font=LABEL_FONT, arrowcolor=PRIMARY_GREEN)
        style.map("Green.TCombobox",
                  fieldbackground=[("readonly", "white")])

        # Buttons
        style.configure("Green.TButton",
                        background=PRIMARY_GREEN, foreground="white",
                        font=BUTTON_FONT, borderwidth=0, focuscolor="none",
                        padding=(8, 4))
        style.map("Green.TButton",
                  background=[("active", SECONDARY_GREEN)])

        # Treeview
        style.configure("Green.Treeview",
                        background="white", foreground=TEXT_COLOR,
                        fieldbackground="white", font=LABEL_FONT,
                        borderwidth=1, relief="solid")
        style.configure("Green.Treeview.Heading",
                        background=PRIMARY_GREEN, foreground="white",
                        font=BUTTON_FONT, relief="flat")
        style.map("Green.Treeview.Heading",
                  background=[("active", PRIMARY_GREEN)])

        # Checkbutton
        style.configure("Green.TCheckbutton",
                        background=BG_COLOR, foreground=LABEL_COLOR,
                        font=LABEL_FONT)

    def _build_ui(self):
        # Main container (card)
        main_card = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        main_card.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # ----- Title Bar (non-ttk for solid color) -----
        title_frame = tk.Frame(main_card, bg=PRIMARY_GREEN, height=45)
        title_frame.grid(row=0, column=0, columnspan=5, sticky="ew", pady=(0, 15))
        title_frame.grid_propagate(False)
        tk.Label(title_frame, text="Finance Tracker", font=TITLE_FONT,
                 bg=PRIMARY_GREEN, fg="white").pack(expand=True)

        # ----- Balance Card -----
        balance_card = ttk.Frame(main_card, style="Card.TFrame", relief="solid", borderwidth=1)
        balance_card.grid(row=1, column=0, columnspan=5, sticky="ew", pady=5)
        balance_card.columnconfigure(0, weight=1)

        ttk.Label(balance_card, textvariable=self.balance_str,
                  style="Balance.TLabel").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        currency_combo = ttk.Combobox(balance_card, textvariable=self.currency_var,
                                      values=["USD", "PHP", "EUR", "JPY"],
                                      state="readonly", width=5, style="Green.TCombobox")
        currency_combo.grid(row=0, column=1, padx=15, pady=10, sticky="e")
        self.currency_var.trace_add("write", self._on_currency_change)

        # ----- Add Transaction Card -----
        add_card = ttk.Frame(main_card, style="Card.TFrame", relief="solid", borderwidth=1)
        add_card.grid(row=2, column=0, columnspan=5, sticky="ew", pady=10)
        for i in range(3):
            add_card.columnconfigure(1, weight=1)

        # Amount row
        ttk.Label(add_card, text="Amount:", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", padx=10, pady=8)
        self.amount_entry = ttk.Entry(add_card, width=20, style="Green.TEntry")
        self.amount_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=8)

        # Type row
        ttk.Label(add_card, text="Type:", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", padx=10, pady=8)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(add_card, textvariable=self.type_var,
                                       values=["Income", "Expense"],
                                       state="readonly", width=18, style="Green.TCombobox")
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=10, pady=8)
        self.type_combo.bind("<<ComboboxSelected>>", self._update_category_options)

        # Category row
        ttk.Label(add_card, text="Category:", style="Card.TLabel").grid(
            row=2, column=0, sticky="w", padx=10, pady=8)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(add_card, textvariable=self.category_var,
                                           state="disabled", width=18, style="Green.TCombobox")
        self.category_combo.grid(row=2, column=1, sticky="ew", padx=10, pady=8)

        # Category management buttons (inline, initially hidden)
        self.cat_button_frame = ttk.Frame(main_card, style="Card.TFrame")
        self.cat_button_frame.grid(row=3, column=0, columnspan=5, pady=5)
        self.add_cat_btn = ttk.Button(self.cat_button_frame, text="Add Category",
                                      command=self._add_category, style="Green.TButton")
        self.add_cat_btn.pack(side="left", padx=5)
        self.del_cat_btn = ttk.Button(self.cat_button_frame, text="Delete Category",
                                      command=self._delete_category, style="Green.TButton")
        self.del_cat_btn.pack(side="left", padx=5)
        self.cat_button_frame.grid_remove()

        # Add transaction button
        self.add_btn = ttk.Button(main_card, text="Add Transaction",
                                   command=self._add_transaction, style="Green.TButton")
        self.add_btn.grid(row=4, column=0, columnspan=5, pady=12, sticky="ew")

        # ----- Transactions List Card -----
        list_card = ttk.Frame(main_card, style="Card.TFrame", relief="solid", borderwidth=1)
        list_card.grid(row=5, column=0, columnspan=5, sticky="nsew", pady=5)
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(0, weight=1)

        columns = ("Category", "Amount", "Date/Time")
        self.tree = ttk.Treeview(list_card, columns=columns, show="headings",
                                  style="Green.Treeview", height=10)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        self.tree.tag_configure("income", foreground=INCOME_COLOR)
        self.tree.tag_configure("expense", foreground=EXPENSE_COLOR)
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Action buttons below the list
        self.tree.bind("<<TreeviewSelect>>", self._on_transaction_select)

        self.action_frame = ttk.Frame(main_card, style="Card.TFrame")
        self.action_frame.grid(row=6, column=0, columnspan=5, pady=5)
        self.edit_btn = ttk.Button(self.action_frame, text="Edit",
                                   command=self._edit_transaction, style="Green.TButton")
        self.delete_btn = ttk.Button(self.action_frame, text="Delete",
                                     command=self._delete_transaction, style="Green.TButton")
        self.save_btn = ttk.Button(self.action_frame, text="Save",
                                   command=self._save_edit, style="Green.TButton")
        self.cancel_btn = ttk.Button(self.action_frame, text="Cancel",
                                     command=self._cancel_edit, style="Green.TButton")
        self.edit_btn.pack(side="left", padx=5)
        self.delete_btn.pack(side="left", padx=5)
        self.save_btn.pack_forget()
        self.cancel_btn.pack_forget()

        # Make the list card expandable
        main_card.rowconfigure(5, weight=1)
        main_card.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Helper Methods (logic unchanged, only adapted to new style)
    # ------------------------------------------------------------------
    def _update_balance_str(self):
        bal = self.transaction_mgr.balance
        self.balance_str.set(f"Balance: {self.currency_var.get()} {bal:.2f}")

    def _on_currency_change(self, *args):
        new_currency = self.currency_var.get()
        self.currency_mgr.save(new_currency)
        self._update_balance_str()
        self._refresh_transaction_list()

    def _update_category_options(self, event=None):
        t_type = self.type_var.get()
        if t_type == "Income":
            cats = self.category_mgr.income
        elif t_type == "Expense":
            cats = self.category_mgr.expense
        else:
            cats = []
        self.category_combo["values"] = cats
        if cats:
            self.category_combo.config(state="readonly")
            self.category_var.set(cats[0])
            self.cat_button_frame.grid()
        else:
            self.category_combo.set("")
            self.category_combo.config(state="disabled")
            self.cat_button_frame.grid_remove()

    def _add_category(self):
        new_cat = simpledialog.askstring("Add Category", "Enter new category:",
                                         parent=self.root)
        if new_cat:
            new_cat = new_cat.strip()
            if not new_cat:
                return
            t_type = self.type_var.get()
            self.category_mgr.add(t_type, new_cat)
            self._update_category_options()
            self.category_var.set(new_cat)

    def _delete_category(self):
        cat = self.category_var.get()
        if not cat:
            messagebox.showwarning("Delete Category", "No category selected.")
            return
        t_type = self.type_var.get()
        try:
            self.category_mgr.delete(t_type, cat)
            self._update_category_options()
            cats = self.category_mgr.income if t_type == "Income" else self.category_mgr.expense
            if cats:
                self.category_var.set(cats[0])
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _add_transaction(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showwarning("Invalid Amount", "Please enter a valid number.")
            return
        t_type = self.type_var.get()
        category = self.category_var.get()
        if not t_type or not category:
            messagebox.showwarning("Missing Info", "Please select type and category.")
            return
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        if t_type == "Income":
            trans = IncomeTransaction(amount, category, timestamp)
        else:
            trans = ExpenseTransaction(amount, category, timestamp)
        self.transaction_mgr.add(trans)
        self.transaction_mgr.save()
        self._update_balance_str()
        self._refresh_transaction_list()
        self._clear_inputs()

    def _edit_transaction(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = int(selected[0])
        transaction = self.transaction_mgr.transactions[index]
        dlg = EditTransactionDialog(self.root, transaction,
                                    self.category_mgr.income,
                                    self.category_mgr.expense)
        self.root.wait_window(dlg)
        if dlg.result is not None:
            self.transaction_mgr.edit(index, dlg.result)
            self.transaction_mgr.save()
            self._update_balance_str()
            self._refresh_transaction_list()

    def _delete_transaction(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = int(selected[0])
        if messagebox.askyesno("Delete Transaction", "Are you sure you want to delete this transaction?",
                                parent=self.root):
            self.transaction_mgr.delete(index)
            self.transaction_mgr.save()
            self._update_balance_str()
            self._refresh_transaction_list()

    def _save_edit(self):
        pass  # kept for compatibility

    def _cancel_edit(self):
        self._clear_inputs()
        self.tree.selection_remove(self.tree.selection())

    def _refresh_transaction_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, trans in enumerate(self.transaction_mgr.transactions):
            if trans.deleted:
                continue
            tag = "income" if isinstance(trans, IncomeTransaction) else "expense"
            sign = "+" if tag == "income" else "-"
            amount_str = f"{sign}{trans.amount}"
            self.tree.insert("", "end", iid=str(idx),
                             values=(trans.category, amount_str, trans.timestamp),
                             tags=(tag,))

    def _on_transaction_select(self, event):
        if self.tree.selection():
            self.edit_btn.pack(side="left", padx=5)
            self.delete_btn.pack(side="left", padx=5)
        else:
            self.edit_btn.pack_forget()
            self.delete_btn.pack_forget()
        self.save_btn.pack_forget()
        self.cancel_btn.pack_forget()

    def _clear_inputs(self):
        self.amount_entry.delete(0, "end")
        self.type_var.set("")
        self.category_var.set("")
        self.category_combo.config(state="disabled")
        self.cat_button_frame.grid_remove()

    # ------------------------------------------------------------------
    # Window Closing
    # ------------------------------------------------------------------
    def on_closing(self):
        if not self.config_mgr.ask_on_exit:
            self.root.destroy()
            return
        dlg = ExitConfirmDialog(self.root)
        self.root.wait_window(dlg)
        if dlg.result:
            if dlg.dont_ask:
                self.config_mgr.ask_on_exit = False
                self.config_mgr.save()
            self.root.destroy()


# ----------------------------------------------------------------------
# Entry Point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()
