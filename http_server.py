import threading
from time import sleep
from flask import Flask
from flask import render_template, request

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config.from_object(__name__)

serverHost = "ws://${location.hostname}:8000"  # ${location.hostname}


@app.route('/')
def projects():
    return render_template("index.html", title='UNO Supreme', serverHost=serverHost)


@app.route('/many')
def many():
    return render_template("many.html", title='UNO Supreme', serverHost=serverHost)


@app.route('/wsT')
def wsT():
    return render_template("websocketTester.html", title='UNO Supreme', serverHost=serverHost)

@app.route('/console')
def console():
    # serverHost: ${location.hostname}
    return render_template("console.html", title='Debug console', serverHost=serverHost)


@app.route("/table")
def desk():
    # serverHost: ${location.hostname}
    return render_template("table.html", title="Table Stuff", serverHost=serverHost)


def flaskServer():
    app.run("0.0.0.0", 80)


def run():
    threading.Thread(target=flaskServer, daemon=True).start()

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "max-age=604800"
    #r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "9999"
    r.headers['Cache-Control'] = 'public, max-age=9999'
    return r

if __name__ == "__main__":
    run()
    while True:
        sleep(100)
