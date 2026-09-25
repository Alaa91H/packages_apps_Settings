#!/usr/bin/env python3
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
SETTINGS_NS = "http://schemas.android.com/apk/res-auto"
AKEY = f"{{{ANDROID_NS}}}key"
AENTRIES = f"{{{ANDROID_NS}}}entries"
AENTRY_VALUES = f"{{{ANDROID_NS}}}entryValues"
SCONTROLLER = f"{{{SETTINGS_NS}}}controller"

ROOT = Path(__file__).resolve().parents[1]

def fail(message: str) -> None:
    raise SystemExit(message)

def parse(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        fail(f"Unable to parse {path}: {exc}")

def read(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")

def resource_items(path: Path, name: str) -> list[str]:
    root = parse(path)
    for child in root:
        if child.attrib.get("name") == name:
            return [(item.text or "").strip() for item in child if item.tag == "item"]
    fail(f"Missing array {name} in {path}")

parser = argparse.ArgumentParser()
parser.add_argument("--evolver-root", required=True, type=Path)
args = parser.parse_args()
evolver = args.evolver_root.resolve()

settings_xml = ROOT / "res/xml/battery_saver_settings.xml"
root = parse(settings_xml)
nodes = {node.attrib[AKEY]: node for node in root.iter() if AKEY in node.attrib}

expected = {
    "low_power_disable_aod": (
        "org.evolution.settings.battery.BatterySaverSwitchPreferenceController", None, None
    ),
    "low_power_cpu_limit_percent": (
        "org.evolution.settings.battery.BatterySaverLevelPreferenceController",
        "@array/battery_saver_cpu_limit_entries",
        "@array/battery_saver_cpu_limit_values",
    ),
    "low_power_brightness_reduction": (
        "org.evolution.settings.battery.BatterySaverLevelPreferenceController",
        "@array/battery_saver_brightness_reduction_entries",
        "@array/battery_saver_brightness_reduction_values",
    ),
    "low_power_disable_5g": (
        "org.evolution.settings.battery.BatterySaverSwitchPreferenceController", None, None
    ),
    "low_power_force_dark": (
        "org.evolution.settings.battery.BatterySaverSwitchPreferenceController", None, None
    ),
    "low_power_screen_timeout": (
        "org.evolution.settings.battery.BatterySaverLevelPreferenceController",
        "@array/battery_saver_screen_timeout_entries",
        "@array/battery_saver_screen_timeout_values",
    ),
}

for key, (controller, entries, values) in expected.items():
    node = nodes.get(key)
    if node is None:
        fail(f"battery_saver_settings.xml missing preference: {key}")
    if node.attrib.get(SCONTROLLER) != controller:
        fail(
            f"{key}: controller mismatch: "
            f"{node.attrib.get(SCONTROLLER)!r} != {controller!r}"
        )
    if entries is not None and node.attrib.get(AENTRIES) != entries:
        fail(f"{key}: entries mismatch")
    if values is not None and node.attrib.get(AENTRY_VALUES) != values:
        fail(f"{key}: entryValues mismatch")

level_path = evolver / "src/org/evolution/settings/battery/BatterySaverLevelPreferenceController.java"
switch_path = evolver / "src/org/evolution/settings/battery/BatterySaverSwitchPreferenceController.java"
arrays_path = evolver / "res/values/battery_saver_arrays.xml"

level = read(level_path)
switches = read(switch_path)

for key in (
    "low_power_cpu_limit_percent",
    "low_power_brightness_reduction",
    "low_power_screen_timeout",
):
    if f'"{key}"' not in level:
        fail(f"Evolver level controller does not define Settings key: {key}")

for key in (
    "low_power_disable_aod",
    "low_power_disable_5g",
    "low_power_force_dark",
):
    if f'"{key}"' not in switches:
        fail(f"Evolver switch controller does not define Settings key: {key}")

expected_values = {
    "battery_saver_cpu_limit_values": ["-1", "60", "50", "40", "30", "20", "10"],
    "battery_saver_brightness_reduction_values": ["-1", "10", "20", "30", "40", "50"],
    "battery_saver_screen_timeout_values": ["-1", "15000", "30000"],
}
for name, expected_items in expected_values.items():
    actual = resource_items(arrays_path, name)
    if actual != expected_items:
        fail(f"Evolver {name} mismatch: expected {expected_items}, got {actual}")

if "PackageManager.FEATURE_TELEPHONY" not in switches:
    fail("5G Battery Saver preference must remain telephony-capability gated")

if "new File(CPUFREQ_DIR).isDirectory()" not in level:
    fail("CPU Battery Saver preference must remain cpufreq-capability gated")

print("Settings/Evolver Battery Saver contract validation passed")
