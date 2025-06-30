import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import io
import base64

app = dash.Dash(__name__)
app.title = "Multi-View Finance Dashboard"

app.layout = html.Div([
    html.H2("📊 Multi-View Finance Dashboard"),
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Excel File'),
        multiple=False
    ),
    html.Div(id='file-upload-status'),
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
            value='channel'
        )
    ]),

    html.Div(id='dynamic-filters'),
    html.Br(),

    html.Div([
        html.H4("Date Range Filter"),
        dcc.DatePickerRange(
            id='date-range',
            start_date_placeholder_text="Start Date",
            end_date_placeholder_text="End Date"
        )
    ]),
    html.Br(),

    dcc.Graph(id='bar-chart'),
    html.Br(),

    html.H4("Filtered Data Table"),
    dash_table.DataTable(
        id='data-table',
        columns=[],
        data=[],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    )
])

# Store uploaded data
data_store = {}

@app.callback(
    Output('file-upload-status', 'children'),
    Output('dynamic-filters', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(content, filename):
    if content is None:
        return "", ""

    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')

    # Store in global variable
    data_store['df'] = df

    return f"Uploaded file: {filename}", generate_filters('channel', df)

@app.callback(
    Output('dynamic-filters', 'children'),
    Input('view-selector', 'value')
)
def update_filters(view):
    df = data_store.get('df')
    if df is None:
        return ""
    return generate_filters(view, df)

def generate_filters(view, df):
    filters = []
    if view == 'channel':
        filters = ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']
    elif view == 'category':
        filters = ['Category', 'Sub Category', 'Item Name']
    elif view == 'city':
        filters = ['City', 'Rep Person Name', 'Category', 'Sub Category', 'Item Name']

    return html.Div([
        html.Label(f"Filter by {col}:"),
        dcc.Dropdown(
            id={'type': 'dynamic-filter', 'index': col},
            options=[{'label': val, 'value': val} for val in sorted(df[col].dropna().unique())],
            multi=True
        )
        for col in filters
    ])

@app.callback(
    Output('bar-chart', 'figure'),
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('view-selector', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date'),
    Input({'type': 'dynamic-filter', 'index': dash.ALL}, 'value')
)
def update_chart(view, start_date, end_date, filter_values):
    df = data_store.get('df')
    if df is None:
        return {}, [], []

    df = df.copy()

    # Convert Doc Date to datetime
    if 'Doc Date' in df.columns:
        df['Doc Date'] = pd.to_datetime(df['Doc Date'], errors='coerce')

    # Apply date filter
    if start_date:
        df = df[df['Doc Date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['Doc Date'] <= pd.to_datetime(end_date)]

    # Apply dynamic filters
    filter_keys = []
    if view == 'channel':
        filter_keys = ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']
        groupby_keys = ['Channel', 'Category']
    elif view == 'category':
        filter_keys = ['Category', 'Sub Category', 'Item Name']
        groupby_keys = ['Category', 'Sub Category']
    elif view == 'city':
        filter_keys = ['City', 'Rep Person Name', 'Category', 'Sub Category', 'Item Name']
        groupby_keys = ['City', 'Rep Person Name']

    for key, selected in zip(filter_keys, filter_values):
        if selected:
            df = df[df[key].isin(selected)]

    # Create bar chart
    if 'Total Price' in df.columns:
        chart_df = df.groupby(groupby_keys)['Total Price'].sum().reset_index()
        fig = px.bar(chart_df, x=groupby_keys[0], y='Total Price', color=groupby_keys[1],
                     title=f"Total Price by {groupby_keys[0]} and {groupby_keys[1]}")
    else:
        fig = {}

    # Prepare data table
    display_cols = ['Rep Person Name', 'Channel', 'Branch', 'City', 'Customer Name',
                    'Category', 'Sub Category', 'Item Name', 'Qty', 'Total Price']
    table_cols = [col for col in display_cols if col in df.columns]
    columns = [{"name": i, "id": i} for i in table_cols]
    data = df[table_cols].to_dict('records')

    return fig, columns, data

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)
