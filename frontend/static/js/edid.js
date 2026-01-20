function setStatus(text) {
    document.getElementById("status").innerText = text;
}

function readEdid() {
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

            // Pretty-print hex (32 chars per line)
            const formatted = data.edid_hex
                .match(/.{1,32}/g)
                .join("\n");

            output.innerText = formatted;
        })
        .catch(err => {
            status.innerText = "Error";
            output.innerText = err.toString();
        });
}


 //   fetch("/edid/read?connector=card0-HDMI-A-1")
 //       .then(r => r.json())
 //       .then(data => {
 //           if (!data.ok) {
 //               throw new Error(data.error);
 //           }
//
 //           document.getElementById("output").innerText =
//                data.edid_hex.match(/.{1,32}/g).join("\n");
//
//            if (data.matches.length > 0) {
//                document.getElementById("match").innerText =
 //                   "✔ Match: " + data.matches[0].filename;
 //           } else {
 //               document.getElementById("match").innerText =
 //                   "❌ No match found";
 //           }
//
//            setStatus("Read OK");
 //       })
//        .catch(err => {
//           setStatus("Error");
 //           alert(err.message);
 //       });


function resetView() {
    document.getElementById("output").innerText = "";
    document.getElementById("match").innerText = "";
    setStatus("Idle");
}
