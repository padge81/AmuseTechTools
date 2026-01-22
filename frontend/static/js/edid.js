// ==============================
// Global EDID state
// ==============================
let lastEdidHex = null;
let currentView = "binary"; // "binary" | "decoded"


// ==============================
// Helpers
// ==============================

function loadConnectors(isRefresh = false) {
    const portSelect = document.getElementById("port");
    const previous = portSelect.value;

    fetch("/edid/connectors")
        .then(res => res.json())
        .then(connectors => {
            portSelect.innerHTML = "";

            if (connectors.length === 0) {
                const opt = document.createElement("option");
                opt.text = "No EDID ports found";
                opt.disabled = true;
                portSelect.appendChild(opt);
                return;
            }

            connectors.forEach(connector => {
                const opt = document.createElement("option");
                opt.value = connector;
                opt.text = connector;
                portSelect.appendChild(opt);
            });

            // Restore previous selection if still valid
            if (isRefresh && connectors.includes(previous)) {
                portSelect.value = previous;
            }
        })
        .catch(err => {
            console.error("Connector load failed:", err);
        });
}



function getEl(id) {
    return document.getElementById(id);
}

function setStatus(text) {
    const status = getEl("status");
    if (status) status.innerText = text;
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
// EDID actions
// ==============================
function readEdid() {
    const port = document.getElementById("port").value;
    const output = document.getElementById("output");
    const status = document.getElementById("status");
    const matchDiv = document.getElementById("match");

    if (!output || !status) {
        console.error("EDID elements not present on this page");
        return;
    }

    status.innerText = "Reading EDID...";
    output.innerText = "";
    matchDiv.innerText = "";

    fetch(`/edid/read?connector=${port}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                status.innerText = "Error";
                output.innerText = data.error;
                return;
            }

            status.innerText = "EDID Read OK";
            lastEdidHex = data.edid_hex;

            // Render binary/decoded view
            renderView();

            // 🔍 MATCH CHECK
           fetch("/edid/match", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				connector: document.getElementById("port").value
			}),
})
                .then(res => res.json())
                .then(result => {
                    if (result.matched) {
                        const names = result.matches.map(m => m.filename).join(", ");
						console.log("MATCH RESPONSE:", data);
                        matchDiv.innerText = `✔ Match found: ${names}`;
                    } else {
                        matchDiv.innerText = "❌ No matching EDID found";
                    }
                })
                .catch(() => {
                    matchDiv.innerText = "⚠ Match check failed";
                });
        })
        .catch(err => {
            status.innerText = "Error";
            output.innerText = err.toString();
        });
}


function updateMatchDisplay(result) {
    const matchDiv = document.getElementById("match");
    const saveBtn = document.getElementById("saveBtn");

    if (result.matched) {
        const names = result.matches.map(m => m.filename).join(", ");
        matchDiv.innerText = `✔ Match found: ${names}`;
        saveBtn.disabled = true;
    } else {
        matchDiv.innerText = "❌ No matching EDID found";
        saveBtn.disabled = false;
    }
}

function resetView() {
    const output = getEl("output");
    const match = getEl("match");
    const status = getEl("status");

    // Clear stored state
    lastEdidHex = null;
    currentView = "binary";

    // Clear UI
    if (output) output.innerText = "";
    if (match) match.innerText = "";
    if (status) status.innerText = "Idle";

    // Reset radio buttons
    const binaryRadio = document.querySelector("input[name='viewMode'][value='binary']");
    if (binaryRadio) binaryRadio.checked = true;
}



// ==============================
// View handling
// ==============================
function switchView() {
    const selected = document.querySelector("input[name='viewMode']:checked");
    if (!selected) return;

    currentView = selected.value;
    renderView();
}

function renderView() {
    const output = getEl("output");
    if (!output) return;

    if (!lastEdidHex) {
        output.innerText = "";
        return;
    }

    if (currentView === "binary") {
        output.innerText = formatHexEdid(lastEdidHex);
    } else {
        output.innerText = decodeEdidPlaceholder();
    }
}


// ==============================
// Placeholder decode
// ==============================
function decodeEdidPlaceholder() {
    return (
        "Decoded EDID (coming next):\n\n" +
        "• Manufacturer: —\n" +
        "• Product Code: —\n" +
        "• Serial Number: —\n" +
        "• Resolution: —\n" +
        "• Refresh Rate: —\n"
    );
}

document.addEventListener("DOMContentLoaded", () => {
    loadConnectors();
});