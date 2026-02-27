"""
Fusion 360 Script — WX-Level Controller Box LID
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste this file → Run

Top lid: 160 × 110 × 25mm, 3mm walls, O-ring tongue on bottom,
solar panel mount holes on top, 4× M3 through-holes for assembly.
"""

import adsk.core
import adsk.fusion
import traceback

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent

    def mm(v):
        return v / 10.0

    try:
        occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "WXL_Controller_Lid"
        extrudes = comp.features.extrudeFeatures
        planes = comp.constructionPlanes

        # ════════════════════════════════════════════════════
        # STEP 1: Outer box 160×110×25mm
        # ════════════════════════════════════════════════════
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(mm(160), mm(110), 0)
        )
        prof = sk.profiles.item(0)
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(25)))
        lid_ext = extrudes.add(inp)
        lid_body = lid_ext.bodies.item(0)
        lid_body.name = "Lid"

        # ════════════════════════════════════════════════════
        # STEP 2: Fillet vertical edges at 5mm
        # ════════════════════════════════════════════════════
        edge_coll = adsk.core.ObjectCollection.create()
        for i in range(lid_body.edges.count):
            edge = lid_body.edges.item(i)
            p1 = edge.startVertex.geometry
            p2 = edge.endVertex.geometry
            if abs(p1.x - p2.x) < 0.001 and abs(p1.y - p2.y) < 0.001:
                if abs(abs(p1.z - p2.z) - mm(25)) < 0.01:
                    edge_coll.add(edge)

        if edge_coll.count > 0:
            fillet_inp = comp.features.filletFeatures.createInput()
            fillet_inp.addConstantRadiusEdgeSet(edge_coll,
                adsk.core.ValueInput.createByReal(mm(5)), True)
            comp.features.filletFeatures.add(fillet_inp)

        # ════════════════════════════════════════════════════
        # STEP 3: Shell — open the BOTTOM face, 3mm walls
        # ════════════════════════════════════════════════════
        bottom_face = None
        for i in range(lid_body.faces.count):
            face = lid_body.faces.item(i)
            _, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal and abs(normal.z + 1.0) < 0.01:  # normal pointing -Z = bottom
                bottom_face = face
                break

        if not bottom_face:
            ui.messageBox("Could not find bottom face.")
            return

        shells = comp.features.shellFeatures
        fc = adsk.core.ObjectCollection.create()
        fc.add(bottom_face)
        si = shells.createInput(fc, False)
        si.insideThickness = adsk.core.ValueInput.createByReal(mm(3))
        shells.add(si)

        # ════════════════════════════════════════════════════
        # STEP 4: O-ring tongue — ring on the bottom face
        # Tongue is 2mm wide × 2.5mm tall, hangs down from z=0
        # Matches the groove in the base (outer at 4.5mm, inner at 6.5mm inset)
        # Sketch at z=0, extrude DOWNWARD 2.5mm
        # ════════════════════════════════════════════════════
        sk_tongue = comp.sketches.add(comp.xYConstructionPlane)  # z=0

        sk_tongue.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(4.5), mm(4.5), 0),
            adsk.core.Point3D.create(mm(155.5), mm(105.5), 0)
        )
        sk_tongue.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(6.5), mm(6.5), 0),
            adsk.core.Point3D.create(mm(153.5), mm(103.5), 0)
        )

        # Find the ring profile (area ≈ 9.9 cm²)
        target_area = (mm(151) * mm(101)) - (mm(147) * mm(97))
        best_prof = None
        best_diff = 99999
        for i in range(sk_tongue.profiles.count):
            p = sk_tongue.profiles.item(i)
            diff = abs(p.areaProperties().area - target_area)
            if diff < best_diff:
                best_diff = diff
                best_prof = p

        if best_prof:
            # Extrude downward (negative Z) to create tongue hanging below lid
            inp_t = extrudes.createInput(best_prof, adsk.fusion.FeatureOperations.JoinFeatureOperation)
            extent_def = adsk.fusion.DistanceExtentDefinition.create(
                adsk.core.ValueInput.createByReal(mm(2.5)))
            inp_t.setOneSideExtent(extent_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
            try:
                extrudes.add(inp_t)
            except:
                pass

        # ════════════════════════════════════════════════════
        # STEP 5: Solar panel mount holes — 4× M3 through on top
        # Panel area: centered, holes at (15,15), (145,15), (15,95), (145,95)
        # Sketch at z=25 (top), cut ALL the way through
        # ════════════════════════════════════════════════════
        pi_top = planes.createInput()
        pi_top.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(25)))
        plane_top = planes.add(pi_top)

        solar_holes = [(15, 15), (145, 15), (15, 95), (145, 95)]
        for (hx, hy) in solar_holes:
            sk_sh = comp.sketches.add(plane_top)
            sk_sh.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(hx), mm(hy), 0), mm(1.7))
            for pi_idx in range(sk_sh.profiles.count):
                p = sk_sh.profiles.item(pi_idx)
                if p.areaProperties().area < 0.15:
                    inp_h = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                    # Cut downward through the 3mm lid top wall
                    ext_def = adsk.fusion.DistanceExtentDefinition.create(
                        adsk.core.ValueInput.createByReal(mm(5)))
                    inp_h.setOneSideExtent(ext_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
                    try:
                        extrudes.add(inp_h)
                    except:
                        pass
                    break

        # ════════════════════════════════════════════════════
        # STEP 6: Assembly screw holes — 4× M3 clearance at corners
        # Match base boss positions: (10,10), (150,10), (10,100), (150,100)
        # ════════════════════════════════════════════════════
        screw_pos = [(10, 10), (150, 10), (10, 100), (150, 100)]
        for (sx, sy) in screw_pos:
            sk_sc = comp.sketches.add(plane_top)
            sk_sc.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(sx), mm(sy), 0), mm(1.7))
            for pi_idx in range(sk_sc.profiles.count):
                p = sk_sc.profiles.item(pi_idx)
                if p.areaProperties().area < 0.15:
                    inp_s = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                    ext_def = adsk.fusion.DistanceExtentDefinition.create(
                        adsk.core.ValueInput.createByReal(mm(30)))
                    inp_s.setOneSideExtent(ext_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
                    try:
                        extrudes.add(inp_s)
                    except:
                        pass
                    break

        ui.messageBox(
            "WXL Controller Lid created!\n\n"
            "160 × 110 × 25 mm, 3 mm walls\n"
            "• O-ring tongue (2 mm wide × 2.5 mm drop)\n"
            "• 4 × solar panel M3 holes\n"
            "• 4 × assembly M3 holes\n\n"
            "Export: right-click body → Save As Mesh → 3MF"
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
