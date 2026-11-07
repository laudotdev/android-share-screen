
# Phone Mirror

Mirror your Android phone's screen live on your computer by scanning a QR code. Built with Python using ADB and scrcpy.

## Requirements

- Android 11+ with Developer Options and Wireless Debugging enabled
- Phone and computer connected to the same Wi-Fi network
- [Android Platform Tools (ADB)](https://developer.android.com/tools/releases/platform-tools)
- [scrcpy](https://github.com/Genymobile/scrcpy)
- Python dependencies:

```bash
pip install "qrcode[pil]" zeroconf
```

## How to Use

1. Run the Python application.
2. A pairing QR code will appear on your computer.
3. On your Android phone, navigate to:
   `Settings > Developer options > Wireless debugging > Pair device with QR code`.
4. Scan the QR code displayed by the application.
5. The app automatically pairs and connects through ADB.
6. **scrcpy** launches and displays your phone's screen live.

## Notes

- Both devices must be connected to the same Wi-Fi network.
- Wireless Debugging must remain enabled.
- No USB cable is required.
