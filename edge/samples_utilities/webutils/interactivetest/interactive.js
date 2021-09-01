var xmlhttp;
var uuid;
var timer;
var canvas;
var context;
var imageObj;
var message;
var authtoken;


function Init() {
	canvas = document.getElementById("thecanvas");
	context = canvas.getContext('2d');
	imageObj = new Image();
	imageObj.onload = function() {
        context.drawImage(imageObj, 0, 0, 400, 300);
		imgwidth = this.width;
		imgheight = this.height;
		xscale = 400 / imgwidth
		yscale = 300 / imgheight
		if (message.data != null ) {
			if (message.data.hasOwnProperty("objects")) {
				for (var i = 0 ; i < message.data.objects.length; i++) {
					xpos = message.data.objects[i].minX * xscale;
					ypos = message.data.objects[i].minY * yscale;
					width = (message.data.objects[i].maxX - message.data.objects[i].minX) * xscale;
					height = (message.data.objects[i].maxY - message.data.objects[i].minY) * yscale;
		
					context.beginPath();
					  context.rect(xpos, ypos, width, height);
					context.lineWidth = 4;
					  context.strokeStyle = 'red';
					  context.stroke();
				}
			}
			if (message.data.hasOwnProperty("ruleresults")) {
				for (var i = 0 ; i < message.data.ruleresults.length; i++) {
					for (var j = 0 ; j < message.data.ruleresults[i].objects.length; j++) {
						xpos = message.data.ruleresults[i].objects[j].xmin * xscale;
						ypos = message.data.ruleresults[i].objects[j].ymin * yscale;
						width = (message.data.ruleresults[i].objects[j].xmax - message.data.ruleresults[i].objects[j].xmin) * xscale;
						height = (message.data.ruleresults[i].objects[j].ymax - message.data.ruleresults[i].objects[j].ymin) * yscale;
			
						context.beginPath();
						  context.rect(xpos, ypos, width, height);
						context.lineWidth = 4;
						  context.strokeStyle = 'red';
						  context.stroke();
					}
					
				}
			}
			
		  };
		}
		
}

function Login() {
	user = document.getElementById("user").value;
	password = document.getElementById("password").value;
	url = "https://" + location.host + "/api/v1/users/sessions"
	body = {
		"grant_type":"password",
		"username":user,
		"password":password
	}
	sendRequest(url, "POST", body, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText + "\n");
			if (xmlhttp.status == 200) {
				resp = JSON.parse(xmlhttp.responseText);
				authtoken = resp.token
			}
		}
	});
}

function Start() {
	uuid = document.getElementById("inspectionUUID").value;
	url = "https://" + location.host + "/api/v1/inspections/interactive/states?uuid=" + uuid + "&enable=true"
	sendRequest(url, "PUT", null, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText + "\n");
			if (xmlhttp.status == 200) {
				
			}
		}
	});
}

function Stop() {
	clearInterval(timer)
	uuid = document.getElementById("inspectionUUID").value;
	url = "https://" + location.host + "/api/v1/inspections/interactive/states?uuid=" + uuid + "&enable=false"
	sendRequest(url, "PUT", null, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText + "\n");
			if (xmlhttp.status == 200) {
				
			}
			
		}
	});
}

function startTriggerEvents() {
	interval = document.getElementById("triggerInterval").value;
	timer = setInterval(triggerEvents,interval)
}

function stopTriggerEvents() {
	clearInterval(timer)
}

function triggerEvents(rules) {
	uuid = document.getElementById("inspectionUUID").value;
	url = "https://" + location.host + "/api/v1/inspections/interactive/triggers?uuid=" + uuid
	if (rules) {
		url += "&refresh=true"
	}
	sendRequest(url, "PUT", null, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText + "\n");
			if (xmlhttp.status == 200) {
				message = JSON.parse(xmlhttp.responseText);
				//document.getElementById("theImage").src = message.filename;
				imageObj.src = message.filename;
				
			}
		}
	});
}

function updateStatus(message) {
	document.getElementById("status").innerHTML += message;
	//status = document.getElementById("status");
	//status.scrollTop = status.scrollHeight;
	//status.innerHTML += message + "\n";
	
}



function subscribeEvents() {
	lastfile = ""
	updateStatus("Entering subscribeEvents\n");
	if (!window.EventSource) {
		alert("EventSource is not enabled in this browser");
		return;
	}
	uuid = document.getElementById("inspectionUUID").value;
	updateStatus("Subscribing to Events\n");
	var source = new EventSource('/api/v1/inspections/interactive/events?uuid=' + uuid);
	source.addEventListener("message", function (e) {
		updateStatus(".");
		if (e.data === "DONE") {
			updateStatus("Closing source\n");
			source.close();
		} else {
			message = JSON.parse(e.data);
			document.getElementById("theImage").src = message.filename;
			if (message.filename != lastfile) {
				lastfile = message.filename;
				updateStatus("#")
			}
		}
	});
	source.addEventListener("error", function (e) {
		updateStatus(e.data + "\n");
		source.close();
	});
}

function sendRequest(url, method, body, callback) {
	xmlhttp = new XMLHttpRequest();

	xmlhttp.onreadystatechange = callback;
	xmlhttp.open(method, url, true);
	xmlhttp.setRequestHeader("Content-Type", "application/json");
	xmlhttp.setRequestHeader("mvie-controller", authtoken);
	if (method != "GET") {
		if (method != "DELETE") {
			xmlhttp.send(JSON.stringify(body));
		} else {
			xmlhttp.send();
		}
	} else {
		xmlhttp.send();
	}
}