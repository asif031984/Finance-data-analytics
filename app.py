from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

# Sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value": [100, 200, 300, 400]
})

# Create a sample chart
fig = px.bar(df, x="Category", y="Value", title="Sample Bar Chart")

# Initialize Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Finance Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8000)
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd

# Sample data
df = pd.DataFrame({
    "Category": ["A", "B", "C", "D"],
    "Value": [100, 200, 300, 400]
})

# Create a sample chart
fig = px.bar(df, x="Category", y="Value", title="Sample Bar Chart")

# Initialize Dash app
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Finance Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8000)
