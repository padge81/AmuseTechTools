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
            fetch("/edid/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ edid_hex: lastEdidHex })
            })
                .then(res => res.json())
                .then(result => {
                    if (!matchDiv) return;

                    if (result.matches && result.matches.length) {
                        const names = result.matches.map(m => m.filename).join(", ");
                        matchDiv.innerText = `✔ Match found: ${names}`;
                    } else {
                        matchDiv.innerText = "❌ No matching EDID found";
                    }
                })
                .catch(() => {
                    if (matchDiv) matchDiv.innerText = "⚠ Match check failed";
                });
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
// Placeholder decode (backend-ready)
// ==============================
function decodeEdidPlaceholder() {
    return (
        "Decoded EDID\n\n" +
        "Manufacturer: —\n" +
        "Product Code: —\n" +
        "Serial Number: —\n" +
        "Week / Year: —\n" +
        "Extensions: —\n\n" +
        "(Full decode coming next)"
    );
}


// ==============================
// Init
// ==============================
document.addEventListener("DOMContentLoaded", () => {
    loadConnectors();
});
