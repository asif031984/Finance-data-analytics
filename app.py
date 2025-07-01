# The previous code failed because the 'dash' module is not available in this environment.
# However, I can generate a downloadable Python file with the complete Dash app code as requested.

# Let's write the Dash app code to a file named 'advanced_sales_dashboard.py'

dash_app_code = '''
import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import io
import base64

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # for Azure deployment

# Global store for uploaded data
data_store = {}

# App layout
app.layout = html.Div([
    html.H1("📊 Sales Dashboard with Advanced Filters", style={"textAlign": "center"}),

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

    html.Div([
        html.Label("📌 Include Item Name in Summary Table"),
        dcc.Checklist(
            options=[{'label': 'Include Item Name', 'value': 'include_item'}],
            value=[],
            id='include-item-checklist',
            inline=True
        )
    ], style={'margin': '10px'}),

    html.Button("⬇️ Download Summary Data", id="download-button", n_clicks=0),
    dcc.Download(id="download-dataframe-xlsx"),

    dcc.Graph(id='bar-chart'),
    dcc.Graph(id='pie-chart'),

    html.Hr(),
    html.H3("📋 Monthly Summary Table"),
    dash_table.DataTable(id='summary-table', page_size=12, style_table={'overflowX': 'auto'})
])

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

    filters = []
    filter_columns = [
        'Rep Person Name', 'Channel', 'Branch', 'City',
        'Customer Name', 'Category', 'Sub Category', 'SKU Family', 'Item Name'
    ]

    for col in filter_columns:
        if col in df.columns:
            filters.append(html.Div([
                html.Label(col),
                dcc.Dropdown(
                    options=[{'label': i, 'value': i} for i in sorted(df[col].dropna().unique())],
                    id=f'filter-{col.replace(" ", "-").lower()}',
                    multi=True
                )
            ], style={'margin': '10px'}))

    return filters

# Callback to update charts and summary table
@app.callback(
    Output('bar-chart', 'figure'),
    Output('pie-chart', 'figure'),
    Output('summary-table', 'data'),
    Output('summary-table', 'columns'),
    Input('include-item-checklist', 'value'),
    Input('filter-rep-person-name', 'value'),
    Input('filter-channel', 'value'),
    Input('filter-branch', 'value'),
    Input('filter-city', 'value'),
    Input('filter-customer-name', 'value'),
    Input('filter-category', 'value'),
    Input('filter-sub-category', 'value'),
    Input('filter-sku-family', 'value'),
    Input('filter-item-name', 'value')
)
def update_outputs(include_item, rep, channel, branch, city, customer, category, subcat, sku, item):
    if 'df' not in data_store:
        return {}, {}, [], []

    df = data_store['df']

    # Apply filters
    filters = {
        'Rep Person Name': rep,
        'Channel': channel,
        'Branch': branch,
        'City': city,
        'Customer Name': customer,
        'Category': category,
        'Sub Category': subcat,
        'SKU Family': sku,
        'Item Name': item
    }

    for col, val in filters.items():
        if val:
            df = df[df[col].isin(val)]

    # Ensure Doc Date is datetime
    if 'Doc Date' in df.columns:
        df['Month'] = df['Doc Date'].dt.to_period('M').astype(str)

    # Create pivot summary
    group_cols = ['Month']
    if 'include_item' in include_item:
        group_cols.append('Item Name')

    summary = df.groupby(group_cols).agg({
        'Qty': 'sum',
        'Total Price': 'sum'
    }).reset_index()

    # Bar chart
    bar_fig = px.bar(summary, x='Month', y='Total Price', color='Month', title="Monthly Total Price")

    # Pie chart
    pie_fig = px.pie(df, names='Category', values='Total Price', title="Total Price by Category") if 'Category' in df.columns else {}

    # Data table
    columns = [{"name": i, "id": i} for i in summary.columns]
    data = summary.to_dict('records')

    # Store for download
    data_store['summary'] = summary

    return bar_fig, pie_fig, data, columns

# Callback to download summary data
@app.callback(
    Output("download-dataframe-xlsx", "data"),
    Input("download-button", "n_clicks"),
    prevent_initial_call=True
)
def download_summary_data(n_clicks):
    if 'summary' in data_store:
        df = data_store['summary']
        return dcc.send_data_frame(df.to_excel, "summary_data.xlsx", index=False)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0", port=8000)
'''

# Write the code to a Python file
with open("advanced_sales_dashboard.py", "w") as f:
    f.write(dash_app_code)

print("Dash app code has been written to 'advanced_sales_dashboard.py'.")
