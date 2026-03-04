"""
Fusion 360 Script — WX-Level: Replace placeholder geometry with real STEP models

Prerequisites:
  1. Run wx_level_full_assembly.py first (creates placeholder geometry)
  2. All STEP files present in hardware/step_library/
  3. Run pressure_transducer.py in Fusion 360 and export as
     step_library/pressure_transducer.step

Run: Utilities → Scripts and Add-Ins → + → select this file → Run
"""

import adsk.core, adsk.fusion, os, traceback

# (step_filename, primary_body_for_positioning, all_bodies_to_delete)
SWAP_MAP = [
    # ICs
    ("esp32_s3_wroom1.step",   "ESP32-S3",          ["ESP32-S3", "ESP32_Antenna"]),
    ("ads1115_tssop10.step",   "ADS1115",           ["ADS1115"]),
    ("bme280_lga8.step",       "BME280",            ["BME280"]),
    ("rfm95w_sx1276.step",     "SX1276_LoRa",       ["SX1276_LoRa", "LoRa_Pad"]),
    ("sim7000g.step",          "SIM7000G",          ["SIM7000G"]),
    ("cn3791_sop8.step",       "CN3791",            ["CN3791"]),
    ("ap2112k_sot23.step",     "AP2112K",           ["AP2112K"]),

    # Resistors (all 0805 — same physical STEP, placed at each location)
    ("0805_resistor.step",     "R250ohm",           ["R250ohm"]),
    ("0805_resistor.step",     "R2_100k_BattHi",    ["R2_100k_BattHi"]),
    ("0805_resistor.step",     "R3_100k_BattLo",    ["R3_100k_BattLo"]),
    ("0805_resistor.step",     "R4_100k_SolHi",     ["R4_100k_SolHi"]),
    ("0805_resistor.step",     "R5_100k_SolLo",     ["R5_100k_SolLo"]),
    ("0805_resistor.step",     "R_I2C_SDA",         ["R_I2C_SDA"]),
    ("0805_resistor.step",     "R_I2C_SCL",         ["R_I2C_SCL"]),
    ("0805_resistor.step",     "Status_LED",        ["Status_LED"]),

    # Capacitors (all 0805)
    ("0805_capacitor.step",    "Cap_0",             ["Cap_0"]),
    ("0805_capacitor.step",    "Cap_1",             ["Cap_1"]),
    ("0805_capacitor.step",    "Cap_2",             ["Cap_2"]),
    ("0805_capacitor.step",    "Cap_3",             ["Cap_3"]),

    # Diode
    ("sod123_schottky.step",   "Schottky_Diode",    ["Schottky_Diode", "Schottky_Band"]),

    # Connectors
    ("sma_bulkhead.step",      "SMA_LoRa_Bulkhead", ["SMA_LoRa_Bulkhead"]),
    ("sma_bulkhead.step",      "SMA_LTE_Bulkhead",  ["SMA_LTE_Bulkhead"]),
    ("sma_antenna_whip.step",  "Antenna_LoRa",      ["Antenna_LoRa", "Antenna_LoRa_Tip"]),
    ("sma_antenna_whip.step",  "Antenna_LTE",       ["Antenna_LTE", "Antenna_LTE_Tip"]),
    ("m12_cable_gland.step",   "Gland_Probe_Inner", ["Gland_Probe_Inner", "Gland_Probe_Nut"]),
    ("m12_cable_gland.step",   "Gland_Solar_Inner", ["Gland_Solar_Inner", "Gland_Solar_Nut"]),
    ("jst_ph_2pin.step",       "JST_Battery",       ["JST_Battery"]),

    # Power
    ("lipo_pouch_3.7v.step",   "LiPo_Battery",      ["LiPo_Battery", "Battery_Label"]),
    ("solar_panel_6v.step",    "Solar_Panel",
     ["Solar_Panel", "Solar_Cell_Row_0", "Solar_Cell_Row_1", "Solar_Cell_Row_2",
      "Solar_Cell_Row_3", "Solar_Cell_Row_4", "Solar_Cell_Row_5"]),

    # Sensor
    ("pressure_transducer.step", "Transducer_Body",
     ["Transducer_Body", "Transducer_Nose", "Transducer_Relief"]),
]


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    try:
        # Resolve step_library path (try relative first, then ask user)
        step_dir = None
        try:
            candidate = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..', '..', 'step_library'))
            if os.path.isdir(candidate):
                step_dir = candidate
        except Exception:
            pass

        if not step_dir:
            dlg = ui.createFolderDialog()
            dlg.title = "Select the 'step_library' folder"
            if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
                return
            step_dir = dlg.folder

        if not os.path.isdir(step_dir):
            ui.messageBox(f"step_library not found at:\n{step_dir}")
            return

        # Find the WX-Level assembly component
        asm_comp = None
        for i in range(root.occurrences.count):
            occ = root.occurrences.item(i)
            if "WX-Level" in occ.component.name:
                asm_comp = occ.component
                break

        if not asm_comp:
            ui.messageBox(
                "WX-Level assembly not found.\n"
                "Run wx_level_full_assembly.py first."
            )
            return

        import_mgr = app.importManager

        # Cache imported STEP components to avoid re-reading from disk
        # step_file -> {'comp': Component, 'center': (x,y,z), 'base_transform': Matrix3D, 'first_occ': Occurrence, 'first_used': bool}
        step_cache = {}

        def find_body(name):
            for i in range(asm_comp.bRepBodies.count):
                b = asm_comp.bRepBodies.item(i)
                if b.name == name:
                    return b
            return None

        def body_center(body):
            bb = body.boundingBox
            return (
                (bb.minPoint.x + bb.maxPoint.x) / 2,
                (bb.minPoint.y + bb.maxPoint.y) / 2,
                (bb.minPoint.z + bb.maxPoint.z) / 2,
            )

        def place_step(step_file, target):
            if step_file not in step_cache:
                path = os.path.join(step_dir, step_file)
                if not os.path.isfile(path):
                    return False

                before = root.occurrences.count
                opts = import_mgr.createSTEPImportOptions(path)
                import_mgr.importToTarget(opts, root)

                if root.occurrences.count <= before:
                    return False

                ref_occ = root.occurrences.item(root.occurrences.count - 1)
                bb = ref_occ.boundingBox
                center = (
                    (bb.minPoint.x + bb.maxPoint.x) / 2,
                    (bb.minPoint.y + bb.maxPoint.y) / 2,
                    (bb.minPoint.z + bb.maxPoint.z) / 2,
                )

                step_cache[step_file] = {
                    'comp': ref_occ.component,
                    'center': center,
                    'base_transform': ref_occ.transform.copy(),
                    'first_occ': ref_occ,
                    'first_used': False,
                }

            entry = step_cache[step_file]
            nc = entry['center']
            bt = entry['base_transform']
            old_t = bt.translation

            new_transform = bt.copy()
            new_transform.translation = adsk.core.Vector3D.create(
                old_t.x + (target[0] - nc[0]),
                old_t.y + (target[1] - nc[1]),
                old_t.z + (target[2] - nc[2]),
            )

            if not entry['first_used']:
                entry['first_occ'].transform = new_transform
                entry['first_used'] = True
            else:
                root.occurrences.addExistingComponent(entry['comp'], new_transform)

            return True

        swapped = []
        skipped = []

        for step_file, primary_name, delete_names in SWAP_MAP:
            primary = find_body(primary_name)
            if not primary:
                skipped.append(f"{primary_name} (body not found)")
                continue

            target = body_center(primary)

            for name in delete_names:
                b = find_body(name)
                if b:
                    b.deleteMe()

            if place_step(step_file, target):
                swapped.append(primary_name)
            else:
                skipped.append(f"{primary_name} ({step_file} missing)")

        msg = f"WX-Level STEP Swap Complete!\n\n"
        msg += f"Replaced: {len(swapped)} components\n"
        if skipped:
            msg += f"\nSkipped ({len(skipped)}):\n"
            for s in skipped:
                msg += f"  {s}\n"
        msg += (
            "\nRemaining placeholders (no STEP needed):\n"
            "  Enclosure, PCB, wiring, O-rings,\n"
            "  standoffs, screws, desiccant, vent cap\n"
            "\nSome parts may need manual orientation adjustment."
        )

        ui.messageBox(msg)

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
