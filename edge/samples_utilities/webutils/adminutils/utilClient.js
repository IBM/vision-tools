var xmlhttp;
var authtoken;
var baseurl;
var users;
var devices
var deviceuuid;
const persist = ['warn', 'error'];

/*
*
*	Session Management functions
*
*/
var sessionUrl;

function login() {
	user = document.getElementById("userid").value;
	password = document.getElementById("pwd").value;
	url = baseurl + "users/sessions"
	body = {
		"grant_type": "password",
		"username": user,
		"password": password
	}
	sendRequest(url, "POST", body, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				resp = JSON.parse(xmlhttp.responseText);
				authtoken = resp.token;
				UX_setLoggedIn();
				subscribeEvents();
				UX_flashsuccess("Logged In");
			} else {
				UX_flasherror("Login Failed");
			}
		}
	});
}


function logout() {
	url = baseurl + "users/sessions"
	sendRequest(url, "DELETE", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_setLoggedOut();
				unsubscribeEvents();
				UX_flashsuccess("Logged Out")
			} else {
				UX_flasherror("Logout Failed")
			}
		}
	}, null, null);
}

/*
*
* Status
*
*/

function subscribeEvents() {
	UX_updateStatus(false, "Entering subscribeEvents", true);
	if (!window.EventSource) {
		alert("EventSource is not enabled in this browser");
		return;
	}
	UX_updateStatus(false, "Subscribing to Events", true);
	source = new EventSource('/api/v1/system/events');
	source.addEventListener("message", function (e) {
		message = JSON.parse(e.data)
		status = message.source + ":" + message.category + ":" + message.id + ":" + message.message
		UX_updateStatus(true, e.data, true);
		if (persist.includes(message.severity)) {
			UX_flash(status, message.severity)
		} else {
			UX_flash(status, message.severity, 5000)
		}

	});
	source.addEventListener("ping", function (e) {
		pingwaslast = true;
		UX_updateStatus(false, "+", false);
	});
}

function getEngineStatus() {
	url = baseurl + "system/engines";
	sendRequest(url, "GET", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_updateStatus(true, xmlhttp.responseText, true);
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

function unsubscribeEvents() {
	UX_updateStatus(true, "Unsubscribing from Events", true);
	source.close();
}

/*
*
* Backup / Restore
*
*/
function backup() {
	url = baseurl + "system/backup";
	UX_showspin();
	sendRequest(url, "GET", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				const devices = xmlhttp.responseText;
				const content = new Blob([devices], { type: 'text/plain' });
				let url = window.URL.createObjectURL(content);
				// download the device json file
				const link = document.createElement('a');
				link.href = url;
				let date = new Date()
				const month = date.getMonth() + 1
				const datestr = date.getFullYear().toString() + "_" + month.toString() + "_" + date.getDate().toString() + "_" + date.getHours().toString() + "_" + date.getMinutes().toString();
				const filename = datestr + '_backup.json';
				link.setAttribute('download', filename);
				document.body.appendChild(link); // Required for FireFox
				link.click();
				UX_flashsuccess("Backup completed")
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
			UX_hidespin();
		}
	});
}

var selectFile = function () {
	document.getElementById("restoreFile").click();
}

var restore = function () {
	let selection = document.getElementById("restoreFile");
	if ('files' in selection) {
		if (selection.files.length < 1 || selection.files.length > 1) {
			UX_flashinfo("Select one file");
			UX_resetfile();
		} else {
			let file = selection.files[0];
			file.text().then(text => {
				let body = JSON.parse(text);
				url = baseurl + "system/restore";
				UX_showspin();
				sendRequest(url, "POST", body, null, null, function () {
					if (xmlhttp.readyState == 4) {
						if (xmlhttp.status == 200) {
							UX_flashsuccess("Restore completed");
						} else {
							UX_flasherror(xmlhttp.responseText);
						}
						UX_resetfile();
						UX_hidespin();
					}
				});

			})
		}
	}
}

/*
*
* Purge
*
*/
var clear_settings = function () {
	url = baseurl + "system/purge/settings";
	sendRequest(url, "PUT", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Settings cleared");
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}
var clear_metadata = function () {
	url = baseurl + "system/purge/metadata";
	sendRequest(url, "PUT", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Metadata cleared");
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}
var clear_configuration = function () {
	url = baseurl + "system/purge/configuration";
	sendRequest(url, "PUT", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Configuration cleared");
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}
var clear_all = function () {
	url = baseurl + "system/purge";
	sendRequest(url, "PUT", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("System cleared");
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

/*
*
*	Users
*
*/
function getUsers() {
	url = baseurl + "users";
	sendRequest(url, "GET", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				users = JSON.parse(xmlhttp.responseText);
				UX_updateUsers();
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

function addUser() {
	newuser = document.getElementById("newuserid").value;
	email = document.getElementById("email").value;
	pwd1 = document.getElementById("newuserpwd").value;
	pwd2 = document.getElementById("confuserpwd").value;
	if (pwd1 != pwd2) {
		UX_flasherror("Passwords do not match!")
		return
	}
	temp = newuser + ":" + pwd1;
	temp1 = btoa(temp);
	credheader = "Basic " + temp1;
	body = { "email": email };
	url = baseurl + "users"
	sendRequest(url, "POST", body, "Authorization", credheader, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("User added");
				getUsers();
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
			document.getElementById("userModal").style.display = "none";;
		}
	});
}

function chgEmail() {
	userid = document.getElementById("emailuserid").value;
	email = document.getElementById("chguseremail").value;
	url = baseurl + "users/email?userid=" + userid;
	body = { "email": email }
	sendRequest(url, "PUT", body, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Email changed");
				getUsers();
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
			document.getElementById("emailModal").style.display = "none";;
		}
	});

}

function chgPwd() {
	userid = document.getElementById("chguserpwduser").value;
	pwd1 = document.getElementById("chguserpwd").value;
	pwd2 = document.getElementById("confchgpwd").value;
	if (pwd1 != pwd2) {
		UX_flasherror("Passwords do not match!")
		return
	}
	temp = userid + ":" + pwd1;
	temp1 = btoa(temp);
	credheader = "Basic " + temp1;
	url = baseurl + "users/password?userid=" + userid;
	sendRequest(url, "PUT", null, "Authorization", credheader, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Password changed");
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
			document.getElementById("pwdModal").style.display = "none";;
		}
	});
}

var delUser = function () {
	userid = actionId;
	url = baseurl + "users?userid=" + userid;
	sendRequest(url, "DELETE", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("User deleted");
				getUsers();
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
			document.getElementById("pwdModal").style.display = "none";
		}
	});
}

/*
*
*	Uploads
*
*/
function getDevices() {
	url = baseurl + "devices";
	sendRequest(url, "GET", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				devices = JSON.parse(xmlhttp.responseText);
				UX_updateDevices();
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

function setupUpload(devuuid) {
	deviceuuid = devuuid;
	document.getElementById("uploadclicker").click();
}

function getFolderStats(devcount, callback) {
	devuuid = document.getElementById("devuuid"+devcount).innerHTML
	url = baseurl + "devices/folders/stats?uuid=" + devuuid;
	sendRequest(url, "GET", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				stats = JSON.parse(xmlhttp.responseText);
				callback(devcount, stats);
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

function restoreFiles(devuuid, devcount) {
	url = baseurl + "devices/folders/restore?uuid=" + devuuid;
	sendRequest(url, "PUT", null, null, null, function () {
		if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
				UX_flashsuccess("Restore completed");
				UX_updateStats(devcount);
			} else {
				UX_flasherror(xmlhttp.responseText);
			}
		}
	});
}

function doUpload() {
	let selection = document.getElementById("uploadImages");
	if ('files' in selection) {
		if (selection.files.length < 1) {
			UX_flashinfo("Select at least one file");
			UX_resetupload();
		} else {
			let body = new FormData();
			for (let i = 0; i < selection.files.length; i++) {
				body.append("file", selection.files[i])
			}
			url = baseurl + "devices/images?uuid=" + deviceuuid;
			UX_showspin();
			sendFormData(url, "POST", body, function () {
				if (xmlhttp.readyState == 4) {
					if (xmlhttp.status == 200) {
						UX_flashsuccess("Upload completed");
					} else {
						UX_flasherror(xmlhttp.responseText);
					}
					UX_resetupload();
					UX_hidespin();
				}
			});
		}
	}
}

function doDragUpload(files, uuid, type) {
	let body = new FormData();
	url = baseurl + "devices/images?uuid=" + uuid;
	let uploadable = false;
	if (type == "videofolder") {
		for (let i = 0; i < files.length; i++) {
			if (files[i].type.startsWith("video") || files[i].endsWith(".zip")) {
				body.append("file", files[i])
				uploadable = true;
			} else {
				UX_flashwarn(files[i].name + " " + files[i].type + "is not a video file and will not be uploaded");
			}
		}
	} else if (type == "folder") {
		for (let i = 0; i < files.length; i++) {
			if (files[i].type.startsWith("image") || files[i].type == "application/x-zip-compressed") {
				body.append("file", files[i])
				uploadable = true;
			} else {
				UX_flashwarn(files[i].name + " " + files[i].type + "is not an image file and will not be uploaded");
			}
		}
	} else {
		UX_flasherror("Unsupported type: " + type);
		return
	}
	if (uploadable) {
		UX_showspin();
		sendFormData(url, "POST", body, function () {
			if (xmlhttp.readyState == 4) {
				if (xmlhttp.status == 200) {
					UX_flashsuccess("Upload completed");
				} else {
					UX_flasherror(xmlhttp.responseText);
				}
				UX_resetupload();
				UX_hidespin();
			}
		});
	}
}
/*
*
*	Service Routines
*
*/
function init() {
	UX_init();
}

function executeAction() {
	action();
	UX_closevalidate();
}

function sendRequest(url, method, body, custheader, headerval, callback) {
	xmlhttp = new XMLHttpRequest();

	xmlhttp.onreadystatechange = callback;
	xmlhttp.open(method, url, true);
	xmlhttp.setRequestHeader("Content-Type", "application/json");
	xmlhttp.setRequestHeader("mvie-controller", authtoken);
	if (custheader != null) {
		xmlhttp.setRequestHeader(custheader, headerval);
	}
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

function sendFormData(url, method, formData, callback) {
	xmlhttp = new XMLHttpRequest();

	xmlhttp.onreadystatechange = callback;
	xmlhttp.open(method, url, true);
	//xmlhttp.setRequestHeader("Content-Type", "multipart/form-data");
	xmlhttp.setRequestHeader("mvie-controller", authtoken);
	if (method != "GET" && method != "DELETE") {
		xmlhttp.send(formData);
	} else {
		xmlhttp.send();
	}
}

function parseParamsToObject(aQueryStr, delimiter) {
	var nvps = aQueryStr.split(delimiter);
	var nvs = {}
	for (i in nvps) {
		nv = nvps[i].split("=");
		nvs[nv[0].trim()] = nv[1].trim();
	}
	return nvs;
}

