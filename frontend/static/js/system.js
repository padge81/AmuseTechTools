function systemAction(action) {
    if (!confirm(`Are you sure you want to ${action.replace("_", " ")}?`)) {
        return;
    }

    fetch("/system/action", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ action: action })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            alert("Action executed: " + action);
        }
    })
    .catch(err => {
        alert("Request failed");
        console.error(err);
    });
}
