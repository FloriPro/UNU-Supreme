let ws
const maxCardRotation = 10;

let typ = "normal";

let password;
async function run() {
    if (getCookie("p") == undefined) {
        password = await prompt("UNU Password")
        setCookie("p", password, 100);
    } else {
        password = getCookie("p");
    }
    ws = new WebSocket(serverHost);

    ws.onclose = function (event) {
        console.error(event);
        document.querySelector("#connected_status").style.display = "";
        addMessage("Fehler: Die verbindung wurde geschlossen!");
    }
    ws.onopen = function (event) {
        ws.send(JSON.stringify({ "type": "typeStatus", "dat": "table", "dat2": typ, "dat3": password }));
        document.querySelector("#connected_status").style.display = "none";
    }

    ws.onmessage = async function (event) {
        var data = JSON.parse(event.data);
        //console.log(data);
        if (data["type"] == "message") {
            addMessage(data["dat"]);
            return;
        }

        if (data["type"] == "players") {
            for (var playerId of data["dat"]["id"]) {
                var name = data["dat"]["name"][playerId];
                if (name == undefined) {
                    name = playerId;
                }
                playerLookup[playerId] = name
            }

            //display players
            document.querySelector("#playerList").innerHTML = "";
            var i = 0;
            for (var x of data["dat"]["id"]) {
                var name = playerLookup[x];

                var div = document.createElement("div");
                div.className = "player"
                div.id = "player_" + i;
                div.style.border = "5px solid #1C6EA4"

                var div2 = document.createElement("div");
                div2.className = "playerCards"
                div2.id = "playerCards_" + x;

                var p = document.createElement("p");
                p.innerText = name;
                p.style.marginBottom = "0px";
                p.style.marginTop = "0px";

                div.append(p);
                div.append(div2);

                document.querySelector("#playerList").append(div);
                i++;
            }

            return;
        }
        if (data["type"] == "currentPlayer") {
            //remove old currentPlayer
            if (currentPlayer != -1) {
                var c = document.querySelector("#player_" + currentPlayer);
                if (c != undefined) {
                    c.style.boxShadow = ``;
                }
            }
            currentPlayer = data["dat"];

            var c = document.querySelector("#player_" + currentPlayer);
            if (c != undefined) {
                c.style.boxShadow = `inset 0px 0px 2px 5px #F00`;
            }
            return;
        }
        if (data["type"] == "playerCardCount") {
            setTimeout(() => {
                var d = data["dat"]
                for (var x of Object.keys(d)) {
                    var c = document.querySelector("#playerCards_" + x + ":not(.remove)")
                    var currentCards = c.querySelectorAll(".playerCard:not(.remove)").length;

                    var toAdd = d[x] - currentCards
                    if (toAdd > 0) {
                        //add
                        for (var x = 0; x < toAdd; x++) {
                            var img = document.createElement("img")
                            img.className = "playerCard"
                            img.src = "static/cards/back.png"

                            img.style.filter = ``;
                            img.style.animation = "moveIn 1s cubic-bezier(0, 0.78, 0.58, 1)";
                            c.append(img);
                        }
                    } else if (toAdd < 0) {
                        //remove
                        for (var x = 0; x < -toAdd; x++) {
                            slowRemove(c.querySelector(".playerCard:not(.remove)"));
                        }
                    }
                }
            }, 10)
            return;
        }

        if (data["type"] == "lyingCards") {
            document.querySelector("#stapel").innerHTML = "";
            for (var card of data["dat"]) {
                var p = getCard(card);
                p.className = "stapelCard";
                p.style.position = "absolute";

                var a = Math.random() * maxCardRotation * 2 - maxCardRotation;
                p.style.transform = "rotate(" + a + "deg)"

                document.querySelector("#stapel").append(p)
            }
            return;
        }
        if (data["type"] == "lyingCardsAdd") {
            var card = data["dat"];

            var p = getCard(card);
            //var img = document.createElement("img")
            //img.src = "/static/cards/" + card + ".png";
            p.className = "stapelCard";
            p.style.position = "absolute";
            //img.onerror = (event) => {
            //    event.srcElement.style.background = "aqua";
            //}
            //img.alt = card;
            //img.width = "86";
            //img.height = "129";

            var a = Math.random() * maxCardRotation * 2 - maxCardRotation;
            p.style.transform = "rotate(" + a + "deg)"

            document.querySelector("#stapel").append(p)
            return;
        }
        if (data["type"] == "removeLastLyingCard") {
            document.querySelector("#stapel").firstChild.remove()
            return;
        }
        if (data["type"] == "playerFinished") {
            document.querySelector("#wonPlayersBody").style.display = "";
            var li = document.createElement("li");
            li.innerText = data["dat"];
            document.querySelector("#wonPlayers").append(li);
            return;
        }
        if (data["type"] == "wrongPass") {
            password = await prompt("UNU password falsch!")
            setCookie("p", password, 100);
            reconnect()
        }

        addMessage(JSON.stringify(data));
        console.log(data);
    }
}
run()

if (location.search != "") {
    var s = location.search.replace("?", "");

    document.querySelector("#playerList").style.display = "none";
    document.querySelector("#stapel").style.display = "none";
    document.querySelector("#wonPlayersBodyHider").style.display = "none";

    if (s == "stapel") {
        document.querySelector("#stapel").style.display = "";
    }
    else if (s == "spieler") {
        document.querySelector("#playerList").style.display = "";
    }
    else if (s == "scoreboard") {
        document.querySelector("#wonPlayersBodyHider").style.display = "";
    }
    else {
        alert("stapel, spieler, scoreboard");
    }
    typ = "other";
}



var playerLookup = {}
var currentPlayer = -1;



function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}
function getCard(card) {
    var img = document.createElement("img")
    img.src = "/static/cards/" + card + ".png";
    img.onerror = (event) => {
        event.srcElement.style.background = event.target.alt.split("_")[0];
    }
    img.alt = card;
    img.width = "86";
    img.style.animation = "fadeIn 1s cubic-bezier(0, 0.78, 0.58, 1)";
    img.height = "129";
    return img;
}
/**
 * @param {HTMLElement} element 
 */
async function slowRemove(element) {
    element.className += " remove"
    //element.style.transition = "width 0.2s"
    element.style.width = "0px";
    element.style.marginRight = "0px";
    element.alt = "remove"
    await delay(1000);
    element.remove();
}
