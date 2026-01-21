function setStatus(text) {
    document.getElementById("status").innerText = text;
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


function readEdid() {
    let lastEdidHex = null;
	let currentView = "binary";

	
	const port = document.getElementById("port").value;
    const output = document.getElementById("output");
    const status = document.getElementById("status");

    status.innerText = "Reading EDID...";
    output.innerText = "";

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
            output.innerText = formatHexEdid(data.edid_hex);
        })
        .catch(err => {
            status.innerText = "Error";
            output.innerText = err.toString();
        });
}

function switchView() {
    const selected = document.querySelector("input[name='viewMode']:checked");
    currentView = selected.value;
    renderView();
}

function renderView() {
    const output = document.getElementById("output");

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

function resetView() {
    lastEdidHex = null;
    document.getElementById("output").innerText = "";
    document.getElementById("status").innerText = "Idle";
}

