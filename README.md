# Data-Driven Curriculum Optimizer

A Python and Streamlit academic analytics application for reviewing student performance, attendance, course performance, learning outcomes, curriculum effectiveness, risk indicators, and recommendations.

## Project structure

```text
app.py
modules/              Python application modules
database/             MySQL schema and sample-data SQL backup
data/                 Input, processed, and generated sample datasets
reports/              Example generated reports
.env.example          Example database configuration (no real credentials)
requirements.txt      Python dependencies
.gitignore            Excludes local secrets and generated cache files
```

## Requirements

- Python 3.10 or newer
- MySQL Server 8.x
- pip

## Installation

1. Clone or download this repository.
2. Open a terminal in the repository root (the folder containing `app.py`).
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Create a MySQL database:

   ```sql
   CREATE DATABASE curriculum_optimizer;
   ```

5. Import the SQL backup from the repository root (adjust the path to your MySQL executable if needed):

   ```bash
   mysql -u root -p curriculum_optimizer < database/curriculum_optimizer.sql
   ```

6. Copy `.env.example` to a new file named `.env` in the repository root. Set the values for your own MySQL installation. Never commit `.env`.

   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=YOUR_LOCAL_MYSQL_PASSWORD
   DB_NAME=curriculum_optimizer
   ```

7. Create/reset demo accounts with passwords you choose locally:

   ```bash
   python -m modules.setup_users
   ```

8. Start the application:

   ```bash
   python -m streamlit run app.py
   ```

9. Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Data and privacy

The repository contains project sample/processed data files used by the application. The SQL backup's pre-existing demo password hashes have been removed; create fresh demo accounts using `python -m modules.setup_users`. Do not add real student records, personal information, database passwords, `.env` files, or other confidential institutional data to a public repository.

## Technologies

Python, Streamlit, MySQL, Pandas, mysql-connector-python, python-dotenv, bcrypt, scikit-learn, and ReportLab.
