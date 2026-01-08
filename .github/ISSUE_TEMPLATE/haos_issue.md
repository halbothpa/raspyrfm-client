---
name: HAOS Installation Issue
about: Report issues specific to Home Assistant OS installation on Raspberry Pi
title: "[HAOS] "
labels: haos, installation
---

**System Information**
- Raspberry Pi Model: [e.g., Raspberry Pi 4 Model B 8GB, Raspberry Pi 5 4GB]
- HAOS Version: [e.g., 12.0]
- Home Assistant Core Version: [e.g., 2024.1.5]
- RaspyRFM Integration Version: [e.g., 0.1.0 from release]

**Installation Method**
- [ ] Downloaded from GitHub Releases
- [ ] Manual installation via Samba
- [ ] Manual installation via SSH
- [ ] Other: [please specify]

**Issue Description**
A clear description of the installation or runtime issue.

**Steps Taken**
1. 
2. 
3. 

**Error Messages**
Please include any error messages from:
- Home Assistant logs (Settings → System → Logs)
- Configuration validation
- Integration setup

```
Paste error messages here
```

**Gateway Configuration**
- Gateway Type: [e.g., RaspyRFM II on separate Pi, ConnAir emulator]
- Gateway Location: [e.g., separate Raspberry Pi, same device]
- Gateway IP: [e.g., 192.168.1.100]
- Gateway Port: [e.g., 49880]
- Can ping gateway from HAOS: [Yes/No]

**Network Setup**
- Same subnet as HAOS: [Yes/No]
- Firewall enabled: [Yes/No]
- VLANs in use: [Yes/No]
- Network configuration: [any special routing, multiple interfaces, etc.]

**Files Checked**
- [ ] Files present in `/config/custom_components/raspyrfm/`
- [ ] `manifest.json` exists
- [ ] Frontend files exist in `frontend/` subdirectory
- [ ] Restarted Home Assistant after installation

**Attempted Solutions**
What have you already tried to fix this?
- 

**Screenshots**
If applicable, add screenshots of:
- File structure in `/config/custom_components/`
- Integration page in Home Assistant
- Error messages

**Additional Context**
Any other relevant information about your setup or the issue.
