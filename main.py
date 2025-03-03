import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, ctx
import numpy as np
import pandas as pd

def calculate_mortgage_payment(principal, annual_rate, years):
    """
    Calculate the fixed monthly mortgage payment using the standard amortization formula.
    
    The formula used is: PMT = P * (r(1+r)^n)/((1+r)^n-1)
    Where:
    - PMT = Monthly Payment
    - P = Principal (loan amount)
    - r = Monthly Interest Rate (annual rate / 12)
    - n = Total Number of Months (years * 12)
    
    Learn more: https://www.bankrate.com/mortgages/mortgage-calculator/
    
    Args:
        principal (float): The loan amount
        annual_rate (float): Annual interest rate as decimal (e.g., 0.05 for 5%)
        years (int): Loan term in years
    
    Returns:
        float: Fixed monthly payment amount
    """
    r = annual_rate / 12  # Convert annual rate to monthly
    n = years * 12        # Convert years to months
    return principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

def calculate_mortgage_data(principal, annual_rate, years, monthly_payment):
    """
    Calculate complete mortgage amortization schedule data.
    
    For each payment period:
    1. Interest = Previous Balance * Monthly Rate
    2. Principal Paid = Monthly Payment - Interest
    3. New Balance = Previous Balance - Principal Paid
    
    Learn more: https://www.investopedia.com/terms/a/amortization.asp
    
    Args:
        principal (float): Initial loan amount
        annual_rate (float): Annual interest rate as decimal
        years (int): Loan term in years
        monthly_payment (float): Fixed monthly payment amount
    
    Returns:
        tuple: (months, balance, interest_paid, cumulative_payments)
        - months: Array of payment periods
        - balance: Array of remaining principal balance
        - interest_paid: Array of cumulative interest paid
        - cumulative_payments: Array of total payments made
    """
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
    return months, balance, interest_paid, cumulative_payments

def calculate_investment_growth(monthly_investment, initial_investment, annual_return, months):
    """
    Calculate growth of regular investments with compound interest.
    
    This function models:
    1. Initial investment growing with compound interest
    2. Regular monthly contributions also growing with compound interest
    3. New contributions made at the end of each month
    
    Uses the compound interest formula with regular contributions:
    FV = P(1 + r)^t + PMT * [((1 + r)^t - 1) / r]
    Where:
    - FV = Future Value
    - P = Principal (initial_investment)
    - PMT = Regular Payment (monthly_investment)
    - r = Monthly Interest Rate
    - t = Time in months
    
    Learn more: https://www.investopedia.com/terms/c/compoundinterest.asp
    
    Args:
        monthly_investment (float): Regular monthly contribution amount
        initial_investment (float): Starting investment amount
        annual_return (float): Annual return rate as decimal
        months (int): Number of months to calculate
    
    Returns:
        numpy.array: Array of investment values over time
    """
    monthly_rate = annual_return / 12
    investment_value = np.zeros(months + 1)
    investment_value[0] = initial_investment
    
    for i in range(1, months + 1):
        # Previous balance grows for one month
        investment_value[i] = investment_value[i-1] * (1 + monthly_rate)
        # Add new monthly investment
        investment_value[i] += monthly_investment
    
    return investment_value

def calculate_home_value(initial_value, annual_appreciation, months):
    """
    Calculate home value appreciation over time using compound growth.
    
    Uses continuous compound growth formula: FV = PV * (1 + r)^t
    Where:
    - FV = Future Value
    - PV = Present Value (initial_value)
    - r = Monthly appreciation rate
    - t = Number of months
    
    Learn more: https://www.investopedia.com/terms/r/real-estate-appreciation.asp
    
    Args:
        initial_value (float): Starting home value
        annual_appreciation (float): Annual appreciation rate as decimal
        months (int): Number of months to calculate
    
    Returns:
        numpy.array: Array of home values over time
    """
    monthly_rate = annual_appreciation / 12
    values = np.zeros(months + 1)
    values[0] = initial_value
    
    for i in range(1, months + 1):
        values[i] = values[i-1] * (1 + monthly_rate)
    
    return values

def calculate_monthly_rent(initial_rent, annual_increase, months):
    """
    Calculate monthly rent amounts accounting for annual increases.
    
    Rent typically increases yearly rather than monthly. This function:
    1. Maintains constant rent within each year
    2. Applies increase at each 12-month mark
    3. Uses compound growth for yearly increases
    
    Learn more: https://www.investopedia.com/terms/r/rental-real-estate-loss-allowance.asp
    
    Args:
        initial_rent (float): Starting monthly rent
        annual_increase (float): Annual rent increase as decimal
        months (int): Number of months to calculate
    
    Returns:
        numpy.array: Array of monthly rent amounts
    """
    monthly_rents = np.zeros(months + 1)
    monthly_rents[0] = initial_rent
    
    for i in range(1, months + 1):
        if i % 12 == 0:  # Increase rent yearly
            monthly_rents[i] = monthly_rents[i-1] * (1 + annual_increase)
        else:
            monthly_rents[i] = monthly_rents[i-1]
    
    return monthly_rents

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Mortgage Cost Calculator', style={'color': 'white', 'textAlign': 'center'}),
    
    # Net Position Plot
    html.Div([
        dcc.Graph(id='net-position-plot', config={'modeBarButtonsToRemove': ['autoScale2d']})
    ], style={'padding': '20px'}),
    
    html.Div([
        # Left column for inputs
        html.Div([
            # Mortgage section
            html.H3('Mortgage Details', style={
                'marginTop': '20px', 
                'marginBottom': '10px',
                'color': 'white'
            }),
            
            html.Label('Home Price ($)'),
            html.Div([
                dcc.Input(id='home-price', type='number', value=375000, style={'width': '50%'}),
                dcc.Slider(id='home-price-slider', min=100000, max=1000000, value=375000, 
                          marks={i: f'${i:,}' for i in range(100000, 1100000, 200000)})
            ]),
            
            html.Label('Down Payment ($)'),
            html.Div([
                dcc.Input(id='down-payment', type='number', value=75000, style={'width': '50%'}),
                dcc.Slider(id='down-payment-slider', min=0, max=200000, value=75000,
                          marks={i: f'${i:,}' for i in range(0, 220000, 40000)})
            ]),
            
            html.Label('Annual Interest Rate (%)'),
            html.Div([
                dcc.Input(id='interest-rate', type='number', value=5, style={'width': '50%'}),
                dcc.Slider(id='interest-rate-slider', min=0, max=10, value=5, step=0.1,
                          marks={i: f'{i}%' for i in range(0, 11, 2)})
            ]),
            
            html.Label('Loan Term (years)'),
            dcc.Dropdown(
                id='loan-term',
                options=[
                    {'label': '15 years', 'value': 15},
                    {'label': '20 years', 'value': 20},
                    {'label': '25 years', 'value': 25},
                    {'label': '30 years', 'value': 30}
                ],
                value=30
            ),
            
            html.Label('Annual Home Appreciation (%)'),
            html.Div([
                dcc.Input(id='home-appreciation', type='number', value=3, style={'width': '50%'}),
                dcc.Slider(id='home-appreciation-slider', min=0, max=10, value=3, step=0.1,
                          marks={i: f'{i}%' for i in range(0, 11, 2)})
            ]),
            
            html.Label('Monthly Home Expenses ($)'),
            html.Div([
                dcc.Input(id='home-expenses', type='number', value=500, style={'width': '50%'}),
                dcc.Slider(id='home-expenses-slider', min=0, max=2000, value=500,
                          marks={i: f'${i}' for i in range(0, 2200, 400)})
            ]),
            
            # Rent comparison section
            html.H3('Rent Comparison', style={
                'marginTop': '30px', 
                'marginBottom': '10px',
                'color': 'white'
            }),
            
            html.Label('Monthly Rent ($)'),
            html.Div([
                dcc.Input(id='monthly-rent', type='number', value=2000, style={'width': '50%'}),
                dcc.Slider(id='monthly-rent-slider', min=500, max=5000, value=2000,
                          marks={i: f'${i}' for i in range(500, 5500, 1000)})
            ]),
            
            html.Label('Annual Rent Increase (%)'),
            html.Div([
                dcc.Input(id='rent-increase', type='number', value=3, style={'width': '50%'}),
                dcc.Slider(id='rent-increase-slider', min=0, max=10, value=3, step=0.1,
                          marks={i: f'{i}%' for i in range(0, 11, 2)})
            ]),
            
            html.Label('Monthly Rental Expenses ($)'),
            html.Div([
                dcc.Input(id='rent-expenses', type='number', value=200, style={'width': '50%'}),
                dcc.Slider(id='rent-expenses-slider', min=0, max=1000, value=200,
                          marks={i: f'${i}' for i in range(0, 1100, 200)})
            ]),
            
            html.Label('Investment Return Rate (%)'),
            html.Div([
                dcc.Input(id='investment-rate', type='number', value=7, style={'width': '50%'}),
                dcc.Slider(id='investment-rate-slider', min=0, max=15, value=7, step=0.1,
                          marks={i: f'{i}%' for i in range(0, 16, 3)})
            ]),
        ], style={
            'width': '25%',
            'padding': '20px',
            'display': 'flex',
            'flexDirection': 'column',
            'gap': '10px',
            'backgroundColor': '#2b2b2b',
            'borderRadius': '10px'
        }),
        
        # Right column for plots
        html.Div([
            dcc.Graph(id='mortgage-plot', config={'modeBarButtonsToRemove': ['autoScale2d']}),
            dcc.Graph(id='rent-vs-buy-plot', config={'modeBarButtonsToRemove': ['autoScale2d']})
        ], style={
            'width': '75%',
            'padding': '20px'
        })
    ], style={
        'display': 'flex',
        'flexDirection': 'row'
    })
], style={
    'backgroundColor': '#1f1f1f',
    'minHeight': '100vh',
    'padding': '20px'
})

@app.callback(
    [Output('net-position-plot', 'figure'),
     Output('mortgage-plot', 'figure'),
     Output('rent-vs-buy-plot', 'figure')],
    [Input('home-price', 'value'),
     Input('down-payment', 'value'),
     Input('interest-rate', 'value'),
     Input('loan-term', 'value'),
     Input('home-appreciation', 'value'),
     Input('home-expenses', 'value'),
     Input('monthly-rent', 'value'),
     Input('rent-increase', 'value'),
     Input('rent-expenses', 'value'),
     Input('investment-rate', 'value'),
     Input('mortgage-plot', 'relayoutData'),
     Input('rent-vs-buy-plot', 'relayoutData'),
     Input('net-position-plot', 'relayoutData')]
)
def update_graphs(home_price, down_payment, interest_rate, loan_term, 
                 home_appreciation, home_expenses, monthly_rent, 
                 rent_increase, rent_expenses, investment_rate,
                 mortgage_relayout, rent_relayout, net_relayout):
    if not all([home_price, down_payment, interest_rate, loan_term, 
                home_appreciation, monthly_rent, rent_increase, investment_rate]):
        return go.Figure(), go.Figure(), go.Figure()
    
    # First plot calculations
    loan_amount = home_price - down_payment
    annual_rate = interest_rate / 100
    monthly_payment = calculate_mortgage_payment(loan_amount, annual_rate, loan_term)
    months, balance, interest_paid, cumulative_payments = calculate_mortgage_data(
        loan_amount, annual_rate, loan_term, monthly_payment
    )
    
    # Calculate home value appreciation
    home_values = calculate_home_value(home_price, home_appreciation/100, len(months)-1)
    
    # Calculate equity including appreciation
    equity = np.zeros(len(months))
    equity[0] = down_payment
    equity[1:] = home_values[1:] - balance[1:]
    
    # Add home expenses to cumulative payments
    cumulative_home_expenses = months * home_expenses
    total_home_costs = cumulative_payments + cumulative_home_expenses
    
    # Calculate monthly rent with annual increases
    monthly_rents = calculate_monthly_rent(monthly_rent, rent_increase/100, len(months)-1)
    cumulative_rent = np.cumsum(monthly_rents)
    
    # Add rental expenses
    cumulative_rent_expenses = months * rent_expenses
    total_rent_costs = cumulative_rent + cumulative_rent_expenses
    
    # Calculate investment opportunity (down payment + monthly savings)
    monthly_investment = monthly_rents + rent_expenses - (monthly_payment + home_expenses)
    investment_return = investment_rate / 100
    
    investment_value = calculate_investment_growth(
        np.mean(monthly_investment),
        down_payment, 
        investment_return, 
        len(months) - 1
    )
    
    # Calculate net position (investment minus total rent costs)
    net_position = investment_value - total_rent_costs
    
    dates = [pd.Timestamp.now() + pd.DateOffset(months=int(m)) for m in months]
    
    # Get the date range from whichever plot was updated
    xaxis_range = None
    ctx_trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if ctx_trigger in ['mortgage-plot', 'rent-vs-buy-plot', 'net-position-plot'] and ctx.triggered[0]['value']:
        relayout_data = ctx.triggered[0]['value']
        if 'xaxis.range[0]' in relayout_data:
            xaxis_range = [
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ]
    
    # Create dark theme template
    dark_template = dict(
        plot_bgcolor='#2b2b2b',
        paper_bgcolor='#2b2b2b',
        font=dict(color='white'),
        xaxis=dict(
            gridcolor='#404040',
            tickformat='%b %Y',
            tickangle=45,
            range=xaxis_range
        ),
        yaxis=dict(
            gridcolor='#404040',
            fixedrange=True
        )
    )
    
    # Net Position Plot
    fig_net = go.Figure()
    fig_net.add_trace(go.Scatter(
        x=dates,
        y=net_position,
        name='Net Position',
        mode='lines+markers',
        line=dict(color='#00ff00', width=3)
    ))
    
    fig_net.update_layout(
        title='Net Position Over Time',
        xaxis_title='Date',
        yaxis_title='Amount ($)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        dragmode='zoom',
        **dark_template
    )
    
    # First figure
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dates, y=balance, name='Principal Balance', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=interest_paid, name='Cumulative Interest', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=cumulative_payments, name='Monthly Payments', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=cumulative_home_expenses, name='Home Expenses', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=total_home_costs, name='Total Costs (incl. Expenses)', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=equity, name='Home Equity', mode='lines+markers'))
    fig1.add_trace(go.Scatter(x=dates, y=home_values, name='Home Value', mode='lines+markers'))
    
    fig1.update_layout(
        title='Mortgage Costs Over Time',
        xaxis_title='Date',
        yaxis_title='Amount ($)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        dragmode='zoom',
        **dark_template
    )
    
    # Second figure
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=dates, y=cumulative_rent, name='Cumulative Rent', mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=dates, y=cumulative_rent_expenses, name='Rental Expenses', mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=dates, y=total_rent_costs, name='Total Rent Costs (incl. Expenses)', mode='lines+markers'))
    fig2.add_trace(go.Scatter(x=dates, y=investment_value, name='Investment Value', mode='lines+markers'))
    
    fig2.update_layout(
        title='Rent vs. Buy Comparison',
        xaxis_title='Date',
        yaxis_title='Amount ($)',
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        dragmode='zoom',
        **dark_template
    )
    
    return fig_net, fig1, fig2

# Replace the individual callbacks with this pattern-matching callback
@app.callback(
    Output('home-price', 'value'),
    Output('home-price-slider', 'value'),
    Input('home-price', 'value'),
    Input('home-price-slider', 'value'),
    prevent_initial_call=True
)
def sync_home_price(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "home-price":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('down-payment', 'value'),
    Output('down-payment-slider', 'value'),
    Input('down-payment', 'value'),
    Input('down-payment-slider', 'value'),
    prevent_initial_call=True
)
def sync_down_payment(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "down-payment":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('interest-rate', 'value'),
    Output('interest-rate-slider', 'value'),
    Input('interest-rate', 'value'),
    Input('interest-rate-slider', 'value'),
    prevent_initial_call=True
)
def sync_interest_rate(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "interest-rate":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('home-appreciation', 'value'),
    Output('home-appreciation-slider', 'value'),
    Input('home-appreciation', 'value'),
    Input('home-appreciation-slider', 'value'),
    prevent_initial_call=True
)
def sync_home_appreciation(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "home-appreciation":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('home-expenses', 'value'),
    Output('home-expenses-slider', 'value'),
    Input('home-expenses', 'value'),
    Input('home-expenses-slider', 'value'),
    prevent_initial_call=True
)
def sync_home_expenses(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "home-expenses":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('monthly-rent', 'value'),
    Output('monthly-rent-slider', 'value'),
    Input('monthly-rent', 'value'),
    Input('monthly-rent-slider', 'value'),
    prevent_initial_call=True
)
def sync_monthly_rent(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "monthly-rent":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('rent-increase', 'value'),
    Output('rent-increase-slider', 'value'),
    Input('rent-increase', 'value'),
    Input('rent-increase-slider', 'value'),
    prevent_initial_call=True
)
def sync_rent_increase(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "rent-increase":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('rent-expenses', 'value'),
    Output('rent-expenses-slider', 'value'),
    Input('rent-expenses', 'value'),
    Input('rent-expenses-slider', 'value'),
    prevent_initial_call=True
)
def sync_rent_expenses(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "rent-expenses":
        return input_value, input_value
    else:
        return slider_value, slider_value

@app.callback(
    Output('investment-rate', 'value'),
    Output('investment-rate-slider', 'value'),
    Input('investment-rate', 'value'),
    Input('investment-rate-slider', 'value'),
    prevent_initial_call=True
)
def sync_investment_rate(input_value, slider_value):
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger_id == "investment-rate":
        return input_value, input_value
    else:
        return slider_value, slider_value

if __name__ == '__main__':
    app.run_server(debug=True)

