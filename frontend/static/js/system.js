function systemAction(action) {
    fetch(`/system/${action}`, {
        method: "POST"
    })
    .then(r => {
        if (!r.ok) throw new Error("Request failed");
        return r.json();
    })
    .catch(err => alert(err));
}
