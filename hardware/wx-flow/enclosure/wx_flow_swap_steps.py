"""
Fusion 360 Script — WX-Flow: Replace placeholder geometry with real STEP models

Prerequisites:
  1. Run wx_flow_full_assembly.py first (creates placeholder geometry)
  2. All STEP files present in hardware/step_library/
  3. Run pressure_transducer.py in Fusion 360 and export as
     step_library/pressure_transducer.step

Note: Probe custom parts (thermistors, heater coil, conductivity electrodes,
PT1000, EZO board, probe tube) stay as placeholders. To upgrade those, run
step_library/probe_custom_parts.py separately and manually position the output.

Run: Utilities → Scripts and Add-Ins → + → select this file → Run
"""

import adsk.core, adsk.fusion, os, traceback

# (step_filename, primary_body_for_positioning, all_bodies_to_delete)
SWAP_MAP = [
    # ── Controller Box ICs ──
    ("esp32_s3_wroom1.step",   "ESP32-S3",          ["ESP32-S3", "ESP32_Antenna"]),
    ("ads1115_tssop10.step",   "ADS1115_Sensors",   ["ADS1115_Sensors"]),
    ("ads1115_tssop10.step",   "ADS1115_Therm",     ["ADS1115_Therm"]),
    ("rfm95w_sx1276.step",     "SX1276_LoRa",       ["SX1276_LoRa"]),
    ("sim7000g.step",          "SIM7000G",          ["SIM7000G"]),
    ("irlz44n_to220.step",    "MOSFET_IRLZ44N",    ["MOSFET_IRLZ44N", "MOSFET_Tab"]),
    ("cn3791_sop8.step",       "CN3791",            ["CN3791"]),
    ("ap2112k_sot23.step",     "AP2112K",           ["AP2112K"]),

    # ── Controller Capacitors (0805) ──
    ("0805_capacitor.step",    "Cap_0",             ["Cap_0"]),
    ("0805_capacitor.step",    "Cap_1",             ["Cap_1"]),
    ("0805_capacitor.step",    "Cap_2",             ["Cap_2"]),
    ("0805_capacitor.step",    "Cap_3",             ["Cap_3"]),

    # ── Controller Resistors (0805) ──
    ("0805_resistor.step",     "R1_250ohm",         ["R1_250ohm"]),
    ("0805_resistor.step",     "R6_100ohm_Gate",    ["R6_100ohm_Gate"]),
    ("0805_resistor.step",     "R7_10k_GatePD",     ["R7_10k_GatePD"]),
    ("0805_resistor.step",     "R8_10k_ThermN",     ["R8_10k_ThermN"]),
    ("0805_resistor.step",     "R9_10k_ThermE",     ["R9_10k_ThermE"]),
    ("0805_resistor.step",     "R10_10k_ThermS",    ["R10_10k_ThermS"]),
    ("0805_resistor.step",     "R11_10k_ThermW",    ["R11_10k_ThermW"]),
    ("0805_resistor.step",     "R12_1k_Bridge",     ["R12_1k_Bridge"]),
    ("0805_resistor.step",     "R13_1k_Bridge",     ["R13_1k_Bridge"]),
    ("0805_resistor.step",     "R14_1k_Bridge",     ["R14_1k_Bridge"]),
    ("0805_resistor.step",     "R_I2C_SDA",         ["R_I2C_SDA"]),
    ("0805_resistor.step",     "R_I2C_SCL",         ["R_I2C_SCL"]),

    # ── Controller Diode ──
    ("1n4007_do41.step",       "Flyback_Diode",
     ["Flyback_Diode", "Diode_Band", "Diode_Lead1", "Diode_Lead2"]),

    # ── Controller Connectors ──
    ("sma_bulkhead.step",      "SMA_LoRa",          ["SMA_LoRa"]),
    ("sma_bulkhead.step",      "SMA_LTE",           ["SMA_LTE"]),
    ("sma_antenna_whip.step",  "Ant_LoRa",          ["Ant_LoRa"]),
    ("sma_antenna_whip.step",  "Ant_LTE",           ["Ant_LTE"]),
    ("m12_cable_gland.step",   "Gland_0_Inner",     ["Gland_0_Inner", "Gland_0_Nut"]),
    ("m12_cable_gland.step",   "Gland_1_Inner",     ["Gland_1_Inner", "Gland_1_Nut"]),
    ("m12_cable_gland.step",   "Gland_2_Inner",     ["Gland_2_Inner", "Gland_2_Nut"]),
    ("jst_ph_2pin.step",       "JST_Battery",       ["JST_Battery"]),
    ("barrel_jack_dc.step",    "Conn_Solar_J6",     ["Conn_Solar_J6", "J6_CenterPin"]),
    ("screw_terminal_4pin.step", "Conn_Pressure_J4",
     ["Conn_Pressure_J4", "J4_Screw_0", "J4_Screw_1", "J4_Screw_2", "J4_Screw_3"]),

    # ── Controller Power ──
    ("lipo_pouch_3.7v.step",   "LiPo_Battery",      ["LiPo_Battery", "Battery_Label"]),
    ("solar_panel_6v.step",    "Solar_Panel",
     ["Solar_Panel", "Solar_Cell_0", "Solar_Cell_1", "Solar_Cell_2",
      "Solar_Cell_3", "Solar_Cell_4", "Solar_Cell_5"]),

    # ── M12 8-pin Waterproof Connectors (controller ↔ probe cable) ──
    ("m12_8pin_connector_female.step", "M12_Female_Body",
     ["M12_Female_Body", "M12_Female_Pins"]),
    ("m12_8pin_connector_male.step", "M12_Male_Body",
     ["M12_Male_Body", "M12_Male_Ring", "M12_Male_Pins"]),

    # ── Probe: Pressure Transducer ──
    ("pressure_transducer.step", "Pressure_Sensor",
     ["Pressure_Sensor", "Pressure_Membrane"]),

    # ── Probe: M12 connector at cable entry ──
    ("m12_8pin_connector_female.step", "Probe_M12_Female",
     ["Probe_M12_Female", "Probe_M12_Pins", "Probe_M12_Nut"]),
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

        # Find the WX-Flow assembly component
        asm_comp = None
        for i in range(root.occurrences.count):
            occ = root.occurrences.item(i)
            if "WX-Flow" in occ.component.name:
                asm_comp = occ.component
                break

        if not asm_comp:
            ui.messageBox(
                "WX-Flow assembly not found.\n"
                "Run wx_flow_full_assembly.py first."
            )
            return

        import_mgr = app.importManager
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

        msg = f"WX-Flow STEP Swap Complete!\n\n"
        msg += f"Replaced: {len(swapped)} components\n"
        if skipped:
            msg += f"\nSkipped ({len(skipped)}):\n"
            for s in skipped:
                msg += f"  {s}\n"
        msg += (
            "\nRemaining placeholders (no STEP needed):\n"
            "  Enclosure, PCB, wiring, O-rings, standoffs,\n"
            "  screws, desiccant, SIM card, cables\n"
            "\nProbe custom parts (thermistors, heater, EC cell,\n"
            "  PT1000, EZO board, tube) stay as placeholders.\n"
            "  Run probe_custom_parts.py to upgrade those.\n"
            "\nSome parts may need manual orientation adjustment."
        )

        ui.messageBox(msg)

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
