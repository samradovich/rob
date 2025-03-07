import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash

# Constants for Gruvbox theme
COLORS = {
    'background': '#282828',
    'surface': '#3c3836',
    'text': '#ebdbb2',
    'green': '#b8bb26',
    'blue': '#83a598',
    'red': '#fb4934',
    'yellow': '#fabd2f'
}

def calculate_buy_vs_rent(
    # Basic inputs
    home_price=375000,
    monthly_rent=2000,
    years=30,
    # Mortgage details
    down_payment_pct=20,
    mortgage_rate=6.5,
    mortgage_term=30,
    pmi_rate=0.5,
    # Future projections
    home_appreciation=3,
    rent_appreciation=3,
    investment_return=7,
    inflation=2,
    # Tax details
    property_tax_rate=1.5,
    marginal_tax_rate=25,
    filing_status="individual",
    other_itemized_deductions=0,
    # Closing costs
    buying_closing_cost_pct=4,
    selling_closing_cost_pct=6,
    # Maintenance and fees
    maintenance_pct=1,
    homeowners_insurance_pct=0.5,
    extra_utilities=200,
    hoa_fees=0,
    hoa_tax_deductible_pct=0,
    # Rental costs
    security_deposit_months=1,
    rental_broker_fee_pct=0,
    renters_insurance_pct=0.5
):
    """
    Calculate comprehensive buy vs rent comparison over time.
    Based on NYT calculator methodology.
    """
    # Convert percentages to decimals
    down_payment = home_price * (down_payment_pct / 100)
    mortgage_rate = mortgage_rate / 100
    home_appreciation = home_appreciation / 100
    rent_appreciation = rent_appreciation / 100
    investment_return = investment_return / 100
    inflation = inflation / 100
    
    # Calculate monthly periods
    months = np.arange(years * 12 + 1)
    
    # BUYING SCENARIO
    # Initial costs
    loan_amount = home_price - down_payment
    buying_closing_costs = home_price * (buying_closing_cost_pct / 100)
    initial_buy_costs = down_payment + buying_closing_costs
    
    # Monthly mortgage payment
    monthly_rate = mortgage_rate / 12
    n_payments = mortgage_term * 12
    monthly_payment = (loan_amount * 
                      (monthly_rate * (1 + monthly_rate)**n_payments) / 
                      ((1 + monthly_rate)**n_payments - 1))
    
    # Calculate amortization schedule
    balance = np.zeros(len(months))
    interest_paid = np.zeros(len(months))
    balance[0] = loan_amount
    
    for i in range(1, len(months)):
        interest = balance[i-1] * monthly_rate
        principal = monthly_payment - interest
        balance[i] = balance[i-1] - principal
        interest_paid[i] = interest_paid[i-1] + interest
    
    # PMI (if down payment < 20%)
    pmi_payments = np.zeros(len(months))
    if down_payment_pct < 20:
        pmi_monthly_rate = pmi_rate / 100 / 12
        pmi_payments = np.where(balance / home_price > 0.8, 
                              balance * pmi_monthly_rate, 0)
    
    # Property taxes and insurance
    home_values = home_price * (1 + home_appreciation)**(months/12)
    property_tax = home_values * (property_tax_rate / 100 / 12)
    homeowners_insurance = home_values * (homeowners_insurance_pct / 100 / 12)
    
    # Maintenance and utilities
    maintenance = home_values * (maintenance_pct / 100 / 12)
    utilities = extra_utilities * (1 + inflation)**(months/12)
    hoa = hoa_fees * np.ones(len(months))
    
    # Tax deductions
    standard_deduction = 13850 if filing_status == "individual" else 27700  # 2023 values
    itemized_deductions = (interest_paid + 
                          np.cumsum(property_tax) + 
                          hoa * (hoa_tax_deductible_pct / 100) +
                          other_itemized_deductions)
    tax_savings = np.maximum(0, itemized_deductions - standard_deduction) * (marginal_tax_rate / 100)
    
    # RENTING SCENARIO
    # Initial costs
    security_deposit = monthly_rent * security_deposit_months
    broker_fee = monthly_rent * 12 * (rental_broker_fee_pct / 100)
    initial_rent_costs = security_deposit + broker_fee
    
    # Monthly rent with appreciation
    monthly_rents = monthly_rent * (1 + rent_appreciation)**(months/12)
    renters_insurance = monthly_rent * 12 * (renters_insurance_pct / 100 / 12)
    
    # Investment returns (on down payment difference)
    investment_base = initial_buy_costs - initial_rent_costs
    monthly_investment = (monthly_payment + 
                         pmi_payments + 
                         property_tax + 
                         homeowners_insurance +
                         maintenance + 
                         utilities + 
                         hoa - 
                         monthly_rents - 
                         renters_insurance)
    
    investment_value = np.zeros(len(months))
    investment_value[0] = investment_base
    
    for i in range(1, len(months)):
        investment_value[i] = (investment_value[i-1] * (1 + investment_return/12) + 
                             monthly_investment[i-1])
    
    # Final selling costs
    final_selling_costs = home_values * (selling_closing_cost_pct / 100)
    
    # Calculate net worth for both scenarios
    buying_net_worth = (home_values - 
                       balance - 
                       np.cumsum(pmi_payments) -
                       np.cumsum(property_tax) -
                       np.cumsum(homeowners_insurance) -
                       np.cumsum(maintenance) -
                       np.cumsum(utilities) -
                       np.cumsum(hoa) +
                       tax_savings -
                       final_selling_costs)
    
    renting_net_worth = (investment_value - 
                        np.cumsum(monthly_rents) - 
                        np.cumsum(renters_insurance))
    
    # Create time series for plotting
    dates = [pd.Timestamp.now() + pd.DateOffset(months=int(m)) for m in months]
    
    # Create the plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=buying_net_worth,
        name='Buying Net Worth',
        mode='lines',
        line=dict(color=COLORS['green'], width=1.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=renting_net_worth,
        name='Renting Net Worth',
        mode='lines',
        line=dict(color=COLORS['blue'], width=1.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=buying_net_worth - renting_net_worth,
        name='Buy vs Rent Advantage',
        mode='lines',
        line=dict(color=COLORS['red'], width=1.5)
    ))
    
    fig.update_layout(
        title='Buy vs. Rent Net Worth Comparison',
        xaxis_title='Date',
        yaxis_title='Net Worth ($)',
        plot_bgcolor=COLORS['surface'],
        paper_bgcolor=COLORS['surface'],
        font=dict(color=COLORS['text']),
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        hovermode='x unified'
    )
    
    return fig

app = Dash(__name__)

# Styles
STYLES = {
    'container': {
        'backgroundColor': COLORS['background'],
        'minHeight': '100vh',
        'padding': '20px',
        'color': COLORS['text']
    },
    'input_container': {
        'width': '25%',
        'padding': '20px',
        'backgroundColor': COLORS['surface'],
        'borderRadius': '10px',
        'marginRight': '20px'
    },
    'plot_container': {
        'width': '75%',
        'padding': '20px'
    },
    'section': {
        'marginBottom': '20px'
    },
    'input_group': {
        'marginBottom': '15px'
    },
    'label': {
        'color': COLORS['text'],
        'marginBottom': '5px'
    }
}

app.layout = html.Div([
    html.H1('Buy vs. Rent Calculator', style={'textAlign': 'center', 'color': COLORS['text']}),
    
    # Main container
    html.Div([
        # Left column - Inputs
        html.Div([
            # Basic Inputs Section
            html.Div([
                html.H3('Basic Information', style={'color': COLORS['text']}),
                
                html.Div([
                    html.Label('Home Price ($)', style=STYLES['label']),
                    dcc.Input(
                        id='home-price-input',
                        type='number',
                        value=375000,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='home-price-slider',
                        min=100000,
                        max=1000000,
                        value=375000,
                        marks={i: f'${i:,}' for i in range(100000, 1100000, 200000)}
                    )
                ], style=STYLES['input_group']),
                
                html.Div([
                    html.Label('Monthly Rent ($)', style=STYLES['label']),
                    dcc.Input(
                        id='monthly-rent-input',
                        type='number',
                        value=2000,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='monthly-rent-slider',
                        min=500,
                        max=5000,
                        value=2000,
                        marks={i: f'${i}' for i in range(500, 5500, 1000)}
                    )
                ], style=STYLES['input_group']),
                
                html.Div([
                    html.Label('Time Horizon (years)', style=STYLES['label']),
                    dcc.Input(
                        id='years-input',
                        type='number',
                        value=30,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='years-slider',
                        min=5,
                        max=30,
                        value=30,
                        marks={i: f'{i}y' for i in range(5, 35, 5)}
                    )
                ], style=STYLES['input_group'])
            ], style=STYLES['section']),
            
            # Mortgage Details Section
            html.Div([
                html.H3('Mortgage Details', style={'color': COLORS['text']}),
                
                html.Div([
                    html.Label('Down Payment ($)', style=STYLES['label']),
                    dcc.Input(
                        id='down-payment-input',
                        type='number',
                        value=75000,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='down-payment-slider',
                        min=0,
                        max=200000,
                        value=75000,
                        marks={i: f'${i:,}' for i in range(0, 220000, 40000)}
                    )
                ], style=STYLES['input_group']),
                
                html.Div([
                    html.Label('Mortgage Rate (%)', style=STYLES['label']),
                    dcc.Input(
                        id='mortgage-rate-input',
                        type='number',
                        value=6.5,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='mortgage-rate-slider',
                        min=2,
                        max=10,
                        value=6.5,
                        step=0.1,
                        marks={i: f'{i}%' for i in range(2, 11, 2)}
                    )
                ], style=STYLES['input_group'])
            ], style=STYLES['section']),
            
            # Future Projections Section
            html.Div([
                html.H3('Future Projections', style={'color': COLORS['text']}),
                
                html.Div([
                    html.Label('Home Appreciation (%)', style=STYLES['label']),
                    dcc.Input(
                        id='home-appreciation-input',
                        type='number',
                        value=3,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='home-appreciation-slider',
                        min=0,
                        max=8,
                        value=3,
                        step=0.1,
                        marks={i: f'{i}%' for i in range(0, 9, 2)}
                    )
                ], style=STYLES['input_group']),
                
                html.Div([
                    html.Label('Rent Appreciation (%)', style=STYLES['label']),
                    dcc.Input(
                        id='rent-appreciation-input',
                        type='number',
                        value=3,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='rent-appreciation-slider',
                        min=0,
                        max=8,
                        value=3,
                        step=0.1,
                        marks={i: f'{i}%' for i in range(0, 9, 2)}
                    )
                ], style=STYLES['input_group']),
                
                html.Div([
                    html.Label('Investment Return (%)', style=STYLES['label']),
                    dcc.Input(
                        id='investment-return-input',
                        type='number',
                        value=7,
                        style={'width': '100%', 'marginBottom': '5px'}
                    ),
                    dcc.Slider(
                        id='investment-return-slider',
                        min=0,
                        max=12,
                        value=7,
                        step=0.1,
                        marks={i: f'{i}%' for i in range(0, 13, 3)}
                    )
                ], style=STYLES['input_group'])
            ], style=STYLES['section'])
        ], style=STYLES['input_container']),
        
        # Right column - Plot
        html.Div([
            dcc.Graph(id='comparison-plot')
        ], style=STYLES['plot_container'])
    ], style={'display': 'flex', 'flexDirection': 'row'})
], style=STYLES['container'])

def create_callbacks(app):
    def create_sync_callback(param):
        @app.callback(
            [Output(f'{param}-input', 'value'),
             Output(f'{param}-slider', 'value')],
            [Input(f'{param}-input', 'value'),
             Input(f'{param}-slider', 'value')],
            prevent_initial_call=True
        )
        def sync_values(input_value, slider_value):
            # Get the ID of the component that triggered the callback
            triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
            
            if triggered_id == f'{param}-input':
                return input_value, input_value
            return slider_value, slider_value

    # Create sync callbacks for each parameter
    params = ['home-price', 'monthly-rent', 'years', 'down-payment', 
              'mortgage-rate', 'home-appreciation', 'rent-appreciation', 
              'investment-return']
    
    for param in params:
        create_sync_callback(param)

    @app.callback(
        Output('comparison-plot', 'figure'),
        [Input(f'{param}-input', 'value') for param in params]
    )
    def update_plot(home_price, monthly_rent, years, down_payment,
                   mortgage_rate, home_appreciation, rent_appreciation,
                   investment_return):
        if not all([home_price, monthly_rent, years, down_payment,
                    mortgage_rate, home_appreciation, rent_appreciation,
                    investment_return]):
            return go.Figure()
        
        # Calculate down payment percentage
        down_payment_pct = (down_payment / home_price * 100) if home_price else 0
        
        return calculate_buy_vs_rent(
            home_price=home_price,
            monthly_rent=monthly_rent,
            years=years,
            down_payment_pct=down_payment_pct,
            mortgage_rate=mortgage_rate,
            home_appreciation=home_appreciation,
            rent_appreciation=rent_appreciation,
            investment_return=investment_return
        )

if __name__ == '__main__':
    create_callbacks(app)
    app.run_server(debug=True)
