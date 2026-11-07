"""
Phone Mirror: scan a QR code with an Android phone and see its screen live on this computer.

How it works:
  1. This script shows a pairing QR code (the same one Android Studio uses).
  2. On the phone: Settings > Developer options > Wireless debugging > Pair device with QR code > scan.
  3. The script pairs over Wi-Fi with ADB, connects, and opens scrcpy, which shows the phone screen live.

Requirements:
  - Android 11+ phone with Developer options and Wireless debugging enabled
  - Phone and computer on the same Wi-Fi network
  - adb (Android platform-tools) and scrcpy installed and on your PATH
  - pip install qrcode[pil] zeroconf
"""

import secrets
import shutil
import subprocess
import sys
import threading
import time

import qrcode
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

PAIR_TYPE = "_adb-tls-pairing._tcp.local."
CONNECT_TYPE = "_adb-tls-connect._tcp.local."


class Finder(ServiceListener):
    """Collects mDNS services of one type as name -> (ip, port)."""

    def __init__(self, zc):
        self.zc = zc
        self.found = {}
        self.lock = threading.Lock()

    def _record(self, type_, name):
        info = self.zc.get_service_info(type_, name, timeout=3000)
        if info and info.parsed_addresses():
            with self.lock:
                self.found[name] = (info.parsed_addresses()[0], info.port)

    def add_service(self, zc, type_, name):
        self._record(type_, name)

    def update_service(self, zc, type_, name):
        self._record(type_, name)

    def remove_service(self, zc, type_, name):
        pass


def wait_for(zc, type_, match, timeout):
    """Wait until a service of type_ satisfies match(name, ip). Returns (ip, port)."""
    finder = Finder(zc)
    browser = ServiceBrowser(zc, type_, finder)
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            with finder.lock:
                items = list(finder.found.items())
            for name, (ip, port) in items:
                if match(name, ip):
                    return ip, port
            time.sleep(0.5)
    finally:
        browser.cancel()
    raise TimeoutError(f"Timed out waiting for {type_}")


def adb(*args):
    return subprocess.run(["adb", *args], capture_output=True, text=True)


def main():
    if not shutil.which("adb") or not shutil.which("scrcpy"):
        sys.exit("adb and scrcpy must both be installed and on your PATH.")

    service_name = "phonemirror-" + secrets.token_hex(3)
    password = "".join(secrets.choice("0123456789") for _ in range(6))
    payload = f"WIFI:T:ADB;S:{service_name};P:{password};;"

    qr = qrcode.QRCode(border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    qr.print_ascii(invert=True)  # QR code drawn right in the terminal
    qr.make_image().save("pair_qr.png")  # also saved as an image file
    print("QR code also saved as pair_qr.png in this folder.")
    print("Scan the QR code on your phone:")
    print("  Settings > Developer options > Wireless debugging > Pair device with QR code")
    print("Waiting for the phone...")

    zc = Zeroconf()
    try:
        # Step 1: pair. The pairing service advertises the name we put in the QR code.
        ip, port = wait_for(
            zc, PAIR_TYPE, lambda name, _ip: name.startswith(service_name), timeout=180
        )
        print(f"Found phone at {ip}:{port}, pairing...")
        result = adb("pair", f"{ip}:{port}", password)
        print(result.stdout.strip() or result.stderr.strip())
        if result.returncode != 0:
            sys.exit("Pairing failed. Check the code and try again.")

        # Step 2: connect. Wireless debugging advertises a connect service on the same IP.
        ip, port = wait_for(zc, CONNECT_TYPE, lambda _name, s_ip: s_ip == ip, timeout=60)
        result = adb("connect", f"{ip}:{port}")
        print(result.stdout.strip() or result.stderr.strip())
    finally:
        zc.close()

    # Step 3: show the screen live.
    print("Starting live view (close the scrcpy window to stop).")
    subprocess.run(["scrcpy", "--stay-awake", "--window-title", "Phone Mirror"])


if __name__ == "__main__":
    main()