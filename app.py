from dash import Dash, html, dcc, Input, Output, State, dash_table
import pandas as pd
import plotly.express as px
import base64
import io

app = Dash(__name__)
app.title = "Sales Hierarchical Report"

# Global store for uploaded data
data_store = {}

app.layout = html.Div([
    html.H2("Upload Sales CSV File"),
    dcc.Upload(
        id='upload-data',
        children=html.Div(['📁 Drag and Drop or ', html.A('Select File')]),
        style={
            'width': '60%',
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
    html.Div(id='file-status'),
    html.Div(id='sunburst-container'),
    html.Div(id='table-container')
])

@app.callback(
    Output('file-status', 'children'),
    Output('sunburst-container', 'children'),
    Output('table-container', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def handle_file_upload(contents, filename):
    if contents is None:
        return "", "", ""

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return f"❌ Error reading file: {e}", "", ""

    required_columns = [
        'Branch', 'City', 'Category', 'Sub Category', 'Item Name',
        'Total Qtys', 'Total Price'
    ]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return f"❌ Missing required columns: {', '.join(missing_cols)}", "", ""

    # Store the dataframe
    data_store['df'] = df

    # Create sunburst chart
    fig = px.sunburst(
        df,
        path=['Branch', 'City', 'Category', 'Sub Category', 'Item Name'],
        values='Total Qtys',
        color='Total Price',
        color_continuous_scale='RdBu',
        title='Sales Hierarchical Report'
    )

    sunburst_chart = dcc.Graph(figure=fig)

    # Create summary table
    summary = df.groupby(
        ['Branch', 'City', 'Category', 'Sub Category', 'Item Name'],
        as_index=False
    ).agg({
        'Total Qtys': 'sum',
        'Total Price': 'sum'
    })

    table = dash_table.DataTable(
        data=summary.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in summary.columns],
        page_size=15,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'}
    )

    return f"✅ File '{filename}' uploaded successfully.", sunburst_chart, table

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", port=8000)

