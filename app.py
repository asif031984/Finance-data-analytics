import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for Azure deployment

# Layout of the app
app.layout = html.Div([
    html.H2("Finance Dashboard with Rep Reporting"),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            '📁 Drag and Drop or ',
            html.A('Select Excel File')
        ]),
        style={
            'width': '100%', 'height': '60px', 'lineHeight': '60px',
            'borderWidth': '1px', 'borderStyle': 'dashed',
            'borderRadius': '5px', 'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    html.Div(id='file-name', style={'margin': '10px', 'fontWeight': 'bold'}),

    html.Div([
        html.Div([
            html.Label("Rep Person Name"),
            dcc.Dropdown(id='rep-filter', multi=True)
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Channel"),
            dcc.Dropdown(id='channel-filter', multi=True)
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Branch"),
            dcc.Dropdown(id='branch-filter', multi=True)
        ], style={'width': '24%', 'display': 'inline-block'}),

        html.Div([
            html.Label("City"),
            dcc.Dropdown(id='city-filter', multi=True)
        ], style={'width': '24%', 'display': 'inline-block'}),
    ], style={'marginTop': '10px'}),

    html.Div([
        html.Div([
            html.Label("Customer Name"),
            dcc.Dropdown(id='customer-filter', multi=True)
        ], style={'width': '32%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Category"),
            dcc.Dropdown(id='category-filter', multi=True)
        ], style={'width': '32%', 'display': 'inline-block'}),

        html.Div([
            html.Label("Sub Category"),
            dcc.Dropdown(id='subcategory-filter', multi=True)
        ], style={'width': '32%', 'display': 'inline-block'}),
    ], style={'marginTop': '10px'}),

    dcc.Graph(id='bar-chart', style={'marginTop': '20px'}),
    dash_table.DataTable(id='data-table', page_size=10, style_table={'overflowX': 'auto'}),

    dcc.Store(id='stored-data')
])

# Callback to parse uploaded Excel file and store data
@app.callback(
    Output('stored-data', 'data'),
    Output('file-name', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def parse_upload(contents, filename):
    if contents is None:
        return dash.no_update, ""
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
    return df.to_dict('records'), f"Uploaded File: {filename}"

# Callback to populate dropdowns based on uploaded data
@app.callback(
    Output('rep-filter', 'options'),
    Output('channel-filter', 'options'),
    Output('branch-filter', 'options'),
    Output('city-filter', 'options'),
    Output('customer-filter', 'options'),
    Output('category-filter', 'options'),
    Output('subcategory-filter', 'options'),
    Input('stored-data', 'data')
)
def populate_filters(data):
    if data is None:
        return [[]]*7
    df = pd.DataFrame(data)
    return [
        [{'label': i, 'value': i} for i in sorted(df['Rep Person Name'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['Channel'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['Branch'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['City'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['Customer Name'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['Category'].dropna().unique())],
        [{'label': i, 'value': i} for i in sorted(df['Sub Category'].dropna().unique())],
    ]

# Callback to update chart and table based on filters
@app.callback(
    Output('bar-chart', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('stored-data', 'data'),
    Input('rep-filter', 'value'),
    Input('channel-filter', 'value'),
    Input('branch-filter', 'value'),
    Input('city-filter', 'value'),
    Input('customer-filter', 'value'),
    Input('category-filter', 'value'),
    Input('subcategory-filter', 'value')
)
def update_output(data, rep, channel, branch, city, customer, category, subcat):
    if data is None:
        return {}, [], []
    df = pd.DataFrame(data)

    # Apply filters
    if rep:
        df = df[df['Rep Person Name'].isin(rep)]
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
    if subcat:
        df = df[df['Sub Category'].isin(subcat)]

    # Create bar chart
    if not df.empty:
        fig = px.bar(df, x='Rep Person Name', y='Total Price', color='Category', barmode='group',
                     title='Total Price by Rep and Category')
    else:
        fig = px.bar(title='No data to display')

    # Prepare data table
    columns = [{"name": i, "id": i} for i in df.columns]
    return fig, df.to_dict('records'), columns

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)

