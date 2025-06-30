import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import io
import base64
from datetime import datetime

app = dash.Dash(__name__)
app.title = "Multi-View Finance Dashboard"
server = app.server

app.layout = html.Div([
    html.H2("📊 Multi-View Finance Dashboard"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['📁 Drag and Drop or ', html.A('Select Excel File')]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='file-name'),
    html.Hr(),
    html.Div([
        html.Label("Select View:"),
        dcc.Dropdown(
            id='view-selector',
            options=[
                {'label': 'Channel View', 'value': 'channel'},
                {'label': 'Category View', 'value': 'category'},
                {'label': 'City View', 'value': 'city'}
            ],
            value='channel',
            clearable=False
        )
    ], style={'width': '30%', 'display': 'inline-block'}),
    html.Div(id='filters-container'),
    html.Hr(),
    dcc.Graph(id='main-chart'),
    html.Hr(),
    html.H4("Filtered Data Table"),
    dash_table.DataTable(
        id='data-table',
        columns=[],
        data=[],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
    ),
    dcc.Store(id='stored-data')
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if 'xls' in filename:
        df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
    else:
        return None
    df['Doc Date'] = pd.to_datetime(df['Doc Date'], errors='coerce')
    return df

@app.callback(
    Output('stored-data', 'data'),
    Output('file-name', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def store_data(contents, filename):
    if contents:
        df = parse_contents(contents, filename)
        if df is not None:
            return df.to_dict('records'), f"✅ Uploaded: {filename}"
    return dash.no_update, ""

@app.callback(
    Output('filters-container', 'children'),
    Input('stored-data', 'data'),
    Input('view-selector', 'value')
)
def update_filters(data, view):
    if not data:
        return html.Div("Please upload a file to begin.")
    df = pd.DataFrame(data)
    filters = []

    # Common date filter
    filters.append(html.Div([
        html.Label("Select Date Range:"),
        dcc.DatePickerRange(
            id='date-filter',
            min_date_allowed=df['Doc Date'].min(),
            max_date_allowed=df['Doc Date'].max(),
            start_date=df['Doc Date'].min(),
            end_date=df['Doc Date'].max()
        )
    ]))

    if view == 'channel':
        for col in ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']:
            filters.append(html.Div([
                html.Label(f"Filter by {col}:"),
                dcc.Dropdown(
                    id=f'filter-{col}',
                    options=[{'label': i, 'value': i} for i in sorted(df[col].dropna().unique())],
                    multi=True
                )
            ]))
    elif view == 'category':
        for col in ['Category', 'Sub Category', 'Item Name']:
            filters.append(html.Div([
                html.Label(f"Filter by {col}:"),
                dcc.Dropdown(
                    id=f'filter-{col}',
                    options=[{'label': i, 'value': i} for i in sorted(df[col].dropna().unique())],
                    multi=True
                )
            ]))
    elif view == 'city':
        for col in ['City', 'Rep Person Name', 'Category', 'Sub Category', 'Item Name']:
            filters.append(html.Div([
                html.Label(f"Filter by {col}:"),
                dcc.Dropdown(
                    id=f'filter-{col}',
                    options=[{'label': i, 'value': i} for i in sorted(df[col].dropna().unique())],
                    multi=True
                )
            ]))
    return filters

@app.callback(
    Output('main-chart', 'figure'),
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('stored-data', 'data'),
    Input('view-selector', 'value'),
    Input('date-filter', 'start_date'),
    Input('date-filter', 'end_date'),
    Input('filter-Channel', 'value'),
    Input('filter-Branch', 'value'),
    Input('filter-City', 'value'),
    Input('filter-Category', 'value'),
    Input('filter-Sub Category', 'value'),
    Input('filter-Item Name', 'value'),
    Input('filter-Rep Person Name', 'value')
)
def update_output(data, view, start_date, end_date,
                  channel, branch, city, category, subcat, item, rep):
    if not data:
        return dash.no_update, [], []

    df = pd.DataFrame(data)
    df = df[(df['Doc Date'] >= pd.to_datetime(start_date)) & (df['Doc Date'] <= pd.to_datetime(end_date))]

    # Apply filters
    if channel: df = df[df['Channel'].isin(channel)]
    if branch: df = df[df['Branch'].isin(branch)]
    if city: df = df[df['City'].isin(city)]
    if category: df = df[df['Category'].isin(category)]
    if subcat: df = df[df['Sub Category'].isin(subcat)]
    if item: df = df[df['Item Name'].isin(item)]
    if rep: df = df[df['Rep Person Name'].isin(rep)]

    # Chart logic
    if view == 'channel':
        fig = px.bar(df, x='Channel', y='Total Price', color='Category', barmode='group', title="Total Price by Channel and Category")
    elif view == 'category':
        fig = px.bar(df, x='Category', y='Total Price', color='Sub Category', barmode='group', title="Total Price by Category and Sub Category")
    elif view == 'city':
        fig = px.bar(df, x='City', y='Total Price', color='Rep Person Name', barmode='group', title="Total Price by City and Sales Rep")
    else:
        fig = px.bar(title="No Data")

    # Data table
    display_cols = ['Rep Person Name', 'Channel', 'Branch', 'City', 'Customer Name',
                    'Category', 'Sub Category', 'Item Name', 'Qty', 'Total Price']
    table_data = df[display_cols].to_dict('records')
    table_columns = [{"name": i, "id": i} for i in display_cols]

    return fig, table_columns, table_data

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)
