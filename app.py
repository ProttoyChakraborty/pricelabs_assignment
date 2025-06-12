import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import calendar

# Initialize the Dash app
app = dash.Dash(__name__)

server = app.server

# Load and process the data
def load_data():
    """Load and process the CSV data for year-over-year analysis"""
    # Read the CSV file
    df = pd.read_csv('cleaned_data.csv')
    
    # Convert Date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Extract year, month, day, and day of year
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['DayOfYear'] = df['Date'].dt.dayofyear
    df['MonthName'] = df['Date'].dt.month_name()
    df['WeekOfYear'] = df['Date'].dt.isocalendar().week
    
    # Create month-day for overlay comparisons
    df['MonthDay'] = df['Date'].dt.strftime('%m-%d')
    
    return df

# Load the data
df = load_data()

available_years = sorted(df['Year'].unique())

# Define the app layout
app.layout = html.Div([
    html.Div([
        html.H1("Year-over-Year Price Analysis Dashboard", 
                style={'textAlign': 'center', 'marginBottom': 30, 'color': '#2c3e50'}),
        
       
        html.Div([
            html.Div([
                html.Label("Select Years to Compare:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in available_years],
                    value=available_years,  
                    multi=True,
                    placeholder="Select years to compare"
                )
            ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            
            html.Div([
                html.Label("Comparison Type:", style={'fontWeight': 'bold', 'marginBottom': 10}),
                dcc.Dropdown(
                    id='comparison-type',
                    options=[
                        {'label': 'Overlay by Day of Year', 'value': 'overlay'},
                        {'label': 'Monthly Averages', 'value': 'monthly'},
                        {'label': 'Quarterly Comparison', 'value': 'quarterly'},
                        {'label': 'Weekly Patterns', 'value': 'weekly'}
                    ],
                    value='overlay',
                    style={'marginTop': 10, }
                )
            ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
        ], style={'marginBottom': 30, 'padding': 20, 'backgroundColor': '#f8f9fa', 'borderRadius': 10,  'height': 'fit-content'}),
        
    
        dcc.Graph(id='main-comparison-chart', style={'height': '500px'}),
        
        
        html.Div([
            html.Div([
                dcc.Graph(id='summary-stats-chart')
            ], style={'width': '50%', 'display': 'inline-block'}),
            
            html.Div([
                dcc.Graph(id='volatility-chart')
            ], style={'width': '50%', 'display': 'inline-block'})
        ], style={'marginTop': 20}),
        
        
        html.Div([
            html.H3("Year-over-Year Summary Statistics", style={'textAlign': 'center', 'marginTop': 30}),
            html.Div(id='summary-table')
        ])
    ], style={'padding': 20, 'maxWidth': '1200px', 'margin': '0 auto'})
])

@callback(
    [Output('main-comparison-chart', 'figure'),
     Output('summary-stats-chart', 'figure'),
     Output('volatility-chart', 'figure'),
     Output('summary-table', 'children')],
    [Input('year-dropdown', 'value'),
     Input('comparison-type', 'value')]
)
def update_charts(selected_years, comparison_type):
    if not selected_years:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Please select at least one year", 
                               xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, empty_fig, empty_fig, html.Div("No data to display")
    
    filtered_df = df[df['Year'].isin(selected_years)].copy()
    
    # Create main comparison chart based on type
    if comparison_type == 'overlay':
        main_fig = create_overlay_chart(filtered_df)
    elif comparison_type == 'monthly':
        main_fig = create_monthly_chart(filtered_df)
    elif comparison_type == 'quarterly':
        main_fig = create_quarterly_chart(filtered_df)
    else:  # weekly
        main_fig = create_weekly_chart(filtered_df)
    
    # Create secondary charts
    stats_fig = create_summary_stats_chart(filtered_df)
    volatility_fig = create_volatility_chart(filtered_df)
    
    # Create summary table
    summary_table = create_summary_table(filtered_df)
    
    return main_fig, stats_fig, volatility_fig, summary_table

def create_overlay_chart(df):
    """Create overlay chart showing all years on same day-of-year axis"""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, year in enumerate(sorted(df['Year'].unique())):
        year_data = df[df['Year'] == year].copy()
        year_data = year_data.sort_values('DayOfYear')
        
        fig.add_trace(go.Scatter(
            x=year_data['DayOfYear'],
            y=year_data['Price'],
            mode='lines',
            name=str(year),
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f'<b>{year}</b><br>Day: %{{x}}<br>Price: $%{{y}}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Year-over-Year Price Comparison (Overlay by Day of Year)',
        xaxis_title='Day of Year',
        yaxis_title='Price ($)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_monthly_chart(df):
    """Create monthly average comparison chart"""
    monthly_data = df.groupby(['Year', 'Month']).agg({
        'Price': ['mean', 'std']
    }).round(2)
    monthly_data.columns = ['AvgPrice', 'StdPrice']
    monthly_data = monthly_data.reset_index()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, year in enumerate(sorted(monthly_data['Year'].unique())):
        year_data = monthly_data[monthly_data['Year'] == year]
        
        fig.add_trace(go.Scatter(
            x=year_data['Month'],
            y=year_data['AvgPrice'],
            mode='lines+markers',
            name=str(year),
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8),
            error_y=dict(type='data', array=year_data['StdPrice'], visible=True),
            hovertemplate=f'<b>{year}</b><br>Month: %{{x}}<br>Avg Price: $%{{y:.2f}}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Monthly Average Price Comparison',
        xaxis_title='Month',
        yaxis_title='Average Price ($)',
        xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), 
                  ticktext=[calendar.month_abbr[i] for i in range(1, 13)]),
        hovermode='x unified'
    )
    
    return fig

def create_quarterly_chart(df):
    """Create quarterly comparison chart"""
    df['Quarter'] = df['Date'].dt.quarter
    quarterly_data = df.groupby(['Year', 'Quarter']).agg({
        'Price': ['mean', 'min', 'max', 'std']
    }).round(2)
    quarterly_data.columns = ['AvgPrice', 'MinPrice', 'MaxPrice', 'StdPrice']
    quarterly_data = quarterly_data.reset_index()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, year in enumerate(sorted(quarterly_data['Year'].unique())):
        year_data = quarterly_data[quarterly_data['Year'] == year]
        
        # Add average line
        fig.add_trace(go.Scatter(
            x=year_data['Quarter'],
            y=year_data['AvgPrice'],
            mode='lines+markers',
            name=f'{year} Avg',
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate=f'<b>{year} Q%{{x}}</b><br>Avg: $%{{y:.2f}}<extra></extra>'
        ))
        
        # Add range as filled area
        fig.add_trace(go.Scatter(
            x=list(year_data['Quarter']) + list(year_data['Quarter'])[::-1],
            y=list(year_data['MaxPrice']) + list(year_data['MinPrice'])[::-1],
            fill='tonexty' if i > 0 else 'tozeroy',
            fillcolor=colors[i % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.2)'),
            line=dict(color='rgba(255,255,255,0)'),
            name=f'{year} Range',
            showlegend=True,
            hoverinfo='skip'
        ))
    
    fig.update_layout(
        title='Quarterly Price Comparison (Average with Min/Max Range)',
        xaxis_title='Quarter',
        yaxis_title='Price ($)',
        xaxis=dict(tickmode='array', tickvals=[1, 2, 3, 4], 
                  ticktext=['Q1', 'Q2', 'Q3', 'Q4'])
    )
    
    return fig

def create_weekly_chart(df):
    """Create weekly pattern comparison"""
    weekly_data = df.groupby(['Year', 'WeekOfYear']).agg({
        'Price': 'mean'
    }).round(2).reset_index()
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set1
    
    for i, year in enumerate(sorted(weekly_data['Year'].unique())):
        year_data = weekly_data[weekly_data['Year'] == year]
        
        fig.add_trace(go.Scatter(
            x=year_data['WeekOfYear'],
            y=year_data['Price'],
            mode='lines',
            name=str(year),
            line=dict(color=colors[i % len(colors)], width=2),
            hovertemplate=f'<b>{year}</b><br>Week: %{{x}}<br>Avg Price: $%{{y:.2f}}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Weekly Average Price Patterns',
        xaxis_title='Week of Year',
        yaxis_title='Average Price ($)',
        hovermode='x unified'
    )
    
    return fig

def create_summary_stats_chart(df):
    """Create summary statistics comparison chart"""
    stats = df.groupby('Year').agg({
        'Price': ['mean', 'median', 'min', 'max']
    }).round(2)
    stats.columns = ['Mean', 'Median', 'Min', 'Max']
    stats = stats.reset_index()
    
    fig = go.Figure()
    
    # Add traces for each statistic
    fig.add_trace(go.Bar(x=stats['Year'], y=stats['Mean'], name='Mean', 
                        marker_color='lightblue', opacity=0.8))
    fig.add_trace(go.Bar(x=stats['Year'], y=stats['Median'], name='Median', 
                        marker_color='lightgreen', opacity=0.8))
    
    fig.update_layout(
        title='Annual Price Statistics Comparison',
        xaxis_title='Year',
        yaxis_title='Price ($)',
        barmode='group'
    )
    
    return fig

def create_volatility_chart(df):
    """Create volatility comparison chart"""
    volatility = df.groupby('Year').agg({
        'Price': ['std', lambda x: (x.max() - x.min()) / x.mean() * 100]
    }).round(2)
    volatility.columns = ['StdDev', 'RangePercent']
    volatility = volatility.reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=volatility['Year'],
        y=volatility['StdDev'],
        name='Standard Deviation',
        marker_color='coral',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=volatility['Year'],
        y=volatility['RangePercent'],
        mode='lines+markers',
        name='Range as % of Mean',
        marker=dict(color='darkred', size=8),
        line=dict(color='darkred', width=3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Price Volatility Comparison',
        xaxis_title='Year',
        yaxis=dict(title='Standard Deviation ($)', side='left'),
        yaxis2=dict(title='Range as % of Mean', side='right', overlaying='y'),
        legend=dict(x=0.01, y=0.99)
    )
    
    return fig

def create_summary_table(df):
    """Create summary statistics table"""
    summary = df.groupby('Year').agg({
        'Price': ['count', 'mean', 'median', 'std', 'min', 'max']
    }).round(2)
    summary.columns = ['Days', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']
    summary = summary.reset_index()
    
    # Calculate year-over-year changes
    summary['YoY Change (Mean)'] = summary['Mean'].pct_change() * 100
    summary['YoY Change (Mean)'] = summary['YoY Change (Mean)'].round(2)
    
    
    table_header = [html.Tr([html.Th(col) for col in ['Year'] + list(summary.columns[1:])])]
    
    table_rows = []
    for _, row in summary.iterrows():
        table_row = [html.Td(row['Year'])]
        for col in summary.columns[1:]:
            value = row[col]
            if col == 'YoY Change (Mean)' and pd.notna(value):
                color = 'green' if value > 0 else 'red' if value < 0 else 'black'
                table_row.append(html.Td(f"{value:.2f}%", style={'color': color}))
            elif pd.notna(value):
                table_row.append(html.Td(f"{value:.2f}" if isinstance(value, float) else str(int(value))))
            else:
                table_row.append(html.Td("-"))
        table_rows.append(html.Tr(table_row))
    
    return html.Table(
        table_header + table_rows,
        style={'width': '100%', 'textAlign': 'center', 'border': '1px solid #ddd'},
        className='table table-striped'
    )

# Add CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .table { border-collapse: collapse; margin: 20px auto; }
            .table th, .table td { padding: 8px 12px; border: 1px solid #ddd; }
            .table th { background-color: #f8f9fa; font-weight: bold; }
            .table tr:nth-child(even) { background-color: #f8f9fa; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)