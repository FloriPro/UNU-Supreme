let connections = 0;

class player {
    constructor() {
        this.deck = []
        this.ws = new WebSocket(`ws://${serverHost}:8000/`);
        this.ws.ws = this.ws;
        this.ws.t = this;
        this.init = false;

        this.ws.onclose = function (event) {
            if (this.ws.init) {
                removeWS();
            }
            if (this.playerStatus == "reconnect") { return; }
            console.error(event);
        }
        this.playerStatus = "waiting_for_connection"

        this.playerId = -1;
        this.currentPlayer = -1;

        this.ws.onopen = function (event) {
            newWS();
            this.ws.init = true;
            this.ws.send(JSON.stringify({ "type": "typeStatus", "dat": "player" }));
        }
        this.ws.onmessage = async function (event) {
            var thi = this.t;
            var data = JSON.parse(event.data);
            //console.log(data);
            if (data["type"] == "message") {
                return;
            }
            else if (data["type"] == "stats") {
                //load/update player names
                if (data["dat"]["type"] == "players") {
                    return;
                }

                //check if you have the right cards
                if (data["dat"]["type"] == "cardsStat") {
                    var ok = cardCheckData(data["dat"]["dat"])
                    if (ok == false) {
                        thi.ws.send(JSON.stringify({ "type": "resend_cards_deck" }))
                    }
                    return;
                }

                //highlight current player (by index not id!)
                if (data["dat"]["type"] == "currentPlayer") {
                    thi.currentPlayer = data["dat"]["dat"];
                    return;
                }

                //sets your id
                if (data["dat"]["type"] == "yourId") {
                    thi.playerId = data["dat"]["dat"];
                    return;
                }

                //how many cards the other players have
                if (data["dat"]["type"] == "playerCardCount") {
                    return;
                }

                //update your available cards
                if (data["dat"]["type"] == "deck") {
                    return;
                }

                //reset the cards that were allready set
                if (data["dat"]["type"] == "lyingCards") {
                    return;
                }
            }
            else if (data["type"] == "action") {
                if (data["dat"] == "get_name") {
                    return;
                }
                if (data["dat"] == "select_color") {
                    return;
                }
                if (data["dat"] == "slect2+Card") {
                    return;
                }
                else if (data["dat"]["type"] == "lyingCards") {
                    return;
                }
                else if (data["dat"] == "removeCard") {
                    return;
                }
                else if (data["dat"]["type"] == "addCard") {
                    return;
                }
                else if (data["dat"] == "startGame") {
                    return
                }
                else if (data["dat"] == "hasTable") {
                    //hide all things displayed on table
                    hasTable = true;
                }
                else if (data["dat"] == "slectCard") {
                    return;
                }
                else if (data["dat"] == "removeLastLyingCard") {
                    return;
                }
                else if (data["dat"] == "reconnect") {
                    reconnect();
                    return;
                }
                else if (data["dat"]["type"] == "won") {
                    reconnect();
                    return;
                }
                else if (data["dat"]["type"] == "playerFinished") {
                }
            }
            else if (data["type"] == "status") {
                thi.playerStatus = data["dat"];
                return;
            }
        }
    }
}

function newWS() {
    connections++;
    document.querySelector("#connections").innerText = connections + "";
}
function removeWS() {
    connections--
    document.querySelector("#connections").innerText = connections + "";
}

let players = []
var a = parseInt(prompt("anzahl"));
for (var x = 0; x < a; x++) {
    players.push(new player());
}