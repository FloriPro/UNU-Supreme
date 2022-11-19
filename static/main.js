let ___connectionId = "";
let ___origin = "";
let ___returns = {}
let ___connectionLoadedWaiters = []
//check if run in floripro.github.io as a frame
async function ___connectionLoaded() {
    if (___connectionId != "") {
        return
    }
    return new Promise((resolve) => {
        ___connectionLoadedWaiters.push(resolve);
    })
}
if (window.self !== window.top) {
    let ___oldalert = alert
    let ___oldprompt = prompt
    let ___oldconfirm = confirm
    //overwrite functions
    alert = async (t) => {
        var r = await ___connectionLoaded();
        if (r == false) {
            return alert(t);
        }
        window.parent.postMessage(JSON.stringify({ "type": "alert", "text": t, "id": ___connectionId }), ___origin)
    }
    prompt = async (t) => {
        var r = await ___connectionLoaded();
        if (r == false) {
            return prompt(t);
        }
        return await new Promise((resolve, reject) => {
            var returnId = Math.floor(Math.random() * 100000).toString();
            ___returns[returnId] = resolve;
            window.parent.postMessage(JSON.stringify({ "type": "prompt", "text": t, "id": ___connectionId, "returnid": returnId }), ___origin)
        })
    }
    confirm = async (t) => {
        var r = await ___connectionLoaded();
        if (r == false) {
            return confirm(t);
        }
        return await new Promise((resolve, reject) => {
            var returnId = Math.floor(Math.random() * 100000).toString();
            ___returns[returnId] = resolve;
            window.parent.postMessage(JSON.stringify({ "type": "confirm", "text": t, "id": ___connectionId, "returnid": returnId }), ___origin)
        })
    }

    //return to normal after one second of no message from the parent window
    setTimeout(() => {
        if (___connectionId == "") {
            alert = ___oldalert
            prompt = ___oldprompt
            confirm = ___oldconfirm
            for (var x of ___connectionLoadedWaiters) {
                x(false);
            }
        }
    }, 5000);
}
window.addEventListener('message', function (e) {
    var data = JSON.parse(e.data);
    if (data["type"] == "newConnection") {
        ___connectionId = data["id"];
        ___origin = data["origin"];
        for (var x of ___connectionLoadedWaiters) {
            x();
        }
    }
    if (data["type"] == "return") {
        ___returns[data["id"]](data["return"]);
    }
});

function setCookie(cname, cvalue, exdays) {
    const d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return undefined;
}

//Messages
function moveAwayEffect(moveAwayTarget) {
    if (moveAwayTarget == undefined) return;
    let moveAwayTargetStyleMarginTopI = 0
    moveAwayTarget.style.marginTop = "0px";
    let moveAwayEffect = setInterval(function () {
        let startHeight = moveAwayTarget.getBoundingClientRect().height
        if (moveAwayTarget == undefined) return;
        if (moveAwayTargetStyleMarginTopI < 22) {
            moveAwayTarget.style.padding = (20 - moveAwayTargetStyleMarginTopI) + "px";
            moveAwayTarget.style.height = (20 - (moveAwayTargetStyleMarginTopI / (20 / startHeight))) + "px";
            moveAwayTarget.style.fontSize = (20 - moveAwayTargetStyleMarginTopI) + "px";
            moveAwayTarget.getElementsByClassName("closebtn")[0].style.fontSize = (20 - moveAwayTargetStyleMarginTopI) + "px";
            moveAwayTargetStyleMarginTopI += 1;
        } else {
            clearInterval(moveAwayEffect);
            document.getElementById(moveAwayTarget.id).remove();
        }
    }, 8);
}
function addMessage(text) {
    addMessageT(text, 5000);
}
function addMessageT(text, time) {
    r = Math.round(Math.random() * 10000000000)
    document.getElementById("alerts").innerHTML += '<div class="alert" style="margin-top: 0;" id="alert_id' + r + '"><span class="closebtn" onclick="moveAwayEffect(this.parentElement)">X </span>' + text + '<br></div>'
    setTimeout(eval, time, "moveAwayEffect(document.getElementById('alert_id' + '" + r + "'))")
}