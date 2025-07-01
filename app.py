# app.py

import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for Azure deployment

# App layout
app.layout = html.Div([
    html.H1("Finance Reporting Dashboard"),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Excel File')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    
    html.Div(id='filter-container'),
    html.Div(id='output-data-upload')
])

# Callback to parse uploaded file and generate filters
@app.callback(
    Output('filter-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_filters(contents, filename):
    if contents is None:
        return None

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')

    # Store dataframe in dcc.Store for later use
    filters = html.Div([
        dcc.Store(id='stored-data', data=df.to_dict('records')),
        html.Label("Channel"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Channel'].dropna().unique()],
                     id='channel-filter', multi=True),
        html.Label("Branch"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Branch'].dropna().unique()],
                     id='branch-filter', multi=True),
        html.Label("City"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['City'].dropna().unique()],
                     id='city-filter', multi=True),
        html.Label("Customer Name"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Customer Name'].dropna().unique()],
                     id='customer-filter', multi=True),
        html.Label("Category"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Category'].dropna().unique()],
                     id='category-filter', multi=True),
        html.Label("Sub Category"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Sub Category'].dropna().unique()],
                     id='subcategory-filter', multi=True),
        html.Label("Item Name"),
        dcc.Dropdown(options=[{'label': i, 'value': i} for i in df['Item Name'].dropna().unique()],
                     id='item-filter', multi=True),
        html.Br(),
        html.Button("Generate Report", id='generate-button', n_clicks=0)
    ])
    return filters

# Callback to generate chart and table
@app.callback(
    Output('output-data-upload', 'children'),
    Input('generate-button', 'n_clicks'),
    State('stored-data', 'data'),
    State('channel-filter', 'value'),
    State('branch-filter', 'value'),
    State('city-filter', 'value'),
    State('customer-filter', 'value'),
    State('category-filter', 'value'),
    State('subcategory-filter', 'value'),
    State('item-filter', 'value')
)
def generate_report(n_clicks, data, channel, branch, city, customer, category, subcategory, item):
    if n_clicks == 0 or data is None:
        return None

    df = pd.DataFrame(data)

    # Apply filters
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

    # Create bar chart
    fig = px.bar(df, x='Channel', y='Total Price', color='Category', title='Total Price by Channel and Category')

    # Create data table
    table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'}
    )

    return html.Div([
        dcc.Graph(figure=fig),
        html.Hr(),
        html.H3("Filtered Data Table"),
        table
    ])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8000)
