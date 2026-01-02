# EZVIZ Camera Connection Guide

This document explains how to find the necessary information from your EZVIZ app to connect to your security camera using the `camera_feed.py` script.

## Required Information

To connect to your EZVIZ camera, you'll typically need:

1. **Camera's IP address** (easiest method)
2. **Verification Code** (also called "Device Verification Code")
3. Optionally: Camera's Serial Number

## Finding Your Camera's Information in the EZVIZ App

### Method 1: Using the EZVIZ Mobile App

1. **Open the EZVIZ app** on your mobile device
2. **Login** to your account
3. **Select the camera** you want to connect to
4. **Tap the Settings icon** (usually a gear icon in the top-right corner)
5. **Find "Device Information"** or similarly named section
   - Here you can find the **Device Serial Number**
   - Note the **IP address** if shown
6. Look for **"Verification Code"** which is sometimes under:
   - "Device Information"
   - "Network Information"
   - "Advanced Settings"
   - "Device Version"

### Method 2: On the Camera or Packaging

1. **Check the camera body or base** - Many EZVIZ cameras have a QR code and information sticker
2. The sticker typically shows:
   - **Serial Number** (may be labeled as "SN" or "Device ID")
   - **Verification Code** (may be labeled as "VC" or "Verification Code")

### Method 3: Using Your Router

1. **Log in to your router's admin panel** (typically at 192.168.1.1 or 192.168.0.1)
2. **Find "Connected Devices"** or similarly named section
3. **Look for a device with EZVIZ in the name** or identify your camera by MAC address
4. **Note the IP address** assigned to the camera

## Using the Information with camera_feed.py

Once you have the necessary information, use the script with these parameters:

### Using IP Address (Recommended Method)
```
python camera_feed.py --ezviz --ip 192.168.1.X --verification-code ABCDEF
```

### Using Serial Number
```
python camera_feed.py --ezviz --camera-serial C12345678 --verification-code ABCDEF
```

## Troubleshooting

1. **Connection Errors**:
   - Ensure the camera and your computer are on the same network
   - Check that your verification code is entered correctly
   - Try using the HTTP protocol: `--protocol http`

2. **No Video Display**:
   - Try the lower resolution stream: `--stream-type sub`
   - Check your firewall settings to allow the connection

3. **Finding Local IP Address of Camera**:
   - In EZVIZ app: Device Settings > Network Information
   - Using a network scanner app like "Fing" or "IP Scanner"
   - From your router's connected devices list
