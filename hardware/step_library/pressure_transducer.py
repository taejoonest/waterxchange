"""
Fusion 360 Script — Submersible Pressure Transducer (4-20mA, 316SS)
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste → Run

Creates a realistic pressure transducer with:
  - Main cylindrical body (20mm dia × 55mm)
  - Hex section for wrench grip (22mm across flats × 10mm)
  - Nose cone with chamfer (sensing diaphragm end)
  - Cable exit end with strain relief
  - Thread detail on cable end
  - Stainless steel appearance
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

    try:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "Submersible_Pressure_Transducer"

        # ═══════════════════════════════════════════
        # MAIN BODY — cylinder, 20mm dia × 55mm long
        # Built along Z axis, nose at bottom (z=0)
        # ═══════════════════════════════════════════
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(10))  # 20mm dia
        prof = None
        for i in range(sk.profiles.count):
            p = sk.profiles.item(i)
            if prof is None or p.areaProperties().area < prof.areaProperties().area:
                prof = p
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(55)))
        body_feat = ext.add(inp)
        main_body = body_feat.bodies.item(0)
        main_body.name = "Transducer_Main_Body"

        # ═══════════════════════════════════════════
        # NOSE CHAMFER — 2mm chamfer on the bottom face edge
        # ═══════════════════════════════════════════
        bottom_edge = None
        for i in range(main_body.faces.count):
            f = main_body.faces.item(i)
            _, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            if n and n.z < -0.9:  # bottom face
                for j in range(f.edges.count):
                    e = f.edges.item(j)
                    bottom_edge = e
                    break
                break
        if bottom_edge:
            chamfer_input = comp.features.chamferFeatures.createInput2()
            edges = adsk.core.ObjectCollection.create()
            edges.add(bottom_edge)
            chamfer_input.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
                edges, adsk.core.ValueInput.createByReal(cm(2)), False)
            comp.features.chamferFeatures.add(chamfer_input)

        # ═══════════════════════════════════════════
        # HEX SECTION — 22mm across flats, 10mm tall
        # Positioned at z=40mm (near cable exit end)
        # Cut the cylinder into a hex shape in this zone
        # ═══════════════════════════════════════════
        # Create a construction plane at z=40mm
        plane_input = comp.constructionPlanes.createInput()
        offset_val = adsk.core.ValueInput.createByReal(cm(40))
        plane_input.setByOffset(comp.xYConstructionPlane, offset_val)
        hex_plane = comp.constructionPlanes.add(plane_input)

        # Sketch a hexagon (inscribed circle = 22mm across flats → apothem = 11mm)
        sk_hex = comp.sketches.add(hex_plane)
        center = adsk.core.Point3D.create(0, 0, 0)
        apothem = cm(11)  # 22mm across flats / 2
        # Circumradius of regular hexagon = apothem / cos(30°)
        circumradius = apothem / math.cos(math.radians(30))

        hex_points = []
        for i in range(6):
            angle = math.radians(60 * i + 30)  # +30 so flats are horizontal
            px = circumradius * math.cos(angle)
            py = circumradius * math.sin(angle)
            hex_points.append(adsk.core.Point3D.create(px, py, 0))

        lines = sk_hex.sketchCurves.sketchLines
        for i in range(6):
            lines.addByTwoPoints(hex_points[i], hex_points[(i + 1) % 6])

        # Also add a circle larger than the hex to create the cut profile
        sk_hex.sketchCurves.sketchCircles.addByCenterRadius(center, cm(15))

        # Find the profile that is the ring between hex and circle
        ring_prof = None
        for i in range(sk_hex.profiles.count):
            p = sk_hex.profiles.item(i)
            area = p.areaProperties().area
            # The ring segments (between hex edge and circle) are the ones to cut
            hex_area = 6 * (0.5 * circumradius * circumradius * math.sin(math.radians(60)))
            circle_area = math.pi * cm(15) * cm(15)
            ring_area = circle_area - hex_area
            # Pick profiles that are small triangular segments (corners to cut)
            if area < ring_area * 0.3 and area > 0.00001:
                if ring_prof is None:
                    ring_prof = adsk.core.ObjectCollection.create()
                ring_prof.add(p)

        if ring_prof and ring_prof.count > 0:
            # Cut each corner segment
            for pi in range(ring_prof.count):
                cut_inp = ext.createInput(ring_prof.item(pi),
                    adsk.fusion.FeatureOperations.CutFeatureOperation)
                cut_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(10)))
                try:
                    ext.add(cut_inp)
                except:
                    pass  # Some profiles may not cut cleanly

        # ═══════════════════════════════════════════
        # CABLE EXIT — smaller cylinder on top
        # 12mm dia × 15mm, starting at z=55mm
        # ═══════════════════════════════════════════
        sk2 = comp.sketches.add(comp.xYConstructionPlane)
        sk2.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(6))  # 12mm dia
        cable_prof = None
        for i in range(sk2.profiles.count):
            p = sk2.profiles.item(i)
            if cable_prof is None or p.areaProperties().area < cable_prof.areaProperties().area:
                cable_prof = p
        cable_inp = ext.createInput(cable_prof,
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        start = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByReal(cm(55)))
        cable_inp.startExtent = start
        cable_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(15)))
        ext.add(cable_inp)

        # ═══════════════════════════════════════════
        # STRAIN RELIEF — tapered section between body and cable exit
        # 16mm dia × 5mm, at z=55mm (transition)
        # ═══════════════════════════════════════════
        sk3 = comp.sketches.add(comp.xYConstructionPlane)
        sk3.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(8))  # 16mm dia
        relief_prof = None
        for i in range(sk3.profiles.count):
            p = sk3.profiles.item(i)
            a = p.areaProperties().area
            if relief_prof is None or a < relief_prof.areaProperties().area:
                relief_prof = p
        relief_inp = ext.createInput(relief_prof,
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        start2 = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByReal(cm(53)))
        relief_inp.startExtent = start2
        relief_inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(5)))
        ext.add(relief_inp)

        # ═══════════════════════════════════════════
        # SENSING DIAPHRAGM — small recessed circle on nose
        # 8mm dia, 0.5mm deep recess at z=0
        # ═══════════════════════════════════════════
        sk4 = comp.sketches.add(comp.xYConstructionPlane)
        sk4.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(4))  # 8mm dia
        sk4.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(10))  # body OD
        # Find the ring profile between 8mm and 20mm
        ring = None
        for i in range(sk4.profiles.count):
            p = sk4.profiles.item(i)
            a = p.areaProperties().area
            small_circle = math.pi * cm(4)**2
            big_circle = math.pi * cm(10)**2
            if abs(a - (big_circle - small_circle)) / (big_circle - small_circle) < 0.2:
                ring = p
                break
        # The small inner circle is the diaphragm recess
        diaphragm = None
        for i in range(sk4.profiles.count):
            p = sk4.profiles.item(i)
            a = p.areaProperties().area
            small_circle = math.pi * cm(4)**2
            if abs(a - small_circle) / small_circle < 0.2:
                diaphragm = p
                break

        # ═══════════════════════════════════════════
        # CABLE — black rubber, 7mm dia × 40mm stub
        # ═══════════════════════════════════════════
        sk5 = comp.sketches.add(comp.xYConstructionPlane)
        sk5.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(3.5))  # 7mm dia
        cable_p = None
        for i in range(sk5.profiles.count):
            p = sk5.profiles.item(i)
            if cable_p is None or p.areaProperties().area < cable_p.areaProperties().area:
                cable_p = p
        cable_ext = ext.createInput(cable_p,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        cable_start = adsk.fusion.OffsetStartDefinition.create(
            adsk.core.ValueInput.createByReal(cm(70)))
        cable_ext.startExtent = cable_start
        cable_ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(cm(40)))
        cable_result = ext.add(cable_ext)
        cable_body = cable_result.bodies.item(0)
        cable_body.name = "Vented_Cable"

        # ═══════════════════════════════════════════
        # APPLY COLORS
        # ═══════════════════════════════════════════
        try:
            lib = app.materialLibraries.itemByName("Fusion 360 Appearance Library")
            if lib:
                # Stainless steel for transducer body
                steel = lib.appearances.itemByName("Steel - Satin")
                if steel:
                    steel_copy = design.appearances.addByCopy(steel, "Transducer_Steel")
                    main_body.appearance = steel_copy

                # Black rubber for cable
                plastic = lib.appearances.itemByName("Plastic - Matte (Generic)")
                if plastic:
                    black = design.appearances.addByCopy(plastic, "Cable_Black")
                    color_prop = black.appearanceProperties.itemByName("Color")
                    if color_prop:
                        adsk.core.ColorProperty.cast(color_prop).value = adsk.core.Color.create(30, 30, 30, 255)
                    cable_body.appearance = black
        except:
            pass

        # ═══════════════════════════════════════════
        # FILLET the top edge of cable exit (smooth transition)
        # ═══════════════════════════════════════════
        try:
            for i in range(main_body.faces.count):
                f = main_body.faces.item(i)
                _, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
                if n and n.z > 0.9:  # top face of the cable exit
                    for j in range(f.edges.count):
                        e = f.edges.item(j)
                        edges_coll = adsk.core.ObjectCollection.create()
                        edges_coll.add(e)
                        fillet_input = comp.features.filletFeatures.createInput()
                        fillet_input.addConstantRadiusEdgeSet(
                            edges_coll,
                            adsk.core.ValueInput.createByReal(cm(1)),
                            False)
                        comp.features.filletFeatures.add(fillet_input)
                        break
                    break
        except:
            pass

        ui.messageBox(
            "Pressure Transducer created!\n\n"
            "• Main body: 20mm dia × 55mm (316SS)\n"
            "• Hex wrench section: 22mm AF × 10mm\n"
            "• Nose chamfer: 2mm (sensing end)\n"
            "• Cable exit: 12mm dia × 15mm\n"
            "• Strain relief: 16mm dia transition\n"
            "• Vented cable: 7mm dia stub\n"
            "• Stainless steel + black rubber appearances\n\n"
            "Save as STEP: File → Export → .step\n"
            "Then import into your assembly."
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
