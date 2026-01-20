function setStatus(text) {
    document.getElementById("status").innerText = text;
}

function readEdid() {
    setStatus("Reading EDID...");

    fetch("/edid/read?connector=card0-HDMI-A-1")
    .then(res => res.json())
    .then(data => {
        console.log("EDID READ RESPONSE:", data);
    })
    .catch(err => {
        console.error("EDID READ ERROR:", err);
    });
            if (!data.ok) {
                throw new Error(data.error);
            }

            document.getElementById("output").innerText =
                data.edid_hex.match(/.{1,32}/g).join("\n");

            if (data.matches.length > 0) {
                document.getElementById("match").innerText =
                    "✔ Match: " + data.matches[0].filename;
            } else {
                document.getElementById("match").innerText =
                    "❌ No match found";
            }

            setStatus("Read OK");
        })
        .catch(err => {
            setStatus("Error");
            alert(err.message);
        });
}

function resetView() {
    document.getElementById("output").innerText = "";
    document.getElementById("match").innerText = "";
    setStatus("Idle");
}
