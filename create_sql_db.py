import sqlite3
import yfinance as yf
from sp500_tickers import sp500_tickers

sp500_tickers = list(sp500_tickers.values())

print(sp500_tickers)

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect('sp500_financials.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS company_financials
(ticker TEXT PRIMARY KEY, 
 company_name TEXT,
 sector TEXT,
 market_cap REAL,
 pe_ratio REAL,
 dividend_yield REAL,
 earnings_per_share REAL,
 fifty_two_week_high REAL,
 fifty_two_week_low REAL)
''')

# Fetch data and insert into database
for ticker in sp500_tickers:
    stock = yf.Ticker(ticker)
    info = stock.info
    
    cursor.execute('''
    INSERT OR REPLACE INTO company_financials 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ticker,
        info.get('longName'),
        info.get('sector'),
        info.get('marketCap'),
        info.get('trailingPE'),
        info.get('dividendYield'),
        info.get('trailingEps'),
        info.get('fiftyTwoWeekHigh'),
        info.get('fiftyTwoWeekLow')
    ))

# Commit changes and close connection
conn.commit()
conn.close()

print("Database created and populated successfully.")