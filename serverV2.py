from math import ceil, floor
import re
from threading import Thread
import asyncio
from time import sleep, time
from turtle import title
from simple_websocket_server import WebSocketServer, WebSocket
from re import S
from tkinter import W
import traceback
import threading
import random
import json
from flask import Flask
from flask import render_template, request

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config.from_object(__name__)


@app.route('/')
def projects():
    return render_template("index.html", title='UNO Supreme')


@app.route("/consoleEval", methods=["POST"])
def runCommand():
    global master
    command = request.data.decode("UTF-8").split(" ")
    if command[0] == "players":
        returnDat = []
        for player in master.players:
            if player in master.playerNames.keys():
                name = master.playerNames[player]
            else:
                name = "undefined"
            returnDat.append(name+": "+str(player))
            pass
        return ",\n".join(returnDat)
    elif command[0] == "give":
        if int(command[2]) not in master.playerDeck.keys():
            return "player doesn't exist"
        master.playerDeck[int(command[2])].append(command[1])
        master.addEvent(int(command[2]),
                        {"type": "action", "dat": {
                            "type": "addCard",
                            "dat": command[1]

                        }})
        master.easyEvents("playerCardCount")
        return "ok!"
    return "command did not return"


@app.route('/console')
def console():
    return render_template("console.html", title='Debug console')


@app.route("/table")
def desk():
    return render_template("table.html", title="Table Stuff")


cards = {"red":    {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9", "komunist"]},
         "green":  {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9", "komunist"]},
         "yellow": {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9", "komunist"]},
         "blue":   {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9", "komunist"]},
         "": {4: ["farbwechsel4+", "farbwechsel"]}}

deck = []
for color in cards.keys():
    for numbers in cards[color].keys():
        for i in range(numbers):
            for cardType in cards[color][numbers]:
                deck.append(color+"_"+cardType)

deck += deck
deck += deck
deck += deck
deck += deck

startCardCount = 2


class gameMaster:
    def __init__(self):
        self.twoPlusAdder = 0

        self.events = {}

        self.status = "waiting_for_players"
        self.currentPlayer = 0
        self.direction = 1

        self.tables = []

        self.players = []
        self.playerNames = {}
        self.playerClasses = {}

        self.playerDeck = {}
        self.availableCards = deck
        self.lyingCards = []

        self.cardCache = ""

    def sendTable(self, dat):
        for value in self.tables:
            value.send_message(json.dumps(dat))

    def setCards(self):
        self.availableCards = deck
        iteration = 0
        for playerId in self.players:
            self.playerDeck[playerId] = []
            for i in range(startCardCount):
                choice = random.randint(0, len(self.availableCards)-1)
                self.playerDeck[playerId].append(self.availableCards[choice])
                self.availableCards.pop(choice)
                iteration += 1

            self.addEvent(playerId,
                          {"type": "stats", "dat": {
                              "type": "deck",
                              "dat": self.playerDeck[playerId]
                          }})
        self.status = "playing"
        self.addEvents({"type": "status", "dat": "playing"})

    def start(self):
        self.setCards()
        choice = random.randint(0, len(self.availableCards)-1)
        self.lyingCards = []
        self.lyingCards.append(self.availableCards[choice])
        self.availableCards.pop(choice)

        self.addEvents({
            "type": "action",
            "dat": "startGame"
        })

        self.easyEvents("cardRedo")
        self.askPlayer()

    def playerHas2x(self, playerId):
        for x in self.playerDeck[playerId]:
            if x.endswith("2+"):
                return True

    def askPlayer(self):
        playerId = self.players[self.currentPlayer]
        self.addEvents({"type": "stats", "dat": {
            "type": "currentPlayer",
            "dat": self.currentPlayer
        }})
        self.sendTable({
            "type": "currentPlayer",
            "dat": self.currentPlayer
        })
        if self.lyingCards[-1].endswith("4+"):
            self.drawCard(playerId)
            self.drawCard(playerId)
            self.drawCard(playerId)
            self.drawCard(playerId)
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du Hast 4 Karten gezogen"}))
        if self.lyingCards[-1].endswith("2+"):
            self.twoPlusAdder += 2
            if self.playerHas2x(playerId):
                self.addEvent(
                    playerId, {"type": "status", "dat": "2+_Desicion"})
                self.addEvent(
                    playerId, {"type": "action", "dat": "slect2+Card", "dat2": self.twoPlusAdder})
            else:
                for x in range(self.twoPlusAdder):
                    self.drawCard(playerId)
                self.playerClasses[playerId].send_message(json.dumps(
                    {"type": "message", "dat": "Du Hast "+str(self.twoPlusAdder)+" Karten gezogen"}))
                self.twoPlusAdder = 0
                self.addEvent(playerId, {"type": "status", "dat": "slectCard"})
                self.addEvent(playerId, {"type": "action", "dat": "slectCard"})
        else:
            self.twoPlusAdder = 0
            self.addEvent(playerId, {"type": "status", "dat": "slectCard"})
            self.addEvent(playerId, {"type": "action", "dat": "slectCard"})

    def withdraw2x(self, playerId):
        for x in range(self.twoPlusAdder):
            self.drawCard(playerId)
        self.playerClasses[playerId].send_message(json.dumps(
            {"type": "message", "dat": "Du Hast "+str(self.twoPlusAdder)+" Karten gezogen"}))
        self.twoPlusAdder = 0
        self.addEvent(playerId, {"type": "status", "dat": "slectCard"})
        self.addEvent(playerId, {"type": "action", "dat": "slectCard"})

    def layCard(self, card, playerId):
        if playerId != self.players[self.currentPlayer]:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du bist zurzeit nicht am zug!"}))
            return
        if len(card) == 1:
            if (card[0] in self.playerDeck[playerId]):
                c = card[0].split("_")
                lc = self.lyingCards[-1].split("_")

                ok = True

                if c[0] == "":
                    pass
                else:
                    if c[0] != lc[0] and c[1] != lc[1]:
                        ok = False
                if ok:
                    if c[1] == "richtungswechsel":
                        self.direction = self.direction*-1
                    if c[1] == "komunist":
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(
                            playerId, {"type": "action", "dat": "removeCard", "dat2": card[0]})

                        self.lyingCards.append(card[0])
                        self.easyEvents("cardAdd", card[0])

                        #self.playerClasses[playerId].send_message(json.dumps(
                        #    {"type": "message", "dat": "Karte gelegt!"}))
                        self.addEvents(
                            {"type": "message", "dat": "Karten werden neu gemischt....."})

                        threading.Thread(target=self.komunist,
                                         daemon=True).start()
                        return
                    if c[1] == "farbwechsel" or c[1] == "farbwechsel4+":
                        self.cardCache = card[0]
                        self.playerClasses[playerId].send_message(json.dumps(
                            {"type": "status", "dat": "waiting_for_color"}))
                        self.playerClasses[playerId].send_message(json.dumps(
                            {"type": "action", "dat": "select_color"}))
                    else:
                        self.lyingCards.append(card[0])
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(
                            playerId, {"type": "action", "dat": "removeCard", "dat2": card[0]})
                        self.easyEvents("cardAdd", card[0])
                        #self.playerClasses[playerId].send_message(json.dumps(
                        #    {"type": "message", "dat": "Karte gelegt!"}))
                        if (card[0].endswith("_aussetzen")):
                            self.nextPlayer(2)
                        else:
                            self.nextPlayer()

                else:
                    self.playerClasses[playerId].send_message(json.dumps(
                        {"type": "message", "dat": "Du darfst diese Karte nicht legen!"}))
            else:
                self.playerClasses[playerId].send_message(json.dumps(
                    {"type": "message", "dat": "Du hast diese Karte garnicht"}))
                self.addEvent(playerId,
                              {"type": "stats", "dat": {
                                  "type": "deck",
                                  "dat": self.playerDeck[playerId]
                              }})
        else:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Karten-combos zurzeit nicht verfügbar!"}))

    def komunist(self):
        toMix = []
        for key, value in self.playerDeck.items():
            self.playerDeck[key] = []
            toMix += value
            sleep(1)
            self.addEvent(key,
                          {"type": "stats", "dat": {
                              "type": "deck",
                              "dat": []
                          }})
            self.easyEvents("playerCardCount")

        for s in range(5):
            sleep(2)
            self.addEvents({"type": "message", "dat": f"mischen... {s+1}/5"})

        cards = ceil(len(toMix)/len(self.players))

        for x in range(cards):
            for player in self.players:
                if len(toMix) != 0:
                    choice = random.randint(0, len(toMix)-1)
                    self.playerDeck[player].append(toMix[choice])
                    toMix.pop(choice)
                else:
                    choice = random.randint(0, len(self.availableCards)-1)
                    self.playerDeck[player].append(self.availableCards[choice])
                    self.availableCards.pop(choice)

        # update players of their deck
        for player in self.players:
            self.addEvent(player,
                          {"type": "stats", "dat": {
                              "type": "deck",
                              "dat": self.playerDeck[player]
                          }})
        self.easyEvents("playerCardCount")
        self.nextPlayer()

    def selectColor(self, playerId, color):
        if self.players[self.currentPlayer] == playerId:
            self.lyingCards.append(color+self.cardCache)
            self.playerDeck[playerId].remove(self.cardCache)
            self.addEvent(
                playerId, {"type": "action", "dat": "removeCard", "dat2": self.cardCache})
            self.easyEvents("cardAdd", color+self.cardCache)
            #self.playerClasses[playerId].send_message(json.dumps(
            #    {"type": "message", "dat": "Karte gelegt!"}))
            self.nextPlayer()
        else:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du bist zurzeit nicht am zug!"}))

    def nextPlayer(self, count=1):
        self.addEvent(self.players[self.currentPlayer], {
                      "type": "status", "dat": "playing"})
        for x in range(count):
            self.currentPlayer += self.direction
            if self.currentPlayer >= len(self.players):
                self.currentPlayer = 0
            if self.currentPlayer < 0:
                self.currentPlayer = len(self.players)-1
        self.askPlayer()

    def easyEvents(self, etype, dat=None):
        if etype == "playerlist":
            self.addEvents({"type": "stats", "dat": {"type": "players", "dat": {
                           "id": self.players, "name": self.playerNames}}})
            self.sendTable({"type": "players",
                            "dat": {
                                "id": self.players,
                                "name": self.playerNames
                            }})
        if etype == "cardList":
            for playerId in self.players:
                self.addEvent(playerId,
                              {"type": "stats", "dat": {
                                  "type": "deck",
                                  "dat": self.playerDeck[playerId]
                              }})
        if etype == "disconnect":
            self.easyEvents("playerlist")
        if etype == "cardRedo":
            self.addEvents({"type": "stats", "dat": {
                "type": "lyingCards",
                "dat": self.lyingCards
            }})
            self.sendTable({
                "type": "lyingCards",
                "dat": self.lyingCards
            })

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})

            self.sendTableAll()
        if etype == "cardAdd":
            self.addEvents({"type": "action", "dat": {
                "type": "lyingCards",
                "dat": dat
            }})
            self.sendTable({
                "type": "lyingCardsAdd",
                "dat": dat
            })

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})
            self.sendTableAll()
        if etype == "playerCardCount":
            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})
            self.sendTable({
                "type": "playerCardCount",
                "dat": counts
            })

    def sendTableAll(self):
        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        self.sendTable({
            "type": "playerCardCount",
            "dat": counts
        })

    def addEvents(self, dat):
        for x in self.players:
            if not x in self.events:
                self.events[x] = []
            self.events[x].append(dat)

        self.runEvents()

    def drawCard(self, playerId):
        if playerId != self.players[self.currentPlayer]:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du bist zurzeit nicht am zug!"}))
            return
        if len(self.playerDeck[playerId]) < 25:
            choice = random.randint(0, len(self.availableCards)-1)
            self.playerDeck[playerId].append(self.availableCards[choice])
            self.addEvent(playerId,
                          {"type": "action", "dat": {
                              "type": "addCard",
                              "dat": self.availableCards[choice]

                          }})
            self.availableCards.pop(choice)
            self.easyEvents("playerCardCount")
        else:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du hast schon zu viele Karten"}))

    def addEvent(self, player, dat):
        if not player in self.events:
            self.events[player] = []
        self.events[player].append(dat)

        self.runEvents()

    def runEvents(self):
        for x in self.players:
            for i in self.events[x]:
                self.playerClasses[x].send_message(json.dumps(i))
            self.events[x] = []


master = gameMaster()


class Player(WebSocket):
    def handle(self):
        try:
            global master
            data = json.loads(self.data)

            if data["type"] == "start_game":
                master.start()

            elif self.currentAction == "get_name" and data["type"] == "get_name":
                if (data["dat"] != "" and data["dat"] not in master.playerNames.values()):
                    self.playerName = data["dat"]
                    master.playerNames[self.playerId] = self.playerName
                    self.currentAction = ""
                    master.easyEvents("playerlist")
                    #self.send_message(json.dumps(
                    #    {"type": "message", "dat": "ok :)"}))
                    self.send_message(json.dumps(
                        {"type": "status", "dat": "waiting_for_beginning"}))
                else:
                    self.send_message(json.dumps(
                        {"type": "action", "dat": "get_name"}))
            elif data["type"] == "lay_card":
                master.layCard(data["dat"], self.playerId)
            elif data["type"] == "drawCard":
                master.drawCard(self.playerId)
            elif data["type"] == "select_color":
                master.selectColor(self.playerId, data["dat"])
                pass
            elif data["type"] == "getCardsStat":
                self.send_message(json.dumps(
                    {"type": "stats",
                     "dat": {
                         "type": "cardsStat",
                         "dat": master.playerDeck[self.playerId]
                     }}))
            elif data["type"] == "resend_cards_deck":
                master.addEvent(self.playerId,
                                {"type": "stats", "dat": {
                                    "type": "deck",
                                    "dat": master.playerDeck[self.playerId]
                                }})
            elif data["type"] == "withdraw2x":
                master.withdraw2x(self.playerId)
            elif data["type"] == "typeStatus":
                if data["dat"] == "player":
                    if len(master.tables) != 0:
                        self.send_message(json.dumps({
                            "type": "action",
                            "dat": "hasTable"
                        }))

                    self.currentAction = ""
                    self.playerId = random.randint(0, 9999999999999)
                    self.send_message(json.dumps(
                        {"type": "stats", "dat": {"type": "yourId", "dat": self.playerId}}))

                    if master.status == "waiting_for_players":
                        master.players.append(self.playerId)
                        master.playerClasses[self.playerId] = self

                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Mit UNO-Supreme Verbunden!"}))
                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Spieler anzahl zurzeit: "+str(len(master.players))}))

                        # select name
                        self.playerName = "["+str(self.playerId)+"]"
                        self.send_message(json.dumps(
                            {"type": "status", "dat": "waiting_for_name"}))
                        self.send_message(json.dumps(
                            {"type": "action", "dat": "get_name"}))
                        self.currentAction = "get_name"
                        master.easyEvents("playerlist")
                    else:
                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Nicht mit UNO-Supreme Verbunden!"}))
                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Zurzeit ist schon ein spiel am laufen."}))
                        self.send_message(json.dumps(
                            {"type": "status", "dat": "watcher"}))
                elif data["dat"] == "table":
                    master.tables.append(self)
                    self.send_message(json.dumps(
                        {"type": "message", "dat": "Als Tisch verbunden"}))
                    master.addEvents({
                        "type": "action",
                        "dat": "hasTable"
                    })
            else:
                self.send_message(json.dumps(
                    {"type": "message", "dat": "action "+data["type"]+" could not be used! (wanted action: "+self.currentAction+")"}))
        except:
            traceback.print_exc()

    def connected(self):
        self.currentAction = ""
        print(self.address, 'connected')

    def handle_close(self):
        global master
        master.players.remove(self.playerId)
        master.playerClasses.pop(self.playerId)
        master.playerNames.pop(self.playerId)

        for x in master.playerDeck[self.playerId]:
            master.availableCards.append(x)
        master.playerDeck.pop(self.playerId)
        master.easyEvents("disconnect")
        print(self.address, 'closed')

# start_server = websockets.serve(player, '', 8000)


def flaskServer():
    app.run("0.0.0.0", 80)


def run():
    server = WebSocketServer('0.0.0.0', 8000, Player)
    server.serve_forever()


Thread(target=run, daemon=True) .start()

threading.Thread(target=flaskServer, daemon=True).start()
while True:
    sleep(100)
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
