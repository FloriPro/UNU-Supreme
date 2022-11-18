import os
import json
from simple_websocket.ws import ConnectionClosed
from math import ceil
from random import randint
import random
import threading
from time import sleep
import traceback
from flask import Flask, render_template, request
from flask_sock import Sock
from threading import Timer, Thread
import logging


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
sock = Sock(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.config.from_object(__name__)
if os.path.isdir("/home/runner") == True:
    # on replit
    serverHost = "wss://${location.hostname}/sock"  # ${location.hostname}
    startCode = os.environ["startKey"]
    loginKey = os.environ["loginKey"]
else:
    # not on replit
    serverHost = "ws://${location.hostname}/sock"  # ${location.hostname}
    startCode = "pls"
    loginKey = "pls"


cards = {
    "red": {
        2: [
            "2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5",
            "6", "7", "8", "9", "komunist"
        ]
    },
    "green": {
        2: [
            "2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5",
            "6", "7", "8", "9", "komunist"
        ]
    },
    "yellow": {
        2: [
            "2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5",
            "6", "7", "8", "9", "komunist"
        ]
    },
    "blue": {
        2: [
            "2+", "aussetzen", "richtungswechsel", "1", "2", "3", "4", "5",
            "6", "7", "8", "9", "komunist"
        ]
    },
    "": {
        4: ["farbwechsel4+", "farbwechsel"]
    }
}

deck = []
for color in cards.keys():
    for numbers in cards[color].keys():
        for i in range(numbers):
            for cardType in cards[color][numbers]:
                deck.append(color + "_" + cardType)
allDeck = []

for x in range(40):
    allDeck += deck

noCardLimit = True
startCardCount = 2


class gameMaster:
    def __init__(self):

        self.twoPlusAdder = 0

        self.scoreboard = {}

        self.events = {}

        self.specialAction = ""
        self.nextPlayerEvents = []

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
                choice = random.randint(0, len(self.availableCards) - 1)
                self.playerDeck[playerId].append(self.availableCards[choice])
                self.availableCards.pop(choice)
                iteration += 1

            self.addEvent(
                playerId, {
                    "type": "stats",
                    "dat": {
                        "type": "deck",
                        "dat": self.playerDeck[playerId]
                    }
                })
        self.status = "playing"
        self.addEvents({"type": "status", "dat": "playing"})

    def start(self):
        self.setCards()
        choice = random.randint(0, len(self.availableCards) - 1)
        self.lyingCards = []
        self.addCard(self.availableCards[choice])
        self.availableCards.pop(choice)

        self.addEvents({"type": "action", "dat": "startGame"})

        self.easyEvents("cardRedo")
        self.askPlayer()

    def playerHas2x(self, playerId):
        for x in self.playerDeck[playerId]:
            if x.endswith("2+"):
                return True

    def askPlayer(self):
        playerId = self.players[self.currentPlayer]
        self.addEvents({
            "type": "stats",
            "dat": {
                "type": "currentPlayer",
                "dat": self.currentPlayer
            }
        })
        self.sendTable({"type": "currentPlayer", "dat": self.currentPlayer})
        self.sendWatcher({
            "type": "stats",
            "dat": {
                "type": "currentPlayer",
                "dat": self.currentPlayer
            }
        })
        # run next Player events
        if self.nextPlayerEvents != [] and self.specialAction == "":
            # doing 4+ and 2+
            for x in self.nextPlayerEvents:
                if x == "4+":
                    self.drawCard(playerId)
                    self.drawCard(playerId)
                    self.drawCard(playerId)
                    self.drawCard(playerId)
                    self.playerClasses[playerId].send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Du Hast 4 Karten gezogen"
                        }))
                if x == "2+":
                    self.drawCard(playerId)
                    self.drawCard(playerId)
                    self.playerClasses[playerId].send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Du Hast 2 Karten gezogen"
                        }))

            # doing Aussetzen
            np = 0
            for x in self.nextPlayerEvents:
                if x == "aussetzen":
                    np += 1
            self.nextPlayerEvents = []
            if np != 0:
                print("next player")
                self.nextPlayer(np)
                return

            # while self.nextPlayerEvents != []:
            #    if self.nextPlayerEvents[0] == "4+":
            #        self.drawCard(playerId)
            #        self.drawCard(playerId)
            #        self.drawCard(playerId)
            #        self.drawCard(playerId)
            #        self.playerClasses[playerId].send_message(
            #            json.dumps({
            #                "type": "message",
            #                "dat": "Du Hast 4 Karten gezogen"
            #            }))
            #    elif self.nextPlayerEvents[0] == "2+":
            #        self.twoPlusAdder += 2
            #        if self.playerHas2x(playerId):
            #            self.addEvent(playerId, {
            #                "type": "status",
            #                "dat": "2+_Desicion"
            #            })
            #            self.addEvent(
            #                playerId, {
            #                    "type": "action",
            #                    "dat": "slect2+Card",
            #                    "dat2": self.twoPlusAdder
            #                })
            #            self.nextPlayerEvents = self.nextPlayerEvents[1:]
            #            return
            #        else:
            #            for x in range(self.twoPlusAdder):
            #                self.drawCard(playerId)
            #            self.playerClasses[playerId].send_message(
            #                json.dumps({
            #                    "type":
            #                    "message",
            #                    "dat":
            #                    "Du Hast " + str(self.twoPlusAdder) +
            #                    " Karten gezogen"
            #                }))
            #            self.twoPlusAdder = 0
            #    elif self.nextPlayerEvents[0] == "aussetzen":
            #        print("aussetzen")
            #        self.nextPlayerEvents = self.nextPlayerEvents[1:]
            #        self.nextPlayer()
            #        return
            #    else:
            #        print("error: unknown playerEvent   : " +
            #              self.nextPlayerEvents[0])
            #    self.nextPlayerEvents = self.nextPlayerEvents[1:]
        # special cards appied to the current player (after the next player is allready selected so actually to the next player)
        if self.lyingCards[-1].endswith("4+"):
            if self.specialAction.startswith("winAussetzen"):
                self.nextPlayerEvents.append("4+")
            else:
                self.drawCard(playerId)
                self.drawCard(playerId)
                self.drawCard(playerId)
                self.drawCard(playerId)
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Du Hast 4 Karten gezogen"
                    }))
        if self.lyingCards[-1].endswith("2+"):
            if self.specialAction.startswith("winAussetzen"):
                self.nextPlayerEvents.append("2+")
            else:
                self.twoPlusAdder += 2
                if self.playerHas2x(playerId):
                    self.addEvent(playerId, {
                        "type": "status",
                        "dat": "2+_Desicion"
                    })
                    self.addEvent(
                        playerId, {
                            "type": "action",
                            "dat": "slect2+Card",
                            "dat2": self.twoPlusAdder
                        })
                else:
                    for x in range(self.twoPlusAdder):
                        self.drawCard(playerId)
                    self.playerClasses[playerId].send_message(
                        json.dumps({
                            "type":
                            "message",
                            "dat":
                            "Du Hast " + str(self.twoPlusAdder) +
                            " Karten gezogen"
                        }))
                    self.twoPlusAdder = 0
                    self.addEvent(
                        playerId, {"type": "status", "dat": "slectCard"})
                    self.addEvent(
                        playerId, {"type": "action", "dat": "slectCard"})
        else:
            self.twoPlusAdder = 0
            self.addEvent(playerId, {"type": "status", "dat": "slectCard"})
            self.addEvent(playerId, {"type": "action", "dat": "slectCard"})

    def withdraw2x(self, playerId):
        for x in range(self.twoPlusAdder):
            self.drawCard(playerId)
        self.playerClasses[playerId].send_message(
            json.dumps({
                "type":
                "message",
                "dat":
                "Du Hast " + str(self.twoPlusAdder) + " Karten gezogen"
            }))
        self.twoPlusAdder = 0
        # if self.nextPlayerEvents == []:
        self.addEvent(playerId, {"type": "status", "dat": "slectCard"})
        self.addEvent(playerId, {"type": "action", "dat": "slectCard"})

    def playerWin(self, playerId):
        print(f"player {playerId} Finished!")

        name = "[" + str(playerId) + "]"
        if (playerId in self.playerNames):
            name = self.playerNames[playerId]
        self.wonPlayers.append(name)

        # message everyone that the player has won/finished
        if len(self.tables) > 0:
            self.sendTable({"type": "playerFinished", "dat": name})
        else:
            self.addEvents({
                "type": "action",
                "dat": {
                    "type": "playerFinished",
                    "dat": name
                }
            })
            self.sendWatcher({
                "type": "action",
                "dat": {
                    "type": "playerFinished",
                    "dat": name
                }
            })

        # tell player he won. Automatically reconnects thus automatically removing all informations of the player in the game
        self.playerClasses[playerId].send_message(
            json.dumps({
                "type": "action",
                "dat": {
                    "type": "won",
                    "dat": str(len(self.wonPlayers))
                }
            }))
        self.playerClasses[playerId].handle_close(True)

    def isThisCombo(self, cards, comboCards, playerId, specificColour=False, topCardColor="green"):
        if len(comboCards) != len(cards):
            return False
        for x in range(len(cards)):
            if specificColour:
                if cards[x] not in comboCards:
                    return False
                comboCards.remove(cards[x])
            else:
                if cards[x].split("_")[1] not in comboCards:
                    return False
                # remove one crad that has the same type ignoring color
                i = 0
                while True:
                    if comboCards[i] == cards[x].split("_")[1]:
                        comboCards.remove(comboCards[i])
                        break
                    i += 1

        if not specificColour and cards[0].split("_")[0] != self.lyingCards[-1].split("_")[0]:
            self.addEvent(
                playerId, {"type": "message", "dat": "du darfst diese Karte nicht legen!"})
            return False

        coulourCard = ""
        if specificColour:
            for x in cards:
                if x.split("_")[0] == topCardColor:
                    coulourCard = x
        for x in cards:
            if specificColour:
                if x != coulourCard:
                    self.easyEvents("cardAdd", x)
                    self.addCard(x)
                    self.playerDeck[playerId].remove(x)
            else:
                i = 0
                while True:
                    if self.playerDeck[playerId][i].split("_")[0] == x.split("_")[0]:
                        self.easyEvents(
                            "cardAdd", self.playerDeck[playerId][i])
                        self.addCard(self.playerDeck[playerId][i])
                        self.playerDeck[playerId].remove(
                            self.playerDeck[playerId][i])
                        break
                    i += 1
                pass
            sleep(0.1)
        if specificColour:
            self.easyEvents("cardAdd", coulourCard)
            self.addCard(coulourCard)
            self.playerDeck[playerId].remove(coulourCard)
        return True

    def layCard(self, card, playerId, topCardColor=None):
        if playerId != self.players[self.currentPlayer]:
            self.playerClasses[playerId].send_message(
                json.dumps({
                    "type": "message",
                    "dat": "Du bist zurzeit nicht am zug!"
                }))
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
                        self.direction = self.direction * -1
                    if c[1] == "komunist":
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(playerId, {
                            "type": "action",
                            "dat": "removeCard",
                            "dat2": card[0]
                        })

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
                        self.playerClasses[playerId].send_message(
                            json.dumps({
                                "type": "status",
                                "dat": "waiting_for_color"
                            }))
                        self.playerClasses[playerId].send_message(
                            json.dumps({
                                "type": "action",
                                "dat": "select_color"
                            }))
                    else:
                        self.addCard(card[0])
                        self.playerDeck[playerId].remove(card[0])
                        self.addEvent(playerId, {
                            "type": "action",
                            "dat": "removeCard",
                            "dat2": card[0]
                        })
                        self.easyEvents("cardAdd", card[0])

                        if len(self.playerDeck[playerId]) == 0:
                            self.playerWin(playerId)

                        if self.specialAction.startswith("winAussetzen"):
                            if card[0].endswith("_aussetzen"):
                                self.nextPlayerEvents.append("aussetzen")
                            self.nextPlayer()
                            return

                        if (card[0].endswith("_aussetzen")):
                            self.nextPlayer(2)

                        elif (card[0].endswith("_richtungswechsel")):
                            self.askPlayer()
                        else:
                            self.nextPlayer()

                else:
                    self.playerClasses[playerId].send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Du darfst diese Karte nicht legen!"
                        }))
            else:
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Du hast diese Karte garnicht"
                    }))
                self.addEvent(
                    playerId, {
                        "type": "stats",
                        "dat": {
                            "type": "deck",
                            "dat": self.playerDeck[playerId]
                        }
                    })
        else:
            # check if has card
            for x in card:
                if x not in self.playerDeck[playerId]:
                    self.playerClasses[playerId].send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Fehler! Du besitzt mindestens eine dieser Karten nicht!"
                        }))
                    return

            if self.isThisCombo(card, ["yellow_richtungswechsel", "blue_richtungswechsel", "green_richtungswechsel", "red_richtungswechsel"], playerId, True, topCardColor):
                if len(self.playerDeck[playerId]) == 0:
                    self.playerWin(playerId)
                    return
                self.playerClasses[playerId].currentAction = "specificSelect_winRichtungswechsel"

                allPlayers = {}
                for x in self.players:
                    if x != playerId:
                        allPlayers[self.playerNames[x]] = x
                if len(allPlayers) == 0:
                    self.playerWin(playerId)
                    return
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "action",
                        "dat": {
                            "type": "specificSelect",
                            "dat": {
                                "title": "Mit welchem spieler willst du tauschen?",
                                "options": allPlayers,
                                "type": "text"
                            }
                        }
                    })
                )
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Karten-combo gelegt"
                    }))
            elif (not self.specialAction.startswith("winAussetzen")) and self.isThisCombo(card, ["yellow_aussetzen", "blue_aussetzen", "green_aussetzen", "red_aussetzen"], playerId, True, topCardColor):
                if len(self.playerDeck[playerId]) == 0:
                    self.playerWin(playerId)
                    return
                self.specialAction = "winAussetzen_4"
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Karten-combo gelegt du kannst nun 4 mal Karten hintereinander legen"
                    }))
                self.nextPlayer()
            elif self.specialAction.startswith("winAussetzen"):
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Windows-aussetzen-combo kann nicht addiert/kombiniert werden"
                    }))
            elif self.isThisCombo(card, ["9", "6"], playerId, False):
                if len(self.playerDeck[playerId]) == 0:
                    self.playerWin(playerId)
                    return
                self.playerClasses[playerId].currentAction = "specificSelect_96"
                self.playerClasses[playerId].i = 4
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "action",
                        "dat": {
                            "type": "specificSelect",
                            "dat": {
                                "title": f"Welche karte möchtest du haben (noch 4 versuch(e))",
                                "options": "_deck",
                                "type": "card",
                                "cancel": True
                            }
                        }
                    })
                )
            elif self.isThisCombo(card, ["yellow_komunist", "blue_komunist", "green_komunist", "red_komunist"], playerId, True, topCardColor):
                if len(self.playerDeck[playerId]) == 0:
                    self.playerWin(playerId)
                    self.komunist()
                    return
                self.komunist(True, playerId)
            else:
                print(card)
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Karten-combo zurzeit nicht verfügbar!"
                    }))

            master.addEvent(
                playerId, {
                    "type": "stats",
                    "dat": {
                        "type": "deck",
                        "dat": master.playerDeck[playerId]
                    }
                })

    def messageAll(self, msg):
        if len(self.tables) > 0:
            self.sendTable({"type": "message", "dat": msg})
        else:
            self.addEvents({"type": "message", "dat": msg})
            self.sendWatcher({"type": "message", "dat": msg})

    def komunist(self, windows=False, windowsPlayer=-1):
        toMix = []
        for key, value in self.playerDeck.items():
            self.playerDeck[key] = []
            toMix += value
            sleep(0.2)
            self.addEvent(key, {
                "type": "stats",
                "dat": {
                    "type": "deck",
                    "dat": []
                }
            })
            self.easyEvents("playerCardCount")

        for s in range(5):
            sleep(0.2)
            self.messageAll(f"mischen... {s+1}/5")

        cards = ceil(len(toMix) / len(self.players))

        if windows == False:
            for x in range(cards):
                for player in self.players:
                    if len(toMix) != 0:
                        choice = random.randint(0, len(toMix) - 1)
                        self.playerDeck[player].append(toMix[choice])
                        toMix.pop(choice)
                    else:
                        choice = random.randint(
                            0, len(self.availableCards) - 1)
                        self.playerDeck[player].append(
                            self.availableCards[choice])
                        self.availableCards.pop(choice)
        else:
            toggle = True
            for x in range(cards):
                for player in self.players:
                    if windowsPlayer != player or toggle:
                        if len(toMix) != 0:
                            choice = random.randint(0, len(toMix) - 1)
                            self.playerDeck[player].append(toMix[choice])
                            toMix.pop(choice)
                        else:
                            choice = random.randint(
                                0, len(self.availableCards) - 1)
                            self.playerDeck[player].append(
                                self.availableCards[choice])
                            self.availableCards.pop(choice)
                    toggle = not toggle
        # update players of their deck
        for player in self.players:
            self.addEvent(
                player, {
                    "type": "stats",
                    "dat": {
                        "type": "deck",
                        "dat": self.playerDeck[player]
                    }
                })
        self.easyEvents("playerCardCount")
        self.nextPlayer()

    def selectColor(self, playerId, color):
        if self.players[self.currentPlayer] == playerId:
            self.addCard(color + self.cardCache)
            self.playerDeck[playerId].remove(self.cardCache)
            self.addEvent(playerId, {
                "type": "action",
                "dat": "removeCard",
                "dat2": self.cardCache
            })
            self.easyEvents("cardAdd", color + self.cardCache)

            if len(self.playerDeck[playerId]) == 0:
                self.playerWin(playerId)

            self.cardCache = ""
            self.nextPlayer()
        else:
            self.playerClasses[playerId].send_message(
                json.dumps({
                    "type": "message",
                    "dat": "Du bist zurzeit nicht am zug!"
                }))

    def nextPlayerWithoutAsking(self):
        self.currentPlayer += self.direction
        if self.currentPlayer >= len(self.players):
            self.currentPlayer = 0
        if self.currentPlayer < 0:
            self.currentPlayer = len(self.players) - 1

    def nextPlayer(self, count=1):
        if len(self.players) <= 1:
            self.gameEnd()
            return
        self.addEvent(self.players[self.currentPlayer], {
            "type": "status",
            "dat": "playing"
        })
        if self.specialAction.startswith("winAussetzen"):
            if int(self.specialAction.split("_")[1]) <= 0:
                self.specialAction = ""
                self.nextPlayer()
                return
            self.specialAction = self.specialAction.split(
                "_")[0] + "_" + str(int(self.specialAction.split("_")[1])-1)
        else:
            for x in range(count):
                self.nextPlayerWithoutAsking()
        self.askPlayer()

    def easyEvents(self, etype, dat=None):
        if etype == "playerlist":
            self.addEvents({
                "type": "stats",
                "dat": {
                    "type": "players",
                    "dat": {
                        "id": self.players,
                        "name": self.playerNames
                    }
                }
            })
            self.sendTable({
                "type": "players",
                "dat": {
                    "id": self.players,
                    "name": self.playerNames
                }
            })
            self.sendWatcher({
                "type": "stats",
                "dat": {
                    "type": "players",
                    "dat": {
                        "id": self.players,
                        "name": self.playerNames
                    }
                }
            })
        if etype == "cardList":
            for playerId in self.players:
                self.addEvent(
                    playerId, {
                        "type": "stats",
                        "dat": {
                            "type": "deck",
                            "dat": self.playerDeck[playerId]
                        }
                    })
        if etype == "disconnect":
            self.easyEvents("playerlist")
        if etype == "cardRedo":
            self.addEvents({
                "type": "stats",
                "dat": {
                    "type": "lyingCards",
                    "dat": self.lyingCards
                }
            })
            self.sendTable({"type": "lyingCards", "dat": self.lyingCards})
            self.sendWatcher({
                "type": "stats",
                "dat": {
                    "type": "lyingCards",
                    "dat": self.lyingCards
                }
            })

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({
                "type": "stats",
                "dat": {
                    "type": "playerCardCount",
                    "dat": counts
                }
            })

            self.updateTable()
        if etype == "cardAdd":
            self.addEvents({
                "type": "action",
                "dat": {
                    "type": "lyingCards",
                    "dat": dat
                }
            })
            self.sendTable({"type": "lyingCardsAdd", "dat": dat})
            self.sendWatcher({
                "type": "action",
                "dat": {
                    "type": "lyingCards",
                    "dat": dat
                }
            })

            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({
                "type": "stats",
                "dat": {
                    "type": "playerCardCount",
                    "dat": counts
                }
            })
            self.updateTable()
        if etype == "playerCardCount":
            counts = {}
            for x in self.playerDeck.keys():
                counts[x] = len(self.playerDeck[x])
            self.addEvents({
                "type": "stats",
                "dat": {
                    "type": "playerCardCount",
                    "dat": counts
                }
            })
            self.sendTable({"type": "playerCardCount", "dat": counts})
            self.sendWatcher({
                "type": "stats",
                "dat": {
                    "type": "playerCardCount",
                    "dat": counts
                }
            })

    def updateTable(self):
        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        self.sendTable({"type": "playerCardCount", "dat": counts})
        self.sendWatcher({
            "type": "stats",
            "dat": {
                "type": "playerCardCount",
                "dat": counts
            }
        })

    def addEvents(self, dat):
        for x in self.players:
            if not x in self.events:
                self.events[x] = []
            self.events[x].append(dat)

        self.runEvents()

    def drawCard(self, playerId):
        if playerId != self.players[self.currentPlayer]:
            self.playerClasses[playerId].send_message(
                json.dumps({
                    "type": "message",
                    "dat": "Du bist zurzeit nicht am zug!"
                }))
            return
        if len(self.playerDeck[playerId]) < 25 or noCardLimit:
            choice = random.randint(0, len(self.availableCards) - 1)
            self.playerDeck[playerId].append(self.availableCards[choice])
            self.addEvent(
                playerId, {
                    "type": "action",
                    "dat": {
                        "type": "addCard",
                        "dat": self.availableCards[choice]
                    }
                })
            self.availableCards.pop(choice)
            self.easyEvents("playerCardCount")
        else:
            self.playerClasses[playerId].send_message(
                json.dumps({
                    "type": "message",
                    "dat": "Du hast schon zu viele Karten"
                }))

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
                self.playerClasses[playerId].send_message(
                    json.dumps({
                        "type": "message",
                        "dat": "Da du keine Karten legen kannst wurde der nächste Spieler aufgerufen."
                    }))
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
                card = "_" + card.split("_")[1]
            self.availableCards.append(card)
            self.lyingCards = self.lyingCards[1:]

    def gameEnd(self):
        threading.Thread(target=self.threadedEnd, daemon=True).start()

    def threadedEnd(self):
        if self.status == "gameEnd":
            return
        self.status = "gameEnd"
        sleep(1)
        self.messageAll("Spiel vorbei. Nur noch ein Spieler übrig!")
        self.messageAll("Ein neues Spiel wird gestarted.")
        sleep(3)
        self.status = "waiting_for_players"

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
        table.send_message(
            json.dumps({
                "type": "players",
                "dat": {
                    "id": self.players,
                    "name": self.playerNames
                }
            }))
        table.send_message(
            json.dumps({
                "type": "lyingCards",
                "dat": self.lyingCards
            }))

        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        table.send_message(
            json.dumps({
                "type": "playerCardCount",
                "dat": counts
            }))
        table.send_message(
            json.dumps({
                "type": "currentPlayer",
                "dat": self.currentPlayer
            }))

        # won players
        for x in self.wonPlayers:
            table.send_message(json.dumps({
                "type": "playerFinished",
                "dat": x
            }))

    def sendWatcherDat(self, watcher):
        # players
        watcher.send_message(
            json.dumps({
                "type": "stats",
                "dat": {
                    "type": "players",
                    "dat": {
                        "id": self.players,
                        "name": self.playerNames
                    }
                }
            }))

        # card counts
        counts = {}
        for x in self.playerDeck.keys():
            counts[x] = len(self.playerDeck[x])
        watcher.send_message(
            json.dumps({
                "type": "stats",
                "dat": {
                    "type": "playerCardCount",
                    "dat": counts
                }
            }))
        watcher.send_message(
            json.dumps({
                "type": "stats",
                "dat": {
                    "type": "lyingCards",
                    "dat": self.lyingCards
                }
            }))
        watcher.send_message(
            json.dumps({
                "type": "stats",
                "dat": {
                    "type": "currentPlayer",
                    "dat": self.currentPlayer
                }
            }))

        # won players
        for x in self.wonPlayers:
            watcher.send_message(
                json.dumps({
                    "type": "action",
                    "dat": {
                        "type": "playerFinished",
                        "dat": x
                    }
                }))


master = gameMaster()


class Player:
    def __init__(self, client, idet) -> None:
        self.type = ""
        self.currentAction = ""
        self.client = client
        self.idet = idet
        self.i = -1

    def send_message(self, dat):
        try:
            if self.idet in self.client.clients:
                if self.client.clients[self.idet].connected:
                    self.client.clients[self.idet].send(dat)
            else:
                self.client.close_connection(self.idet)
        except ConnectionClosed:
            self.client.close_connection(self.idet)

    def handle(self, data):
        try:
            global master
            data = json.loads(data)
            # print(self.data)

            if data["type"] == "start_game":
                if data["dat"] == startCode:
                    master.start()
                else:
                    self.send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Error: Wrong start code"
                        }))
            elif data["type"] == "allCards":
                self.send_message(
                    json.dumps({
                        "type": "stats",
                        "dat": {
                            "type": "allCards",
                            "dat": deck
                        }
                    }))

            elif self.currentAction.startswith("specificSelect_") and data["type"] == "selectResponse":
                if self.currentAction == "specificSelect_winRichtungswechsel":
                    if data["dat"] in master.players:
                        p = master.playerDeck[self.playerId]
                        master.playerDeck[self.playerId] = master.playerDeck[data["dat"]]
                        master.playerDeck[data["dat"]] = p

                        master.easyEvents("playerCardCount")
                        master.addEvent(
                            data["dat"], {
                                "type": "stats",
                                "dat": {
                                    "type": "deck",
                                    "dat": master.playerDeck[data["dat"]]
                                }
                            })
                        master.addEvent(
                            self.playerId, {
                                "type": "stats",
                                "dat": {
                                    "type": "deck",
                                    "dat": master.playerDeck[self.playerId]
                                }
                            })

                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Karten getauscht"}))
                        master.addEvent(
                            data["dat"], {"type": "message", "dat": master.playerNames[self.playerId]+" hat deine Karten getauscht"})
                        master.nextPlayer()
                    else:
                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Dieser Spieler existiert nicht!"}))
                        return
                elif self.currentAction == "specificSelect_96":
                    if data["dat"] == "_cancel":
                        self.currentAction = ""
                        master.nextPlayer()
                        self.send_message(json.dumps(
                            {"type": "action", "dat": "closeSpecificSelect"}))
                        return

                    # get all users that have the specified card and select a random user
                    availableUsers = []
                    for x in master.players:
                        for y in master.playerDeck[x]:
                            if y == data["dat"]:
                                if x not in availableUsers:
                                    availableUsers.append(x)
                    if len(availableUsers) == 0:
                        self.send_message(json.dumps(
                            {"type": "message", "dat": "Es gibt keinen Spieler mit dieser Karte!"}))
                        self.send_message(
                            json.dumps({
                                "type": "action",
                                "dat": {
                                    "type": "specificSelect",
                                    "dat": {
                                        "title": f"Welche karte möchtest du haben, die vorherige gibt es nicht (noch {self.i} versuch(e))",
                                        "options": "_deck",
                                        "type": "card",
                                        "cancel": True
                                    }
                                }
                            })
                        )
                        return
                    else:
                        selectedUser = availableUsers[randint(
                            0, len(availableUsers)-1)]
                        master.playerDeck[selectedUser].remove(data["dat"])
                        if len(master.playerDeck[selectedUser]) == 0:
                            master.playerWin(selectedUser)
                        master.addEvent(selectedUser, {
                            "type": "action",
                            "dat": "removeCard",
                            "dat2": data["dat"]
                        })

                        master.playerDeck[self.playerId].append(data["dat"])
                        master.addEvent(
                            self.playerId, {
                                "type": "action",
                                "dat": {
                                    "type": "addCard",
                                    "dat": data["dat"]
                                }
                            })
                        self.i -= 1
                        if self.i <= 0:
                            self.currentAction = ""
                            self.send_message(json.dumps(
                                {"type": "action", "dat": "closeSpecificSelect"}))
                            master.nextPlayer()
                        else:
                            self.send_message(
                                json.dumps({
                                    "type": "action",
                                    "dat": {
                                        "type": "specificSelect",
                                        "dat": {
                                            "title": f"Welche karte möchtest du haben, die vorherige gibt es nicht (noch {self.i} versuch(e))",
                                            "options": "_deck",
                                            "type": "card",
                                            "cancel": True
                                        }
                                    }
                                })
                            )
                        return

                self.send_message(json.dumps(
                    {"type": "action", "dat": "closeSpecificSelect"}))
            elif self.currentAction == "get_name" and data["type"] == "get_name":
                if (data["dat"] != ""
                        and data["dat"] not in master.playerNames.values()):
                    self.playerName = data["dat"]
                    master.playerNames[self.playerId] = self.playerName
                    self.currentAction = ""
                    master.easyEvents("playerlist")
                    # self.send_message(json.dumps(
                    #    {"type": "message", "dat": "ok :)"}))
                    self.send_message(
                        json.dumps({
                            "type": "status",
                            "dat": "waiting_for_beginning"
                        }))
                else:
                    self.send_message(
                        json.dumps({
                            "type": "action",
                            "dat": "get_name"
                        }))
            elif data["type"] == "lay_card":
                d2 = None
                if "dat2" in data.keys():
                    d2 = data["dat2"]
                master.layCard(data["dat"], self.playerId, d2)
            elif data["type"] == "drawCard":
                master.drawCard(self.playerId)
            elif data["type"] == "select_color":
                master.selectColor(self.playerId, data["dat"])
                pass
            elif data["type"] == "getCardsStat":
                self.send_message(
                    json.dumps({
                        "type": "stats",
                        "dat": {
                            "type": "cardsStat",
                            "dat": master.playerDeck[self.playerId]
                        }
                    }))
            elif data["type"] == "resend_cards_deck":
                master.addEvent(
                    self.playerId, {
                        "type": "stats",
                        "dat": {
                            "type": "deck",
                            "dat": master.playerDeck[self.playerId]
                        }
                    })
            elif data["type"] == "withdraw2x":
                master.withdraw2x(self.playerId)
            elif data["type"] == "typeStatus":
                if ("dat3" not in data or data["dat3"] != loginKey) and loginKey != "":
                    self.send_message('{"type":"wrongPass"}')
                    sleep(0.5)
                    self.handle_close()
                    self.client.close_connection(self.idet)
                    return
                if data["dat"] == "player":
                    secondTime = False
                    if "dat2" in data:
                        if data["dat2"] == "secondTime":
                            secondTime = True

                    self.type = "player"
                    if len(master.tables) != 0:
                        self.send_message(
                            json.dumps({
                                "type": "action",
                                "dat": "hasTable"
                            }))

                    self.currentAction = ""
                    r = 0  # random.randint(0, 9999999999999)
                    while r in master.players:
                        r = r + 1  # random.randint(0, 9999999999999)
                    self.playerId = r

                    self.send_message(
                        json.dumps({
                            "type": "stats",
                            "dat": {
                                "type": "yourId",
                                "dat": self.playerId
                            }
                        }))

                    if master.status == "waiting_for_players":
                        master.players.append(self.playerId)
                        master.playerClasses[self.playerId] = self

                        if not secondTime:
                            self.send_message(
                                json.dumps({
                                    "type": "message",
                                    "dat": "Mit UNO-Supreme Verbunden!"
                                }))
                            self.send_message(
                                json.dumps({
                                    "type":
                                    "message",
                                    "dat":
                                    "Spieler anzahl zurzeit: " +
                                    str(len(master.players))
                                }))

                        # select name
                        self.playerName = "[" + str(self.playerId) + "]"
                        self.send_message(
                            json.dumps({
                                "type": "status",
                                "dat": "waiting_for_name"
                            }))
                        self.send_message(
                            json.dumps({
                                "type": "action",
                                "dat": "get_name"
                            }))
                        self.currentAction = "get_name"
                        master.easyEvents("playerlist")
                    else:
                        self.send_message(
                            json.dumps({
                                "type": "message",
                                "dat": "Du bist als zuschauer verbunden"
                            }))
                        self.send_message(
                            json.dumps({
                                "type": "status",
                                "dat": "watcher"
                            }))
                        master.watchers.append(self)
                        master.sendWatcherDat(self)
                elif data["dat"] == "watcher":
                    self.type = "watcher"
                    if len(master.tables) != 0:
                        self.send_message(
                            json.dumps({
                                "type": "action",
                                "dat": "hasTable"
                            }))
                    self.send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Du bist als zuschauer verbunden"
                        }))
                    self.send_message(
                        json.dumps({
                            "type": "status",
                            "dat": "watcher"
                        }))
                    master.watchers.append(self)
                    master.sendWatcherDat(self)
                elif data["dat"] == "table":
                    self.type = "table"
                    self.send_message(
                        json.dumps({
                            "type": "message",
                            "dat": "Als Tisch verbunden"
                        }))
                    master.sendTableDat(self)
                    if (data["dat2"] == "normal"):
                        master.tables.append(self)
                        master.addEvents({"type": "action", "dat": "hasTable"})
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
                self.send_message(
                    json.dumps({
                        "type":
                        "message",
                        "dat":
                        "action " + data["type"] +
                        " could not be used! (wanted action: " +
                        self.currentAction + ")"
                    }))
        except:
            traceback.print_exc()

    def connected(self):
        print(self.idet, 'connected')

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
                if master.status == "playing" and master.currentPlayer >= len(
                        master.players):
                    print("toBig currentPlayer")
                    master.currentPlayer = len(master.players) - 1
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
                #print(self.idet, 'closed')
                pass
        except:
            if not notReal:
                print(self.idet, 'closed')
            traceback.print_exc()


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
                returnDat.append(name + ": " + str(player))
                pass
            return ",\n".join(returnDat)
        elif command[0] == "give":
            playerId = genPlayerId(command[2])
            if playerId not in master.playerDeck.keys():
                return "player doesn't exist"
            master.playerDeck[playerId].append(command[1])
            master.addEvent(playerId, {
                "type": "action",
                "dat": {
                    "type": "addCard",
                    "dat": command[1]
                }
            })
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
            master.addEvent(playerId, {
                "type": "stats",
                "dat": {
                    "type": "deck",
                    "dat": []
                }
            })

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


@app.route('/')
def projects():
    return render_template("index.html",
                           title='UNO Supreme',
                           serverHost=serverHost)


@app.route('/many')
def many():
    return render_template("many.html",
                           title='UNO Supreme',
                           serverHost=serverHost)


@app.route('/wsT')
def wsT():
    return render_template("websocketTester.html",
                           title='UNO Supreme',
                           serverHost=serverHost)


@app.route('/console')
def console():
    # serverHost: ${location.hostname}
    return render_template("console.html",
                           title='Debug console',
                           serverHost=serverHost)


@app.route("/table")
def desk():
    # serverHost: ${location.hostname}
    return render_template("table.html",
                           title="Table Stuff",
                           serverHost=serverHost)


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


class Client():
    def __init__(self):
        self.clients = {}
        self.rec = {}

    def add_client(self, ws):
        idet = randint(0, 100000)
        self.clients[idet] = ws
        self.rec[idet] = Player(self, idet)
        #Timer(10, self.close_connection, (ws,)).start()
        Thread(target=self.check_disconnect, args=(idet, )).start()
        return idet

    def run(self, idet):
        data = self.clients[idet].receive()
        self.rec[idet].handle(data)

    def active_client(self, idet):
        if idet in self.clients.keys():
            return True
        #print("not active_client")
        return False

    def check_disconnect(self, idet):
        try:
            while self.clients[idet].connected:
                #print("Is connected")
                sleep(0.05)
            self.close_connection(idet)
        except Exception as e:
            #print("check disconnected errored")
            # print(e)
            pass

    def close_connection(self, idet):
        if idet in self.rec.keys():
            self.rec[idet].handle_close()
            self.rec.pop(idet)
        if idet in self.clients.keys():
            self.clients.pop(idet)


client = Client()


@sock.route('/sock')
def echo(ws):
    idet = client.add_client(ws)
    while client.active_client(idet):
        client.run(idet)
    ws.close(1006, "Invalid Message")
    return
    print("Client disconnected because of an error")


if __name__ == "__main__":
    run()
    while True:
        sleep(100)
