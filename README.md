# 💰 Financial Budget Tracker API

> A RESTful microservice built with **Python 3.11+**, **FastAPI**, and **Pydantic** to manage financial ledgers, category balances, transfers, and generate text-based spending charts.

---

## 🚀 Features

- **Object-Oriented Architecture (OOP)**: Core business logic implemented with encapsulated `Category` classes.
- **Ledger & Balance Management**: Record deposits and withdrawals with auto-calculated balances.
- **Inter-Category Transfers**: Safely transfer funds between categories with validation (`check_funds`).
- **ASCII Spend Charting**: Generate percentage-based spending charts across categories (calculated exclusively from withdrawals).
- **Interactive Documentation**: Auto-generated OpenAPI/Swagger UI endpoints.

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **FastAPI**: Modern, fast web framework for building APIs with Python.
- **Uvicorn**: Lightning-fast ASGI server.
- **Pydantic**: Data validation and setting management using Python type annotations.

---

## 📂 Project Structure

```text
budget-tracker-api/
│
├── main.py              # Application entry point, core logic, and FastAPI endpoints
├── requirements.txt     # Third-party Python dependencies
└── README.md            # Technical documentation
