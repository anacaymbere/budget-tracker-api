import gradio as gr
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

# Initialize FastAPI application
app = FastAPI(
    title="Financial Budget API",
    description="A microservice for managing budget categories, ledgers, transfers, and spend charts built with Python & Object-Oriented Programming (OOP).",
    version="1.0.0"
)


# Core OOP Category class
class Category:
    def __init__(self, name: str):
        self.name = name
        self.ledger: List[dict] = []  

    def deposit(self, amount: float, description: str = ""):
        """Deposits an amount into the category ledger."""
        self.ledger.append({'amount': amount, 'description': description})

    def withdraw(self, amount: float, description: str = "") -> bool:
        """Withdraws an amount if funds are sufficient, storing it as a negative value."""
        if self.check_funds(amount):
            self.ledger.append({'amount': -amount, 'description': description})
            return True
        return False

    def get_balance(self) -> float:
        """Returns the current balance of the category based on the ledger."""
        return sum(item['amount'] for item in self.ledger)

    def transfer(self, amount: float, category: 'Category') -> bool:
        """Transfers an amount to another Category instance if funds permit."""
        if self.withdraw(amount, f'Transfer to {category.name}'):
            category.deposit(amount, f'Transfer from {self.name}')
            return True
        return False

    def check_funds(self, amount: float) -> bool:
        """Returns False if the amount exceeds the current balance, True otherwise."""
        if amount > self.get_balance():
            return False
        return True

    def __str__(self) -> str:
        """Returns a formatted ASCII representation of the category ledger and total."""
        title = self.name.center(30, '*') + '\n'
        items_str = ''
        for item in self.ledger:
            desc = item['description'][:23]
            amount_str = f"{item['amount']:.2f}"
            items_str += f"{desc:<23}{amount_str:>7}\n"
        total = f"Total: {self.get_balance():.2f}"
        return title + items_str + total


# Standalone function to generate a spend chart across multiple categories
def create_spend_chart(categories: List[Category]) -> str:
    """Generates a bar-chart string representing percentage spent by category based on withdrawals."""
    chart = 'Percentage spent by category\n'
    spent_per_category = []
    
    for cat in categories:
        spent = sum(-item['amount'] for item in cat.ledger if item['amount'] < 0)
        spent_per_category.append(spent)
        
    total_spent = sum(spent_per_category)
    
    percentages = []
    if total_spent > 0:
        for spent in spent_per_category:
            percent = int((spent / total_spent) * 100 // 10) * 10
            percentages.append(percent)
    else:
        percentages = [0 for _ in categories]

    # Build the y-axis and chart bars
    for i in range(100, -1, -10):
        chart += f"{i:>3}|"
        for percent in percentages:
            if percent >= i:
                chart += ' o '
            else:
                chart += '   '
        chart += ' \n'

    # Build the horizontal line
    chart += '    ' + '-' * (len(categories) * 3 + 1) + '\n'
    
    # Build the vertical category names
    max_len = max(len(cat.name) for cat in categories)
    names = [cat.name.ljust(max_len) for cat in categories]
    
    for i in range(max_len):
        chart += '     '
        for name in names:
            chart += f'{name[i]}  '
        if i < max_len - 1:
            chart += '\n'
            
    return chart


# In-memory database storage for active categories
database_categories = {}


# Pydantic Schemas
class CategoryCreate(BaseModel):
    name: str = Field(..., example="Food")

class TransactionRequest(BaseModel):
    amount: float = Field(..., example=50.25)
    description: str = Field(default="", example="Groceries")

class TransferRequest(BaseModel):
    amount: float = Field(..., example=20.00)
    destination_category: str = Field(..., example="Clothing")


# API Endpoints
@app.get("/")
def home():
    """Root endpoint for healthcheck and information."""
    return {
        "status": "Financial Budget API online",
        "documentation": "/docs"
    }

@app.post("/categories", status_code=201)
def create_category(payload: CategoryCreate):
    """Creates a new budget category."""
    if payload.name in database_categories:
        raise HTTPException(status_code=400, detail="Category already exists.")
    
    database_categories[payload.name] = Category(payload.name)
    return {"message": f"Category '{payload.name}' created successfully."}

@app.get("/categories")
def list_categories():
    """Returns all active categories and their formatted ASCII ledgers."""
    return {
        name: str(cat) for name, cat in database_categories.items()
    }

@app.post("/categories/{name}/deposit")
def deposit_amount(name: str, payload: TransactionRequest):
    """Deposits funds into a specific category."""
    if name not in database_categories:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    category = database_categories[name]
    category.deposit(payload.amount, payload.description)
    return {"message": "Deposit successful", "new_balance": category.get_balance()}

@app.post("/categories/{name}/withdraw")
def withdraw_amount(name: str, payload: TransactionRequest):
    """Withdraws funds from a category if sufficient balance exists."""
    if name not in database_categories:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    category = database_categories[name]
    success = category.withdraw(payload.amount, payload.description)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient funds for withdrawal.")
    
    return {"message": "Withdrawal successful", "new_balance": category.get_balance()}

@app.post("/categories/{name}/transfer")
def transfer_amount(name: str, payload: TransferRequest):
    """Transfers funds from source category to destination category."""
    if name not in database_categories or payload.destination_category not in database_categories:
        raise HTTPException(status_code=404, detail="Source or destination category not found.")
    
    source = database_categories[name]
    destination = database_categories[payload.destination_category]
    
    success = source.transfer(payload.amount, destination)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient funds for transfer.")
        
    return {
        "message": "Transfer successful",
        f"source_{name}_balance": source.get_balance(),
        f"destination_{payload.destination_category}_balance": destination.get_balance()
    }

@app.get("/spend-chart")
def get_spend_chart():
    """Generates an ASCII spend bar chart for all existing categories."""
    categories_list = list(database_categories.values())
    if not categories_list:
        raise HTTPException(status_code=400, detail="No categories available to generate a chart.")
    
    chart_str = create_spend_chart(categories_list)
    return {"spend_chart": chart_str}


# --- Gradio UI Integration Layer ---

def ui_create_category(name: str) -> str:
    """UI action to create a new budget category."""
    if not name.strip():
        return "Error: Category name cannot be empty."
    if name in database_categories:
        return f"Error: Category '{name}' already exists."
    database_categories[name] = Category(name)
    return f"Success: Category '{name}' created successfully!"

def ui_deposit(category_name: str, amount: float, description: str) -> str:
    """UI action to deposit funds into a category."""
    if category_name not in database_categories:
        return "Error: Category not found."
    if amount <= 0:
        return "Error: Amount must be greater than zero."
    
    category = database_categories[category_name]
    category.deposit(amount, description)
    return f"Success: Deposited {amount:.2f} into '{category_name}'. New Balance: {category.get_balance():.2f}"

def ui_withdraw(category_name: str, amount: float, description: str) -> str:
    """UI action to withdraw funds from a category."""
    if category_name not in database_categories:
        return "Error: Category not found."
    if amount <= 0:
        return "Error: Amount must be greater than zero."
    
    category = database_categories[category_name]
    success = category.withdraw(amount, description)
    if not success:
        return f"Error: Insufficient funds in '{category_name}' for withdrawal."
    
    return f"Success: Withdrew {amount:.2f} from '{category_name}'. New Balance: {category.get_balance():.2f}"

def ui_transfer(source_name: str, dest_name: str, amount: float) -> str:
    """UI action to transfer funds between two categories."""
    if source_name not in database_categories or dest_name not in database_categories:
        return "Error: Source or destination category not found."
    if source_name == dest_name:
        return "Error: Source and destination categories must be different."
    if amount <= 0:
        return "Error: Amount must be greater than zero."
        
    source = database_categories[source_name]
    destination = database_categories[dest_name]
    
    success = source.transfer(amount, destination)
    if not success:
        return f"Error: Insufficient funds in '{source_name}' to execute transfer."
        
    return f"Success: Transferred {amount:.2f} from '{source_name}' to '{dest_name}'."

def ui_list_categories() -> str:
    """UI action to list all categories and their formatted ledgers."""
    if not database_categories:
        return "No categories available yet."
    return "\n\n".join([str(cat) for cat in database_categories.values()])

def ui_get_spend_chart() -> str:
    """UI action to generate and display the spend chart."""
    categories_list = list(database_categories.values())
    if not categories_list:
        return "No categories available to generate a chart."
    return create_spend_chart(categories_list)

def get_category_choices():
    """Helper to dynamically populate dropdown choices."""
    choices = list(database_categories.keys())
    return gr.Dropdown(choices=choices), gr.Dropdown(choices=choices), gr.Dropdown(choices=choices)


# Build Gradio Blocks Layout
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 💰 Financial Budget Tracker")
    gr.Markdown("Manage your categories, deposits, withdrawals, transfers, and view visual ASCII spend charts.")

    with gr.Tabs():
        # Tab 1: Create Category
        with gr.TabItem("Create Category"):
            new_cat_input = gr.Textbox(label="Category Name", placeholder="e.g., Food, Clothing, Auto")
            btn_create = gr.Button("Create Category", variant="primary")
            out_create = gr.Textbox(label="Output Status")
            btn_create.click(fn=ui_create_category, inputs=new_cat_input, outputs=out_create)

        # Tab 2: Deposit
        with gr.TabItem("Deposit"):
            dep_cat_dropdown = gr.Dropdown(label="Select Category", choices=list(database_categories.keys()))
            dep_amount = gr.Number(label="Amount", value=0.0)
            dep_desc = gr.Textbox(label="Description", placeholder="e.g., Initial paycheck")
            btn_deposit = gr.Button("Submit Deposit", variant="primary")
            out_deposit = gr.Textbox(label="Output Status")
            
            # Refresh choices when opening or clicking
            demo.load(fn=get_category_choices, outputs=[dep_cat_dropdown, gr.Dropdown(visible=False), gr.Dropdown(visible=False)])
            btn_deposit.click(fn=ui_deposit, inputs=[dep_cat_dropdown, dep_amount, dep_desc], outputs=out_deposit)

        # Tab 3: Withdraw
        with gr.TabItem("Withdraw"):
            wit_cat_dropdown = gr.Dropdown(label="Select Category", choices=list(database_categories.keys()))
            wit_amount = gr.Number(label="Amount", value=0.0)
            wit_desc = gr.Textbox(label="Description", placeholder="e.g., Groceries")
            btn_withdraw = gr.Button("Submit Withdrawal", variant="primary")
            out_withdraw = gr.Textbox(label="Output Status")
            btn_withdraw.click(fn=ui_withdraw, inputs=[wit_cat_dropdown, wit_amount, wit_desc], outputs=out_withdraw)

        # Tab 4: Transfer
        with gr.TabItem("Transfer"):
            tr_source = gr.Dropdown(label="Source Category", choices=list(database_categories.keys()))
            tr_dest = gr.Dropdown(label="Destination Category", choices=list(database_categories.keys()))
            tr_amount = gr.Number(label="Amount", value=0.0)
            btn_transfer = gr.Button("Submit Transfer", variant="primary")
            out_transfer = gr.Textbox(label="Output Status")
            btn_transfer.click(fn=ui_transfer, inputs=[tr_source, tr_dest, tr_amount], outputs=out_transfer)

        # Tab 5: Ledgers & Summary
        with gr.TabItem("Ledgers & Summary"):
            btn_refresh_ledgers = gr.Button("Refresh All Ledgers")
            out_ledgers = gr.Code(label="Ledgers Overview", language="markdown")
            btn_refresh_ledgers.click(fn=ui_list_categories, outputs=out_ledgers)

        # Tab 6: Spend Chart
        with gr.TabItem("Spend Chart"):
            btn_refresh_chart = gr.Button("Generate Spend Chart")
            out_chart = gr.Code(label="ASCII Spend Chart", language="markdown")
            btn_refresh_chart.click(fn=ui_get_spend_chart, outputs=out_chart)

# Mount Gradio app onto FastAPI root path ("/")
app = gr.mount_gradio_app(app, demo, path="/")