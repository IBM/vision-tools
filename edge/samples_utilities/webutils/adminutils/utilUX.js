var login;
var logout;
var status;
var backup;
var purge;
var user;
var flashcontainer;
var actionId;
var action;


function UX_init() {
	flashcontainer = document.createElement("div");
	flashcontainer.className = "flash_container";
	document.body.append(flashcontainer);
	UX_setLoggedOut();
	UX_status();
	baseurl = "https://" + location.host + "/api/v1/";
}

function UX_flashsuccess(message) {
	var flash = document.createElement("div");
	flash.classList.add("success");
	flash.innerHTML = message;
	setTimeout(function () {
		flash.remove();
	}, 5000);
	UX_flashcommon(flash);
}

function UX_flasherror(message) {
	var flash = document.createElement("div");
	flash.classList.add("error");
	flash.innerHTML = message;
	UX_flashcommon(flash);
}

function UX_flashwarn(message) {
	var flash = document.createElement("div");
	flash.classList.add("warn");
	flash.innerHTML = message;
	UX_flashcommon(flash);
}

function UX_flashinfo(message) {
	var flash = document.createElement("div");
	flash.classList.add("info");
	flash.innerHTML = message;
	setTimeout(function () {
		flash.remove();
	}, 5000);
	UX_flashcommon(flash);
}

function UX_flashcommon(flash) {
	flash.classList.add("flash");
	flash.addEventListener("click", function () {
		flash.remove();
	});
	flashcontainer.append(flash)
}

function UX_flash(message, type, timeout) {
	var flash = document.createElement("div");
	flash.classList.add("flash");
	flash.classList.add(type);
	flash.innerHTML = message;
	if (timeout != null) {
		setTimeout(function () {
			flash.remove();
		}, timeout);
	}
	flash.addEventListener("click", function () {
		flash.remove();
	});
	flashcontainer.append(flash)
}

function UX_setLoggedIn() {
	document.getElementById("login").style.display = "none"
	document.getElementById("logout").style.display = "inline-block"
}

function UX_setLoggedOut() {
	document.getElementById("login").style.display = "inline-block"
	document.getElementById("logout").style.display = "none"
}

function UX_status() {
	document.getElementById("status").classList.add("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "block"
	document.getElementById("backupdiv").style.display = "none"
	document.getElementById("purgediv").style.display = "none"
	document.getElementById("userdiv").style.display = "none"
	document.getElementById("uploaddiv").style.display = "none"
}
function UX_backup() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.add("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none"
	document.getElementById("backupdiv").style.display = "block"
	document.getElementById("purgediv").style.display = "none"
	document.getElementById("userdiv").style.display = "none"
	document.getElementById("uploaddiv").style.display = "none"
}
function UX_purge() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.add("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none"
	document.getElementById("backupdiv").style.display = "none"
	document.getElementById("purgediv").style.display = "block"
	document.getElementById("userdiv").style.display = "none"
	document.getElementById("uploaddiv").style.display = "none"
}
function UX_user() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.add("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none"
	document.getElementById("backupdiv").style.display = "none"
	document.getElementById("purgediv").style.display = "none"
	document.getElementById("userdiv").style.display = "block"
	document.getElementById("uploaddiv").style.display = "none"
	getUsers();
}
function UX_images() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.add("selected");
	document.getElementById("statusdiv").style.display = "none"
	document.getElementById("backupdiv").style.display = "none"
	document.getElementById("purgediv").style.display = "none"
	document.getElementById("userdiv").style.display = "none"
	document.getElementById("uploaddiv").style.display = "block"
	getDevices()
}

function UX_updateStatus(leading, message, trailing) {
	let output = message;
	if (leading) {
		output = "\n" + output;
	}
	if (trailing) {
		output = output + "\n";
	}
	newstatus = output + document.getElementById("statustext").innerHTML;
	document.getElementById("statustext").innerHTML = newstatus;

}

function UX_updateUsers() {
	usertab = document.getElementById("usertable");
	rowcount = usertab.rows.length
	for (i = 1; i < rowcount; i++) {
		usertab.deleteRow(1);
	}
	for (i = 0; i < users.length; i++) {
		row = usertab.insertRow(i + 1);
		//row.className = ("utr");
		cell1 = row.insertCell(0);
		cell2 = row.insertCell(1);
		cell3 = row.insertCell(2);
		cell1.innerHTML = users[i].userid;
		cell2.innerHTML = users[i].email;
		deluser = "<button type=\"button\" class=\"tightbutton\" onclick=\"UX_validate('delete the user',delUser,'";
		deluser += users[i].userid;
		deluser += "');\" >Delete User</button>"
		chgemail = "<button type=\"button\" class=\"tightbutton\" onclick=\"UX_emailModal('";
		chgemail += users[i].userid;
		chgemail += "');\" >Change Email</button>"
		chgpwd = "<button type=\"button\" class=\"tightbutton\" onclick=\"UX_pwdModal('";
		chgpwd += users[i].userid;
		chgpwd += "');\" >Change Password</button>"
		cell3.innerHTML = deluser + chgemail + chgpwd;
	}
}

function UX_userModal() {
	var modal = document.getElementById("userModal");
	var span = document.getElementById("closeAddUser");
	document.getElementById("newuserid").value = "";
	document.getElementById("email").value = "";
	document.getElementById("newuserpwd").value = "";
	document.getElementById("confuserpwd").value = "";
	span.onclick = function () {
		modal.style.display = "none";
	}
	modal.style.display = "block";
}

function UX_emailModal(userid) {
	var modal = document.getElementById("emailModal");
	var span = document.getElementById("closeEmail")
	document.getElementById("emailuserid").value = userid;
	document.getElementById("chguseremail").value = "";
	span.onclick = function () {
		modal.style.display = "none";
	}
	modal.style.display = "block";
}

function UX_pwdModal(userid) {
	var modal = document.getElementById("pwdModal");
	var span = document.getElementById("closeChgPwd")
	document.getElementById("chguserpwduser").value = userid;
	document.getElementById("chguserpwd").value = "";
	document.getElementById("confchgpwd").value = "";
	span.onclick = function () {
		modal.style.display = "none";
	}
	modal.style.display = "block";
}

function UX_deluserModal(userid) {
	var modal = document.getElementById("deluserModal");
	var span = document.getElementById("closeDelUser")
	document.getElementById("deluserid").value = userid;
	span.onclick = function () {
		modal.style.display = "none";
	}
	modal.style.display = "block";
}

function UX_resetfile() {
	document.getElementById("restoreFile").value = "";
}

function UX_resetupload() {
	document.getElementById("uploadImages").value = "";
}

function UX_updateDevices() {
	devicetab = document.getElementById("devicetable");
	rowcount = devicetab.rows.length
	for (i = 1; i < rowcount; i++) {
		devicetab.deleteRow(1);
	}
	devcount = 0;
	for (i = 0; i < devices.length; i++) {
		if (devices[i].type === "camera") {
			continue
		}
		devcount++;
		row = devicetab.insertRow(devcount);
		//row.className = ("utr");
		cell1 = row.insertCell(0);
		cell2 = row.insertCell(1);
		cell3 = row.insertCell(2);
		cell1content = devices[i].name + "<br><img id=\"drop" + devcount + "\" style='vertical-align:middle'";
		cell1content += " src=\"" + window.location.origin + devices[i].imageURL + "\" width=160 height=120>";
		cell1content += "<== Drop files to upload";
		cell1.innerHTML = cell1content;
		UX_setupDrop(devcount, devices[i].uuid, devices[i].type)
		cell2.innerHTML = devices[i].type;
		device_uuid = "<div id=\"devuuid" + devcount + "\" style='display:none'>" + devices[i].uuid + "</div>";
		folderstats = "<div><span id=\"folder" + devcount + "\"></span><br><span id=\"processed" + devcount + "\"></span></div>";
		refreshstats = "<button type=\"button\" class=\"tightbutton\" onclick=\"UX_updateStats(";
		refreshstats += devcount + ",function(){});\" >Refresh Stats</button><br>";
		restore = "<button type=\"button\" class=\"tightbutton\" onclick=\"restoreFiles('";
		restore += devices[i].uuid + "'," + devcount;
		restore += ");\">Restore Processed Files</button>";
		cell3.innerHTML = device_uuid + folderstats + refreshstats + restore;
	}
	statrowcount = devcount;
	currcount = 1;
	UX_updateNextStats();	
}

var currcount;
var statrowcount;

function UX_updateNextStats() {
	UX_updateStats(currcount, function(){
		currcount++;
		if (currcount <= statrowcount) {
			UX_updateNextStats();
		}
	});
}

function UX_updateStats(devcount, callback) {
	getFolderStats(devcount, function (row, stats) {
		folderspan = document.getElementById("folder" + row)
		processedspan = document.getElementById("processed" + row)
		folderspan.innerHTML = "Unprocessed: " + stats.unprocessed;
		processedspan.innerHTML = "Processed: " + stats.processed;
		callback()
	});
}

function UX_setupDrop(id, uuid, type) {
	dropid = "drop" + id
	dropzone = document.getElementById(dropid);
	dropzone.addEventListener("dragover", function (e) {
		e.preventDefault();
		e.stopPropagation();
	});
	dropzone.addEventListener("drop", function (e) {
		e.preventDefault();
		e.stopPropagation();
		doDragUpload(e.dataTransfer.files, uuid, type);
	});
}

function UX_validate(message, callback, id) {
	actionId = id;
	action = callback;
	document.getElementById("validateMessage").innerHTML = "<h4>Are you sure you want to " + message + "?</h4>"
	var modal = document.getElementById("validateModal");
	var span = document.getElementById("closeValidate");
	span.onclick = function () {
		modal.style.display = "none";
	}
	modal.style.display = "block";
}

function UX_closevalidate() {
	actionId = "";
	action = null;
	document.getElementById("validateMessage").innerHTML = ""
	document.getElementById("validateModal").style.display = "none"
}

function UX_showspin() {
	document.getElementById("spin").style.display = "block"
}

function UX_hidespin() {
	document.getElementById("spin").style.display = "none"
}