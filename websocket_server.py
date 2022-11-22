from math import ceil
from threading import Thread
from time import sleep
from simple_websocket_server import WebSocketServer, WebSocket
import traceback
import threading
import random
import json


cards = {"red":    {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                        "komunist"
                        ]},
         "green":  {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                        "komunist"
                        ]},
         "yellow": {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                        "komunist"
                        ]},
         "blue":   {2: ["2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                        "komunist"
                        ]},
         "": {4: ["farbwechsel4+", "farbwechsel"]}}

deck = []
for color in cards.keys():
    for numbers in cards[color].keys():
        for i in range(numbers):
            for cardType in cards[color][numbers]:
                deck.append(color + "_" + cardType)
allDeck = []

for x in range(40):
    allDeck += deck

noCardLimit = False
startCardCount = 2
startCode = "pls"


class gameMaster:
    def __init__(self):

        self.twoPlusAdder = 0

        self.scoreboard = {}

        self.events = {}

        self.status = "waiting_for_players"
        self.currentPlayer = 0
        self.direction = 1

        self.tables = []
        self.otherTables = []

        self.players = []
        self.playerNames = {}
        self.playerClasses = {}
        self.watchers = []
        self.wonPlayers = []

        self.playerDeck = {}
        self.availableCards = allDeck
        self.lyingCards = []

        self.cardCache = ""

    def sendTable(self, dat):
        for value in self.tables:
            value.send_message(json.dumps(dat))
        for value in self.otherTables:
            value.send_message(json.dumps(dat))

    def sendWatcher(self, dat):
        for x in self.watchers:
            x.send_message(json.dumps(dat))

    def setCards(self):
        self.availableCards = allDeck
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
        self.addCard(self.availableCards[choice])
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
        self.sendWatcher({
            "type": "stats",
            "dat": {
                "type": "currentPlayer",
                "dat": self.currentPlayer
            }
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

    def playerWin(self, playerId):
        print(f"player {playerId} Finished!")

        name = "["+str(playerId)+"]"
        if (playerId in self.playerNames):
            name = self.playerNames[playerId]
        self.wonPlayers.append(name)

        # message everyone that the player has won/finished
        if len(self.tables) > 0:
            self.sendTable({"type": "playerFinished",
                           "dat": name})
        else:
            self.addEvents({"type": "action", "dat":
                            {"type": "playerFinished",
                             "dat": name}})
            self.sendWatcher({"type": "action", "dat":
                              {"type": "playerFinished",
                               "dat": name}})

        # tell player he won. Automatically reconnects thus automatically removing all informations of the player in the game
        self.playerClasses[playerId].send_message(
            json.dumps({"type": "action", "dat": {"type": "won", "dat": str(len(self.wonPlayers))}}))
        self.playerClasses[playerId].handle_close(True)

    def layCard(self, card, playerId):
        if playerId != self.players[self.currentPlayer]:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du bist zurzeit nicht am zug!"}))
            return
        if len(card) == 1:
            if (card[0] in self.playerDeck[playerId]):
                c = card[0].split("_")
                lc = self.lyingCards[-1].split("_")

                # if card is the right type
                ok = True
                if c[0] == "":
                    pass
                else:
                    if c[0] != lc[0] and c[1] != lc[1]:
                        ok = False

                # then
                if ok:
                    if c[1] == "richtungswechsel":
                        self.direction = self.direction*-1
                    if c[1] == "komunist":
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(
                            playerId, {"type": "action", "dat": "removeCard", "dat2": card[0]})

                        if len(self.playerDeck[playerId]) == 0:
                            self.playerWin(playerId)

                        self.addCard(card[0])
                        self.easyEvents("cardAdd", card[0])

                        self.messageAll("Karten werden neu gemischt.....")

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
                        self.addCard(card[0])
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(
                            playerId, {"type": "action", "dat": "removeCard", "dat2": card[0]})
                        self.easyEvents("cardAdd", card[0])

                        if len(self.playerDeck[playerId]) == 0:
                            self.playerWin(playerId)

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

    def messageAll(self, msg):
        if len(self.tables) > 0:
            self.sendTable({"type": "message", "dat": msg})
        else:
            self.addEvents(
                {"type": "message", "dat": msg})
            self.sendWatcher(
                {"type": "message", "dat": msg})

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
            self.messageAll(f"mischen... {s+1}/5")

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
            self.addCard(color+self.cardCache)
            self.playerDeck[playerId].remove(self.cardCache)
            self.addEvent(
                playerId, {"type": "action", "dat": "removeCard", "dat2": self.cardCache})
            self.easyEvents("cardAdd", color+self.cardCache)

            if len(self.playerDeck[playerId]) == 0:
                self.playerWin(playerId)

            self.cardCache = ""
            self.nextPlayer()
        else:
            self.playerClasses[playerId].send_message(json.dumps(
                {"type": "message", "dat": "Du bist zurzeit nicht am zug!"}))

    def nextPlayer(self, count=1):
        if len(self.players) <= 1:
            self.gameEnd()
            return
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
            self.sendWatcher({
                "type": "stats",
                "dat": {
                    "type": "players",
                    "dat": {
                        "id": self.players,
                        "name": self.playerNames
                    }}})
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
            self.sendWatcher({"type": "stats", "dat": {
                "type": "lyingCards",
                "dat": self.lyingCards
            }})

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})

            self.updateTable()
        if etype == "cardAdd":
            self.addEvents({"type": "action", "dat": {
                "type": "lyingCards",
                "dat": dat
            }})
            self.sendTable({
                "type": "lyingCardsAdd",
                "dat": dat
            })
            self.sendWatcher({
                "type": "action",
                "dat": {
                    "type": "lyingCards",
                    "dat": dat
                }})

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})
            self.updateTable()
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
            self.sendWatcher({"type": "stats", "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})

    def updateTable(self):
        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        self.sendTable({
            "type": "playerCardCount",
            "dat": counts
        })
        self.sendWatcher({
            "type": "stats",
            "dat": {
                "type": "playerCardCount",
                "dat": counts
            }})

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
        if len(self.playerDeck[playerId]) < 25 or noCardLimit:
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

            # check if player has any card to lay down
            has = False
            maybeCard = None
            for card in self.playerDeck[playerId]:
                c = card.split("_")
                lc = self.lyingCards[-1].split("_")
                ok = True
                if c[0] == "":
                    pass
                else:
                    if c[0] != lc[0] and c[1] != lc[1]:
                        ok = False
                if ok:
                    has = True
                    maybeCard = card
            if not has:
                self.playerClasses[playerId].send_message(json.dumps(
                    {"type": "message", "dat": "Da du keine Karten legen kannst wurde der nächste Spieler aufgerufen."}))
                self.nextPlayer()
            else:
                pass

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

    def addCard(self, dat):
        self.lyingCards.append(dat)

        # remove old cards
        if len(self.lyingCards) > 10:
            self.addEvents({"type": "action", "dat": "removeLastLyingCard"})
            self.sendWatcher({"type": "action", "dat": "removeLastLyingCard"})
            self.sendTable({"type": "removeLastLyingCard"})

            card = self.lyingCards[0]
            if card.split("_")[1] in ["farbwechsel", "farbwechsel4+"]:
                card = "_"+card.split("_")[1]
            self.availableCards.append(card)
            self.lyingCards = self.lyingCards[1:]

    def gameEnd(self):
        threading.Thread(target=self.threadedEnd, daemon=True).start()

    def threadedEnd(self):
        sleep(1)
        self.messageAll("Spiel vorbei. Nur noch ein Spieler übrig!")
        self.messageAll("Ein neues Spiel wird gestarted.")
        self.status = "waiting_for_players"
        sleep(3)
        for x in self.watchers:
            # x.send_message(json.dumps(
            #    {"type": "message", "dat": "Neues Spiel!"}))
            x.send_message(json.dumps({"type": "action", "dat": "reconnect"}))

        for y in self.players:
            x = self.playerClasses[y]
            # x.send_message(json.dumps(
            #    {"type": "message", "dat": "Neues Spiel!"}))
            x.send_message(json.dumps({"type": "action", "dat": "reconnect"}))

        # for x in self.tables:
        #    x.send_message(json.dumps(
        #        {"type": "message", "dat": "Neues Spiel!"}))
        # for x in self.otherTables:
        #    x.send_message(json.dumps(
        #        {"type": "message", "dat": "Neues Spiel!"}))

        self.wonPlayers = []

    def sendTableDat(self, table):
        #table.send_message(json.dumps({"type": "", "dat": ""}))
        table.send_message(json.dumps({"type": "players",
                                       "dat": {
                                           "id": self.players,
                                           "name": self.playerNames
                                       }}))
        table.send_message(json.dumps({
            "type": "lyingCards",
            "dat": self.lyingCards
        }))

        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        table.send_message(json.dumps({
            "type": "playerCardCount",
            "dat": counts
        }))
        table.send_message(json.dumps({
            "type": "currentPlayer",
            "dat": self.currentPlayer
        }))

        # won players
        for x in self.wonPlayers:
            table.send_message(json.dumps({"type": "playerFinished",
                                           "dat": x}))

    def sendWatcherDat(self, watcher):
        # players
        watcher.send_message(json.dumps({
            "type": "stats",
            "dat": {
                "type": "players",
                "dat": {
                    "id": self.players,
                    "name": self.playerNames
                }}}))

        # card counts
        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        watcher.send_message(json.dumps({"type": "stats", "dat": {
            "type": "playerCardCount",
            "dat": counts
        }}))
        watcher.send_message(json.dumps(
            {"type": "stats", "dat": {
                "type": "lyingCards",
                "dat": self.lyingCards
            }}))
        watcher.send_message(json.dumps({"type": "stats", "dat": {
            "type": "currentPlayer",
            "dat": self.currentPlayer
        }}))

        # won players
        for x in self.wonPlayers:
            watcher.send_message(json.dumps({"type": "action", "dat":
                                             {"type": "playerFinished",
                                              "dat": x}}))


master = gameMaster()


def genPlayerId(inp):
    global master
    inp = str(inp)

    if (inp.startswith("{")):
        inp = master.players[int(inp[1:-1])]

    return int(inp)


def consoleEval(dat):
    global master
    command = dat.split(" ")
    try:
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
            playerId = genPlayerId(command[2])
            if playerId not in master.playerDeck.keys():
                return "player doesn't exist"
            master.playerDeck[playerId].append(command[1])
            master.addEvent(playerId,
                            {"type": "action", "dat": {
                                "type": "addCard",
                                "dat": command[1]

                            }})
            master.easyEvents("playerCardCount")
            return "ok!"
        elif command[0] == "get":
            playerId = genPlayerId(command[1])
            if playerId in master.playerDeck:
                cards = ", ".join(master.playerDeck[playerId])
            else:
                cards = "player does not exist!"
            return cards
        elif command[0] == "setCurrentPlayer":
            playerId = genPlayerId(command[1])
            master.currentPlayer = playerId
            return "set to " + str(master.currentPlayer)
        elif command[0] == "getCurrentPlayer":
            return "CurrentPlayer: " + str(master.currentPlayer)
        elif command[0] == "win":
            playerId = genPlayerId(command[1])
            master.easyEvents("playerCardCount")
            master.addEvent(playerId, {"type": "stats",
                                       "dat": {
                                           "type": "deck",
                                           "dat": []
                                       }})

            master.playerWin(playerId)
            master.nextPlayer()

            return f"player {playerId} has now finished!"
        elif command[0] == "start":
            master.start()
            return "started"
        elif command[0] == "nextPlayer":
            master.nextPlayer()
            return "ok"
    except Exception as e:
        return traceback.format_exc()
        # return "error: " + str(e)
    return "command did not return! Does it realy exist?"


class Player(WebSocket):
    def handle(self):
        try:
            global master
            data = json.loads(self.data)
            # print(self.data)

            if data["type"] == "start_game":
                if data["dat"] == startCode:
                    master.start()
                else:
                    self.send_message(json.dumps(
                        {"type": "message", "dat": "Error: Wrong start code"}))
            elif data["type"] == "allCards":
                self.send_message(json.dumps(
                    {"type": "stats", "dat": {"type": "allCards", "dat": deck}}))

            elif self.currentAction == "get_name" and data["type"] == "get_name":
                if (data["dat"] != "" and data["dat"] not in master.playerNames.values()):
                    self.playerName = data["dat"]
                    master.playerNames[self.playerId] = self.playerName
                    self.currentAction = ""
                    master.easyEvents("playerlist")
                    # self.send_message(json.dumps(
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
                    secondTime = False
                    if "dat2" in data:
                        if data["dat2"] == "secondTime":
                            secondTime = True

                    self.type = "player"
                    if len(master.tables) != 0:
                        self.send_message(json.dumps({
                            "type": "action",
                            "dat": "hasTable"
                        }))

                    self.currentAction = ""
                    r = 0  # random.randint(0, 9999999999999)
                    while r in master.players:
                        r = r+1  # random.randint(0, 9999999999999)
                    self.playerId = r

                    self.send_message(json.dumps(
                        {"type": "stats", "dat": {"type": "yourId", "dat": self.playerId}}))

                    if master.status == "waiting_for_players":
                        master.players.append(self.playerId)
                        master.playerClasses[self.playerId] = self

                        if not secondTime:
                            self.send_message(json.dumps(
                                {"type": "message", "dat": "Mit UNU-Supreme Verbunden!"}))
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
                            {"type": "message", "dat": "Du bist als zuschauer verbunden"}))
                        self.send_message(json.dumps(
                            {"type": "status", "dat": "watcher"}))
                        master.watchers.append(self)
                        master.sendWatcherDat(self)
                elif data["dat"] == "watcher":
                    self.type = "watcher"
                    if len(master.tables) != 0:
                        self.send_message(json.dumps({
                            "type": "action",
                            "dat": "hasTable"
                        }))
                    self.send_message(json.dumps(
                        {"type": "message", "dat": "Du bist als zuschauer verbunden"}))
                    self.send_message(json.dumps(
                        {"type": "status", "dat": "watcher"}))
                    master.watchers.append(self)
                    master.sendWatcherDat(self)
                elif data["dat"] == "table":
                    self.type = "table"
                    self.send_message(json.dumps(
                        {"type": "message", "dat": "Als Tisch verbunden"}))
                    master.sendTableDat(self)
                    if (data["dat2"] == "normal"):
                        master.tables.append(self)
                        master.addEvents({
                            "type": "action",
                            "dat": "hasTable"
                        })
                        master.sendWatcher({
                            "type": "action",
                            "dat": "hasTable"
                        })
                    else:
                        master.otherTables.append(self)
                elif data["dat"] == "console":
                    self.type = "console"
                    self.send_message("connected!")
            elif self.type == "console" and data["type"] == "eval":
                self.send_message(consoleEval(data["dat"]))
            else:
                self.send_message(json.dumps(
                    {"type": "message", "dat": "action "+data["type"]+" could not be used! (wanted action: "+self.currentAction+")"}))
        except:
            traceback.print_exc()

    def connected(self):
        self.type = ""
        self.currentAction = ""
        print(self.address, 'connected')

    def handle_close(self, notReal=False):
        try:
            global master
            if self.type == "player":
                if self.playerId in master.players:
                    master.players.remove(self.playerId)

                if self.playerId in master.playerClasses.keys():
                    master.playerClasses.pop(self.playerId)

                if self.playerId in master.playerNames.keys():
                    master.playerNames.pop(self.playerId)

                if self.playerId in master.playerDeck.keys():
                    for x in master.playerDeck[self.playerId]:
                        master.availableCards.append(x)
                    master.playerDeck.pop(self.playerId)

                # check if currentPlayer id needs to change, because the player has disconnected
                if master.status == "playing" and master.currentPlayer >= len(master.players):
                    print("toBig currentPlayer")
                    master.currentPlayer = len(master.players)-1
                    if master.currentPlayer < 0:
                        master.currentPlayer = 0
                        master.gameEnd()
                        print("no Players anymore!")
                    else:
                        master.askPlayer()
                if master.status == "playing" and len(master.players) <= 1:
                    master.gameEnd()
                    return
            elif self.type == "table":
                if self in master.tables:
                    master.tables.remove(self)
                if self in master.otherTables:
                    master.otherTables.remove(self)
            elif self.type == "watcher":
                master.watchers.remove(self)
            master.easyEvents("disconnect")
            if not notReal:
                print(self.address, 'closed')
        except:
            if not notReal:
                print(self.address, 'closed')
            traceback.print_exc()
# start_server = websockets.serve(player, '', 8000)


def startWebsocket():
    server = WebSocketServer('0.0.0.0', 8000, Player)
    server.serve_forever()


def run():
    Thread(target=startWebsocket, daemon=True).start()


if __name__ == "__main__":
    run()
    while True:
        sleep(100)
