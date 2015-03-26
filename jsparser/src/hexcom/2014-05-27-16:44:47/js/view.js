var colors = ["#e74c3c", "#f1c40f", "#3498db", "#2ecc71"];
var hexagonBackgroundColor = 'rgb(236, 240, 241)';
var hexagonBackgroundColorClear = 'rgba(236, 240, 241, 0.5)';
var centerBlue = '#2c3e50'; //tumblr?

function showModal(text, secondaryText) {
    var buttonSize = 150;
    var fontSizeLarge = 50;
    var fontSizeSmall = 25;
    drawPolygon(trueCanvas.width / 2, trueCanvas.height / 2, 6, trueCanvas.width / 2 - 25, 30, hexagonBackgroundColorClear);
    // drawPolygon(trueCanvas.width / 2, trueCanvas.height / 2, 6, buttonSize, 30, swegBlue);
    ctx.font = fontSizeLarge + 'px Helvetica'; // figure out what is not working
    ctx.textAlign = 'center';
    ctx.fillStyle = centerBlue;
    // ctx.fillStyle = hexagonBackgroundColor;
    ctx.fillText(text, trueCanvas.width / 2, trueCanvas.height / 2 + (fontSizeLarge / 4));
    ctx.font = fontSizeSmall + 'px Helvetica';
    ctx.fillText(secondaryText, trueCanvas.width / 2, trueCanvas.height / 2 + fontSizeLarge / 4 + fontSizeSmall / 4 + 30);
}

function renderText(x, y, fontSize, color, text) {
    ctx.font = fontSize + 'px/0 Roboto'; 
    ctx.textAlign = 'center';
    ctx.fillStyle = color;

    ctx.fillText(text, x, y + (fontSize / 4) + 3.5);

}
var scoreOpacity = 0;
function drawScoreboard() {
    if(scoreOpacity < 1){
	scoreOpacity+=0.01;
    }
    ctx.globalAlpha = scoreOpacity;
    renderText(trueCanvas.width/2+ gdx, trueCanvas.height/2+ gdy, 50, "#fff", score);
    ctx.globalAlpha = 1;
}

function clearGameBoard() {
    drawPolygon(trueCanvas.width / 2, trueCanvas.height / 2, 6, trueCanvas.width / 2, 30, hexagonBackgroundColor, 0, 'rgba(0,0,0,0)');
}

function drawPolygon(x, y, sides, radius, theta, fillColor, lineWidth, lineColor) {
    ctx.fillStyle = fillColor;
    ctx.lineWidth = lineWidth;
    ctx.strokeStyle = lineColor;
    
    ctx.beginPath();
    var coords = rotatePoint(0, radius, theta);
    ctx.moveTo(coords.x + x, coords.y + y);
    var oldX = coords.x;
    var oldY = coords.y;
    for (var i = 0; i < sides; i++) {
        coords = rotatePoint(oldX, oldY, 360 / sides);
        ctx.lineTo(coords.x + x, coords.y + y);
        oldX = coords.x;
        oldY = coords.y;
    }

    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.strokeStyle = 'rgba(0,0,0,0)';
}

function showHighScores() {
    $('#highscores').html(function() {
        var str = '<li> High Scores: </li>';
        for (var i = 0; i < highscores.length; i++) {
            str += '<li>' + highscores[i]+ '</li>';
        }
        return str;
    });
    toggleClass('#highscores', 'not-visible');
}

function toggleClass(element, active) {
    if ($(element).hasClass(active)) {
        $(element).removeClass(active);
    }
    else {
        $(element).addClass(active);
    }
}
