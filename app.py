import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import base64
import io

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for Azure deployment

# === Modular Components ===

def create_upload_component():
    return dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Excel File')]),
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
    )

def create_filter_dropdown(df, column_name, dropdown_id):
    return html.Div([
        html.Label(column_name),
        dcc.Dropdown(
            options=[{'label': i, 'value': i} for i in df[column_name].dropna().unique()],
            id=dropdown_id,
            multi=True
        )
    ])

def create_filters(df):
    return html.Div([
        dcc.Store(id='stored-data', data=df.to_dict('records')),
        create_filter_dropdown(df, 'Channel', 'channel-filter'),
        create_filter_dropdown(df, 'Branch', 'branch-filter'),
        create_filter_dropdown(df, 'City', 'city-filter'),
        create_filter_dropdown(df, 'Customer Name', 'customer-filter'),
        create_filter_dropdown(df, 'Category', 'category-filter'),
        create_filter_dropdown(df, 'Sub Category', 'subcategory-filter'),
        create_filter_dropdown(df, 'Item Name', 'item-filter'),
        html.Br(),
        html.Button("Generate Report", id='generate-button', n_clicks=0)
    ])

def create_chart(df):
    fig = px.bar(df, x='Channel', y='Total Price', color='Category', title='Total Price by Channel and Category')
    return dcc.Graph(figure=fig)

def create_data_table(df):
    return dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'}
    )

# === App Layout ===
app.layout = html.Div([
    html.H1("Finance Reporting Dashboard"),
    create_upload_component(),
    html.Div(id='filter-container'),
    html.Div(id='output-data-upload')
])

# === Callbacks ===

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
    return create_filters(df)

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

    return html.Div([
        create_chart(df),
        html.Hr(),
        html.H3("Filtered Data Table"),
        create_data_table(df)
    ])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, host="0.0.0.0", port=8000)
