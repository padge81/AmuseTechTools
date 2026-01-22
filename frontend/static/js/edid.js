// ==============================
// Global EDID state
// ==============================
let lastEdidHex = null;
let currentView = "binary"; // "binary" | "decoded"


// ==============================
// Helpers
// ==============================
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

            connectors.forEach(connector => {
                const opt = document.createElement("option");
                opt.value = connector;
                opt.text = connector;
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

    if (!port || !output) {
        console.error("EDID UI elements missing");
        return;
    }

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

            // 🔍 MATCH CHECK — FIXED
            return fetch("/edid/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ edid_hex: lastEdidHex })
            });
        })
        .then(res => res?.json())
        .then(result => {
            if (!result) return;
            renderMatch(result.matches);
        })
        .catch(err => {
            setStatus("Error");
            output.innerText = err.toString();
        });
}


// ==============================
// Match rendering
// ==============================
function renderMatch(matches) {
    const matchDiv = getEl("match");
    if (!matchDiv) return;

    if (!matches || matches.length === 0) {
        matchDiv.innerText = "❌ No matching EDID found";
        return;
    }

    matchDiv.innerHTML =
        "✔ Matching EDID(s):<br>" +
        matches.map(m => `• ${m.filename}`).join("<br>");
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

    output.innerText =
        currentView === "binary"
            ? formatHexEdid(lastEdidHex)
            : decodeEdidPlaceholder();
}


// ==============================
// Reset
// ==============================
function resetView() {
    lastEdidHex = null;
    currentView = "binary";

    if (getEl("output")) getEl("output").innerText = "";
    if (getEl("match")) getEl("match").innerText = "";
    setStatus("Idle");

    const binaryRadio =
        document.querySelector("input[name='viewMode'][value='binary']");
    if (binaryRadio) binaryRadio.checked = true;
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


// ==============================
// Init
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    loadConnectors();
});
