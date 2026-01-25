// ==============================
// Global EDID state
// ==============================
let lastEdidHex = null;
let currentView = "binary"; // "binary" | "decoded"
let usbScanResults = [];
let selectedPort = null;
let selectedFile = null;

// ==============================
// Helpers
// ==============================
function getEl(id) {
    return document.getElementById(id);
}

function setStatus(text) {
    const el = getEl("status");
    if (el) el.innerText = text;
}

function formatHexEdid(hexString) {
    let lines = [];
    let offset = 0;

    for (let i = 0; i < hexString.length; i += 32) {
        const chunk = hexString.slice(i, i + 32);
        const bytes = chunk.match(/.{1,2}/g).join(" ");
        lines.push(offset.toString(16).padStart(4, "0") + ": " + bytes);
        offset += 16;
    }

    return lines.join("\n");
}


// ==============================
// Connector handling
// ==============================
function loadConnectors(isRefresh = false) {
    const portSelect = getEl("port");
    if (!portSelect) return;

    const previous = portSelect.value;

    fetch("/edid/connectors")
        .then(res => res.json())
        .then(connectors => {
            portSelect.innerHTML = "";

            if (!connectors.length) {
                const opt = document.createElement("option");
                opt.text = "No EDID ports found";
                opt.disabled = true;
                portSelect.appendChild(opt);
                return;
            }

            connectors.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c;
                opt.text = c;
                portSelect.appendChild(opt);
            });

            if (isRefresh && connectors.includes(previous)) {
                portSelect.value = previous;
            }
        })
        .catch(err => console.error("Connector load failed:", err));
}


// ==============================
// EDID actions
// ==============================
function readEdid() {
    const port = getEl("port")?.value;
    const output = getEl("output");
    const matchDiv = getEl("match");

    if (!port || !output) return;

    setStatus("Reading EDID...");
    output.innerText = "";
    if (matchDiv) matchDiv.innerText = "";

    fetch(`/edid/read?connector=${port}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                setStatus("Error");
                output.innerText = data.error;
                return;
            }

            lastEdidHex = data.edid_hex;
            setStatus("EDID Read OK");

            renderView();

            // 🔍 Match check
            return fetch("/edid/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ edid_hex: lastEdidHex }),
            });
        })
        .then(res => {
            if (!res) return;
            return res.json();
        })
        .then(result => {
            if (!result) return;

            const matchDiv = getEl("match");
            const saveBtn = getEl("saveBtn");

            if (result.matches && result.matches.length > 0) {
                const names = result.matches.map(m => m.filename).join(", ");
                if (matchDiv) matchDiv.innerText = `✔ Match found: ${names}`;
                if (saveBtn) saveBtn.disabled = true;
            } else {
                if (matchDiv) matchDiv.innerText = "❌ No matching EDID found";
                if (saveBtn) saveBtn.disabled = false;
            }
        })
        .catch(err => {
            setStatus("Error");
            output.innerText = err.toString();
        });
}



function resetView() {
    lastEdidHex = null;
    currentView = "binary";

    const output = getEl("output");
    const match = getEl("match");

    if (output) output.innerText = "";
    if (match) match.innerText = "";

    setStatus("Idle");

    const binaryRadio = document.querySelector("input[name='viewMode'][value='binary']");
    if (binaryRadio) binaryRadio.checked = true;
}


// ==============================
// View handling  ✅ FIXED
// ==============================
function switchView() {
    const selected = document.querySelector("input[name='viewMode']:checked");
    if (!selected) return;

    currentView = selected.value;
    renderView();
}

function renderView() {
    const output = document.getElementById("output");
    if (!output) return;

    if (!lastEdidHex) {
        output.innerText = "";
        return;
    }

    if (currentView === "binary") {
        output.innerText = formatHexEdid(lastEdidHex);
        return;
    }

    // 🔍 DECODED VIEW (backend-driven)
    output.innerText = "Decoding EDID...";

    fetch("/edid/decode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ edid_hex: lastEdidHex }),
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                output.innerText = "Decode error:\n" + data.error;
                return;
            }
            output.innerText = data.decoded;
        })
        .catch(err => {
            output.innerText = "Decode failed:\n" + err.toString();
        });
}

// ==============================
// Save EDID
// ==============================
function saveEdid() {
    const input = document.getElementById("saveFilename");
    const saveBtn = document.getElementById("saveBtn");

    if (!input) return;

    let filename = input.value.trim();

    if (!filename) {
        alert("Please enter a filename");
        return;
    }

    // ❌ Reject filenames with dots unless it ends with .bin
    const dotCount = (filename.match(/\./g) || []).length;

    if (dotCount > 1 || (dotCount === 1 && !filename.endsWith(".bin"))) {
        alert("Filename may only contain one dot, and it must be .bin");
        return;
    }

    // ✅ Auto-add .bin if missing
    if (!filename.endsWith(".bin")) {
        filename += ".bin";
    }

    fetch("/edid/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            edid_hex: lastEdidHex,
            filename: filename,
        }),
    })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            alert(`Saved as ${data.filename}`);
            input.value = data.filename;
            if (saveBtn) saveBtn.disabled = true;
        })
        .catch(err => {
            alert("Save failed: " + err.toString());
        });
}

// ==============================
// USB IMPORT EXPORT
// ==============================
//Load USB Drives
function loadUsbDrives() {
    const sel = getEl("usbDrive");
    const status = getEl("usbStatus");
    if (!sel || !status) return;

    fetch("/usb/status")
        .then(r => r.json())
        .then(drives => {
            sel.innerHTML = "";

            if (!drives.length) {
                status.innerText = "No USB drives found";
                return;
            }

            drives.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d.path;   // ✅ MUST be string
                opt.textContent = d.name;
                sel.appendChild(opt);
            });

            status.innerText = "USB ready";
        })
        .catch(err => {
            console.error(err);
            status.innerText = "USB scan failed";
        });
}


//IMPORT

function importEdids() {
    const mount = getEl("usbDrive")?.value;
    const status = getEl("usbStatus");

    if (!mount) {
        alert("Please select a USB drive");
        return;
    }

    // 1️⃣ Preview
    fetch("/usb/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mount, dry_run: true })
    })
    .then(r => r.json())
    .then(summary => {
        const msg =
`Import from USB?

New files: ${summary.new}
Skipped (already exist): ${summary.skipped}

Proceed?`;

        if (!confirm(msg)) return;

        // 2️⃣ Commit
        return fetch("/usb/import", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mount, dry_run: false })
        });
    })
    .then(r => r?.json())
    .then(result => {
        if (!result) return;
        status.innerText = `Import complete: ${result.new} new, ${result.skipped} skipped`;
    })
    .catch(err => {
        console.error(err);
        status.innerText = "Import failed";
    });
}

//EXPORT

function exportEdids() {
    const mount = getEl("usbDrive")?.value;
    const status = getEl("usbStatus");

    if (!mount) {
        alert("Please select a USB drive");
        return;
    }

    // 1️⃣ Preview
    fetch("/usb/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mount, dry_run: true })
    })
    .then(r => r.json())
    .then(summary => {
        const msg =
`Export to USB?

New files: ${summary.new}
Skipped (already exist): ${summary.skipped}

Proceed?`;

        if (!confirm(msg)) return;

        // 2️⃣ Commit
        return fetch("/usb/export", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mount, dry_run: false })
        });
    })
    .then(r => r?.json())
    .then(result => {
        if (!result) return;
        status.innerText = `Export complete: ${result.new} new, ${result.skipped} skipped`;
    })
    .catch(err => {
        console.error(err);
        status.innerText = "Export failed";
    });
}

// ==============================
// Write to EDID device
// ==============================

//Load EDID File List
function loadEdidFiles() {
    const sel = getEl("edidFile");
    if (!sel) return;

    fetch("/edid/files")
        .then(r => r.json())
        .then(files => {
            sel.innerHTML = '<option value="">-- select EDID --</option>';
            files.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f;
                opt.text = f;
                sel.appendChild(opt);
            });
        });
}

//Track Selections
function onFileSelect() {
    selectedFile = getEl("edidFile").value || null;
    updateWriteButton();
}

// Modify readEdid() succes path
selectedPort = port;
updateWriteButton();

//Enable Logic
function updateWriteButton() {
    const btn = getEl("writeBtn");
    btn.disabled = !(selectedPort && lastEdidHex && selectedFile);
}

//Write Handler
function writeEdid() {
    const connector = document.getElementById("port").value;
    const filename = document.getElementById("edidFile").value;

    if (!connector || !filename) {
        alert("Select a connector and EDID file first");
        return;
    }

    if (!confirm(
        "WARNING:\n\n" +
        `Connector: ${connector}\n` +
        `EDID file: ${filename}\n\n` +
        "This will overwrite the EDID EEPROM.\n" +
        "A power cycle may be required to revert.\n\n" +
        "Proceed?"
    )) return;

    fetch("/edid/write", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            connector: connector,
            filename: filename,
            force: true
        })
    })
    .then(r => r.json())
	.then(res => {
		if (res.error) {
			alert(res.error);
			return;
		}

		const msg =
			"EDID written successfully!\n\n" +
			`Connector: ${res.connector}\n` +
			`I2C bus: ${res.bus}\n` +
			`Verified (I2C): ${res.verified_i2c ? "Yes" : "No"}\n` +
			`Verified (DRM): ${res.verified_drm ? "Yes" : "No"}`

		if (confirm(msg)) {
			// Trigger a fresh EDID read
			readEdid();
		}
	});
}

function navHome() {
    window.location.href = "/";
}

function navBack() {
    // For now: same behavior
    window.history.back();
    // Or: window.location.href = "/";
}

// ==============================
// Init
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    loadConnectors();
	loadUsbDrives();
	loadEdidFiles();
});
