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
	document.getElementById("login").addEventListener("click", login);
	document.getElementById("logout").addEventListener("click", logout);
	document.getElementById("status").addEventListener("click", UX_status);
	document.getElementById("backup").addEventListener("click", UX_backup);
	document.getElementById("purge").addEventListener("click", UX_purge);
	document.getElementById("user").addEventListener("click", UX_user);
	document.getElementById("images").addEventListener("click", UX_images);
	document.getElementById("inspections").addEventListener("click", UX_inspections);
	document.getElementById("engineStatus").addEventListener("click", getEngineStatus);
	document.getElementById("backupbutton").addEventListener("click", backup);
	document.getElementById("restoreFile").addEventListener("change", restore);
	document.getElementById("restorebutton").addEventListener("click", function() {
		UX_validate('restore the system',function() {
			selectFile();
		},null);
	});
	document.getElementById("clearsettingsbutton").addEventListener("click", function() {
		UX_validate('clear system settings',function() {
			clear_settings();
		},null);
	});
	document.getElementById("clearmetadatabutton").addEventListener("click", function() {
		UX_validate('clear all metadata',function() {
			clear_metadata();
		},null);
	});
	document.getElementById("clearconfigsbutton").addEventListener("click", function() {
		UX_validate('clear all configurations',function() {
			clear_configuration();
		},null);
	});
	document.getElementById("clearsystembutton").addEventListener("click", function() {
		UX_validate('clear the system',function() {
			clear_all();
		},null);
	});
	document.getElementById("adduserbutton").addEventListener("click", UX_userModal);
	document.getElementById("uploadImages").addEventListener("change", doUpload);
	document.getElementById("uploadclicker").addEventListener("click", function() {
		document.getElementById('uploadImages').click();
	});
	document.getElementById("inspSelButton").addEventListener("click", selectAllInsp);
	document.getElementById("inspStartlButton").addEventListener("click", function() {
		selInspSetState(true);
	});
	document.getElementById("inspStopButton").addEventListener("click", function() {
		selInspSetState(false);
	});
	document.getElementById("inspClearButton").addEventListener("click", clearSelInsp);
	document.getElementById("addUser").addEventListener("click", addUser);
	document.getElementById("chgEmail").addEventListener("click", chgEmail);
	document.getElementById("chgPwd").addEventListener("click", chgPwd);
	document.getElementById("validated").addEventListener("click", executeAction);
	document.getElementById("cancel").addEventListener("click", UX_closevalidate);
	document.body.addEventListener("unload",logout);


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
	document.getElementById("inspections").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "block";
	document.getElementById("backupdiv").style.display = "none";
	document.getElementById("purgediv").style.display = "none";
	document.getElementById("userdiv").style.display = "none";
	document.getElementById("uploaddiv").style.display = "none";
	document.getElementById("inspectionsdiv").style.display = "none";
}
function UX_backup() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.add("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("inspections").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none";
	document.getElementById("backupdiv").style.display = "block";
	document.getElementById("purgediv").style.display = "none";
	document.getElementById("userdiv").style.display = "none";
	document.getElementById("uploaddiv").style.display = "none";
	document.getElementById("inspectionsdiv").style.display = "none";
}
function UX_purge() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.add("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("inspections").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none";
	document.getElementById("backupdiv").style.display = "none";
	document.getElementById("purgediv").style.display = "block";
	document.getElementById("userdiv").style.display = "none";
	document.getElementById("uploaddiv").style.display = "none";
	document.getElementById("inspectionsdiv").style.display = "none";
}
function UX_user() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.add("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("inspections").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none";
	document.getElementById("backupdiv").style.display = "none";
	document.getElementById("purgediv").style.display = "none";
	document.getElementById("userdiv").style.display = "block";
	document.getElementById("uploaddiv").style.display = "none";
	document.getElementById("inspectionsdiv").style.display = "none"
	getUsers();
}
function UX_images() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.add("selected");
	document.getElementById("inspections").classList.remove("selected");
	document.getElementById("statusdiv").style.display = "none";
	document.getElementById("backupdiv").style.display = "none";
	document.getElementById("purgediv").style.display = "none";
	document.getElementById("userdiv").style.display = "none";
	document.getElementById("uploaddiv").style.display = "block";
	document.getElementById("inspectionsdiv").style.display = "none";
	getDevices()
}
function UX_inspections() {
	document.getElementById("status").classList.remove("selected");
	document.getElementById("backup").classList.remove("selected");
	document.getElementById("purge").classList.remove("selected");
	document.getElementById("user").classList.remove("selected");
	document.getElementById("images").classList.remove("selected");
	document.getElementById("inspections").classList.add("selected");
	document.getElementById("statusdiv").style.display = "none";
	document.getElementById("backupdiv").style.display = "none";
	document.getElementById("purgediv").style.display = "none";
	document.getElementById("userdiv").style.display = "none";
	document.getElementById("uploaddiv").style.display = "none";
	document.getElementById("inspectionsdiv").style.display = "block";
	getInspections()
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
		deluser = "<button type=\"button\" class=\"tightbutton\" id=\"deluserbutton"
		deluser += i + "\" name=\"";
		deluser += users[i].userid + "\">Delete User</button>"
		chgemail = "<button type=\"button\" class=\"tightbutton\" id=\"chguseremailbutton"
		chgemail += i + "\" name=\"";
		chgemail += users[i].userid + "\">Change Email</button>"
		chgpwd = "<button type=\"button\" class=\"tightbutton\" id=\"chguserpwdbutton"
		chgpwd += i + "\" name=\"";
		chgpwd += users[i].userid + "\" >Change Password</button>"
		cell3.innerHTML = deluser + chgemail + chgpwd;
		document.getElementById("deluserbutton"+i).addEventListener("click", function() {
			UX_validate('delete the user',delUser,this.name);
		});
		document.getElementById("chguseremailbutton"+i).addEventListener("click", function() {
			UX_emailModal(this.name);
		});
		document.getElementById("chguserpwdbutton"+i).addEventListener("click", function() {
			UX_pwdModal(this.name);
		});
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
		refreshstats = "<button type=\"button\" class=\"tightbutton\" id=\"refreshstatsbutton" + devcount + "\" ";
		refreshstats += "name=\"" + devcount + "\" >Refresh Stats</button><br>";
		restore = "<button type=\"button\" class=\"tightbutton\" id=\"restorefilesbutton" + devcount + "\" ";
		restore += "name=\"" + devices[i].uuid + "\">Restore Processed Files</button>";
		cell3.innerHTML = device_uuid + folderstats + refreshstats + restore;
		document.getElementById("refreshstatsbutton"+devcount).addEventListener("click", function() {
			UX_updateStats(this.name, function(){});
		});
		document.getElementById("restorefilesbutton"+devcount).addEventListener("click", function() {
			restoreFiles(this.name, this.id.replace("restorefilesbutton",""));
		});
	}
	statrowcount = devcount;
	currcount = 1;
	UX_updateNextStats();
}

function UX_updateInspections() {
	insptab = document.getElementById("inspectiontable");
	rowcount = insptab.rows.length
	for (i = 1; i < rowcount; i++) {
		insptab.deleteRow(1);
	}
	devcount = 0;
	for (i = 0; i < inspections.length; i++) {
		devcount++;
		row = insptab.insertRow(devcount);
		//row.className = ("utr");
		cell1 = row.insertCell(0);
		cell2 = row.insertCell(1);
		cell3 = row.insertCell(2);
		cell4 = row.insertCell(3);
		cell5 = row.insertCell(4);
		cell6 = row.insertCell(5);
		cell7 = row.insertCell(6);
		cell8 = row.insertCell(7);
		cell9 = row.insertCell(8);
		var chk = document.createElement('input');
		chk.setAttribute('type', 'checkbox');
		chk.setAttribute('value', '');
		chk.setAttribute('id', 'inspcheck' + i);
		cell1.appendChild(chk);
		cell2.innerHTML = inspections[i].name;
		cell3.innerHTML = inspections[i].mode;
		cell4.innerHTML = inspections[i].enabled ? "enabled" : "disabled";
		cell5.innerHTML = inspections[i].stats.imagecnt;
		cell6.innerHTML = inspections[i].stats.pass;
		cell7.innerHTML = inspections[i].stats.fail;
		cell8.innerHTML = inspections[i].stats.inconclusive;
		cell9.innerHTML = inspections[i].stats.alerts;

	}
}

var currcount;
var statrowcount;

function UX_updateNextStats() {
	UX_updateStats(currcount, function () {
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