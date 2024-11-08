# S&P 500 Financial Text-To-SQL

## Overview
A Streamlit application that allows users to explore and compare financial metrics across S&P 500 companies using natural language queries.

## Database Schema
 ```sql
TABLE company_financials (
company_name TEXT PRIMARY KEY,
sector TEXT,
market_cap REAL,
pe_ratio REAL,
dividend_yield REAL,
earnings_per_share REAL
);
```

## Installation

1. Clone the repository
    ```bash
    git clone [repository-url]
    cd [repository-name]
    ```

2. Install required packages
    ```bash
    pip install -r requirements.txt
    ```

3. Set up OpenAI API key
    ```bash
    touch .streamlit/secrets.toml
    ```
    Add to secrets.toml:
    ```toml
    OPENAI_API_KEY = "your-api-key-here"
    ```

4. Ensure `sp500_financials.db` is in your project directory

## Usage

1. Start the app
    ```bash
    streamlit run main.py
    ```

2. Enter queries like:
    - "Apple, market cap"
    - "Microsoft, p/e ratio"
    - "Google, dividend yield"

## Technical Details

### Components
- OpenAI GPT-3.5-turbo for query processing
- Plotly for interactive charts
- SQLite for data storage
- Streamlit for web interface

## Dependencies
- streamlit
- plotly
- pandas
- sqlite3
- openai