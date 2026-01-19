function systemAction(action) {
    let message = "";

    switch (action) {
        case "exit_browser":
            message = "Are you sure you want to exit the browser?";
            break;
        case "reboot":
            message = "Are you sure you want to reboot the Raspberry Pi?";
            break;
        case "shutdown":
            message = "Are you sure you want to shut down the Raspberry Pi?";
            break;
        case "update":
            message = "Update from GitHub now?";
            break;
        default:
            return;
    }

    if (!confirm(message)) {
        return;
    }

    fetch(`/system/${action}`, {
        method: "POST"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Request failed");
        }
        return response.text();
    })
    .then(text => {
        alert(text);
    })
    .catch(err => {
        alert("Error: " + err.message);
    });
}
