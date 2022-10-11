import asyncio
from re import S
from tkinter import W
import websockets
import threading
import random
import json
from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config.from_object(__name__)


@app.route('/')
def projects():
    return render_template("index.html", title='UNO Supreme')


cards = {"red":    {8: ["2+", "aussetzen", "richtungswechsel"], 4: ["komunist"], 2: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
         "green":  {8: ["2+", "aussetzen", "richtungswechsel"], 4: ["komunist"], 2: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
         "yellow": {8: ["2+", "aussetzen", "richtungswechsel"], 4: ["komunist"], 2: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
         "blue":   {8: ["2+", "aussetzen", "richtungswechsel"], 4: ["komunist"], 2: ["1", "2", "3", "4", "5", "6", "7", "8", "9"]},
         "": {8: ["farbwechsel"], 4: ["fabwechsel4+"]}}

deck = []
for color in cards.keys():
    for numbers in cards[color].keys():
        for i in range(numbers):
            for player in cards[color][numbers]:
                deck.append(color+"_"+player)


class gameMaster:
    def __init__(self):
        self.events = {}

        self.status = {"type": "waiting_for_players"}
        self.currentPlayer = 0

        self.players = []
        self.playerNames = {}
        self.playerWebsocket = {}

        self.playerDeck = {}
        self.availableCards = deck
        self.lyingCards = []

    def setCards(self):
        i = 0
        for playerId in self.players:
            for i in range(2):
                choice = random.randint(0, len(self.availableCards)-1)
                self.playerDeck[playerId] = self.availableCards[choice]
                self.availableCards.pop(choice)
                i += 1

            self.addEvent(playerId,
                          {"type": "stats", "dat": {
                              "type": "deck",
                              "dat": self.playerDeck[playerId]
                          }})
        self.status = "playing"

    def addEvents(self, dat):
        for x in self.players:
            if not x in self.events:
                self.events[x] = []
            self.events[x].append(dat)

    def addEvent(self, player, dat):
        if not player in self.events:
            self.events[player] = []
        self.events[player].append(dat)


master = gameMaster()


async def handleEvents(playerId, websocket, master):
    for x in master.events[playerId]:
        await websocket.send(x)


async def player(websocket, path):
    global master

    playerId = random.randint(0, 9999999999999)
    master.players.append(playerId)
    master.playerWebsocket[playerId] = websocket
    try:
        await websocket.send(json.dumps({"type": "message", "dat": "Mit UNO-Supreme Verbunden!"}))
        await websocket.send(json.dumps({"type": "message", "dat": "Spieler anzahl zurzeit: "+str(len(master.players))}))

        playerName = ""
        while not (playerName != "" and not playerName in master.playerNames.values()):
            await websocket.send(json.dumps({"type": "action", "dat": "get_name"}))
            playerName = await websocket.recv()
        master.playerNames[playerId] = playerName

        playing = True
        while playing:
            # waiting for players to join
            while master.status["type"] == "waiting_for_players":
                await websocket.send(json.dumps({"type": "stats", "dat": {"type": "players", "dat": {"id": master.players, "name": master.playerNames}}}))
                await asyncio.sleep(2)
                await handleEvents(playerId, websocket, master)

    except websockets.ConnectionClosed as e:
        pass
    except websockets.ConnectionClosedError as e:
        pass
    print("disconnect")
    master.players.remove(playerId)
    master.playerWebsocket.pop(playerId)
    master.playerNames.pop(playerId)


start_server = websockets.serve(player, '', 8000)


def flaskServer():
    app.run("0.0.0.0", 80)


threading.Thread(target=flaskServer, daemon=True).start()
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
