import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import io
import base64
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for Azure deployment

# App layout
app.layout = html.Div([
    html.H1("📊 Finance Dashboard with Excel Upload", style={"textAlign": "center"}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            '📁 Drag and Drop or ',
            html.A('Select Excel File')
        ]),
        style={
            'width': '98%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px auto'
        },
        multiple=False
    ),

    html.Div(id='filter-container', children=[]),

    html.Div(id='kpi-cards', style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '20px'}),

    dcc.Graph(id='line-chart'),
    dcc.Graph(id='pie-chart'),

    html.Button("⬇️ Download Filtered Data", id="download-button", n_clicks=0),
    dcc.Download(id="download-dataframe-xlsx"),

    html.Hr(),
    html.H3("📋 Filtered Data Table"),
    dash_table.DataTable(id='data-table', page_size=10, style_table={'overflowX': 'auto'})
])

# Global store for uploaded data
data_store = {}

# Callback to parse uploaded Excel and generate filters
@app.callback(
    Output('filter-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_filters(contents, filename):
    if contents is None:
        return []

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')

    # Store in global variable
    data_store['df'] = df

    # Convert Doc Date to datetime
    if 'Doc Date' in df.columns:
        df['Doc Date'] = pd.to_datetime(df['Doc Date'], errors='coerce')

    filters = [
        html.Div([
            html.Label("📅 Date Range"),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=df['Doc Date'].min(),
                max_date_allowed=df['Doc Date'].max(),
                start_date=df['Doc Date'].min(),
                end_date=df['Doc Date'].max()
            )
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("📦 Channel"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Channel'].dropna().unique())],
                         id='channel-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("🏢 Branch"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Branch'].dropna().unique())],
                         id='branch-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("🏙️ City"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['City'].dropna().unique())],
                         id='city-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("👤 Customer Name"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Customer Name'].dropna().unique())],
                         id='customer-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("📂 Category"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Category'].dropna().unique())],
                         id='category-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("📁 Sub Category"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Sub Category'].dropna().unique())],
                         id='subcategory-filter', multi=True)
        ], style={'margin': '10px'}),

        html.Div([
            html.Label("🛒 Item Name"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Item Name'].dropna().unique())],
                         id='item-filter', multi=True)
        ], style={'margin': '10px'})
    ]

    return filters

# Callback to update charts, KPIs, and table
@app.callback(
    Output('line-chart', 'figure'),
    Output('pie-chart', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Output('kpi-cards', 'children'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input('channel-filter', 'value'),
    Input('branch-filter', 'value'),
    Input('city-filter', 'value'),
    Input('customer-filter', 'value'),
    Input('category-filter', 'value'),
    Input('subcategory-filter', 'value'),
    Input('item-filter', 'value')
)
def update_outputs(start_date, end_date, channel, branch, city, customer, category, subcategory, item):
    if 'df' not in data_store:
        return dash.no_update

    df = data_store['df']

    # Apply filters
    if start_date and end_date:
        df = df[(df['Doc Date'] >= start_date) & (df['Doc Date'] <= end_date)]
    if channel:
        df = df[df['Channel'].isin(channel)]
    if branch:
        df = df[df['Branch'].isin(branch)]
    if city:
        df = df[df['City'].isin(city)]
    if customer:
        df = df[df['Customer Name'].isin(customer)]
    if category:
        df = df[df['Category'].isin(category)]
    if subcategory:
        df = df[df['Sub Category'].isin(subcategory)]
    if item:
        df = df[df['Item Name'].isin(item)]

    # KPI Cards
    total_qty = df['Qty'].sum() if 'Qty' in df.columns else 0
    total_price = df['Total Price'].sum() if 'Total Price' in df.columns else 0

    kpis = [
        html.Div([
            html.H4("📦 Total Quantity"),
            html.H2(f"{total_qty:,.0f}")
        ], style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px'}),

        html.Div([
            html.H4("💰 Total Price"),
            html.H2(f"{total_price:,.2f}")
        ], style={'padding': '10px', 'border': '1px solid #ccc', 'borderRadius': '5px'})
    ]

    # Line Chart
    line_fig = px.line(df, x='Doc Date', y='Total Price', title="Total Price Over Time") if 'Doc Date' in df.columns and 'Total Price' in df.columns else {}

    # Pie Chart
    pie_fig = px.pie(df, names='Category', values='Total Price', title="Total Price by Category") if 'Category' in df.columns and 'Total Price' in df.columns else {}

    # Data Table
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')

    # Store filtered data for download
    data_store['filtered'] = df

    return line_fig, pie_fig, data, columns, kpis

# Callback to download filtered data
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def download_filtered_data(n_clicks):
    if 'filtered' in data_store:
        df = data_store['filtered']
        return dcc.send_data_frame(df.to_excel, "filtered_data.xlsx", index=False)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8000)
