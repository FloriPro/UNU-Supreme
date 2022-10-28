import threading
from flask import Flask
from flask import render_template, request

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config.from_object(__name__)

serverHost = "${location.hostname}" #${location.hostname}


@app.route('/')
def projects():
    return render_template("index.html", title='UNO Supreme', serverHost=serverHost)


@app.route("/consoleEval", methods=["POST"])
def runCommand():
    global master
    command = request.data.decode("UTF-8")


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
