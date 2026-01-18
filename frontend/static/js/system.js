function systemAction(action) {
    fetch(`/system/${action}`, {
        method: "POST"
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Request failed");
        }
        return response.json();
    })
    .then(data => {
        alert(data.message || "Command sent");
    })
    .catch(err => {
        alert("Request failed");
        console.error(err);
    });
}
