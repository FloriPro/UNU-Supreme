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