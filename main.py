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