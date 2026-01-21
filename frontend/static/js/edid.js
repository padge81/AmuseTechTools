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
// EDID actions
// ==============================
function readEdid() {
    const portEl = getEl("port");
    const output = getEl("output");
    const status = getEl("status");

    if (!portEl || !output || !status) {
        console.warn("EDID elements not present on this page");
        return;
    }

    setStatus("Reading EDID...");
    output.innerText = "";
    lastEdidHex = null;

    fetch(`/edid/read?connector=${portEl.value}`)
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
        })
        .catch(err => {
            setStatus("Error");
            output.innerText = err.toString();
        });
}


function resetView() {
    const output = getEl("output");
    if (!output) return;

    lastEdidHex = null;
    currentView = "binary";
    output.innerText = "";
    setStatus("Idle");
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
