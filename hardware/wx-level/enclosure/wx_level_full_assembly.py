"""
Fusion 360 Script — WX-Level FULL ASSEMBLY with all components
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste → Run

Creates the complete WX-Level product with every component:
  - Controller box base (white PETG)
  - Controller box lid with solar panel
  - PCB (green, 80×50mm) with component blocks for:
      ESP32-S3, ADS1115, BME280, SX1276, SIM7000G, CN3791, AP2112K
  - LiPo battery pouch
  - 2× SMA antenna stubs
  - 2× M12 cable glands
  - Submersible pressure transducer on cable
  - Vented cable going down into well
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
        """Create a rectangular block at (x,y,z) with size (w,d,h)."""
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(x), mm(y), 0),
            adsk.core.Point3D.create(mm(x + w), mm(y + d), 0)
        )
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
        """Create a cylinder centered at (cx,cy) starting at z."""
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(cx), mm(cy), 0), mm(radius))

        # Get the circle profile (smallest)
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
        """Apply a solid color to a body. rgb = (r, g, b) 0-255."""
        design = adsk.fusion.Design.cast(app.activeProduct)
        appearances = design.appearances
        try:
            # Create a unique appearance
            lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            if lib:
                base_appear = lib.appearances.itemByName("Plastic - Matte (Generic)")
                if base_appear:
                    appear = design.appearances.addByCopy(base_appear, f"color_{rgb[0]}_{rgb[1]}_{rgb[2]}_{body.name}")
                    color_prop = appear.appearanceProperties.itemByName("Color")
                    if color_prop:
                        color_val = adsk.core.ColorProperty.cast(color_prop)
                        color_val.value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    body.appearance = appear
                    return
        except:
            pass

        # Fallback: try simpler approach
        try:
            appear = adsk.core.Appearance.cast(None)
            for i in range(appearances.count):
                a = appearances.item(i)
                if "Generic" in a.name:
                    appear = a
                    break
            if appear:
                body.appearance = appear
        except:
            pass

    try:
        # ════════════════════════════════════════════════════
        # Create main component
        # ════════════════════════════════════════════════════
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "WX-Level Complete Assembly"

        # ════════════════════════════════════════════════════
        # ENCLOSURE BASE (white, 160×110×30mm)
        # ════════════════════════════════════════════════════
        base = make_box(comp, "Enclosure_Base", 0, 0, 0, 160, 110, 30, (240, 240, 235))

        # Shell it
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

        # ════════════════════════════════════════════════════
        # ENCLOSURE LID (white, sits on top)
        # ════════════════════════════════════════════════════
        lid = make_box(comp, "Enclosure_Lid", 0, 0, 31, 160, 110, 25, (240, 240, 235))

        # ════════════════════════════════════════════════════
        # SOLAR PANEL on lid top (dark blue/black)
        # ════════════════════════════════════════════════════
        make_box(comp, "Solar_Panel", 5, 5, 56.5, 150, 100, 3, (20, 40, 80))
        # Solar cell grid lines
        for i in range(6):
            make_box(comp, f"Solar_Cell_Row_{i}", 10, 8 + i * 16, 59.6, 140, 14, 0.3, (30, 55, 120))

        # ════════════════════════════════════════════════════
        # PCB (green, 80×50mm, 1.6mm thick)
        # Positioned inside the base, left side
        # ════════════════════════════════════════════════════
        pcb_x, pcb_y, pcb_z = 15, 30, 8  # on standoffs at z=8mm
        make_box(comp, "PCB", pcb_x, pcb_y, pcb_z, 80, 50, 1.6, (0, 100, 30))

        # ════════════════════════════════════════════════════
        # ELECTRONIC COMPONENTS on PCB
        # ════════════════════════════════════════════════════
        chip_z = pcb_z + 1.6  # top of PCB

        # ESP32-S3-WROOM-1 (18×25.5×3.2mm, silver shielding can)
        make_box(comp, "ESP32-S3", pcb_x + 5, pcb_y + 12, chip_z, 18, 25.5, 3.2, (180, 180, 180))
        # ESP32 antenna area (small strip at end)
        make_box(comp, "ESP32_Antenna", pcb_x + 5, pcb_y + 37, chip_z, 18, 0.5, 3.2, (200, 170, 50))

        # ADS1115 (TSSOP-10, 3×5×1mm, black IC)
        make_box(comp, "ADS1115", pcb_x + 30, pcb_y + 10, chip_z, 5, 3, 1, (30, 30, 30))

        # BME280 (LGA, 2.5×2.5×0.9mm, silver)
        make_box(comp, "BME280", pcb_x + 30, pcb_y + 18, chip_z, 2.5, 2.5, 0.9, (190, 190, 190))

        # SX1276 / RFM95W LoRa module (16×16×3mm, PCB module with shield)
        make_box(comp, "SX1276_LoRa", pcb_x + 40, pcb_y + 5, chip_z, 16, 16, 3, (30, 30, 30))
        # LoRa module text pad (gold)
        make_box(comp, "LoRa_Pad", pcb_x + 42, pcb_y + 7, chip_z + 3, 12, 12, 0.2, (200, 170, 50))

        # SIM7000G (24×24×2.5mm, large cellular module, silver shield)
        make_box(comp, "SIM7000G", pcb_x + 40, pcb_y + 25, chip_z, 24, 24, 2.5, (200, 200, 200))
        # SIM card slot under the module
        make_box(comp, "SIM_Slot", pcb_x + 45, pcb_y + 30, chip_z - 1.6, 15, 12, 1.6, (40, 40, 40))

        # CN3791 MPPT charger (SOP-8, 5×4×1.5mm)
        make_box(comp, "CN3791", pcb_x + 5, pcb_y + 3, chip_z, 5, 4, 1.5, (30, 30, 30))

        # AP2112K LDO (SOT-23-5, 3×3×1mm)
        make_box(comp, "AP2112K", pcb_x + 15, pcb_y + 3, chip_z, 3, 3, 1, (30, 30, 30))

        # 250Ω precision resistor (0805 package, 2×1.2×0.5mm)
        make_box(comp, "R250ohm", pcb_x + 28, pcb_y + 25, chip_z, 2, 1.2, 0.6, (20, 20, 20))

        # Capacitors (ceramic, 0805, several)
        for ci, (cx, cy) in enumerate([(12, 8), (25, 5), (38, 22), (65, 15)]):
            make_box(comp, f"Cap_{ci}", pcb_x + cx, pcb_y + cy, chip_z, 2, 1.2, 0.6, (180, 150, 80))

        # Pin headers / connectors on PCB edge
        make_box(comp, "Connector_Probe", pcb_x, pcb_y + 20, chip_z, 2.5, 10, 8, (240, 240, 230))
        make_box(comp, "Connector_Solar", pcb_x + 78, pcb_y + 20, chip_z, 2, 5, 5, (240, 240, 230))

        # ════════════════════════════════════════════════════
        # LIPO BATTERY (pouch cell, 70×40×8mm, blue wrap)
        # ════════════════════════════════════════════════════
        make_box(comp, "LiPo_Battery", 100, 30, 5, 50, 40, 10, (50, 100, 180))
        # Battery label strip
        make_box(comp, "Battery_Label", 105, 35, 15.1, 40, 30, 0.2, (255, 255, 255))

        # ════════════════════════════════════════════════════
        # SMA CONNECTORS + ANTENNAS (on front wall y=0)
        # ════════════════════════════════════════════════════
        # SMA bulkhead (gold cylinder through wall)
        make_cylinder(comp, "SMA_LoRa_Bulkhead", 60, 0, 12, 3.5, 6, (200, 170, 50))
        make_cylinder(comp, "SMA_LTE_Bulkhead", 90, 0, 12, 3.5, 6, (200, 170, 50))
        # Antenna stubs (black rubber, 3mm dia × 40mm tall)
        make_cylinder(comp, "Antenna_LoRa", 60, -3, 10, 2.5, 45, (30, 30, 30))
        make_cylinder(comp, "Antenna_LTE", 90, -3, 10, 2.5, 50, (30, 30, 30))
        # Antenna tips (small cylinder)
        make_cylinder(comp, "Antenna_LoRa_Tip", 60, -3, 55, 1.5, 3, (30, 30, 30))
        make_cylinder(comp, "Antenna_LTE_Tip", 90, -3, 60, 1.5, 3, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # M12 CABLE GLANDS (on bottom, black nylon)
        # ════════════════════════════════════════════════════
        # Gland body (threaded, inside box)
        make_cylinder(comp, "Gland_Probe_Inner", 50, 55, 0, 6, 5, (40, 40, 40))
        make_cylinder(comp, "Gland_Solar_Inner", 100, 55, 0, 6, 5, (40, 40, 40))
        # Gland nut (outside box, wider)
        make_cylinder(comp, "Gland_Probe_Nut", 50, 55, -5, 8, 5, (40, 40, 40))
        make_cylinder(comp, "Gland_Solar_Nut", 100, 55, -5, 8, 5, (40, 40, 40))

        # ════════════════════════════════════════════════════
        # CABLE from gland going down (black, to transducer)
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Cable_Probe", 50, 55, -80, 3.5, 75, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # SUBMERSIBLE PRESSURE TRANSDUCER (stainless steel)
        # 316SS body: 20mm dia × 80mm long
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Transducer_Body", 50, 55, -170, 10, 80, (160, 165, 170))
        # Transducer nose cone
        make_cylinder(comp, "Transducer_Nose", 50, 55, -180, 8, 10, (140, 145, 150))
        # Transducer cable strain relief
        make_cylinder(comp, "Transducer_Relief", 50, 55, -92, 6, 12, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # SOLAR CABLE from other gland (shorter, going off to the side)
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "Cable_Solar", 100, 55, -20, 3, 15, (30, 30, 30))

        # ════════════════════════════════════════════════════
        # MOUNTING BRACKET (zip tie slots visible on back)
        # ════════════════════════════════════════════════════
        # Zip ties (thin strips through back wall slots)
        make_box(comp, "ZipTie_1", 47, 109, 7, 6, 3, 16, (240, 240, 240))
        make_box(comp, "ZipTie_2", 107, 109, 7, 6, 3, 16, (240, 240, 240))

        # ════════════════════════════════════════════════════
        # PCB STANDOFFS (brass M3, visible under PCB)
        # ════════════════════════════════════════════════════
        for (sx, sy) in [(25, 35), (85, 35), (25, 75), (85, 75)]:
            make_cylinder(comp, f"Standoff_{sx}_{sy}", sx, sy, 3, 2.5, 5, (200, 170, 50))

        # ════════════════════════════════════════════════════
        # SCREWS holding lid (4× M3 in corners)
        # ════════════════════════════════════════════════════
        for (sx, sy) in [(10, 10), (150, 10), (10, 100), (150, 100)]:
            make_cylinder(comp, f"Screw_{sx}_{sy}", sx, sy, 56, 2.5, 3, (160, 165, 170))
            # Screw head
            make_cylinder(comp, f"ScrewHead_{sx}_{sy}", sx, sy, 59, 3, 2, (160, 165, 170))

        # ════════════════════════════════════════════════════
        # VOLTAGE DIVIDER RESISTORS on PCB (0805 package)
        # R2/R3: battery monitoring, R4/R5: solar monitoring
        # ════════════════════════════════════════════════════
        make_box(comp, "R2_100k_BattHi", pcb_x + 68, pcb_y + 35, chip_z, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R3_100k_BattLo", pcb_x + 68, pcb_y + 38, chip_z, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R4_100k_SolHi", pcb_x + 72, pcb_y + 35, chip_z, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R5_100k_SolLo", pcb_x + 72, pcb_y + 38, chip_z, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # I2C PULL-UP RESISTORS (4.7kΩ × 2, 0805)
        # ════════════════════════════════════════════════════
        make_box(comp, "R_I2C_SDA", pcb_x + 25, pcb_y + 15, chip_z, 2, 1.2, 0.6, (20, 20, 20))
        make_box(comp, "R_I2C_SCL", pcb_x + 25, pcb_y + 18, chip_z, 2, 1.2, 0.6, (20, 20, 20))

        # ════════════════════════════════════════════════════
        # SCHOTTKY DIODE (solar input protection, SOD-123)
        # Small black package near CN3791
        # ════════════════════════════════════════════════════
        make_box(comp, "Schottky_Diode", pcb_x + 10, pcb_y + 3, chip_z, 2.8, 1.6, 1.0, (30, 30, 30))
        # Cathode band (silver)
        make_box(comp, "Schottky_Band", pcb_x + 12, pcb_y + 3, chip_z + 0.5, 0.5, 1.6, 0.6, (190, 190, 190))

        # ════════════════════════════════════════════════════
        # STATUS LED (green, 0805, near CN3791 DONE pin)
        # ════════════════════════════════════════════════════
        make_box(comp, "Status_LED", pcb_x + 8, pcb_y + 8, chip_z, 2, 1.2, 0.7, (50, 200, 80))

        # ════════════════════════════════════════════════════
        # O-RING GASKET (teal silicone, sits between base and lid)
        # Rectangular loop around the top rim of the base
        # ════════════════════════════════════════════════════
        # Top edge segments (2mm cross-section silicone cord)
        make_box(comp, "ORing_Front", 3, 3, 29.5, 154, 2, 2, (0, 180, 170))
        make_box(comp, "ORing_Back", 3, 105, 29.5, 154, 2, 2, (0, 180, 170))
        make_box(comp, "ORing_Left", 3, 3, 29.5, 2, 104, 2, (0, 180, 170))
        make_box(comp, "ORing_Right", 155, 3, 29.5, 2, 104, 2, (0, 180, 170))

        # ════════════════════════════════════════════════════
        # DESICCANT PACK (white sachet, tucked next to battery)
        # ════════════════════════════════════════════════════
        make_box(comp, "Desiccant_Pack", 100, 72, 5, 30, 20, 4, (240, 240, 240))
        # Desiccant label text (thin colored strip)
        make_box(comp, "Desiccant_Label", 103, 74, 9.1, 24, 16, 0.2, (80, 140, 200))

        # ════════════════════════════════════════════════════
        # SIM CARD (nano SIM, gold + black, in the SIM slot)
        # 12.3 × 8.8 × 0.67mm
        # ════════════════════════════════════════════════════
        make_box(comp, "SIM_Card", pcb_x + 47, pcb_y + 32, chip_z - 1.0, 12.3, 8.8, 0.67, (30, 30, 30))
        make_box(comp, "SIM_Card_Contacts", pcb_x + 48, pcb_y + 33, chip_z - 0.3, 10, 6.5, 0.05, (210, 185, 80))

        # ════════════════════════════════════════════════════
        # VENT TUBE CAP (on the vented cable, small gray cylinder)
        # 25mm OD × 30mm tall, sits near the cable gland
        # ════════════════════════════════════════════════════
        make_cylinder(comp, "VentCap_Body", 50, 55, -10, 12.5, 30, (180, 180, 175))
        # Vent holes (3 small white dots on top)
        for vi, vang in enumerate([0, 120, 240]):
            vr = math.radians(vang)
            vx = 50 + 6 * math.cos(vr)
            vy = 55 + 6 * math.sin(vr)
            make_cylinder(comp, f"VentHole_{vi}", vx, vy, 20, 0.5, 1, (240, 240, 240))
        # Gore-Tex membrane (thin white disc inside)
        make_cylinder(comp, "GoreTex_Membrane", 50, 55, 17, 10, 0.5, (240, 240, 240))
        # Desiccant chamber inside cap
        make_cylinder(comp, "VentCap_Desiccant", 50, 55, 10, 9, 7, (200, 220, 240))

        # ════════════════════════════════════════════════════
        # INTERNAL WIRING HARNESS
        # Colored wires connecting PCB to connectors/glands
        # ════════════════════════════════════════════════════
        # Power wires: solar connector → CN3791 (red + black)
        make_box(comp, "Wire_Solar_Pos", pcb_x + 78, pcb_y + 23, chip_z + 2, 22, 0.8, 0.8, (220, 40, 40))
        make_box(comp, "Wire_Solar_Neg", pcb_x + 78, pcb_y + 25, chip_z + 2, 22, 0.8, 0.8, (30, 30, 30))

        # Signal wires: probe connector → ADS1115 (blue + white)
        make_box(comp, "Wire_Probe_Sig", pcb_x + 2, pcb_y + 22, chip_z + 3, 28, 0.6, 0.6, (50, 100, 200))
        make_box(comp, "Wire_Probe_Gnd", pcb_x + 2, pcb_y + 24, chip_z + 3, 28, 0.6, 0.6, (240, 240, 240))
        make_box(comp, "Wire_Probe_Vex", pcb_x + 2, pcb_y + 26, chip_z + 3, 28, 0.6, 0.6, (220, 40, 40))

        # LoRa SPI wires: ESP32 → SX1276 (yellow bundle)
        make_box(comp, "Wire_SPI_Bundle", pcb_x + 23, pcb_y + 8, chip_z + 4, 20, 1.2, 0.6, (220, 200, 50))

        # Antenna pigtails: SX1276/SIM7000G → SMA (thin coax, black)
        make_box(comp, "Coax_LoRa", pcb_x + 56, pcb_y + 5, chip_z + 3, 3, 0.8, 0.8, (30, 30, 30))
        make_box(comp, "Coax_LTE", pcb_x + 56, pcb_y + 25, chip_z + 2.5, 3, 0.8, 0.8, (30, 30, 30))

        # Battery wires: LiPo → CN3791 (red + black JST)
        make_box(comp, "Wire_Batt_Pos", 98, 45, 12, 5, 0.8, 0.8, (220, 40, 40))
        make_box(comp, "Wire_Batt_Neg", 98, 47, 12, 5, 0.8, 0.8, (30, 30, 30))
        # JST connector (small white block)
        make_box(comp, "JST_Battery", 96, 44, 11, 3, 5, 3, (240, 240, 230))

        ui.messageBox(
            "WX-Level Full Assembly created!\n\n"
            "Components:\n"
            "• Enclosure base + lid + O-ring gasket\n"
            "• Solar panel (dark blue, 6 cell rows)\n"
            "• PCB with ESP32, ADS1115, BME280, SX1276,\n"
            "  SIM7000G, CN3791, AP2112K, resistors, caps\n"
            "• SIM card in slot\n"
            "• LiPo battery + JST connector\n"
            "• 2× SMA antennas (LoRa + LTE)\n"
            "• 2× M12 cable glands\n"
            "• Internal wiring harness (power, signal, SPI, coax)\n"
            "• Submersible pressure transducer on cable\n"
            "• Vent tube cap (Gore-Tex + desiccant)\n"
            "• Desiccant pack inside box\n"
            "• Mounting hardware (standoffs, screws, zip ties)\n\n"
            "ALL components present. Use Render workspace\n"
            "for photorealistic output."
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
