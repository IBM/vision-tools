var xmlhttp;
var source;
var authtoken;
var inspections;

function Login() {
	user = document.getElementById("user").value;
	password = document.getElementById("password").value;
	url = "https://" + location.host + "/api/v1/users/sessions"
	body = {
		"grant_type": "password",
		"username": user,
		"password": password
	}
	sendRequest(url, "POST", body, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText, true);
			if (xmlhttp.status == 200) {
				resp = JSON.parse(xmlhttp.responseText);
				authtoken = resp.token
				GetInspections()
			}
		}
	});
}

function Logout() {
	url = "https://" + location.host + "/api/v1/users/sessions"
	sendRequest(url, "DELETE", null, function () {
		if (xmlhttp.readyState == 4) {
			updateStatus(xmlhttp.responseText, true);
			if (xmlhttp.status == 200) {
				unsubscribeEvents()
			}
		}
	});
}

function GetInspections() {
	insptab = document.getElementById("inspectiontable");
	rowcount = insptab.rows.length
	for (i = 1; i < rowcount; i++) {
		insptab.deleteRow(1);
	}
	url = "https://" + location.host + "/api/v1/inspections"
	sendRequest(url, "GET", null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				inspections = JSON.parse(xmlhttp.responseText)
				for (i = 0; i < inspections.length; i++) {
					row = insptab.insertRow(i + 1);
					cell = row.insertCell(0);
					cell.innerHTML = inspections[i].name;
				}
				GetStats(0)
			} else {
				updateStatus(xmlhttp.responseText, true);
			}
		}
	});
}

function GetStats(row) {
	url = "https://" + location.host + "/api/v1/inspections/synopsis?uuid=" + inspections[row].uuid
	insptab = document.getElementById("inspectiontable");
	sendRequest(url, "GET", null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				synopsis = JSON.parse(xmlhttp.responseText);
				currRow = insptab.rows[row + 1];
				cell1 = currRow.insertCell(1);
				cell1.innerHTML = synopsis.stats.imagecnt;
				cell2 = currRow.insertCell(2);
				cell2.innerHTML = synopsis.stats.total;
				cell3 = currRow.insertCell(3);
				cell3.innerHTML = synopsis.stats.pass;
				cell4 = currRow.insertCell(4);
				cell4.innerHTML = synopsis.stats.fail;
				cell5 = currRow.insertCell(5);
				cell5.innerHTML = synopsis.stats.inconclusive;
				cell6 = currRow.insertCell(6);
				cell6.innerHTML = synopsis.stats.alerts;
				cell7 = currRow.insertCell(7);
				delbutton = "<button type=\"button\" class=\"tightbutton\" onclick=\"BatchDelete('";
				delbutton += inspections[row].uuid;
				delbutton += "');\" >Delete</button>";
				cell7.innerHTML = delbutton;
				passbutton = "<button type=\"button\" class=\"tightbutton\" onclick=\"BatchReassign('";
				passbutton += inspections[row].uuid;
				passbutton += "','pass');\" >Pass</button>";
				failbutton = "<button type=\"button\" class=\"tightbutton\" onclick=\"BatchReassign('";
				failbutton += inspections[row].uuid;
				failbutton += "','fail');\" >Fail</button>";
				incbutton = "<button type=\"button\" class=\"tightbutton\" onclick=\"BatchReassign('";
				incbutton += inspections[row].uuid;
				incbutton += "','inconclusive');\" >Inconclusive</button>";
				cell8 = currRow.insertCell(8);
				cell8.innerHTML = passbutton + failbutton + incbutton;
				filterbutton = "<button type=\"button\" class=\"tightbutton\" onclick=\"GetFilterData('";
				filterbutton += inspections[row].uuid;
				filterbutton += "');\" >Get FilterData</button>";
				cell9 = currRow.insertCell(9);
				cell9.innerHTML = filterbutton;
				row++
				if (row < inspections.length) {
					GetStats(row)
				}
			} else {
				updateStatus(xmlhttp.responseText, true);
			}
		}
	});
}

function BatchDelete(uuid) {
	body = {};
	body.action = "delete";
	body.inspectionUUID = uuid;
	GetIDs(uuid, function(ids) {
		body.filenames = ids;
		url = "https://" + location.host + "/api/v1/inspections/images/batchactions";
		sendRequest(url, "PUT", body, function () {
			if (xmlhttp.readyState == 4) {
				if (xmlhttp.status == 202) {
					resp = JSON.parse(xmlhttp.responseText);
					jobID = resp.job_id;
					updateStatus(jobID, true);
					subscribeEvents(jobID);
				} else {
					updateStatus(xmlhttp.responseText, true);
				}
			}
		});
	});
}

function BatchReassign(uuid, newvalue) {
	body = {};
	body.action = "reassign";
	body.inspectionUUID = uuid;
	body.value = newvalue;
	GetIDs(uuid, function(ids) {
		body.filenames = ids;
		url = "https://" + location.host + "/api/v1/inspections/images/batchactions";
		sendRequest(url, "PUT", body, function () {
			if (xmlhttp.readyState == 4) {
				if (xmlhttp.status == 202) {
					resp = JSON.parse(xmlhttp.responseText);
					jobID = resp.job_id;
					updateStatus(jobID, true);
					subscribeEvents(jobID);
				} else {
					updateStatus(xmlhttp.responseText, true);
				}
			}
		});
	});
}

function GetIDs(uuid, callback) {
	url = "https://" + location.host + "/api/v1/inspections/images/filterdata?uuid=" + uuid;
	sendRequest(url, "GET", null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				filterdata = JSON.parse(xmlhttp.responseText);
				ids = [];
				for (i=0; i < filterdata.i.length; i++) {
					ids.push(filterdata.i[i].f)
				}
				callback(ids);
			} else {
				updateStatus(xmlhttp.responseText, true);
			}
		}
	});
}

function GetFilterData(uuid) {
	url = "https://" + location.host + "/api/v1/inspections/images/filterdata?uuid=" + uuid;
	showspin();
	sendRequest(url, "GET", null, function () {
		if (xmlhttp.readyState == 4) {
			hidespin();
			if (xmlhttp.status == 200) {
				updateStatus("Got FilterData", true);
			} else {
				updateStatus(xmlhttp.responseText, true);
			}
		}
	});
}

function updateStatus(message, newline) {
	document.getElementById("status").innerHTML += message
	if (newline) {
		document.getElementById("status").innerHTML += "\n"
	}
}

function clearStatus() {
	document.getElementById("status").innerHTML = "";
}

function showspin() {
	document.getElementById("spin").style.display = "block";
}

function hidespin() {
	document.getElementById("spin").style.display = "none";
}

function showprogress() {
	modal = document.getElementById("progressModal");
	modal.style.display = "block";
	var span = document.getElementById("closeProgress");
	span.onclick = function () {
		modal.style.display = "none";
	}
}

function hideprogress() {
	document.getElementById("progressModal").style.display = "none";
}

function updateprogress(msg) {
	document.getElementById("progressMessage").innerHTML = msg;
}

function subscribeEvents(jobID) {
	updateStatus("Entering subscribeEvents", true);
	if (!window.EventSource) {
		alert("EventSource is not enabled in this browser");
		return;
	}
	updateStatus("Subscribing to Events", true);
	showprogress();
	source = new EventSource('/api/v1/system/events');
	source.addEventListener("message", function (e) {
		message = JSON.parse(e.data)
		if (message.id === jobID) {
			status = message.severity + ":" + message.source + ":" + message.id + ":" + message.category + ":" + message.message
			updateStatus(status, true);
			updateprogress(message.message);
			if (message.severity === "error" || message.severity === "success") {
				unsubscribeEvents();
				GetInspections();
			}
		}
	});
	source.addEventListener("error", function (e) {
		updateStatus(e.data, true);
		source.close();
	});
	source.addEventListener("ping", function (e) {
		updateStatus("+", false);
	});
}

function unsubscribeEvents() {
	updateStatus("Unsubscribing from Events", true);
	source.close();
}

function sendRequest(url, method, body, callback) {
	xmlhttp = new XMLHttpRequest();

	xmlhttp.onreadystatechange = callback;
	xmlhttp.open(method, url, true);
	xmlhttp.setRequestHeader("Content-Type", "application/json");
	xmlhttp.setRequestHeader("mvie-controller", authtoken);
	if (method != "GET" && method != "DELETE") {
		if (body != null) {
			xmlhttp.send(JSON.stringify(body));
		} else {
			xmlhttp.send();
		}
	} else {
		xmlhttp.send();
	}
}