import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import numpy as np

def calculate_mortgage_payment(principal, annual_rate, years):
    """Calculate the monthly mortgage payment."""
    r = annual_rate / 12
    n = years * 12
    return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

def calculate_mortgage_data(principal, annual_rate, years, monthly_payment):
    """Calculate mortgage amortization data."""
    monthly_rate = annual_rate / 12
    n_payments = years * 12
    
    months = np.arange(n_payments + 1)
    balance = np.zeros(n_payments + 1)
    interest_paid = np.zeros(n_payments + 1)
    
    balance[0] = principal
    
    for i in range(1, n_payments + 1):
        interest = balance[i-1] * monthly_rate
        principal_paid = monthly_payment - interest
        balance[i] = balance[i-1] - principal_paid
        interest_paid[i] = interest_paid[i-1] + interest
    
    cumulative_payments = months * monthly_payment
    
    return months/12, balance, interest_paid, cumulative_payments

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Mortgage Cost Calculator'),
    
    html.Div([
        html.Label('Loan Amount ($)'),
        dcc.Input(id='loan-amount', type='number', value=300000),
        
        html.Label('Annual Interest Rate (%)'),
        dcc.Input(id='interest-rate', type='number', value=5),
        
        html.Label('Loan Term (years)'),
        dcc.Input(id='loan-term', type='number', value=30),
    ]),
    
    dcc.Graph(id='mortgage-plot')
])

@app.callback(
    Output('mortgage-plot', 'figure'),
    [Input('loan-amount', 'value'),
     Input('interest-rate', 'value'),
     Input('loan-term', 'value')]
)
def update_graph(loan_amount, interest_rate, loan_term):
    if not all([loan_amount, interest_rate, loan_term]):
        return go.Figure()
    
    annual_rate = interest_rate / 100
    monthly_payment = calculate_mortgage_payment(loan_amount, annual_rate, loan_term)
    years, balance, interest_paid, cumulative_payments = calculate_mortgage_data(
        loan_amount, annual_rate, loan_term, monthly_payment
    )
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=balance, name='Principal Balance'))
    fig.add_trace(go.Scatter(x=years, y=interest_paid, name='Cumulative Interest'))
    fig.add_trace(go.Scatter(x=years, y=cumulative_payments, name='Total Payments'))
    
    fig.update_layout(
        title='Mortgage Costs Over Time',
        xaxis_title='Years',
        yaxis_title='Amount ($)',
        hovermode='x unified'
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)

