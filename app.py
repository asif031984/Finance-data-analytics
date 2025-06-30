import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import base64
import io

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Finance Dashboard with Predictive Modeling"),
    dcc.Tabs(id="tabs", value='tab-analytics', children=[
        dcc.Tab(label='📊 Data Analytics', value='tab-analytics'),
        dcc.Tab(label='🤖 Predictive Modeling', value='tab-modeling'),
    ]),
    html.Div(id='tabs-content')
])

# Store uploaded data
data_store = {}

# Layout for Data Analytics Tab
analytics_layout = html.Div([
    dcc.Upload(
        id='upload-data-analytics',
        children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
        style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
               'borderWidth': '1px', 'borderStyle': 'dashed',
               'borderRadius': '5px', 'textAlign': 'center'},
        multiple=False
    ),
    html.Div(id='file-name-analytics'),
    html.Div([
        html.Label("Filter by Channel"),
        dcc.Dropdown(id='channel-filter', multi=True),
        html.Label("Filter by Branch"),
        dcc.Dropdown(id='branch-filter', multi=True),
        html.Label("Filter by City"),
        dcc.Dropdown(id='city-filter', multi=True),
        html.Label("Filter by Category"),
        dcc.Dropdown(id='category-filter', multi=True),
        html.Label("Filter by Sub Category"),
        dcc.Dropdown(id='subcategory-filter', multi=True),
        html.Label("Filter by Item Name"),
        dcc.Dropdown(id='item-filter', multi=True),
        html.Label("Filter by Date Range"),
        dcc.DatePickerRange(id='date-filter')
    ], style={'columnCount': 2}),
    dcc.Graph(id='analytics-chart'),
    dash_table.DataTable(id='analytics-table',
                         page_size=10,
                         style_table={'overflowX': 'auto'},
                         style_cell={'textAlign': 'left'})
])

# Layout for Predictive Modeling Tab
modeling_layout = html.Div([
    dcc.Upload(
        id='upload-data-modeling',
        children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
        style={'width': '100%', 'height': '60px', 'lineHeight': '60px',
               'borderWidth': '1px', 'borderStyle': 'dashed',
               'borderRadius': '5px', 'textAlign': 'center'},
        multiple=False
    ),
    html.Div(id='file-name-modeling'),
    html.Div([
        html.Label("Select Feature Columns"),
        dcc.Dropdown(id='feature-columns', multi=True),
        html.Label("Select Target Column"),
        dcc.Dropdown(id='target-column'),
        html.Button("Train Model", id='train-button', n_clicks=0)
    ]),
    html.Div(id='model-output'),
    dcc.Graph(id='prediction-chart'),
    dash_table.DataTable(id='prediction-table',
                         page_size=10,
                         style_table={'overflowX': 'auto'},
                         style_cell={'textAlign': 'left'})
])

@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-analytics':
        return analytics_layout
    elif tab == 'tab-modeling':
        return modeling_layout

@app.callback(
    Output('file-name-analytics', 'children'),
    Output('channel-filter', 'options'),
    Output('branch-filter', 'options'),
    Output('city-filter', 'options'),
    Output('category-filter', 'options'),
    Output('subcategory-filter', 'options'),
    Output('item-filter', 'options'),
    Output('date-filter', 'start_date'),
    Output('date-filter', 'end_date'),
    Input('upload-data-analytics', 'contents'),
    State('upload-data-analytics', 'filename')
)
def update_analytics_filters(contents, filename):
    if contents is None:
        return "", [], [], [], [], [], [], None, None

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    data_store['analytics'] = df

    options = lambda col: [{'label': i, 'value': i} for i in sorted(df[col].dropna().unique())] if col in df else []

    start_date = pd.to_datetime(df['Doc Date']).min() if 'Doc Date' in df else None
    end_date = pd.to_datetime(df['Doc Date']).max() if 'Doc Date' in df else None

    return f"Uploaded: {filename}", options('Channel'), options('Branch'), options('City'), options('Category'), options('Sub Category'), options('Item Name'), start_date, end_date

@app.callback(
    Output('analytics-chart', 'figure'),
    Output('analytics-table', 'data'),
    Output('analytics-table', 'columns'),
    Input('channel-filter', 'value'),
    Input('branch-filter', 'value'),
    Input('city-filter', 'value'),
    Input('category-filter', 'value'),
    Input('subcategory-filter', 'value'),
    Input('item-filter', 'value'),
    Input('date-filter', 'start_date'),
    Input('date-filter', 'end_date')
)
def update_analytics_output(channel, branch, city, category, subcategory, item, start_date, end_date):
    df = data_store.get('analytics')
    if df is None:
        return {}, [], []

    df['Doc Date'] = pd.to_datetime(df['Doc Date'], errors='coerce')
    if start_date and end_date:
        df = df[(df['Doc Date'] >= start_date) & (df['Doc Date'] <= end_date)]

    filters = {
        'Channel': channel,
        'Branch': branch,
        'City': city,
        'Category': category,
        'Sub Category': subcategory,
        'Item Name': item
    }

    for col, val in filters.items():
        if val and col in df:
            df = df[df[col].isin(val)]

    if 'Channel' in df and 'Total Price' in df:
        fig = px.bar(df, x='Channel', y='Total Price', color='Category', title='Total Price by Channel and Category')
    else:
        fig = {}

    table_data = df.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df.columns]

    return fig, table_data, table_columns

@app.callback(
    Output('file-name-modeling', 'children'),
    Output('feature-columns', 'options'),
    Output('target-column', 'options'),
    Input('upload-data-modeling', 'contents'),
    State('upload-data-modeling', 'filename')
)
def update_modeling_inputs(contents, filename):
    if contents is None:
        return "", [], []

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    data_store['modeling'] = df

    options = [{'label': col, 'value': col} for col in df.columns]
    return f"Uploaded: {filename}", options, options

@app.callback(
    Output('model-output', 'children'),
    Output('prediction-chart', 'figure'),
    Output('prediction-table', 'data'),
    Output('prediction-table', 'columns'),
    Input('train-button', 'n_clicks'),
    State('feature-columns', 'value'),
    State('target-column', 'value')
)
def train_model(n_clicks, features, target):
    if n_clicks == 0 or not features or not target:
        return "", {}, [], []

    df = data_store.get('modeling')
    if df is None or any(col not in df for col in features + [target]):
        return "Invalid data or columns", {}, [], []

    df = df.dropna(subset=features + [target])
    X = df[features]
    y = df[target]

    try:
        X = X.apply(pd.to_numeric)
        y = pd.to_numeric(y)
    except:
        return "Non-numeric data found. Please select numeric columns.", {}, [], []

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    result_df = X_test.copy()
    result_df['Actual'] = y_test
    result_df['Predicted'] = y_pred

    fig = px.scatter(result_df, x='Actual', y='Predicted', title='Actual vs Predicted')

    return f"Model Trained. MSE: {mse:.2f}, R²: {r2:.2f}", fig, result_df.to_dict('records'), [{"name": i, "id": i} for i in result_df.columns]

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)
