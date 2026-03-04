"""
Fusion 360 Script — WX-Flow Probe Custom Parts
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste → Run

Creates the 6 custom probe components that have no STEP files available:
  1. NTC 10kΩ Glass Bead Thermistor (×1, copy it 4 times)
  2. Nichrome Heater Coil
  3. Platinum Conductivity Electrode (×1, copy it 4 times)
  4. PT1000 RTD Sensor
  5. Atlas EZO-EC Circuit Board
  6. Probe Outer Tube with 8 flow slots

Each part is created as a separate component.
After running, export each as .step for use in the full assembly.
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

    def cm(mm_val):
        return mm_val / 10.0

    def set_color(app, body, rgb):
        try:
            design = adsk.fusion.Design.cast(app.activeProduct)
            lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            if lib:
                base = lib.appearances.itemByName("Plastic - Matte (Generic)")
                if base:
                    appear = design.appearances.addByCopy(base, f"c_{rgb[0]}_{rgb[1]}_{rgb[2]}_{body.name}")
                    prop = appear.appearanceProperties.itemByName("Color")
                    if prop:
                        adsk.core.ColorProperty.cast(prop).value = adsk.core.Color.create(rgb[0], rgb[1], rgb[2], 255)
                    body.appearance = appear
        except:
            pass

    def make_cylinder(comp, name, cx, cy, z, radius, height, color=None):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(cm(cx), cm(cy), 0), cm(radius))
        prof = None
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if prof is None or p.areaProperties().area < prof.areaProperties().area:
                prof = p
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if z != 0:
            start = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(cm(z)))
            inp.startExtent = start
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(height)))
        result = ext.add(inp)
        body = result.bodies.item(0)
        body.name = name
        if color:
            set_color(app, body, color)
        return body

    def make_box(comp, name, x, y, z, w, d, h, color=None):
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(cm(x), cm(y), 0),
            adsk.core.Point3D.create(cm(x + w), cm(y + d), 0))
        prof = sk.profiles.item(0)
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if z != 0:
            start = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(cm(z)))
            inp.startExtent = start
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(h)))
        result = ext.add(inp)
        body = result.bodies.item(0)
        body.name = name
        if color:
            set_color(app, body, color)
        return body

    try:
        parts_created = []

        # ═══════════════════════════════════════════
        # 1. NTC GLASS BEAD THERMISTOR
        #    3mm sphere + 2 wire leads (0.3mm × 15mm)
        # ═══════════════════════════════════════════
        occ1 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c1 = occ1.component
        c1.name = "NTC_Thermistor"

        # Glass bead: sphere via revolve (semicircle revolved 360°)
        sk_sphere = c1.sketches.add(c1.xZConstructionPlane)
        center_pt = adsk.core.Point3D.create(0, 0, 0)
        # Draw semicircle: arc from (0, 1.5mm) to (0, -1.5mm) through (1.5mm, 0)
        sk_sphere.sketchCurves.sketchArcs.addByThreePoints(
            adsk.core.Point3D.create(0, cm(1.5), 0),
            adsk.core.Point3D.create(cm(1.5), 0, 0),
            adsk.core.Point3D.create(0, cm(-1.5), 0))
        # Close with a line on the axis
        sk_sphere.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, cm(-1.5), 0),
            adsk.core.Point3D.create(0, cm(1.5), 0))

        # Find the closed profile
        sphere_prof = None
        for i in range(sk_sphere.profiles.count):
            p = sk_sphere.profiles.item(i)
            if sphere_prof is None or p.areaProperties().area > sphere_prof.areaProperties().area:
                sphere_prof = p

        if sphere_prof:
            # Revolve axis = the vertical line
            axis_line = None
            for i in range(sk_sphere.sketchCurves.sketchLines.count):
                axis_line = sk_sphere.sketchCurves.sketchLines.item(i)
                break

            if axis_line:
                revolves = c1.features.revolveFeatures
                rev_inp = revolves.createInput(sphere_prof, axis_line,
                    adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                rev_inp.setAngleExtent(False, adsk.core.ValueInput.createByReal(math.pi * 2))
                rev_result = revolves.add(rev_inp)
                bead = rev_result.bodies.item(0)
                bead.name = "Glass_Bead"
                set_color(app, bead, (50, 180, 80))  # green glass

        # Wire leads
        make_cylinder(c1, "Wire_Lead_1", 0, 0, -15, 0.15, 15, (200, 130, 50))
        make_cylinder(c1, "Wire_Lead_2", 0.5, 0, -15, 0.15, 15, (200, 130, 50))

        parts_created.append("NTC Thermistor (sphere + 2 wire leads)")

        # ═══════════════════════════════════════════
        # 2. NICHROME HEATER COIL
        #    Using stacked rings to approximate a coil
        #    8mm OD, 4mm core, 40mm tall, ~8 turns
        # ═══════════════════════════════════════════
        occ2 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c2 = occ2.component
        c2.name = "Nichrome_Heater_Coil"

        # Center core rod (ceramic insulator, 4mm dia)
        make_cylinder(c2, "Ceramic_Core", 0, 0, 0, 2, 40, (220, 210, 190))

        # Coil turns — ring torus approximated as offset ring cylinders
        for turn in range(8):
            z_pos = 2 + turn * 4.5
            # Each coil ring: outer ring
            make_cylinder(c2, f"Coil_Outer_{turn}", 0, 0, z_pos, 4, 1.5, (200, 60, 40))

        # Lead wires at top
        make_cylinder(c2, "Heater_Lead_Pos", 3, 0, 38, 0.4, 15, (200, 60, 40))
        make_cylinder(c2, "Heater_Lead_Neg", -3, 0, 38, 0.4, 15, (200, 60, 40))

        parts_created.append("Nichrome Heater Coil (ceramic core + 8 rings + leads)")

        # ═══════════════════════════════════════════
        # 3. PLATINUM CONDUCTIVITY ELECTRODE
        #    Ring: 24mm OD, 20mm ID, 2mm thick
        #    Create 1 — user copies 4 times
        # ═══════════════════════════════════════════
        occ3 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c3 = occ3.component
        c3.name = "Pt_Conductivity_Electrode"

        sk_ring = c3.sketches.add(c3.xYConstructionPlane)
        sk_ring.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(12))  # 24mm OD
        sk_ring.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(10))  # 20mm ID

        # Find the ring profile (between inner and outer circles)
        ring_prof = None
        target_area = math.pi * (cm(12)**2 - cm(10)**2)
        for i in range(sk_ring.profiles.count):
            p = sk_ring.profiles.item(i)
            a = p.areaProperties().area
            if abs(a - target_area) / target_area < 0.3:
                ring_prof = p
                break

        if ring_prof:
            ext3 = c3.features.extrudeFeatures
            ring_inp = ext3.createInput(ring_prof,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            ring_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(2)))
            ring_result = ext3.add(ring_inp)
            electrode = ring_result.bodies.item(0)
            electrode.name = "Platinum_Ring"
            set_color(app, electrode, (200, 200, 210))  # platinum/silver

        parts_created.append("Platinum Electrode Ring (24mm OD, 20mm ID, 2mm thick)")

        # ═══════════════════════════════════════════
        # 4. PT1000 RTD SENSOR
        #    4mm dia × 8mm ceramic body + 3 wire leads
        # ═══════════════════════════════════════════
        occ4 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c4 = occ4.component
        c4.name = "PT1000_RTD"

        make_cylinder(c4, "Ceramic_Body", 0, 0, 0, 2, 8, (240, 240, 240))
        # 3-wire leads (red, red, white)
        make_cylinder(c4, "Wire_Red_1", -0.8, 0, 8, 0.15, 20, (200, 50, 50))
        make_cylinder(c4, "Wire_Red_2", 0, 0, 8, 0.15, 20, (200, 50, 50))
        make_cylinder(c4, "Wire_White", 0.8, 0, 8, 0.15, 20, (240, 240, 240))

        # Rounded tip on ceramic body
        try:
            for body in c4.bRepBodies:
                if body.name == "Ceramic_Body":
                    for face in body.faces:
                        _, n = face.evaluator.getNormalAtPoint(face.pointOnFace)
                        if n and n.z < -0.9:  # bottom face
                            for edge in face.edges:
                                edges_coll = adsk.core.ObjectCollection.create()
                                edges_coll.add(edge)
                                fi = c4.features.filletFeatures.createInput()
                                fi.addConstantRadiusEdgeSet(edges_coll,
                                    adsk.core.ValueInput.createByReal(cm(0.8)), False)
                                c4.features.filletFeatures.add(fi)
                                break
                            break
        except:
            pass

        parts_created.append("PT1000 RTD (ceramic cylinder + 3-wire leads, filleted tip)")

        # ═══════════════════════════════════════════
        # 5. ATLAS EZO-EC CIRCUIT BOARD
        #    13.97 × 20.16 × 1.6mm PCB
        #    + IC chip, gold pads, LED
        # ═══════════════════════════════════════════
        occ5 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c5 = occ5.component
        c5.name = "Atlas_EZO_EC"

        make_box(c5, "EZO_PCB", -7, -10, 0, 13.97, 20.16, 1.6, (50, 20, 100))
        make_box(c5, "EZO_Main_IC", -4, -6, 1.6, 6, 6, 1.2, (30, 30, 30))
        make_box(c5, "EZO_Pads_Top", -5, 6, 1.6, 10, 3, 0.3, (210, 185, 80))
        make_box(c5, "EZO_Pads_Bottom", -5, -10, 1.6, 10, 3, 0.3, (210, 185, 80))
        make_box(c5, "EZO_LED", 3, -3, 1.6, 1.6, 1.2, 0.8, (50, 200, 80))
        # Small passives on board
        make_box(c5, "EZO_Cap_1", -2, 2, 1.6, 1.5, 0.8, 0.5, (180, 150, 80))
        make_box(c5, "EZO_Cap_2", 1, 2, 1.6, 1.5, 0.8, 0.5, (180, 150, 80))
        make_box(c5, "EZO_Res_1", -2, 4, 1.6, 1.5, 0.8, 0.5, (20, 20, 20))

        parts_created.append("Atlas EZO-EC Board (PCB + IC + pads + LED + passives)")

        # ═══════════════════════════════════════════
        # 6. PROBE OUTER TUBE with 8 FLOW SLOTS
        #    45mm OD, 40mm ID, 300mm long
        #    8 slots: 5mm wide × 60mm tall at mid-section
        # ═══════════════════════════════════════════
        occ6 = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        c6 = occ6.component
        c6.name = "Probe_Outer_Tube"

        # Create hollow tube via sketch with two circles
        sk_tube = c6.sketches.add(c6.xYConstructionPlane)
        sk_tube.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(22.5))  # 45mm OD
        sk_tube.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(20))    # 40mm ID

        # Find the ring profile
        tube_prof = None
        wall_area = math.pi * (cm(22.5)**2 - cm(20)**2)
        for i in range(sk_tube.profiles.count):
            p = sk_tube.profiles.item(i)
            a = p.areaProperties().area
            if abs(a - wall_area) / wall_area < 0.3:
                tube_prof = p
                break

        if tube_prof:
            ext6 = c6.features.extrudeFeatures
            tube_inp = ext6.createInput(tube_prof,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            tube_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(300)))
            tube_result = ext6.add(tube_inp)
            tube_body = tube_result.bodies.item(0)
            tube_body.name = "Outer_Tube"
            set_color(app, tube_body, (60, 60, 65))

        # Cut 8 flow slots at z=120 to z=180 (60mm tall)
        slot_z = cm(120)
        slot_h = cm(60)
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            # Slot center on the outer wall
            sx = 21.25 * math.cos(rad)  # midpoint of wall thickness
            sy = 21.25 * math.sin(rad)

            # Create construction plane at the slot height
            plane_inp = c6.constructionPlanes.createInput()
            plane_inp.setByOffset(c6.xYConstructionPlane,
                adsk.core.ValueInput.createByReal(slot_z))
            slot_plane = c6.constructionPlanes.add(plane_inp)

            # Sketch a small rectangle at the wall position
            sk_slot = c6.sketches.add(slot_plane)
            # Rectangle oriented radially: 5mm wide × 2.5mm deep (through wall)
            # Tangent direction
            tx = -math.sin(rad)
            ty = math.cos(rad)

            half_w = cm(2.5)  # tangential half-width
            half_d = cm(2.5)  # radial half-depth (through wall)
            rx = math.cos(rad)
            ry = math.sin(rad)
            cx_s, cy_s = cm(sx), cm(sy)

            c1 = adsk.core.Point3D.create(cx_s - half_w*tx - half_d*rx,
                                           cy_s - half_w*ty - half_d*ry, 0)
            c2 = adsk.core.Point3D.create(cx_s + half_w*tx - half_d*rx,
                                           cy_s + half_w*ty - half_d*ry, 0)
            c3 = adsk.core.Point3D.create(cx_s + half_w*tx + half_d*rx,
                                           cy_s + half_w*ty + half_d*ry, 0)
            c4 = adsk.core.Point3D.create(cx_s - half_w*tx + half_d*rx,
                                           cy_s - half_w*ty + half_d*ry, 0)

            lines = sk_slot.sketchCurves.sketchLines
            lines.addByTwoPoints(c1, c2)
            lines.addByTwoPoints(c2, c3)
            lines.addByTwoPoints(c3, c4)
            lines.addByTwoPoints(c4, c1)

            # Find smallest profile and cut
            cut_prof = None
            for i in range(sk_slot.profiles.count):
                p = sk_slot.profiles.item(i)
                if cut_prof is None or p.areaProperties().area < cut_prof.areaProperties().area:
                    cut_prof = p

            if cut_prof:
                try:
                    cut_ext = c6.features.extrudeFeatures
                    cut_inp = cut_ext.createInput(cut_prof,
                        adsk.fusion.FeatureOperations.CutFeatureOperation)
                    cut_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(slot_h))
                    cut_ext.add(cut_inp)
                except:
                    pass

        parts_created.append("Probe Tube (hollow, 45/40mm, 300mm, 8 flow slots)")

        msg = f"Created {len(parts_created)} custom probe parts!\n\n"
        for i, p in enumerate(parts_created, 1):
            msg += f"{i}. {p}\n"
        msg += "\nEach is a separate component in the browser.\n"
        msg += "Export each as .step: right-click component → Save As → .step"
        ui.messageBox(msg)

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
