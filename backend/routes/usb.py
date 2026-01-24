@app.route("/usb/status")
def usb_status():
    mounts = list_usb_mounts()
    result = []
    for m in mounts:
        result.append({
            "path": m,
            "name": os.path.basename(m),
            "read_only": is_read_only(m)
        })
    return jsonify(result)

@app.route("/usb/scan")
def usb_scan():
    mount = request.args.get("mount")
    if not mount or not os.path.isdir(mount):
        return jsonify({"error": "Invalid mount"}), 400

    usb_bins = [
        f for f in os.listdir(mount)
        if f.lower().endswith(".bin")
        and os.path.isfile(os.path.join(mount, f))
    ]

    local_hashes = {
        f: file_hash(os.path.join(SAVE_DIR, f))
        for f in os.listdir(SAVE_DIR)
        if f.lower().endswith(".bin")
    }

    files = []
    for f in usb_bins:
        usb_path = os.path.join(mount, f)
        usb_hash = file_hash(usb_path)
        exists = usb_hash in local_hashes.values()

        files.append({
            "name": f,
            "exists": exists
        })

    return jsonify(files)

@app.route("/usb/import", methods=["POST"])
def usb_import():
    data = request.json
    mount = data.get("mount")
    files = data.get("files", [])

    imported = []

    for f in files:
        src = os.path.join(mount, f)
        dst = os.path.join(SAVE_DIR, f)

        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            imported.append(f)

    return jsonify({"imported": imported})

@app.route("/usb/export", methods=["POST"])
def usb_export():
    data = request.json
    mount = data.get("mount")
    files = data.get("files", [])

    exported = []

    for f in files:
        src = os.path.join(SAVE_DIR, f)
        dst = os.path.join(mount, f)

        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
            exported.append(f)

    return jsonify({"exported": exported})