import pandas as pd
from threading import Thread
from flask import Flask,render_template,request,redirect
from tornado.ioloop import IOLoop
import simplejson as json
import requests
import datetime

from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, HoverTool, TextInput, CustomJS
from bokeh.io import curdoc
from bokeh.plotting import figure, output_file, show
from bokeh.server.server import Server
from bokeh.themes import Theme


app = Flask(__name__)

print("HI")

def bkapp(doc):
    def callback(attrname, old, new):
        symbol = text_input.value
        doc.clear()
        print(symbol)
        get_graph(get_data(symbol))

    text_input = TextInput(value="aapl",title="Stock Ticker:")
    text_input.on_change("value", callback)

    def get_data(symbol):
        API_URL = "https://www.alphavantage.co/query"
        # symbol = input("Stock Ticker:").upper()

        data = { "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize" : "full",
            "datatype": "json",
            "apikey": "GH5U75JGWCE1C0C3" }

        response = requests.get(API_URL, data)
        response_json = response.json()

        print('JSON: ', response_json)

        df = pd.DataFrame.from_dict(response_json['Time Series (Daily)'], orient= 'index').sort_index(axis=1)
        df = df.rename(columns={ '1. open': 'Open', '2. high': 'High', '3. low': 'Low', '4. close': 'Close', '5. volume': 'Volume'})
        df = df[[ 'Open', 'High', 'Low', 'Close', 'Volume']]
        df.reset_index(inplace=True)
        df['index'] = pd.to_datetime(df['index'])
        mask = (df['index'] >= '2020-07-01') & (df['index'] <= '2020-08-31')
        df1 = df.loc[mask]
        return df1

    def get_graph(dataframe):
        # output_file("graph.html")
        
        p = figure(plot_width=800 ,plot_height=800, x_axis_type="datetime")
        p.background_fill_color="#f5f5f5"
        p.grid.grid_line_color="white"
        p.xaxis.axis_label = "Dates of August 2020"
        p.yaxis.axis_label = "Closing Price"
        p.axis.axis_line_color = None
        p.title.text = 'Monthly Stock Data of ' + text_input.value.upper()
        p.title.text_font = "Times"
        p.title.text_font_size = "20px"

        # add a line renderer
        p.line(dataframe['index'], dataframe['Close'], line_width=2)

        p.add_tools(HoverTool(
            tooltips=[
                ( 'Date',   '@x{%F}'     ), # does not seem to show the correct format
                ( 'Close',  '$@y{%0.2f}' ),
            ],

            formatters={
                '@x'      : 'datetime',
                '@y'     : 'printf',
            },

            # display a tooltip whenever the cursor is vertically in line with a glyph
            mode='vline'
        ))
        doc.add_root(column(p, text_input))

        # show(column(p, text_input))

    get_graph(get_data("AAPL"))

@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': bkapp}, io_loop=IOLoop(), allow_websocket_origin=["localhost:8000"])
    server.start()
    server.io_loop.start()

Thread(target=bk_worker).start()

if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)
