import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Multi-View Finance Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Finance Dashboard with Multi-View Filters", style={'textAlign': 'center'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div(['📁 Drag and Drop or ', html.A('Select Excel File')]),
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

    dcc.Tabs(id='view-tabs', value='channel', children=[
        dcc.Tab(label='Channel View', value='channel'),
        dcc.Tab(label='Category View', value='category'),
        dcc.Tab(label='City View', value='city'),
    ]),

    html.Div(id='filters-container'),
    html.Div(dcc.Graph(id='main-chart')),
    html.Div(dash_table.DataTable(id='data-table', page_size=10, style_table={'overflowX': 'auto'})),

    dcc.Store(id='stored-data')
])

# Helper to parse uploaded Excel file
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
    df['Doc Date'] = pd.to_datetime(df['Doc Date'])
    return df

# Callback to store uploaded data
@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents')
)
def store_data(contents):
    if contents is None:
        return None
    df = parse_contents(contents)
    return df.to_dict('records')

# Callback to generate filters based on selected view
@app.callback(
    Output('filters-container', 'children'),
    Input('view-tabs', 'value'),
    Input('stored-data', 'data')
)
def update_filters(view, data):
    if data is None:
        return html.Div("Please upload an Excel file to begin.")
    df = pd.DataFrame(data)
    filters = []

    # Common date filter
    filters.append(html.Label("Doc Date Range"))
    filters.append(dcc.DatePickerRange(
        id='date-filter',
        start_date=df['Doc Date'].min(),
        end_date=df['Doc Date'].max(),
        display_format='YYYY-MM-DD'
    ))

    if view == 'channel':
        filters += [
            html.Label("Channel"),
            dcc.Dropdown(df['Channel'].dropna().unique(), id='channel-filter', multi=True),
            html.Label("Branch"),
            dcc.Dropdown(df['Branch'].dropna().unique(), id='branch-filter', multi=True),
            html.Label("City"),
            dcc.Dropdown(df['City'].dropna().unique(), id='city-filter', multi=True),
            html.Label("Category"),
            dcc.Dropdown(df['Category'].dropna().unique(), id='category-filter', multi=True),
            html.Label("Sub Category"),
            dcc.Dropdown(df['Sub Category'].dropna().unique(), id='subcategory-filter', multi=True),
            html.Label("Item Name"),
            dcc.Dropdown(df['Item Name'].dropna().unique(), id='item-filter', multi=True),
        ]
    elif view == 'category':
        filters += [
            html.Label("Category"),
            dcc.Dropdown(df['Category'].dropna().unique(), id='category-filter', multi=True),
            html.Label("Sub Category"),
            dcc.Dropdown(df['Sub Category'].dropna().unique(), id='subcategory-filter', multi=True),
            html.Label("Item Name"),
            dcc.Dropdown(df['Item Name'].dropna().unique(), id='item-filter', multi=True),
        ]
    elif view == 'city':
        filters += [
            html.Label("City"),
            dcc.Dropdown(df['City'].dropna().unique(), id='city-filter', multi=True),
            html.Label("Rep Person Name"),
            dcc.Dropdown(df['Rep Person Name'].dropna().unique(), id='rep-filter', multi=True),
            html.Label("Category"),
            dcc.Dropdown(df['Category'].dropna().unique(), id='category-filter', multi=True),
            html.Label("Sub Category"),
            dcc.Dropdown(df['Sub Category'].dropna().unique(), id='subcategory-filter', multi=True),
            html.Label("Item Name"),
            dcc.Dropdown(df['Item Name'].dropna().unique(), id='item-filter', multi=True),
        ]
    return html.Div(filters, style={'columnCount': 2, 'margin': '20px'})

# Callback to update chart and table
@app.callback(
    Output('main-chart', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('view-tabs', 'value'),
    Input('stored-data', 'data'),
    Input('date-filter', 'start_date'),
    Input('date-filter', 'end_date'),
    Input('channel-filter', 'value'),
    Input('branch-filter', 'value'),
    Input('city-filter', 'value'),
    Input('category-filter', 'value'),
    Input('subcategory-filter', 'value'),
    Input('item-filter', 'value'),
    Input('rep-filter', 'value')
)
def update_output(view, data, start_date, end_date,
                  channel, branch, city, category, subcategory, item, rep):
    if data is None:
        return {}, [], []

    df = pd.DataFrame(data)

    # Apply date filter
    if start_date and end_date:
        df = df[(df['Doc Date'] >= pd.to_datetime(start_date)) & (df['Doc Date'] <= pd.to_datetime(end_date))]

    # Apply filters
    if channel: df = df[df['Channel'].isin(channel)]
    if branch: df = df[df['Branch'].isin(branch)]
    if city: df = df[df['City'].isin(city)]
    if category: df = df[df['Category'].isin(category)]
    if subcategory: df = df[df['Sub Category'].isin(subcategory)]
    if item: df = df[df['Item Name'].isin(item)]
    if rep: df = df[df['Rep Person Name'].isin(rep)]

    # Create chart
    if view == 'channel':
        fig = px.bar(df, x='Channel', y='Total Price', color='Category', barmode='group', title='Total Price by Channel and Category')
    elif view == 'category':
        fig = px.bar(df, x='Category', y='Total Price', color='Sub Category', barmode='group', title='Total Price by Category and Sub Category')
    elif view == 'city':
        fig = px.bar(df, x='City', y='Total Price', color='Rep Person Name', barmode='group', title='Total Price by City and Sales Rep')
    else:
        fig = {}

    # Prepare table
    display_cols = ['Rep Person Name', 'Channel', 'Branch', 'City', 'Customer Name',
                    'Category', 'Sub Category', 'Item Name', 'Qty', 'Total Price']
    table_data = df[display_cols].to_dict('records')
    table_columns = [{"name": i, "id": i} for i in display_cols]

    return fig, table_data, table_columns

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)
