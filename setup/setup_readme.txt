--setup_sudo_perm--

sudo python3 setup/setup_sudo_perm.py

Expected output:

✔ Configuring sudo permissions for user: att
✍ Writing sudoers file...
🔍 Validating sudoers...
✔ Sudo permissions successfully installed

After this:
Your Flask backend can safely call system actions
No password prompts
No hacks
No broken sudo


---------------------------------------------------------
🛠️ Install modetest (correct package)

On Raspberry Pi OS:

sudo apt update
sudo apt install -y libdrm-tests


This provides:

modetest

other DRM debugging tools

Verify:

which modetest
modetest -v