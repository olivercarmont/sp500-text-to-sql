import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Custom CSS to set sidebar width
st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 300px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 300px;
        margin-left: -300px;
    }
    .stCode {
        max-height: 300px;
        overflow-y: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Function to execute SQL query and return results as a DataFrame
def execute_query(query):
    conn = sqlite3.connect('sp500_financials.db')
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except sqlite3.Error as e:
        st.error(f"An error occurred: {e}")
        return None
    finally:
        conn.close()

# Function to shorten company name
def shorten_company_name(name):
    # Remove common suffixes and trim
    suffixes = [' Inc.', ' Corp.', ' Corporation', ' Co.', ' Company', ' Ltd.', ' Limited', ' Group', ' Holdings', ' Incorporated']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name.strip()

import plotly.graph_objects as go

def format_market_cap(value):
    if value >= 1e12:
        return f'{value/1e12:.2f}T'
    elif value >= 1e9:
        return f'{value/1e9:.2f}B'
    elif value >= 1e6:
        return f'{value/1e6:.2f}M'
    else:
        return f'{value:.2f}'

# Function to create a bar chart
def create_chart(df, search_term, metric, title):
    fig = go.Figure()
    
    # Shorten company names
    df['short_name'] = df['company_name'].apply(shorten_company_name)
    
    # Sort dataframe by metric value in descending order
    df = df.sort_values(by=metric, ascending=False)
    
    # Define colors
    highlight_color = 'rgba(0, 123, 255, 0.8)'  # Bright blue
    other_color = 'rgba(158, 202, 225, 0.6)'    # Light blue

    # Format hover text
    if metric == 'market_cap':
        hover_text = df[metric].apply(format_market_cap)
    else:
        hover_text = df[metric].apply(lambda x: f'{x:.2f}')

    # Add bars for all companies
    fig.add_trace(go.Bar(
        x=df['short_name'],
        y=df[metric],
        marker_color=[highlight_color if search_term.lower() in company.lower() else other_color for company in df['company_name']],
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        xaxis_title="Company",
        yaxis_title=metric.replace('_', ' ').title(),
        xaxis_tickangle=-45,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(gridcolor='rgba(200,200,200,0.2)'),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_color="black",
            bordercolor="black",
        ),
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    # Format y-axis labels if metric is market_cap
    if metric == 'market_cap':
        fig.update_yaxes(tickformat='.2s', ticksuffix='')
    
    return fig

# Function to display table schema
def display_schema(schema_df):
    for _, row in schema_df.iterrows():
        st.sidebar.text(f"{row['name']} ({row['type']})")

# Streamlit app
st.title('S&P 500 Financials Search Engine')

# Search input using a text input
query = st.text_input("Enter a company name and metric (e.g., 'Apple, market cap' or 'Microsoft, p/e ratio'):")

if query:
    # Clear previous results
    st.empty()

    # Prepare the message for the API
    messages = [
        {"role": "system", "content": """You are a helpful assistant specialized in financial data analysis. You can interpret user queries about S&P 500 companies and their financial metrics.

When a user mentions a company and a metric, identify the company name and the specific metric they're interested in. Valid metrics include market_cap, pe_ratio, dividend_yield, earnings_per_share.

Respond with a JSON object containing:
1. company_name: The name of the company mentioned
2. metric: The financial metric requested (use the database column name)
3. sql_query: An SQL query to fetch the requested data for the company and similar companies

Example SQL query structure:
SELECT company_name, {metric}
FROM company_financials
WHERE company_name LIKE '%{company_name}%' OR {metric} IS NOT NULL
ORDER BY ABS({metric} - (SELECT {metric} FROM company_financials WHERE company_name LIKE '%{company_name}%' LIMIT 1))
LIMIT 10

If you can't interpret the query, respond with: "I'm sorry, I couldn't understand your query. Please try again with a company name and a specific metric."
"""},
        {"role": "user", "content": query}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            response_format={ "type": "json_object" }
        )
        
        response_content = response.choices[0].message.content
        parsed_response = eval(response_content)

        if 'sql_query' in parsed_response:
            st.code(parsed_response['sql_query'], language='sql', line_numbers=True)
            
            results = execute_query(parsed_response['sql_query'])
            if results is not None and not results.empty:
                # Display only the searched company's results
                searched_company = results[results['company_name'].str.contains(parsed_response['company_name'], case=False)].iloc[0]
                searched_company['short_name'] = shorten_company_name(searched_company['company_name'])
                
                # Format the metric value
                if parsed_response['metric'] == 'market_cap':
                    formatted_value = format_market_cap(searched_company[parsed_response['metric']])
                else:
                    formatted_value = f"{searched_company[parsed_response['metric']]:.2f}"
                
                st.dataframe(pd.DataFrame({'Company': [searched_company['short_name']], 
                                           parsed_response['metric'].replace('_', ' ').title(): [formatted_value]}))
                
                # Create chart with all similar companies
                chart = create_chart(results, parsed_response['company_name'], parsed_response['metric'], 
                                     f"{parsed_response['metric'].replace('_', ' ').title()} Comparison")
                st.plotly_chart(chart)
            else:
                st.warning("No results found.")
        else:
            st.warning(parsed_response)

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Display table schema in the sidebar
st.sidebar.header("Table Schema")
schema_query = "PRAGMA table_info(company_financials)"
schema = execute_query(schema_query)
if schema is not None:
    display_schema(schema)