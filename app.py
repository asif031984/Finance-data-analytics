from dash import Dash, html

app = Dash(__name__)
app.layout = html.Div("Hello from Dash on Azure!")

if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8000)
