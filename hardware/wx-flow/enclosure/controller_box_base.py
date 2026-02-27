"""
Fusion 360 Script — WX-Flow Controller Box BASE (3 cable glands)
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste this file → Run

Same as WX-Level box but with 3× M12 cable glands for the extra probe cable.
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

    def cut_down(comp, profile, depth_mm):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        extent_def = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(mm(depth_mm)))
        inp.setOneSideExtent(extent_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        return ext.add(inp)

    def cut_positive(comp, profile, depth_mm):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(depth_mm)))
        return ext.add(inp)

    def cut_negative(comp, profile, depth_mm):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        extent_def = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(mm(depth_mm)))
        inp.setOneSideExtent(extent_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        return ext.add(inp)

    def join_up(comp, profile, height_mm):
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(height_mm)))
        return ext.add(inp)

    try:
        occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "WXF_Controller_Base"
        extrudes = comp.features.extrudeFeatures
        planes = comp.constructionPlanes

        # ── Outer box ───────────────────────────────────────
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(mm(160), mm(110), 0)
        )
        prof = sk.profiles.item(0)
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(30)))
        box_ext = extrudes.add(inp)
        body = box_ext.bodies.item(0)
        body.name = "Base"

        # ── Fillet vertical edges ───────────────────────────
        edge_coll = adsk.core.ObjectCollection.create()
        for i in range(body.edges.count):
            e = body.edges.item(i)
            p1, p2 = e.startVertex.geometry, e.endVertex.geometry
            if abs(p1.x - p2.x) < 0.001 and abs(p1.y - p2.y) < 0.001:
                if abs(abs(p1.z - p2.z) - mm(30)) < 0.01:
                    edge_coll.add(e)
        if edge_coll.count > 0:
            fi = comp.features.filletFeatures.createInput()
            fi.addConstantRadiusEdgeSet(edge_coll, adsk.core.ValueInput.createByReal(mm(5)), True)
            comp.features.filletFeatures.add(fi)

        # ── Shell (open top, 3mm walls) ─────────────────────
        top_face = None
        for i in range(body.faces.count):
            f = body.faces.item(i)
            _, n = f.evaluator.getNormalAtPoint(f.pointOnFace)
            if n and abs(n.z - 1.0) < 0.01:
                top_face = f
                break
        if not top_face:
            ui.messageBox("Cannot find top face"); return

        fc = adsk.core.ObjectCollection.create()
        fc.add(top_face)
        si = comp.features.shellFeatures.createInput(fc, False)
        si.insideThickness = adsk.core.ValueInput.createByReal(mm(3))
        comp.features.shellFeatures.add(si)

        # ── O-ring groove ───────────────────────────────────
        pi_top = planes.createInput()
        pi_top.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(30)))
        plane_top = planes.add(pi_top)

        sk2 = comp.sketches.add(plane_top)
        sk2.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(4.5), mm(4.5), 0),
            adsk.core.Point3D.create(mm(155.5), mm(105.5), 0))
        sk2.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(6.5), mm(6.5), 0),
            adsk.core.Point3D.create(mm(153.5), mm(103.5), 0))

        target_area = (mm(151) * mm(101)) - (mm(147) * mm(97))
        best_prof = None
        best_diff = 99999
        for i in range(sk2.profiles.count):
            p = sk2.profiles.item(i)
            diff = abs(p.areaProperties().area - target_area)
            if diff < best_diff:
                best_diff = diff
                best_prof = p
        if best_prof:
            try:
                cut_down(comp, best_prof, 2)
            except:
                pass

        # ── PCB Standoffs ───────────────────────────────────
        pi_floor = planes.createInput()
        pi_floor.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(3)))
        plane_floor = planes.add(pi_floor)

        standoff_pos = [(25, 35), (95, 35), (25, 75), (95, 75)]
        for (sx, sy) in standoff_pos:
            sk_so = comp.sketches.add(plane_floor)
            sk_so.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(sx), mm(sy), 0), mm(3))
            for pi_idx in range(sk_so.profiles.count):
                p = sk_so.profiles.item(pi_idx)
                if p.areaProperties().area < 0.5:
                    try: join_up(comp, p, 5)
                    except: pass
                    break

        for (sx, sy) in standoff_pos:
            pi_st = planes.createInput()
            pi_st.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(8)))
            pst = planes.add(pi_st)
            sk_h = comp.sketches.add(pst)
            sk_h.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(sx), mm(sy), 0), mm(1.25))
            for pi_idx in range(sk_h.profiles.count):
                p = sk_h.profiles.item(pi_idx)
                if p.areaProperties().area < 0.1:
                    try: cut_down(comp, p, 8)
                    except: pass
                    break

        # ── 3× Cable gland holes (KEY DIFFERENCE: 3 not 2) ─
        sk_gl = comp.sketches.add(comp.xYConstructionPlane)
        for (gx, gy) in [(40, 55), (80, 55), (120, 55)]:
            sk_gl.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(gx), mm(gy), 0), mm(6))
        for pi_idx in range(sk_gl.profiles.count):
            p = sk_gl.profiles.item(pi_idx)
            if p.areaProperties().area < 1.5:
                try: cut_positive(comp, p, 3)
                except: pass

        # ── SMA holes ───────────────────────────────────────
        sk_sma = comp.sketches.add(comp.xZConstructionPlane)
        sk_sma.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(60), mm(15), 0), mm(3.25))
        sk_sma.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(90), mm(15), 0), mm(3.25))
        for pi_idx in range(sk_sma.profiles.count):
            p = sk_sma.profiles.item(pi_idx)
            if p.areaProperties().area < 0.5:
                try: cut_positive(comp, p, 3)
                except: pass

        # ── Mounting slots on back wall ─────────────────────
        pi_bk = planes.createInput()
        pi_bk.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByReal(mm(110)))
        plane_bk = planes.add(pi_bk)
        sk_sl = comp.sketches.add(plane_bk)
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(47.5), mm(7.5), 0),
            adsk.core.Point3D.create(mm(52.5), mm(22.5), 0))
        sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(107.5), mm(7.5), 0),
            adsk.core.Point3D.create(mm(112.5), mm(22.5), 0))
        for pi_idx in range(sk_sl.profiles.count):
            p = sk_sl.profiles.item(pi_idx)
            if p.areaProperties().area < 1.0:
                try: cut_negative(comp, p, 3)
                except: pass

        # ── Screw bosses ────────────────────────────────────
        boss_pos = [(10, 10), (150, 10), (10, 100), (150, 100)]
        for (bx, by) in boss_pos:
            sk_b = comp.sketches.add(plane_floor)
            sk_b.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(bx), mm(by), 0), mm(4))
            for pi_idx in range(sk_b.profiles.count):
                p = sk_b.profiles.item(pi_idx)
                a = p.areaProperties().area
                if 0.3 < a < 0.7:
                    try: join_up(comp, p, 27)
                    except: pass
                    break

        for (bx, by) in boss_pos:
            sk_bh = comp.sketches.add(plane_top)
            sk_bh.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(bx), mm(by), 0), mm(1.25))
            for pi_idx in range(sk_bh.profiles.count):
                p = sk_bh.profiles.item(pi_idx)
                if p.areaProperties().area < 0.1:
                    try: cut_down(comp, p, 10)
                    except: pass
                    break

        ui.messageBox(
            "WX-Flow Controller Box BASE created!\n\n"
            "160 × 110 × 30 mm with 3 × M12 cable glands\n"
            "(probe + solar + pressure transducer)\n\n"
            "Export: right-click body → Save As Mesh → 3MF"
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
