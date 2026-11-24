# Ajith Food Corner — Restaurant Ordering Web App

A responsive restaurant ordering starter application for **Ajith Food Corner, Chennai**.
Frontend: HTML, CSS, vanilla JavaScript. Backend: Python + Flask. Database: SQLite.

## Included features
- Restaurant landing page with food-led visual design and responsive layout
- Menu loaded from the backend, category filters and search
- Add/remove items, quantity controls, cart subtotal and delivery fee calculation
- Hanging-poster style order summary panel
- Pickup and delivery checkout with basic validation
- Order confirmation with unique tracking code
- Customer order tracking by order code
- Admin login and dashboard to view orders and update order status
- SQLite database is created automatically on first run

## Requirements
- Python 3.10+
- pip

## Run on Windows (Git Bash / PowerShell)
```bash
cd ajith_food_corner
python -m venv venv
# Git Bash:
source venv/Scripts/activate
# PowerShell:
# .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Admin
Open http://127.0.0.1:5000/admin/login

Development default:
- Username: `admin`
- Password: `ChangeMe123!`

Change the password before sharing or deploying. Set environment variables:
```bash
# Git Bash
export SECRET_KEY="use-a-long-random-value"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-strong-password"
python app.py
```

For production, set `ADMIN_PASSWORD_HASH` to a Werkzeug password hash and do not use the development fallback. Generate a hash:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YourStrongPassword'))"
```
Then set `ADMIN_PASSWORD_HASH` to the printed value and unset `ADMIN_PASSWORD`.

## Project structure
```text
ajith_food_corner/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── restaurant.db          # generated automatically after first run
├── templates/
│   ├── index.html
│   ├── admin.html
│   └── admin_login.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## Important before real-world launch
This is a functional starter, not a production payment or delivery platform.
- Replace demo menu/prices in `MENU_SEED` inside `app.py` with the restaurant's approved menu.
- Replace the sample phone/location/contact details in the page with verified business details.
- Add HTTPS, production WSGI server (e.g. Gunicorn), secure secret management, database backups, CSRF protection, rate limiting and proper admin user management.
- Payment is currently **Cash on Delivery / Pay at Counter**. No card/UPI payment is collected by this demo. Add a verified payment gateway only after merchant onboarding.
- Delivery fee is a sample ₹30. Update it to the restaurant's actual delivery policy.
- Food images use remotely hosted Unsplash image URLs; replace them with licensed restaurant photos for launch.
