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
app.title = "Finance Dashboard with Predictive Modeling"

# Layout with Tabs
app.layout = html.Div([
    html.H1("Finance Dashboard with Predictive Modeling", style={"textAlign": "center"}),

    dcc.Tabs(id="tabs", value='tab-analytics', children=[
        dcc.Tab(label='📊 Data Analytics Dashboard', value='tab-analytics'),
        dcc.Tab(label='🤖 Predictive Modeling', value='tab-predictive'),
    ]),
    html.Div(id='tabs-content')
])

# Store uploaded data
uploaded_data = {}

# Callback to render tab content
@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-analytics':
        return html.Div([
            dcc.Upload(
                id='upload-data-analytics',
                children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='analytics-output')
        ])
    elif tab == 'tab-predictive':
        return html.Div([
            dcc.Upload(
                id='upload-data-predictive',
                children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
            html.Div(id='predictive-controls'),
            html.Div(id='predictive-output')
        ])

# Callback for analytics tab
@app.callback(Output('analytics-output', 'children'),
              Input('upload-data-analytics', 'contents'),
              State('upload-data-analytics', 'filename'))
def update_analytics(contents, filename):
    if contents is None:
        return html.Div("Upload a CSV file to begin.")
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    uploaded_data['analytics'] = df

    # Basic filters
    filters = ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']
    filter_dropdowns = []
    for col in filters:
        if col in df.columns:
            filter_dropdowns.append(
                dcc.Dropdown(
                    id=f'filter-{col}',
                    options=[{'label': val, 'value': val} for val in sorted(df[col].dropna().unique())],
                    placeholder=f'Select {col}',
                    multi=True
                )
            )

    return html.Div([
        html.Div(filter_dropdowns, style={'columnCount': 2}),
        dcc.Graph(id='analytics-chart'),
        dash_table.DataTable(id='analytics-table', page_size=10, style_table={'overflowX': 'auto'})
    ])

# Callback to update chart and table based on filters
@app.callback(
    Output('analytics-chart', 'figure'),
    Output('analytics-table', 'data'),
    Output('analytics-table', 'columns'),
    [Input(f'filter-{col}', 'value') for col in ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']]
)
def update_analytics_chart(*filter_values):
    df = uploaded_data.get('analytics')
    if df is None:
        return {}, [], []

    filters = ['Channel', 'Branch', 'City', 'Category', 'Sub Category', 'Item Name']
    for col, val in zip(filters, filter_values):
        if val:
            df = df[df[col].isin(val)]

    if 'Total Price' in df.columns and 'Category' in df.columns:
        fig = px.bar(df, x='Category', y='Total Price', color='Category', title='Total Price by Category')
    else:
        fig = px.bar(title="Missing required columns")

    table_data = df.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df.columns]

    return fig, table_data, table_columns

# Callback for predictive tab
@app.callback(
    Output('predictive-controls', 'children'),
    Input('upload-data-predictive', 'contents'),
    State('upload-data-predictive', 'filename')
)
def update_predictive_controls(contents, filename):
    if contents is None:
        return html.Div("Upload a CSV file to begin.")
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    uploaded_data['predictive'] = df

    return html.Div([
        html.Label("Select Feature Columns:"),
        dcc.Dropdown(
            id='feature-columns',
            options=[{'label': col, 'value': col} for col in df.columns],
            multi=True
        ),
        html.Label("Select Target Column:"),
        dcc.Dropdown(
            id='target-column',
            options=[{'label': col, 'value': col} for col in df.columns],
            multi=False
        ),
        html.Button("Train Model", id='train-model', n_clicks=0)
    ])

# Callback to train model and show results
@app.callback(
    Output('predictive-output', 'children'),
    Input('train-model', 'n_clicks'),
    State('feature-columns', 'value'),
    State('target-column', 'value')
)
def train_model(n_clicks, features, target):
    if n_clicks == 0 or not features or not target:
        return html.Div()

    df = uploaded_data.get('predictive')
    if df is None or not all(col in df.columns for col in features + [target]):
        return html.Div("Invalid data or missing columns.")

    X = df[features]
    y = df[target]
    X = pd.get_dummies(X, drop_first=True)  # Handle categorical variables
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    results_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
    fig = px.scatter(results_df, x='Actual', y='Predicted', title='Actual vs Predicted')

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    return html.Div([
        html.H4("Model Evaluation"),
        html.P(f"Mean Squared Error: {mse:.2f}"),
        html.P(f"R² Score: {r2:.2f}"),
        dcc.Graph(figure=fig),
        dash_table.DataTable(
            data=results_df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in results_df.columns],
            page_size=10
        )
    ])

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=8000)
