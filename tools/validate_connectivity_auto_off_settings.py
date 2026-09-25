#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"
SETTINGS = "{http://schemas.android.com/apk/res-auto}"

CONTROLLER = ROOT / "src/com/android/settings/network/ConnectivityAutoOffPreferenceController.java"
ARRAYS = ROOT / "res/values/evolution_arrays.xml"
WIFI_XML = ROOT / "res/xml/network_provider_settings.xml"
BT_XML = ROOT / "res/xml/bluetooth_screen.xml"

EXPECTED_VALUES = [
    "0", "15000", "30000", "60000", "120000", "300000",
    "600000", "1800000", "3600000", "7200000", "14400000", "28800000",
]
EXPECTED_CONTROLLER = "com.android.settings.network.ConnectivityAutoOffPreferenceController"

def fail(message: str) -> None:
    raise SystemExit(message)

def parse(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        fail(f"Unable to parse {path}: {exc}")

def find_pref(root: ET.Element, key: str) -> ET.Element:
    for node in root.iter():
        if node.attrib.get(ANDROID + "key") == key:
            return node
    fail(f"Missing preference: {key}")

arrays = parse(ARRAYS)
values = None
entries = None
for node in arrays:
    name = node.attrib.get("name")
    if name == "custom_timeout_values":
        values = [(item.text or "").strip() for item in node if item.tag == "item"]
    elif name == "custom_timeout_entries":
        entries = [(item.text or "").strip() for item in node if item.tag == "item"]

if values != EXPECTED_VALUES:
    fail(f"custom_timeout_values mismatch: {values}")
if entries is None or len(entries) != len(EXPECTED_VALUES):
    fail("custom_timeout_entries must match custom_timeout_values length")

for xml_path, key in (
    (WIFI_XML, "wifi_auto_off_timeout"),
    (BT_XML, "bluetooth_auto_off_timeout"),
):
    pref = find_pref(parse(xml_path), key)
    if pref.attrib.get(SETTINGS + "controller") != EXPECTED_CONTROLLER:
        fail(f"{key}: wrong controller")
    if pref.attrib.get(ANDROID + "entries") != "@array/custom_timeout_entries":
        fail(f"{key}: wrong entries array")
    if pref.attrib.get(ANDROID + "entryValues") != "@array/custom_timeout_values":
        fail(f"{key}: wrong values array")
    if pref.attrib.get(ANDROID + "defaultValue") != "0":
        fail(f"{key}: default must be disabled")
    if pref.attrib.get(ANDROID + "persistent") != "false":
        fail(f"{key}: preference must not persist locally")

controller = CONTROLLER.read_text(encoding="utf-8")
for token in (
    'KEY_WIFI_AUTO_OFF_TIMEOUT = "wifi_auto_off_timeout"',
    'KEY_BLUETOOTH_AUTO_OFF_TIMEOUT = "bluetooth_auto_off_timeout"',
    'TIMEOUT_MIN = 15_000L',
    'TIMEOUT_MAX = 8 * 60 * 60 * 1000L',
    'PackageManager.FEATURE_WIFI',
    'PackageManager.FEATURE_BLUETOOTH',
    'Settings.Global.putLong(',
    'timeout < TIMEOUT_MIN || timeout > TIMEOUT_MAX',
):
    if token not in controller:
        fail(f"Controller invariant missing: {token}")

print("Connectivity Auto-off Settings validation passed")
