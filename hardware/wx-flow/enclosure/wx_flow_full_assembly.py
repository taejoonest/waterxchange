"""
Fusion 360 Script — WX-Flow FULL ASSEMBLY with all components
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste → Run

Creates the complete WX-Flow product with every component:
  SURFACE CONTROLLER BOX:
    - Enclosure base (white, 3 cable glands) + lid + solar panel
    - PCB with ESP32, 2×ADS1115, SX1276, SIM7000G, MOSFET, CN3791
    - LiPo battery, SMA antennas, M12 cable glands

  SUBMERSIBLE PROBE:
    - Outer tube (45mm OD, charcoal gray)
    - Flow chamber with 8 visible slots
    - Heater element (red nichrome coil)
    - 4× thermistors (green glass beads on posts)
    - Conductivity cell (4 platinum electrodes)
    - PT1000 RTD sensor
    - Pressure transducer at bottom
    - Internal signal conditioning PCB
    - Epoxy potted top with cable exit

  12-CONDUCTOR CABLE connecting them
"""

import adsk.core
import adsk.fusion
import math
import traceback

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    def mm(v):
        return v / 10.0

    def make_box(comp, name, x, y, z, w, d, h, color=None):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(x), mm(y), 0),
            adsk.core.Point3D.create(mm(x + w), mm(y + d), 0))
        prof = sk.profiles.item(0)
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if z == 0:
            inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(h)))
        else:
            start = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(mm(z)))
            inp.startExtent = start
            inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(h)))
        result = ext.add(inp)
        body = result.bodies.item(0)
        body.name = name
        if color:
            set_color(app, body, color)
        return body

    def make_cylinder(comp, name, cx, cy, z, radius, height, color=None):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(cx), mm(cy), 0), mm(radius))
        prof = None
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if prof is None or p.areaProperties().area < prof.areaProperties().area:
                prof = p
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if z == 0:
            inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(height)))
        else:
            start = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(mm(z)))
            inp.startExtent = start
            inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(height)))
        result = ext.add(inp)
        body = result.bodies.item(0)
        body.name = name
        if color:
            set_color(app, body, color)
        return body

    def set_color(app, body, rgb):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            if lib:
                base_appear = lib.appearances.itemByName("Plastic - Matte (Generic)")
                if base_appear:
                    appear = design.appearances.addByCopy(base_appear, f"c_{rgb[0]}_{rgb[1]}_{rgb[2]}_{body.name}")
                    color_prop = appear.appearanceProperties.itemByName("Color")
                    if color_prop:
                        adsk.core.ColorProperty.cast(color_prop).value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    body.appearance = appear
        except:
            pass

    try:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "WX-Flow Complete Assembly"

        # ════════════════════════════════════════════════════
        # OFFSET: Controller box at origin, probe at x=250
        # ════════════════════════════════════════════════════
        BOX_X = 0
        PROBE_X = 250  # probe center X, displayed to the right

        # ════════════════════════════════════════════════════
        # ═══ SURFACE CONTROLLER BOX ═══════════════════════
        # ════════════════════════════════════════════════════

        # Enclosure base (white)
        base = make_box(comp, "Box_Base", BOX_X, 0, 0, 160, 110, 30, (240, 240, 235))
        top_face = None
        for i in range(base.faces.count):
            f = base.faces.item(i)
            _, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            if n and abs(n.z - 1.0) < 0.01:
                top_face = f
                break
        if top_face:
            fc = adsk.core.ObjectCollection.create()
            fc.add(top_face)
            si = comp.features.shellFeatures.createInput(fc, False)
            si.insideThickness = adsk.core.ValueInput.createByReal(mm(3))
            comp.features.shellFeatures.add(si)

        # Lid
        make_box(comp, "Box_Lid", BOX_X, 0, 31, 160, 110, 25, (240, 240, 235))

        # Solar panel
        make_box(comp, "Solar_Panel", BOX_X + 5, 5, 56.5, 150, 100, 3, (20, 40, 80))
        for i in range(6):
            make_box(comp, f"Solar_Cell_{i}", BOX_X + 10, 8 + i * 16, 59.6, 140, 14, 0.3, (30, 55, 120))

        # PCB (green)
        pcb_z = 8
        make_box(comp, "PCB", BOX_X + 15, 30, pcb_z, 80, 50, 1.6, (0, 100, 30))
        cz = pcb_z + 1.6

        # ESP32-S3
        make_box(comp, "ESP32-S3", BOX_X + 20, 42, cz, 18, 25.5, 3.2, (180, 180, 180))

        # ADS1115 #1 (sensors)
        make_box(comp, "ADS1115_Sensors", BOX_X + 45, 35, cz, 5, 3, 1, (30, 30, 30))
        # ADS1115 #2 (thermistors)
        make_box(comp, "ADS1115_Therm", BOX_X + 45, 42, cz, 5, 3, 1, (30, 30, 30))

        # SX1276 LoRa module
        make_box(comp, "SX1276_LoRa", BOX_X + 55, 32, cz, 16, 16, 3, (30, 30, 30))

        # SIM7000G
        make_box(comp, "SIM7000G", BOX_X + 55, 52, cz, 24, 24, 2.5, (200, 200, 200))

        # MOSFET heater driver (TO-220 package)
        make_box(comp, "MOSFET_IRLZ44N", BOX_X + 42, 50, cz, 10, 4, 4.5, (30, 30, 30))
        # MOSFET heatsink tab
        make_box(comp, "MOSFET_Tab", BOX_X + 43, 54, cz, 8, 1, 7, (180, 180, 180))

        # CN3791 + AP2112K
        make_box(comp, "CN3791", BOX_X + 20, 33, cz, 5, 4, 1.5, (30, 30, 30))
        make_box(comp, "AP2112K", BOX_X + 28, 33, cz, 3, 3, 1, (30, 30, 30))

        # Capacitors
        for ci, (cx, cy) in enumerate([(22, 39), (35, 36), (50, 48), (70, 45)]):
            make_box(comp, f"Cap_{ci}", BOX_X + cx, cy, cz, 2, 1.2, 0.6, (180, 150, 80))

        # ════════════════════════════════════════════════════
        # 250Ω PRECISION RESISTOR (0805, for pressure 4-20mA shunt)
        # ════════════════════════════════════════════════════
        make_box(comp, "R1_250ohm", BOX_X + 50, 36, cz, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # MOSFET GATE RESISTORS
        # R6: 100Ω gate series, R7: 10kΩ gate pull-down
        # ════════════════════════════════════════════════════
        make_box(comp, "R6_100ohm_Gate", BOX_X + 40, 48, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R7_10k_GatePD", BOX_X + 40, 46, cz, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # THERMISTOR VOLTAGE DIVIDER RESISTORS (4× 10kΩ 0.1%)
        # R8 (N), R9 (E), R10 (S), R11 (W)
        # ════════════════════════════════════════════════════
        make_box(comp, "R8_10k_ThermN", BOX_X + 50, 42, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R9_10k_ThermE", BOX_X + 50, 44, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R10_10k_ThermS", BOX_X + 53, 42, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R11_10k_ThermW", BOX_X + 53, 44, cz, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # PT1000 WHEATSTONE BRIDGE RESISTORS (3× 1kΩ)
        # R12, R13, R14
        # ════════════════════════════════════════════════════
        make_box(comp, "R12_1k_Bridge", BOX_X + 38, 35, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R13_1k_Bridge", BOX_X + 38, 37, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R14_1k_Bridge", BOX_X + 38, 39, cz, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # I2C PULL-UP RESISTORS (2× 4.7kΩ, 0805)
        # ════════════════════════════════════════════════════
        make_box(comp, "R_I2C_SDA", BOX_X + 35, 42, cz, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R_I2C_SCL", BOX_X + 35, 44, cz, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # ESP32 ANTENNA KEEP-OUT STRIP
        # ════════════════════════════════════════════════════
        make_box(comp, "ESP32_Antenna", BOX_X + 20, 67, cz, 18, 0.5, 3.2, (200, 170, 50))

        # ════════════════════════════════════════════════════
        # SOLAR PANEL CONNECTOR (barrel jack / screw terminal, J6)
        # ════════════════════════════════════════════════════
        make_box(comp, "Conn_Solar_J6", BOX_X + 80, 30, cz, 9, 9, 11, (30, 30, 30))
        # Barrel jack center pin
        make_cylinder(comp, "J6_CenterPin", BOX_X + 84.5, 34.5, cz + 3, 1, 8, (210, 185, 80))

        # ════════════════════════════════════════════════════
        # PRESSURE TRANSDUCER SCREW TERMINAL (J4, 4-pin)
        # ════════════════════════════════════════════════════
        make_box(comp, "Conn_Pressure_J4", BOX_X + 15, 65, cz, 10, 7, 8, (50, 120, 50))
        # Screw heads (4 tiny cylinders)
        for si in range(4):
            make_cylinder(comp, f"J4_Screw_{si}", BOX_X + 17 + si * 2.5, 68, cz + 8, 1, 1.5, (160, 165, 170))

        # LiPo battery
        make_box(comp, "LiPo_Battery", BOX_X + 100, 30, 5, 50, 40, 10, (50, 100, 180))
        # Battery label
        make_box(comp, "Battery_Label", BOX_X + 105, 35, 15.1, 40, 30, 0.2, (255, 255, 255))

        # SMA antennas
        make_cylinder(comp, "SMA_LoRa", BOX_X + 60, -1, 12, 3.5, 6, (200, 170, 50))
        make_cylinder(comp, "SMA_LTE", BOX_X + 90, -1, 12, 3.5, 6, (200, 170, 50))
        make_cylinder(comp, "Ant_LoRa", BOX_X + 60, -4, 10, 2.5, 45, (30, 30, 30))
        make_cylinder(comp, "Ant_LTE", BOX_X + 90, -4, 10, 2.5, 50, (30, 30, 30))

        # 3× M12 cable glands (bottom)
        for gi, gx in enumerate([40, 80, 120]):
            make_cylinder(comp, f"Gland_{gi}_Inner", BOX_X + gx, 55, 0, 6, 5, (40, 40, 40))
            make_cylinder(comp, f"Gland_{gi}_Nut", BOX_X + gx, 55, -5, 8, 5, (40, 40, 40))

        # Cable from box down to probe
        make_cylinder(comp, "Cable_12cond", BOX_X + 40, 55, -60, 4, 55, (30, 30, 30))

        # Screws
        for (sx, sy) in [(10, 10), (150, 10), (10, 100), (150, 100)]:
            make_cylinder(comp, f"Screw_{sx}_{sy}", BOX_X + sx, sy, 56, 2.5, 3, (160, 165, 170))
            make_cylinder(comp, f"ScrewHead_{sx}_{sy}", BOX_X + sx, sy, 59, 3, 2, (160, 165, 170))

        # ════════════════════════════════════════════════════
        # ═══ SUBMERSIBLE PROBE ════════════════════════════
        # (displayed to the right, laying on its side for visibility)
        # ════════════════════════════════════════════════════
        PX = PROBE_X  # center X of probe
        PY = 55       # center Y

        # Outer tube (charcoal gray, 45mm OD × 300mm)
        make_cylinder(comp, "Probe_Outer_Tube", PX, PY, 0, 22.5, 300, (60, 60, 65))

        # Inner bore (cut out — make slightly smaller cylinder as visual indicator)
        # We'll leave the outer solid and add components inside/on it

        # Flow slots (8 rectangular cuts represented as lighter colored strips)
        slot_z_start = 110
        slot_h = 60
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            sx = PX + 21 * math.cos(rad)
            sy = PY + 21 * math.sin(rad)
            make_box(comp, f"FlowSlot_{angle_deg}",
                     sx - 1.5, sy - 1.5, slot_z_start,
                     3, 3, slot_h, (100, 200, 200))

        # ── Internal components (shown protruding for visibility) ──

        # HEATER ELEMENT (red, center post)
        make_cylinder(comp, "Heater_Nichrome", PX, PY, 83, 4, 40, (200, 50, 40))
        # Nichrome wire coil (visual: thin torus-like rings)
        for hz in range(0, 35, 5):
            make_cylinder(comp, f"Heater_Coil_{hz}", PX, PY, 85 + hz, 5.5, 1.5, (220, 80, 50))

        # 4× THERMISTORS (green glass beads, 3mm dia on posts)
        THERM_R = 15
        therm_colors = {0: "N", 90: "E", 180: "S", 270: "W"}
        for angle_deg, label in therm_colors.items():
            rad = math.radians(angle_deg)
            tx = PX + THERM_R * math.cos(rad)
            ty = PY + THERM_R * math.sin(rad)
            # Post (thin rod)
            make_cylinder(comp, f"Therm_Post_{label}", tx, ty, 83, 1, 40, (180, 180, 180))
            # Glass bead sensor (green, at top of post)
            make_cylinder(comp, f"Thermistor_{label}", tx, ty, 100, 2, 5, (50, 180, 80))
            # Wire leads (thin)
            make_cylinder(comp, f"Therm_Wire_{label}", tx, ty, 105, 0.3, 20, (200, 130, 50))

        # CONDUCTIVITY CELL (platinum electrodes, 4 rings)
        for ei in range(4):
            make_cylinder(comp, f"EC_Electrode_{ei}", PX, PY, 42 + ei * 6, 12, 2, (200, 200, 210))

        # PT1000 RTD (small white ceramic cylinder)
        make_cylinder(comp, "PT1000_RTD", PX - 8, PY, 33, 2, 8, (240, 240, 240))
        # RTD wires
        make_cylinder(comp, "PT1000_Wire1", PX - 8, PY - 1, 41, 0.3, 10, (200, 50, 50))
        make_cylinder(comp, "PT1000_Wire2", PX - 8, PY + 1, 41, 0.3, 10, (200, 50, 50))

        # PRESSURE TRANSDUCER at bottom (stainless steel)
        make_cylinder(comp, "Pressure_Sensor", PX, PY, 0, 12, 25, (160, 165, 170))
        # Sensor face (exposed to water, gold membrane)
        make_cylinder(comp, "Pressure_Membrane", PX, PY, -1, 8, 1, (200, 180, 100))

        # INTERNAL PCB (signal conditioning, green, small)
        make_box(comp, "Probe_PCB", PX - 15, PY - 10, 225, 30, 20, 1.6, (0, 100, 30))
        # Components on probe PCB
        make_box(comp, "Probe_MOSFET", PX - 12, PY - 7, 226.6, 6, 4, 2, (30, 30, 30))
        make_box(comp, "Probe_Connector", PX + 5, PY - 5, 226.6, 8, 10, 5, (240, 240, 230))

        # EPOXY POTTING at top (amber/clear, seals the cable entry)
        make_cylinder(comp, "Epoxy_Top", PX, PY, 270, 20, 30, (180, 150, 80))

        # CABLE EXIT from top
        make_cylinder(comp, "Probe_Cable_Exit", PX, PY, 300, 4, 20, (30, 30, 30))

        # ALIGNMENT FLAT (small flat notch on outer wall, marks North)
        make_box(comp, "North_Flat", PX + 19, PY - 2, 100, 5, 4, 80, (255, 200, 50))

        # ════════════════════════════════════════════════════
        # PCB STANDOFFS (brass M3, under PCB)
        # ════════════════════════════════════════════════════
        for (sx, sy) in [(25, 35), (85, 35), (25, 75), (85, 75)]:
            make_cylinder(comp, f"Standoff_{sx}_{sy}", BOX_X + sx, sy, 3, 2.5, 5, (200, 170, 50))

        # ════════════════════════════════════════════════════
        # ZIP TIE MOUNTING SLOTS (back wall)
        # ════════════════════════════════════════════════════
        make_box(comp, "ZipTie_1", BOX_X + 47, 109, 7, 6, 3, 16, (240, 240, 240))
        make_box(comp, "ZipTie_2", BOX_X + 107, 109, 7, 6, 3, 16, (240, 240, 240))

        # ════════════════════════════════════════════════════
        # SOLAR CABLE from gland (going off to panel)
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Cable_Solar", BOX_X + 80, 55, -20, 3, 15, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # CONTROLLER BOX — O-RING GASKET
        # ════════════════════════════════════════════════════
        make_box(comp, "ORing_Front", BOX_X + 3, 3, 29.5, 154, 2, 2, (0, 180, 170))
        make_box(comp, "ORing_Back", BOX_X + 3, 105, 29.5, 154, 2, 2, (0, 180, 170))
        make_box(comp, "ORing_Left", BOX_X + 3, 3, 29.5, 2, 104, 2, (0, 180, 170))
        make_box(comp, "ORing_Right", BOX_X + 155, 3, 29.5, 2, 104, 2, (0, 180, 170))

        # ════════════════════════════════════════════════════
        # CONTROLLER BOX — DESICCANT PACK
        # ════════════════════════════════════════════════════
        make_box(comp, "Desiccant_Pack", BOX_X + 100, 72, 5, 30, 20, 4, (240, 240, 240))
        make_box(comp, "Desiccant_Label", BOX_X + 103, 74, 9.1, 24, 16, 0.2, (80, 140, 200))

        # ════════════════════════════════════════════════════
        # CONTROLLER BOX — SIM CARD in slot
        # ════════════════════════════════════════════════════
        make_box(comp, "SIM_Card", BOX_X + 60, 57, cz - 1.0, 12.3, 8.8, 0.67, (30, 30, 30))
        make_box(comp, "SIM_Contacts", BOX_X + 61, 58, cz - 0.3, 10, 6.5, 0.05, (210, 185, 80))

        # ════════════════════════════════════════════════════
        # CONTROLLER BOX — FLYBACK DIODE next to MOSFET
        # (1N4007, DO-41 axial, 2.7×4.2mm)
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Flyback_Diode", BOX_X + 44, 56, cz, 1.3, 4.2, (30, 30, 30))
        # Cathode band (silver stripe)
        make_cylinder(comp, "Diode_Band", BOX_X + 44, 56, cz + 3.5, 1.4, 0.5, (190, 190, 190))
        # Diode leads
        make_cylinder(comp, "Diode_Lead1", BOX_X + 44, 56, cz - 2, 0.3, 2, (180, 180, 180))
        make_cylinder(comp, "Diode_Lead2", BOX_X + 44, 56, cz + 4.7, 0.3, 2, (180, 180, 180))

        # ════════════════════════════════════════════════════
        # CONTROLLER BOX — INTERNAL WIRING HARNESS
        # ════════════════════════════════════════════════════
        # Power wires (red/black)
        make_box(comp, "Wire_Solar_Pos", BOX_X + 78, 52, cz + 2, 22, 0.8, 0.8, (220, 40, 40))
        make_box(comp, "Wire_Solar_Neg", BOX_X + 78, 54, cz + 2, 22, 0.8, 0.8, (30, 30, 30))
        # Battery JST connector + wires
        make_box(comp, "JST_Battery", BOX_X + 96, 44, 11, 3, 5, 3, (240, 240, 230))
        make_box(comp, "Wire_Batt_Pos", BOX_X + 93, 45, 12, 5, 0.8, 0.8, (220, 40, 40))
        make_box(comp, "Wire_Batt_Neg", BOX_X + 93, 47, 12, 5, 0.8, 0.8, (30, 30, 30))
        # Probe cable wires (12-conductor, multicolor bundle going to PCB)
        for wi in range(6):
            colors_12 = [(220,40,40),(30,30,30),(50,100,200),(240,240,240),(220,200,50),(50,180,80)]
            c = colors_12[wi]
            make_box(comp, f"Wire_Probe_{wi}", BOX_X + 15, 30 + wi * 2, cz + 3, 25, 0.6, 0.6, c)
        # SPI bus (yellow bundle)
        make_box(comp, "Wire_SPI", BOX_X + 38, 38, cz + 4, 17, 1.2, 0.6, (220, 200, 50))
        # Coax pigtails to SMA
        make_box(comp, "Coax_LoRa", BOX_X + 55, 32, cz + 3, 4, 0.8, 0.8, (30, 30, 30))
        make_box(comp, "Coax_LTE", BOX_X + 55, 52, cz + 2.5, 4, 0.8, 0.8, (30, 30, 30))
        # Heater power wires (thicker, from MOSFET → gland)
        make_box(comp, "Wire_Heater_Pos", BOX_X + 15, 50, cz + 5, 27, 1.0, 1.0, (220, 100, 40))
        make_box(comp, "Wire_Heater_Neg", BOX_X + 15, 52, cz + 5, 27, 1.0, 1.0, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # M12 8-PIN WATERPROOF CONNECTOR PAIR
        # (at the junction between cable and controller box)
        # Male on cable side, female on box side
        # ════════════════════════════════════════════════════
        # Female socket (inside box, mounted to gland)
        make_cylinder(comp, "M12_Female_Body", BOX_X + 40, 55, 3, 7, 15, (40, 40, 45))
        # Pin insert (gold contacts visible)
        make_cylinder(comp, "M12_Female_Pins", BOX_X + 40, 55, 3, 4, 3, (210, 185, 80))
        # Male plug (on cable end, below box)
        make_cylinder(comp, "M12_Male_Body", BOX_X + 40, 55, -15, 7, 18, (40, 40, 45))
        make_cylinder(comp, "M12_Male_Ring", BOX_X + 40, 55, -15, 9, 5, (160, 165, 170))
        # Male pins
        make_cylinder(comp, "M12_Male_Pins", BOX_X + 40, 55, -1, 4, 4, (210, 185, 80))

        # ════════════════════════════════════════════════════
        # PROBE — BOTTOM CAP (seals pressure sensor end)
        # Threaded or press-fit, with O-ring
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Probe_BottomCap", PX, PY, -5, 22.5, 8, (60, 60, 65))
        # Bottom cap O-ring (teal)
        make_cylinder(comp, "Probe_BottomCap_ORing", PX, PY, -1, 20, 1.5, (0, 180, 170))
        # Pressure port (hole in bottom cap, water access)
        make_cylinder(comp, "Probe_PressurePort", PX, PY, -6, 5, 2, (160, 165, 170))

        # ════════════════════════════════════════════════════
        # PROBE — TOP CAP with cable entry and O-ring
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Probe_TopCap", PX, PY, 295, 22.5, 8, (60, 60, 65))
        make_cylinder(comp, "Probe_TopCap_ORing", PX, PY, 295, 20, 1.5, (0, 180, 170))

        # ════════════════════════════════════════════════════
        # PROBE — CONDUCTIVITY CIRCUIT BOARD (Atlas EZO-EC)
        # Small separate board near the conductivity cell
        # 13.97 × 20.16mm (standard Atlas EZO form factor)
        # ════════════════════════════════════════════════════
        make_box(comp, "EZO_EC_Board", PX - 10, PY - 7, 180, 14, 20, 1.6, (50, 20, 100))
        # EZO IC (main chip, black)
        make_box(comp, "EZO_EC_Chip", PX - 8, PY - 4, 181.6, 6, 6, 1.2, (30, 30, 30))
        # EZO connector pads (gold)
        make_box(comp, "EZO_EC_Pads", PX - 9, PY + 8, 181.6, 12, 3, 0.3, (210, 185, 80))
        # Wires from EZO → main probe PCB
        make_cylinder(comp, "EZO_Wire1", PX - 5, PY - 2, 200, 0.3, 25, (50, 100, 200))
        make_cylinder(comp, "EZO_Wire2", PX - 3, PY - 2, 200, 0.3, 25, (240, 240, 240))
        # Wires from EZO → conductivity electrodes (down)
        make_cylinder(comp, "EZO_EC_Wire1", PX - 5, PY + 2, 65, 0.3, 115, (200, 200, 210))
        make_cylinder(comp, "EZO_EC_Wire2", PX - 3, PY + 2, 65, 0.3, 115, (200, 200, 210))

        # ════════════════════════════════════════════════════
        # PROBE — INTERNAL WIRING (thermistors/heater → probe PCB)
        # ════════════════════════════════════════════════════
        # Heater power wires (red pair, from heater up to PCB)
        make_cylinder(comp, "Heater_Wire_Pos", PX + 2, PY, 123, 0.5, 102, (220, 60, 40))
        make_cylinder(comp, "Heater_Wire_Neg", PX - 2, PY, 123, 0.5, 102, (30, 30, 30))
        # Pressure sensor wires (blue pair)
        make_cylinder(comp, "Pressure_Wire1", PX + 5, PY + 3, 25, 0.4, 200, (50, 100, 200))
        make_cylinder(comp, "Pressure_Wire2", PX + 5, PY - 3, 25, 0.4, 200, (240, 240, 240))
        # PT1000 wires (3-wire, red/red/white)
        make_cylinder(comp, "PT1000_Wire_R1", PX - 6, PY + 3, 41, 0.3, 184, (200, 50, 50))
        make_cylinder(comp, "PT1000_Wire_R2", PX - 6, PY - 3, 41, 0.3, 184, (200, 50, 50))
        make_cylinder(comp, "PT1000_Wire_W", PX - 4, PY - 3, 41, 0.3, 184, (240, 240, 240))

        # ════════════════════════════════════════════════════
        # PROBE — M12 8-PIN CONNECTOR at cable entry (top)
        # (waterproof connector between cable and probe)
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Probe_M12_Female", PX, PY, 303, 7, 12, (40, 40, 45))
        make_cylinder(comp, "Probe_M12_Pins", PX, PY, 303, 4, 3, (210, 185, 80))
        make_cylinder(comp, "Probe_M12_Nut", PX, PY, 312, 9, 5, (160, 165, 170))

        ui.messageBox(
            "WX-Flow Full Assembly created!\n\n"
            "SURFACE CONTROLLER:\n"
            "• Enclosure + lid + O-ring gasket\n"
            "• Solar panel (6 cell rows)\n"
            "• PCB: ESP32, 2×ADS1115, SX1276, SIM7000G,\n"
            "  MOSFET + flyback diode, CN3791, AP2112K\n"
            "• SIM card, LiPo battery + JST\n"
            "• 2× SMA antennas, 3× M12 cable glands\n"
            "• M12 8-pin waterproof connector pair\n"
            "• Full internal wiring harness\n"
            "• Desiccant pack\n\n"
            "SUBMERSIBLE PROBE:\n"
            "• 45mm tube + top/bottom caps with O-rings\n"
            "• 8 flow slots\n"
            "• Heater element (nichrome coil) + power wires\n"
            "• 4× thermistors (N/E/S/W) with posts + leads\n"
            "• Conductivity cell (4 Pt electrodes)\n"
            "• Atlas EZO-EC circuit board + wiring\n"
            "• PT1000 RTD (3-wire) + wiring\n"
            "• Pressure sensor + wiring\n"
            "• Signal conditioning PCB\n"
            "• Epoxy potted top\n"
            "• M12 8-pin connector at cable entry\n"
            "• North alignment flat\n\n"
            "ALL components present. Use Render workspace\n"
            "for photorealistic output."
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
