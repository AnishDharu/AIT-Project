# BizFlow — Smart Business Operations & Profit Intelligence System

MCA Advanced Internet Technology (AIT) project starter built with **React + Vite**, **Django REST Framework**, and **MySQL**.

## Included in this starter

- Django REST API with JWT authentication
- MySQL configuration through environment variables
- Business profile, products, categories, customers, suppliers, sales, sale items, expenses, purchases, purchase items, stock movements
- Dashboard summary and sales chart endpoints
- Stock validation and transactional sales/purchase workflows
- Basic React dashboard and pages for products, sales, expenses, customers
- Responsive sidebar layout and API client
- Development seed command
- Environment examples and setup instructions

> This is a runnable starter/MVP, not a production-audited financial system. Before production use, add stronger test coverage, deployment hardening, tax/accounting review, and any missing UI workflows.

## Requirements

- Python 3.11+ (use a Python version supported by your chosen Django release)
- Node.js 20+
- MySQL 8+
- MySQL Workbench (optional, for viewing the database)

## 1. Create the MySQL database

Open MySQL Workbench and run:

```sql
CREATE DATABASE bizflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Create a dedicated database user if preferred. Do not use your root account in a deployed application.

## 2. Configure the backend

Open PowerShell in `BizFlow/backend`:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your local MySQL credentials. Do not commit `.env` to Git.

```powershell
python manage.py makemigrations core
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend: `http://127.0.0.1:8000/`  
Django admin: `http://127.0.0.1:8000/admin/`  
API root: `http://127.0.0.1:8000/api/`

If `mysqlclient` fails to install on Windows, check the package's current Windows/Python compatibility notes. The project uses Django's MySQL backend and expects a working MySQL driver.

## 3. Configure the frontend

Open a second PowerShell terminal in `BizFlow/frontend`:

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Frontend: `http://localhost:5173/`

The React app uses `VITE_API_BASE_URL=http://127.0.0.1:8000/api`.

## 4. API endpoints

Authentication:
- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`

Business data:
- `GET/POST /api/categories/`
- `GET/POST /api/products/`
- `GET/POST /api/customers/`
- `GET/POST /api/suppliers/`
- `GET/POST /api/expenses/`
- `GET/POST /api/sales/`
- `GET /api/sales/{id}/`
- `GET/POST /api/purchases/`
- `GET /api/dashboard/summary/`
- `GET /api/dashboard/sales-chart/`

The API uses JWT bearer tokens. Obtain a token from `/api/auth/token/` with `username` and `password`; send it as `Authorization: Bearer <access-token>`.

## 5. Business rules in this starter

- Products, customers, suppliers, expenses and transactions are scoped to the authenticated user's business.
- A user creates a default business at registration.
- Sales are saved with line items and reduce stock inside a database transaction.
- Purchases are saved with line items and increase stock inside a database transaction.
- A sale cannot be completed when available stock is insufficient.
- Money fields use decimal database fields and backend-side calculations.
- Dashboard net profit is a simplified estimate: sales revenue minus the recorded cost of goods sold for sold items minus operating expenses in the selected aggregate. It is not a substitute for professional accounting/tax advice.
- GST/tax calculation is intentionally not hard-coded; configure applicable tax rules for the business and jurisdiction before using real invoices.

## 6. Seed sample data (optional)

After creating a superuser and logging in, you can run:

```powershell
python manage.py seed_demo
```

This command creates demo categories and products for the first available user. It will not create duplicate demo SKUs.

## 7. Suggested next milestones

1. Add comprehensive unit and integration tests for every workflow.
2. Add PDF invoices and CSV exports.
3. Add date filters and detailed reports.
4. Add role-based staff memberships and business-level multi-user isolation.
5. Add pagination, search and filtering to all list endpoints.
6. Add frontend forms for purchases, suppliers, categories, settings and reports.
7. Add secure refresh-token lifecycle handling and production deployment settings.
8. Add a formal ER diagram and MCA report.

## Folder structure

```text
BizFlow/
  backend/
    config/
    core/
      management/commands/seed_demo.py
    manage.py
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      pages/
      services/
    package.json
    .env.example
  docs/
    database-design.md
    viva-questions.md
```

## Expanded feature modules (October 2026)

The expanded version adds:
- Business health endpoint (`/api/dashboard/health/`) with inventory, sales and profit indicators.
- Dead-stock endpoint (`/api/dead-stock/`): products with no recorded sale or a last sale at least 15 days ago.
- Purchase planner (`/api/purchase-planner/`) using last-30-day sales and minimum stock thresholds.
- Rule-based Business Copilot (`POST /api/copilot/`) that analyses saved business records. It is **not** an external LLM integration.
- Date-filtered reports (`/api/reports/?range=today|7d|30d|6m`, or `range=custom&start=YYYY-MM-DD&end=YYYY-MM-DD`).
- Manual stock adjustment endpoint (`POST /api/products/<id>/stock-adjustment/`).
- Invoice PDF endpoint (`/api/sales/<id>/invoice.pdf`) and download button in Sales history.
- Purchase OCR review endpoint (`POST /api/purchase-ocr/`, multipart field `file`) and review UI. OCR output is not auto-imported; verify it before entering a purchase.
- Supplier and purchase recording pages. Receiving a purchase increases stock and updates indicative purchase cost.
- React Intelligence Hub with health scores, Copilot, purchase planner, OCR review, dead stock and date-filtered reports.

### Setup / migration

From `backend` with the backend virtual environment activated:

```powershell
python -m pip install -r requirements.txt
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver
```

From `frontend` in a separate terminal:

```powershell
npm install
npm run dev
```

### OCR note

PDF text extraction uses PyMuPDF. Image OCR uses Pillow + pytesseract and also requires the **Tesseract OCR engine** installed on the operating system. If Tesseract is missing, the endpoint returns an explanatory error. OCR results are drafts; automatic product matching/import is not claimed as completed. The PDF invoice is a basic project invoice layout; add and verify your registered business GST details before treating it as a statutory tax invoice.

### Honest capability notes

The business health scores and purchase planner are transparent heuristics, not trained predictive models. The Copilot is database-driven/rule-based until an external AI provider is configured. The OCR endpoint extracts text and candidate amounts/dates, but does not guarantee line-item accuracy. Test all workflows with demo records before a project presentation.


## Gemini Business Copilot (optional)

1. Copy `backend/.env.example` to `backend/.env`.
2. Put a newly generated Gemini API key in `GEMINI_API_KEY`. Do not share or commit the key.
3. Restart Django. The Copilot uses Gemini when configured and falls back to local rule-based insights if the key/network is unavailable.
4. Configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` for your local MySQL instance. The database and MySQL user must already exist and have appropriate privileges.

If an API key was posted in chat or another public/shared place, revoke it and create a replacement before use. The real key is intentionally not included in the ZIP.
