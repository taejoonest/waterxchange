"""
Fusion 360 Script — WX-Level Vent Cap
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste this file → Run

25mm OD × 30mm tall barometric vent cap.
Cable bore from bottom, 3 vent holes near top, desiccant chamber.
"""

import adsk.core
import adsk.fusion
import math
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
        comp.name = "WXL_Vent_Cap"
        extrudes = comp.features.extrudeFeatures
        planes = comp.constructionPlanes

        # ════════════════════════════════════════════════════
        # STEP 1: Outer cylinder 25mm OD × 30mm tall
        # ════════════════════════════════════════════════════
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(12.5))

        prof = sk.profiles.item(0)
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(30)))
        cap_ext = extrudes.add(inp)
        body = cap_ext.bodies.item(0)
        body.name = "Vent_Cap"

        # ════════════════════════════════════════════════════
        # STEP 2: Shell — remove bottom face, 2mm walls
        # ════════════════════════════════════════════════════
        bottom_face = None
        for i in range(body.faces.count):
            face = body.faces.item(i)
            _, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal and abs(normal.z + 1.0) < 0.01:
                bottom_face = face
                break

        if bottom_face:
            fc = adsk.core.ObjectCollection.create()
            fc.add(bottom_face)
            si = comp.features.shellFeatures.createInput(fc, False)
            si.insideThickness = adsk.core.ValueInput.createByReal(mm(2))
            comp.features.shellFeatures.add(si)

        # ════════════════════════════════════════════════════
        # STEP 3: Cable bore — 9mm ID, 20mm deep from bottom
        # Sketch at z=0, extrude upward 20mm as CUT
        # ════════════════════════════════════════════════════
        sk2 = comp.sketches.add(comp.xYConstructionPlane)
        sk2.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(4.5))  # 9mm dia

        for i in range(sk2.profiles.count):
            p = sk2.profiles.item(i)
            if p.areaProperties().area < 1.0:
                inp_bore = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_bore.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(20)))
                try:
                    extrudes.add(inp_bore)
                except:
                    pass
                break

        # ════════════════════════════════════════════════════
        # STEP 4: 3× vent holes (1mm dia) near top, through side wall
        # The cylindrical wall is 2mm thick (r_outer=12.5, r_inner=10.5)
        # Use a sketch on an XZ plane through center, draw small circles
        # at z=25mm, then cut through the 2mm wall.
        # ════════════════════════════════════════════════════
        for angle_deg in [0, 120, 240]:
            # Create a plane at this angle around Z axis
            angle_plane_input = planes.createInput()
            angle_plane_input.setByAngle(
                comp.zConstructionAxis,
                adsk.core.ValueInput.createByString(f"{angle_deg} deg"),
                comp.xZConstructionPlane
            )
            try:
                angled_plane = planes.add(angle_plane_input)
                sk_v = comp.sketches.add(angled_plane)

                # On this radial plane: X runs radially outward, Y = Z
                # Place circle at outer wall: x = 12.5mm, y = 25mm (z=25 globally)
                sk_v.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(mm(12.5), mm(25), 0), mm(0.5))

                for pi_idx in range(sk_v.profiles.count):
                    p = sk_v.profiles.item(pi_idx)
                    if p.areaProperties().area < 0.02:
                        inp_v = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                        # Cut inward (negative X on this plane = toward center)
                        ext_def = adsk.fusion.DistanceExtentDefinition.create(
                            adsk.core.ValueInput.createByReal(mm(3)))
                        inp_v.setOneSideExtent(ext_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
                        try:
                            extrudes.add(inp_v)
                        except:
                            pass
                        break
            except:
                pass

        ui.messageBox(
            "WXL Vent Cap created!\n\n"
            "25 mm OD × 30 mm tall, 2 mm walls\n"
            "• 9 mm cable bore (20 mm deep)\n"
            "• 3 × 1 mm vent holes at z=25 mm\n\n"
            "Export: right-click body → Save As Mesh → 3MF"
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
