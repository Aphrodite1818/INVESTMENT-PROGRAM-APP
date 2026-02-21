# Family Investment App

A Streamlit-based contribution management app for a family investment program.

The app uses Google Sheets as the backend datastore and supports:
- Secure login/signup (hashed passwords)
- Persistent login across refresh (until logout)
- User contribution submission
- User analytics dashboard
- Admin dashboard and review workflows
- CSV exports for admin reporting

## Current Contribution Rules

- Program duration: 10 months
- Current active week starts at week 6
- Allowed contribution week range: week 6 to week 40
- Minimum contribution amount: `N1000`
- One submission per user per week (duplicate week submissions are blocked)

## Roles and Pages

### Login (`src/pages/login.py`)
- Users can log in or sign up
- New users are automatically logged in after successful signup
- Passwords are hashed with SHA-256 + salt before storage
- `admin` username is routed to admin pages

### User Dashboard (`src/pages/user_dashboard.py`)
- Shows user KPIs and fund-wide analytics
- Displays contribution trends and equity split
- Provides quick navigation to submission page

### Submit Contribution (`src/pages/submit_receipt.py`)
- Accepts only:
  - contribution amount
- Validates:
  - amount >= `N1000`
  - weekly order enforcement (missed weeks are paid first)
  - one contribution per open week
  - no duplicate submission for same user/week
- Saves to Google Sheets and redirects back to dashboard automatically

### Admin Dashboard (`src/pages/Admin_dashboard.py`)
- Tracks fund health with KPIs
- Filters by member, month, and week
- Shows top contributors, monthly inflow, and recent submissions
- CSV export for recent submissions

### Admin Review (`src/pages/Admin_review.py`)
- Reviews submission coverage for weeks 6-40
- Identifies missing weeks by member
- Member-level drilldown with missing week list
- CSV exports for:
  - missing weeks by member
  - selected member missing weeks
  - full contribution log

## Data Layer

### Transactions (`src/Database/GOOGLE_SHEETS.py`)
- `get_transaction_data()` reads transaction records
- `append_transaction()` appends new contribution entries
- Uses caching (`st.cache_resource` + `st.cache_data`) for faster page response
- Automatically clears cache after write operations

### Authentication (`src/Database/GOOGLE_SHEETS_AUTH.py`)
- Reads authentication worksheet
- Uses caching for fast auth lookups
- Cache is invalidated after signup changes

### Cleaning (`src/Tools/data_clean.py`)
- Normalizes columns
- Cleans amount/date/week values
- Ensures downstream dashboards are stable

## Google Sheet Requirements

Your Google Sheet should include at least:
- `NAME`
- `AMOUNT PAID`
- `DATE` (format `dd/mm/YYYY`)
- `WEEK` (example: `week 6`)

Authentication worksheet should include:
- `USERNAME`
- `PASSWORD`

## Project Structure

```text
src/
  app.py
  Database/
    GOOGLE_SHEETS.py
    GOOGLE_SHEETS_AUTH.py
  Tools/
    Auth.py
    data_clean.py
    background.py
  pages/
    login.py
    user_dashboard.py
    submit_receipt.py
    Admin_dashboard.py
    Admin_review.py
```

## Setup

1. Create and activate virtual environment

```powershell
python -m venv Venv
.\Venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Place your service account key in project root:
- `Database_credentials.json`

4. Run app

```powershell
streamlit run src/app.py
```

## Deployment Notes

- Do not commit `Database_credentials.json`
- Ensure the deployed environment has access to the same Google Sheet
- Service account must have edit access to transaction and authentication worksheets
- Caching is enabled for speed; admin refresh buttons force a fresh read

## Troubleshooting

- `NoSessionContext` error: run with `streamlit run src/app.py` (not `python src/app.py`)
- Missing columns error: verify sheet headers match required names exactly
- Permission errors: recheck service account sharing on the sheet

## Tech Stack

- Streamlit
- Pandas
- Plotly
- gspread
- google-auth
