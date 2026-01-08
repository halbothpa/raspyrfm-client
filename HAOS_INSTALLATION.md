# RaspyRFM Installation Guide for Home Assistant OS (Raspberry Pi 4/5)

## Overview

This guide will help you install and configure the RaspyRFM integration on Home Assistant OS running on Raspberry Pi 4 or 5.

## Prerequisites

- **Home Assistant OS** installed on Raspberry Pi 4 or 5
- **RaspyRFM gateway** or compatible 433MHz RF gateway on your network
- Network access to your HAOS installation
- Basic knowledge of Home Assistant configuration

## Quick Installation

### Step 1: Download the Integration

1. Go to the [Releases page](https://github.com/halbothpa/raspyrfm-client/releases)
2. Download the latest `raspyrfm-X.X.X.zip` file

### Step 2: Install the Custom Component

**Option A: Using the Samba/SMB Share (Recommended)**

1. Enable the Samba add-on in Home Assistant if not already enabled
2. Connect to your Home Assistant via network share:
   - Windows: `\\homeassistant.local\config`
   - macOS: `smb://homeassistant.local/config`
   - Linux: `smb://homeassistant.local/config`
3. Create a `custom_components` folder if it doesn't exist
4. Extract the contents of the ZIP file into `config/custom_components/raspyrfm/`

**Option B: Using SSH/Terminal**

1. Enable SSH access via the SSH add-on
2. Connect to your Home Assistant:
   ```bash
   ssh root@homeassistant.local
   ```
3. Navigate to the config directory:
   ```bash
   cd /config
   mkdir -p custom_components
   cd custom_components
   ```
4. Extract the integration (if you've uploaded the ZIP file):
   ```bash
   unzip /config/raspyrfm-X.X.X.zip -d /config/custom_components/
   ```

### Step 3: Restart Home Assistant

1. Go to **Settings** → **System**
2. Click **Restart** → **Restart Home Assistant**
3. Wait for Home Assistant to restart (1-2 minutes)

### Step 4: Configure the Integration

1. Navigate to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "RaspyRFM"
4. Enter your gateway configuration:
   - **Host**: IP address of your RaspyRFM gateway (e.g., `192.168.1.100`)
   - **Port**: Gateway port (default: `49880`)
5. Click **Submit**

## Setting Up a RaspyRFM Gateway

If you don't have a gateway yet, you can set one up on a separate Raspberry Pi.

### Hardware Requirements

- Raspberry Pi (any model, but Pi 4/5 recommended for best performance)
- 433MHz RF transceiver module (e.g., RaspyRFM II from Seegel Systeme)
- SD card with Raspberry Pi OS
- Stable 5V power supply

### Software Installation

1. **Install Raspberry Pi OS** on your gateway Pi:
   ```bash
   # On the gateway Pi
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install the RaspyRFM software**:
   ```bash
   git clone https://github.com/Phunkafizer/RaspyRFM.git
   cd RaspyRFM
   sudo python3 setup.py install
   ```

3. **Configure and test**:
   ```bash
   # Start the gateway manually for testing
   python3 connair.py
   ```

4. **Set up auto-start** (optional but recommended):
   
   Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/raspyrfm.service
   ```
   
   Add the following content:
   ```ini
   [Unit]
   Description=RaspyRFM Gateway Service
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/RaspyRFM
   ExecStart=/usr/bin/python3 /home/pi/RaspyRFM/connair.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start the service:
   ```bash
   sudo systemctl enable raspyrfm.service
   sudo systemctl start raspyrfm.service
   sudo systemctl status raspyrfm.service
   ```

### Network Configuration

1. **Assign a static IP** to your gateway Pi (recommended)
2. Ensure the gateway is on the same network as your HAOS installation
3. Test connectivity from HAOS:
   ```bash
   ping <gateway-ip>
   ```
4. Ensure port 49880 is accessible (check firewall if needed)

## Using the Integration

### Accessing the RaspyRFM Panel

1. After installation, find **RaspyRFM** in your Home Assistant sidebar
2. Click to open the management panel

### Learning RF Signals

1. Click **Start Learning** in the panel
2. Press buttons on your RF remote controls or trigger your sensors
3. Captured signals will appear in the "Captured Signals" section
4. Click **Stop Learning** when done

### Creating Entities

1. In the form section, select the entity type:
   - **Switch**: On/Off devices
   - **Light**: Dimmable lights (if supported)
   - **Button**: Single-action buttons
   - **Binary Sensor**: Door/window sensors
   - **Sensor**: Temperature, humidity sensors

2. Enter a name for your device
3. Assign captured signals to actions (On, Off, etc.)
4. Click **Create** to add the entity

### Controlling Devices

Once created, your devices will appear in Home Assistant:
- Control them from the **Devices & Services** page
- Add them to Lovelace dashboards
- Use them in automations and scripts

## Troubleshooting

### Integration Won't Load

**Problem**: RaspyRFM doesn't appear in the integrations list

**Solutions**:
1. Verify files are in `/config/custom_components/raspyrfm/`
2. Check Home Assistant logs: **Settings** → **System** → **Logs**
3. Ensure you restarted Home Assistant after installation
4. Clear browser cache and refresh

### Cannot Connect to Gateway

**Problem**: "Cannot connect" error during setup

**Solutions**:
1. Verify gateway IP address is correct
2. Ensure gateway is powered on and running
3. Check network connectivity: `ping <gateway-ip>`
4. Verify port 49880 is open and not blocked by firewall
5. Ensure gateway and HAOS are on the same network/VLAN

### No Signals Captured

**Problem**: Learning mode doesn't capture any signals

**Solutions**:
1. Ensure the gateway is receiving power
2. Check RF module is properly connected to the gateway
3. Verify the remote/sensor uses 433MHz frequency
4. Try moving the remote closer to the gateway
5. Check gateway logs for errors

### Devices Not Responding

**Problem**: Created devices don't control physical devices

**Solutions**:
1. Verify the correct signals were captured
2. Test sending signals multiple times (RF can be unreliable)
3. Ensure physical devices are powered and in range
4. Check if devices need to be paired/learned with new codes
5. Verify no interference from other RF devices

### Performance Issues on Raspberry Pi

**Problem**: Slow response or high CPU usage

**Solutions**:
1. Use a quality power supply (5V, 2.5A minimum for Pi 4/5)
2. Ensure adequate cooling (heatsinks or fan)
3. Consider using a separate Pi for the gateway
4. Limit the number of learned signals (keep it under 100)
5. Check for other resource-intensive add-ons

## Advanced Configuration

### Multiple Gateways

You can set up multiple RaspyRFM gateways for larger homes:

1. Install each gateway on a separate Raspberry Pi
2. Add each gateway as a separate integration instance
3. Assign unique names to differentiate them

### Home Automation Examples

**Example 1: Turn on lights at sunset**
```yaml
automation:
  - alias: "Outdoor lights at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garden_lights
```

**Example 2: Temperature-based fan control**
```yaml
automation:
  - alias: "Auto fan control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.room_temperature
        above: 25
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.ceiling_fan
```

### Backup and Restore

Your RaspyRFM configuration is included in Home Assistant backups:

1. Go to **Settings** → **System** → **Backups**
2. Create a backup before major changes
3. Backups include all learned signals and entity configurations

## Getting Help

- **Documentation**: https://halbothpa.github.io/raspyrfm-client/
- **Manual**: [MANUAL.md](MANUAL.md)
- **Issues**: [GitHub Issues](https://github.com/halbothpa/raspyrfm-client/issues)
- **Home Assistant Community**: Search for RaspyRFM in the forums

## Version Information

- **Tested on**: Home Assistant OS 2024.1+
- **Compatible with**: Raspberry Pi 4 and Raspberry Pi 5
- **Python version**: 3.10+
- **Home Assistant version**: 2023.12+

## License

This integration is licensed under GPL-3.0. See [LICENSE](LICENSE) for details.

---

**Need more help?** Open an issue on GitHub or check the documentation at https://halbothpa.github.io/raspyrfm-client/
