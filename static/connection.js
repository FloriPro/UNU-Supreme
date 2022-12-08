const rot = 40;
const colors = ["red", "green", "blue", "yellow"];
const windowsCombos = ["aussetzen", "richtungswechsel", "komunist"];
const otherCombos = [["9", "6"], ["0", "2", "4"], ['9', '8', '7', '6', '5', '4', '3', '2', '1', '0']];

let wantsType = "player";
/**
 * @type {{[cardName: string]:string}}
 */
let cardImages = {};
let allCards = []
/**
 * @type {HTMLImageElement}
 */
let coulorSelectType = "send"
/**
 * resolve promise
 */
let coulorSelectAsync = () => { }

let currentlyClicked = undefined;
let secondTime = false;
/**
 * @type {WebSocket}
 */
let ws;
let playerStatus;
let playerId;
let currentPlayer;
let hasTable = false;
//addMessage("ok");
async function connect() {
    ws = new WebSocket(serverHost);
    ws.onclose = function (event) {
        if (playerStatus == "reconnect") { return; }
        console.error(event);
        document.querySelector("#connected_status").style.display = "";
        addMessage("Fehler: Die verbindung wurde geschlossen!");
    }
    playerStatus = "waiting_for_connection"
    document.querySelector("#status").innerText = "Status: " + playerStatus;

    playerId = -1;
    currentPlayer = -1;

    ws.onopen = function (event) {
        if (!secondTime) {
            ws.send(JSON.stringify({ "type": "allCards" }));
        }
        var isSecondTime = "false";
        if (secondTime) {
            isSecondTime = "secondTime";
        }

        document.querySelector("#wonPlayers").innerHTML = "";
        ws.send(JSON.stringify({ "type": "typeStatus", "dat": wantsType, "dat2": isSecondTime, "dat3": password }));
        document.querySelector("#connected_status").style.display = "none";
        secondTime = true;
    }
    ws.onmessage = async function (event) {
        var data = JSON.parse(event.data);
        //console.log(data);
        if (data["type"] == "message") {
            addMessage(data["dat"]);
            return;
        }
        else if (data["type"] == "stats") {
            //preloading all card images
            if (data["dat"]["type"] == "allCards") {
                loadCardImages(data["dat"]["dat"])
            }

            //load/update player names
            if (data["dat"]["type"] == "players") {
                document.querySelector("#playerList").innerHTML = "";
                var i = 0;
                for (var x of data["dat"]["dat"]["id"]) {
                    var name = "error";
                    if (data["dat"]["dat"]["name"][x] != undefined) {
                        //id to name
                        name = data["dat"]["dat"]["name"][x]
                    } else {
                        //no name defined
                        name = "[" + x + "]"
                    }

                    if (x == playerId) {
                        name = "Du: " + name
                    }

                    var div = document.createElement("div");
                    div.className = "player"
                    div.id = "player_" + i;
                    div.style.border = "5px solid #1C6EA4"

                    var div2 = document.createElement("div");
                    div2.className = "playerCards"
                    div2.id = "playerCards_" + x;

                    var button = document.createElement("p");
                    button.innerText = name;
                    button.style.marginBottom = "0px";
                    button.style.marginTop = "0px";

                    div.append(button);
                    div.append(div2);

                    document.querySelector("#playerList").append(div);
                    i++;
                }
                return;
            }

            //check if you have the right cards
            if (data["dat"]["type"] == "cardsStat") {
                var ok = cardCheckData(data["dat"]["dat"])
                if (ok == false) {
                    //addMessage("Fehler: falsche karten angezeigt!")
                    ws.send(JSON.stringify({ "type": "resend_cards_deck" }))
                }
                return;
            }

            //highlight current player (by index not id!)
            if (data["dat"]["type"] == "currentPlayer") {
                //remove old currentPlayer
                if (currentPlayer != -1) {
                    var c = document.querySelector("#player_" + currentPlayer);
                    if (c != undefined) {
                        c.style.filter = ``;
                    }
                }
                currentPlayer = data["dat"]["dat"];

                var c = document.querySelector("#player_" + currentPlayer);
                if (c != undefined) {
                    c.style.filter = `drop-shadow(yellow 0px 0px 8px)`;
                }
                return;
            }

            //sets your id
            if (data["dat"]["type"] == "yourId") {
                playerId = data["dat"]["dat"];
                return;
            }

            //how many cards the other players have
            if (data["dat"]["type"] == "playerCardCount") {
                setTimeout(() => {

                    var d = data["dat"]["dat"]
                    for (var x of Object.keys(d)) {
                        var c = document.querySelector("#playerCards_" + x + ":not(.remove)")
                        if (c != null) {
                            var currentCards = c.querySelectorAll(".playerCard:not(.remove)").length;

                            var toAdd = d[x] - currentCards
                            if (toAdd > 0) {
                                //add
                                for (var x = 0; x < toAdd; x++) {
                                    var img = document.createElement("img")
                                    img.className = "playerCard"
                                    img.src = "static/cards/back.png"
                                    //img.width = "86";
                                    //img.height = "129";
                                    //img.style.marginRight = "-45px";
                                    //img.style.height = "auto";
                                    //img.style.width = "30px";

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
                        } else {
                            //only if player is removed by winning. No panic
                        }
                    }
                }, 10)
                return;
            }

            //update your available cards
            if (data["dat"]["type"] == "deck") {
                document.querySelector("#deck").innerHTML = "";
                for (var x of data["dat"]["dat"]) {
                    var button = getCard(x);

                    //var img = document.createElement("img")
                    //img.src = "/static/cards/" + x + ".png"
                    //img.onerror = (event) => {
                    //    event.srcElement.style.background = "aqua";
                    //}
                    button.onclick = (event) => {
                        layCard(event.target.alt, button);
                    }
                    button.className = "ownDeck"
                    //img.alt = x
                    //img.width = "86";
                    //img.height = "129";

                    document.querySelector("#deck").append(button)
                }
                updateCombinations();
                return;
            }

            //reset the cards that were allready set
            if (data["dat"]["type"] == "lyingCards") {
                document.querySelector("#stapel").innerHTML = "";
                for (var card of data["dat"]["dat"]) {
                    var button = getCard(card);
                    //var img = document.createElement("img")
                    //img.src = "/static/cards/" + card + ".png";
                    button.className = "stapelCard";
                    button.style.position = "absolute";
                    //img.onerror = (event) => {
                    //    event.srcElement.style.background = "aqua";
                    //}
                    //img.alt = card;
                    //img.width = "86";
                    //img.height = "129";

                    var a = Math.random() * rot * 2 - rot;
                    button.style.transform = "rotate(" + a + "deg)"

                    document.querySelector("#stapel").append(button)
                }
                return;
            }
        }
        else if (data["type"] == "action") {
            if (data["dat"] == "get_name") {
                if (document.querySelector("#nameInputInput").value != "") {
                    ws.send(JSON.stringify({ "type": "get_name", "dat": document.querySelector("#nameInputInput").value }));
                } else {
                    document.querySelector("#nameInput").style.display = "";
                }
                return;
            }
            if (data["dat"] == "select_color") {
                document.querySelector("#colorInput").style.display = "flex";
                return;
            }
            if (data["dat"] == "slect2+Card") {
                document.querySelector("#withdrawTwo").innerText = data["dat2"] + " Ziehen"
                document.querySelector("#twoxInput").style.display = "flex";

                //load stuff
                var cards = document.querySelectorAll(".ownDeck");

                for (var c of cards) {
                    if (c.alt != "remove" && c.alt.endsWith("2+")) {
                        var button = getCard(c.alt)
                        button.onclick = (event) => {
                            layCard(event.target.alt);
                        }
                        document.querySelector("#twoxinputPositions").append(button);
                    }
                }
                return;

            }
            else if (data["dat"]["type"] == "lyingCards") {
                var card = data["dat"]["dat"];

                var button = getCard(card);
                //var img = document.createElement("img")
                //img.src = "/static/cards/" + card + ".png";
                button.className = "stapelCard";
                button.style.position = "absolute";
                //img.onerror = (event) => {
                //    event.srcElement.style.background = "aqua";
                //}
                //img.alt = card;
                //img.width = "86";
                //img.height = "129";

                var a = Math.random() * rot * 2 - rot;
                button.style.transform = "rotate(" + a + "deg)"

                document.querySelector("#stapel").append(button)
                return;
            }
            else if (data["dat"] == "removeCard") {
                var c = undefined;
                if (currentlyClicked != undefined && currentlyClicked.alt == data["dat2"]) {
                    c = currentlyClicked;
                } else {
                    c = document.querySelector('.ownDeck[alt="' + data["dat2"] + '"]:not(.remove)');
                }

                slowRemove(c);
                updateCombinations();
                return;
            }
            else if (data["dat"]["type"] == "addCard") {
                var x = data["dat"]["dat"];

                var button = getCard(x);
                button.onclick = (event) => {
                    layCard(event.target.alt, button);
                }
                button.className = "ownDeck"

                document.querySelector("#deck").append(button);
                updateCombinations();
                return;
            }
            else if (data["dat"] == "startGame") {
                document.querySelector("#drawCard").style.display = "";
                document.querySelector("#startGame").style.display = "none";
                return
            }
            else if (data["dat"] == "hasTable") {
                //hide all things displayed on table
                hasTable = true;
                var toHide = ["#playerList", "#stapel", "#wonPlayersBody"];
                for (var x of toHide) {
                    document.querySelector(x).style.display = "none";
                }

                if (playerStatus == "watcher") {
                    if (hasTable) {
                        document.querySelector("#lookOnTable").style.display = "";
                    } else {
                        document.querySelector("#lookOnTable").style.display = "none";
                    }
                } else {
                    document.querySelector("#lookOnTable").style.display = "none";
                }
            }
            else if (data["dat"] == "slectCard") {
                //handled by status
                return;
            }
            else if (data["dat"] == "removeLastLyingCard") {
                document.querySelector("#stapel").firstChild.remove()
                return;
            }
            else if (data["dat"] == "reconnect") {
                reconnect();
                return;
            }
            else if (data["dat"]["type"] == "won") {
                reconnect();
                document.querySelector("#winNum").innerText = data["dat"]["dat"];
                document.querySelector("#winScreen").style.display = "flex";
                return;
            }
            else if (data["dat"]["type"] == "playerFinished") {
                if (hasTable == false) {
                    document.querySelector("#wonPlayersBody").style.display = "";
                }
                var li = document.createElement("li");
                li.innerText = data["dat"]["dat"];
                document.querySelector("#wonPlayers").append(li);
                return;
            }
            else if (data["dat"]["type"] == "specificSelect") {
                document.querySelector("#specificSelect").style.display = "flex";
                document.querySelector("#specificSelectHolder").innerHTML = "";

                if (data["dat"]["dat"]["options"] == "_deck") {
                    var o = {}
                    for (var x of allCards) {
                        o[x] = x;
                    }
                    data["dat"]["dat"]["options"] = o
                }

                var h = document.createElement("h1");
                h.innerText = data["dat"]["dat"]["title"]
                document.querySelector("#specificSelectHolder").append(h)
                if (data["dat"]["dat"]["cancel"] == true) {
                    document.querySelector("#specificSelectCancel").style.display = "";
                } else {
                    document.querySelector("#specificSelectCancel").style.display = "none";
                }

                for (var x of Object.keys(data["dat"]["dat"]["options"])) {
                    var button;
                    if (data["dat"]["dat"]["type"] == "text") {
                        button = document.createElement("button")
                        button.innerText = x;
                    } else if (data["dat"]["dat"]["type"] == "card") {
                        button = getCard(x);
                    } else {
                        button = document.createElement("button")
                        button.innerText = "Error: no type " + data["dat"]["dat"]["type"] + " | " + x;
                    }
                    button.alt = data["dat"]["dat"]["options"][x]
                    button.onclick = (event) => { ws.send(JSON.stringify({ "type": "selectResponse", "dat": event.target.alt })) }
                    document.querySelector("#specificSelectHolder").append(button)
                }
                return;
            }
            else if (data["dat"] == "closeSpecificSelect") {
                document.querySelector("#specificSelect").style.display = "none";
                document.querySelector("#specificSelectHolder").innerHTML = "";
            }
        }
        else if (data["type"] == "status") {
            playerStatus = data["dat"];
            document.querySelector("#status").innerText = "Status: " + playerStatus;

            if (playerStatus != "slectCard") {
                document.querySelector("#deck").style.filter = "";//"blur(1px)";
            } else {
                document.querySelector("#deck").style.filter = "drop-shadow(0px 0px 37px yellow)";
            }
            if (playerStatus == "waiting_for_beginning") {
                document.querySelector("#startGame").style.display = "";
            }
            if (playerStatus == "watcher") {
                if (hasTable) {
                    document.querySelector("#lookOnTable").style.display = "";
                } else {
                    document.querySelector("#lookOnTable").style.display = "none";
                }
            } else {
                document.querySelector("#lookOnTable").style.display = "none";
            }

            if (playerStatus != "waiting_for_name") {
                document.querySelector("#nameInput").style.display = "none";
            }
            if (playerStatus != "waiting_for_color") {
                document.querySelector("#colorInput").style.display = "none";
            }
            if (playerStatus != "2+_Desicion") {
                document.querySelector("#twoxInput").style.display = "none";
            } else {
                document.querySelector("#twoxinputPositions").innerHTML = "";
            }
            return;
        }
        else if (data["type"] == "wrongPass") {
            password = await prompt("Password falsch!")
            setCookie("p", password, 100);
            reconnect()
        }

        console.log(data);
    }
}

let preloadCard = 0;
let preloadedCard = 0;
async function loadCardImages(cards) {
    allCards = cards;
    preloadCard = cards.length;
    document.querySelector("#preloadIMG").style.display = "flex";
    document.querySelector("#preloadIMGText").innerText = "Preloading Images 0/" + preloadCard;
    for (var x of cards) {
        loadCardImage(x);
    }
}
async function loadCardImage(x, i) {
    if (i == undefined) { i = 0; }
    if (i >= 10) { console.error("could not load img " + x) }

    if (cardImages[x] != undefined) { return; }
    var p = new Promise(async (resolve, reject) => {
        var reader = new FileReader();
        reader.onload = async () => {
            resolve(reader.result);
        }
        try {
            reader.readAsDataURL(await (await fetch("/static/cards/" + x + ".png")).blob());
        } catch {
            await new Promise((resolve) => { setTimeout(resolve, 100) });
            console.log("retrying " + x)
            loadCardImage(x, i + 1);
        }
    });
    var out = await p;
    cardImages[x] = out;
    preloadedCard++;
    document.querySelector("#preloadIMGText").innerText = "Preloading Images " + preloadedCard + "/" + preloadCard;
    if (preloadCard == preloadedCard) {
        document.querySelector("#preloadIMG").style.display = "none";
    }
}

function genCombiTeller(cards, needsColour) {
    var div = document.createElement("div");
    div.className = "combiShowerBody"

    for (var x of cards) {
        var img = getCard(x);
        img.className = "combiShower";
        img.style.animation = "";

        div.append(img);
    }

    if (needsColour) {
        div.onclick = async () => {
            ws.send(JSON.stringify({ "type": "lay_card", "dat": cards, "dat2": await asColourSelect() }))
        }
    } else {
        div.onclick = async () => {
            ws.send(JSON.stringify({ "type": "lay_card", "dat": cards }))
        }
    }

    return div;
}
/**
 * 
 * @param {string} card 
 * @param {string} color 
 * @param {Array<HTMLImageElement>} allCards 
 */
function cardExists(card, color, allCards) {
    for (var x of allCards) {
        if (x.alt == color + "_" + card) {
            return true;
        }
    }
    return false;
}

function updateCombinations() {
    var cards = document.querySelectorAll(".ownDeck:not(.remove)");
    ///////////////////////////////
    //          WINDOWS          //
    //gleiche karte, alle Farben //
    ///////////////////////////////

    var combinations = [];

    //windowsCombos
    for (var x of windowsCombos) {
        var e = true;
        for (var y of ["red", "green", "blue", "yellow"]) {
            if (!cardExists(x, y, cards)) {
                e = false;
            }
        }

        if (e == true) {
            combinations.push([["red_" + x, "green_" + x, "blue_" + x, "yellow_" + x], true]);
        }
    }

    //otherCombos
    for (var x of otherCombos) {
        for (var z of ["red", "green", "blue", "yellow"]) {
            var e = true;
            for (var y of x) {
                if (!cardExists(y, z, cards)) {
                    e = false;
                }
            }

            if (e == true) {
                var t = []
                for (var y of x.reverse()) {
                    t.push(z + "_" + y)
                }
                x.reverse()

                combinations.push([t, false]);
            }
        }
    }

    //show them with no animation
    document.querySelector("#combinations").innerHTML = "";
    for (var x of combinations) {
        document.querySelector("#combinations").append(genCombiTeller(x[0], x[1]));
    }


    //////////// Other ////////////
    //9 + 6

}

function reconnect() {
    document.querySelector("#playerList").innerHTML = "";
    document.querySelector("#drawCard").style.display = "none";
    document.querySelector("#wonPlayersBody").style.display = "none";
    document.querySelector("#deck").innerHTML = "";
    document.querySelector("#stapel").innerHTML = "";
    document.querySelector("#combinations").innerHTML = "";
    document.querySelector("#specificSelect").style.display = "none";
    document.querySelector("#specificSelectHolder").innerHTML = "";

    playerStatus = "reconnect";
    ws.onclose = () => { };
    ws.close();
    connect();
}

let password;
async function run() {
    if (getCookie("p") == undefined) {
        password = await prompt("Password")
        setCookie("p", password, 100);
    } else {
        password = getCookie("p");
    }
    connect();
}
setTimeout(run, 1);

function getCard(card) {
    var img = document.createElement("img")
    if (cardImages[card] !== undefined) {
        img.src = cardImages[card];
    } else {
        img.src = "/static/cards/" + card + ".png";
    }
    img.onerror = (event) => {
        event.srcElement.style.background = event.target.alt.split("_")[0];
    }
    img.alt = card;
    img.width = "86";
    img.style.animation = "fadeIn 1s cubic-bezier(0, 0.78, 0.58, 1)";
    img.height = "129";
    return img;
}

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}
/**
 * 
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

async function asColourSelect() {
    var p = new Promise((resolve, reject) => { coulorSelectAsync = resolve; })
    document.querySelector("#colorInput").style.display = "flex";
    coulorSelectType = "async";
    return p
}

function selectColor(color) {
    if (coulorSelectType == "send") {
        ws.send(JSON.stringify({ "type": "select_color", "dat": color }))
    } else if (coulorSelectType == "async") {
        coulorSelectAsync(color);
        document.querySelector("#colorInput").style.display = "none";
        coulorSelectType = "send"
    }
}
function layCard(card, thisCard) {
    currentlyClicked = thisCard;
    ws.send(JSON.stringify({ "type": "lay_card", "dat": [card] }))
}

function cardCheck() {
    if (!["waiting_for_connection", "waiting_for_name", "waiting_for_beginning", "watcher", "reconnect"].includes(playerStatus))
        ws.send(JSON.stringify({ "type": "getCardsStat" }))
}
function cardCheckData(data) {
    var cards = document.querySelectorAll(".ownDeck:not(.remove)");
    var allCards = []
    for (var c of cards) {
        if (c.alt != "remove") {
            allCards.push(c.alt);
        }
    }

    if (data.length != allCards.length) {
        return false;
    }

    for (var x of data) {
        if (!allCards.includes(x)) {
            return false;
        }
        var index = allCards.indexOf(x);
        if (index > -1) {
            allCards.splice(index, 1);
        } else {
            return false;
        }
    }
    return true;
}

setInterval(cardCheck, 5000)

for (var x = 0; x < 8; x++) {
    //<img src="static/cards/back.png" style="width: 86px; position:absolute;">
    var img = document.createElement("img")
    img.src = "static/cards/back.png"
    img.width = "86";
    img.height = "129";
    img.style.position = "absolute";

    img.style.filter = `blur(${(8 - x) / 5}px)`;
    img.style.animation = "moveIn 1s cubic-bezier(0, 0.78, 0.58, 1)";


    var rot2 = 10;

    var a = Math.random() * rot2 * 2 - rot2;
    img.style.transform = "rotate(" + a + "deg)"
    document.querySelector("#drawCard").append(img);
}