import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import io
import base64
from datetime import datetime

# Initialize the Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # for Azure deployment

# Global store for uploaded and filtered data
data_store = {}

# App layout
app.layout = dbc.Container([
    html.H1("📊 Multi-File Finance Dashboard", className="text-center my-4"),

    dcc.Upload(
        id='upload-data',
        children=html.Div(['📁 Drag and Drop or ', html.A('Select Excel Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'marginBottom': '20px'
        },
        multiple=True
    ),

    html.Div(id='filter-container'),

    dbc.Tabs([
        dbc.Tab(label="Summary", tab_id="tab-summary"),
        dbc.Tab(label="Trends", tab_id="tab-trends"),
        dbc.Tab(label="Customer Insights", tab_id="tab-insights"),
        dbc.Tab(label="Data Table", tab_id="tab-table")
    ], id="tabs", active_tab="tab-summary", className="mb-3"),

    html.Div(id="tab-content"),

    html.Div([
        html.Button("⬇️ Download Filtered Data", id="download-button", n_clicks=0, className="btn btn-primary"),
        dcc.Download(id="download-dataframe-xlsx")
    ], className="my-3")
], fluid=True)


# Callback to parse uploaded Excel files and generate filters
@app.callback(
    Output('filter-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_filters(contents, filenames):
    if contents is None:
        return []

    all_dfs = []
    for content, filename in zip(contents, filenames):
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        excel_data = pd.read_excel(io.BytesIO(decoded), sheet_name=None, engine='openpyxl')
        for sheet_name, df in excel_data.items():
            df['Source File'] = filename
            df['Sheet Name'] = sheet_name
            all_dfs.append(df)

    df = pd.concat(all_dfs, ignore_index=True)

    # Convert Doc Date to datetime
    if 'Doc Date' in df.columns:
        df['Doc Date'] = pd.to_datetime(df['Doc Date'], errors='coerce')

    data_store['df'] = df

    filters = dbc.Row([
        dbc.Col([
            html.Label("📅 Date Range"),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=df['Doc Date'].min(),
                max_date_allowed=df['Doc Date'].max(),
                start_date=df['Doc Date'].min(),
                end_date=df['Doc Date'].max()
            )
        ], md=4),

        dbc.Col([
            html.Label("📦 Channel"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Channel'].dropna().unique())],
                         id='channel-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("🏢 Branch"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Branch'].dropna().unique())],
                         id='branch-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("🏙️ City"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['City'].dropna().unique())],
                         id='city-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("👤 Customer Name"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Customer Name'].dropna().unique())],
                         id='customer-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("📂 Category"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Category'].dropna().unique())],
                         id='category-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("📁 Sub Category"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Sub Category'].dropna().unique())],
                         id='subcategory-filter', multi=True)
        ], md=4),

        dbc.Col([
            html.Label("🛒 Item Name"),
            dcc.Dropdown(options=[{'label': i, 'value': i} for i in sorted(df['Item Name'].dropna().unique())],
                         id='item-filter', multi=True)
        ], md=4)
    ], className="mb-4")

    return filters


# Callback to update tab content based on filters
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
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
def update_tabs(tab, start_date, end_date, channel, branch, city, customer, category, subcategory, item):
    if 'df' not in data_store:
        return html.Div()

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

    data_store['filtered'] = df

    # KPI Cards
    total_qty = df['Qty'].sum() if 'Qty' in df.columns else 0
    total_price = df['Total Price'].sum() if 'Total Price' in df.columns else 0

    kpis = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("📦 Total Quantity"),
            dbc.CardBody(html.H4(f"{total_qty:,.0f}", className="card-title"))
        ]), md=6),

        dbc.Col(dbc.Card([
            dbc.CardHeader("💰 Total Price"),
            dbc.CardBody(html.H4(f"{total_price:,.2f}", className="card-title"))
        ]), md=6)
    ])

    # Line Chart
    line_fig = px.line(df, x='Doc Date', y='Total Price', title="Total Price Over Time") if 'Doc Date' in df.columns and 'Total Price' in df.columns else {}

    # Pie Chart
    pie_fig = px.pie(df, names='Category', values='Total Price', title="Total Price by Category") if 'Category' in df.columns and 'Total Price' in df.columns else {}

    # Data Table
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')
    table = dash_table.DataTable(data=data, columns=columns, page_size=10, style_table={'overflowX': 'auto'})

    if tab == "tab-summary":
        return kpis
    elif tab == "tab-trends":
        return dcc.Graph(figure=line_fig)
    elif tab == "tab-insights":
        return dcc.Graph(figure=pie_fig)
    elif tab == "tab-table":
        return table
    else:
        return html.Div()


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
