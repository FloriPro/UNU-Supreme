let connections = 0;

let password;
if (getCookie("p") == undefined) {
    password = await prompt("UNO Password")
    setCookie("p", password, 100);
} else {
    password = getCookie("p");
}

class player {
    constructor(id) {
        this.id = id;
        this.debug = [];

        this.deck = []
        this.top = "";

        this.ws = new WebSocket(serverHost);
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
            this.ws.send(JSON.stringify({ "type": "typeStatus", "dat": "player" ,"dat3":password}));
        }
        this.ws.onmessage = async function (event) {
            /**
             * @type {player}
             */
            var thi = this.t;
            var data = JSON.parse(event.data);
            thi.debug.push(data);
            if (thi.debug.length > 500) {
                thi.debug.shift();
            }
            if (data["type"] != "stats" && data["dat"]["type"] != "players") {
                //console.log(thi.id + " | " + event.data);
            }


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
                    thi.deck = data["dat"]["dat"];
                    return;
                }

                //reset the cards that were allready set
                if (data["dat"]["type"] == "lyingCards") {
                    thi.top = data["dat"]["dat"][data["dat"]["dat"].length - 1];
                    return;
                }
            }
            else if (data["type"] == "action") {
                if (data["dat"] == "get_name") {
                    thi.ws.send(JSON.stringify({ "type": "get_name", "dat": "Bot_" + thi.id }))
                    return;
                }
                if (data["dat"] == "select_color") {
                    thi.ws.send(JSON.stringify({ "type": "select_color", "dat": "green" }))
                    return;
                }
                if (data["dat"] == "slect2+Card") {
                    thi.ws.send(JSON.stringify({ "type": "withdraw2x" }));
                    return;
                }
                else if (data["dat"]["type"] == "lyingCards") {
                    thi.top = data["dat"]["dat"];
                    return;
                }
                else if (data["dat"] == "removeCard") {
                    var i = thi.deck.indexOf(data["dat2"]);
                    thi.deck.splice(i, 1);
                    if (thi.deck.length == 0) {
                        //reconnect
                        thi.ws.close();
                    }
                    return;
                }
                else if (data["dat"]["type"] == "addCard") {
                    thi.deck.push(data["dat"]["dat"]);
                    if (thi.playerStatus == "slectCard") {
                        okCards(thi);
                    }
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
                    okCards(thi);
                    return;
                }
                else if (data["dat"] == "removeLastLyingCard") {
                    return;
                }
                else if (data["dat"] == "reconnect") {
                    //reconnect
                    thi.ws.close();
                    return;
                }
                else if (data["dat"]["type"] == "won") {
                    //reconnect
                    thi.ws.close();
                    thi.playerStatus = "exit";
                    return;
                }
                else if (data["dat"]["type"] == "playerFinished") {
                }
            }
            else if (data["type"] == "status") {
                thi.playerStatus = data["dat"];
                return;
            }
            else if (data["type"] == "wrongPass"){
                password=await prompt("UNO password falsch!")
                setCookie("p",password,100);
                reconnect()
            }
        }
    }
}

/**
 * 
 * @param {player} thi 
 */
async function okCards(thi) {
    if (thi.playerStatus == "exit") {
        console.log("err");
        return;
    }

    var lay = undefined;;

    var top = thi.top.split("_");

    for (var x of thi.deck) {
        var c = x.split("_");
        if ([].includes(c[1])) {
            //pass
        }
        else if (c[0] == top[0]) {
            lay = x;
        }
        else if (c[1] == top[1]) {
            lay = x;
        }
    }

    await new Promise((resolve, reject) => { setTimeout(resolve, 1) })

    if (lay == undefined) {
        thi.ws.send(JSON.stringify({ "type": "drawCard" }));
    } else {
        thi.ws.send(JSON.stringify({ "type": "lay_card", "dat": [lay] }));
        //console.log("lay " + lay + " | " + thi.id);
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
var a = parseInt(await prompt("anzahl"));
//var a = 1;
for (var x = 0; x < a; x++) {
    players.push(new player(x));
}