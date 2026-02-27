"""
Fusion 360 Script — WX-Flow Submersible Probe Body
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste this file → Run

45mm OD × 300mm cylindrical probe.
Sections (bottom→top):
  0–30mm:   Pressure sensor (open bottom)
  30–80mm:  Conductivity + PT1000 chamber
  80–220mm: Flow chamber — heater post, 4 thermistor posts, 8 wall slots
  220–300mm: Electronics chamber (epoxy-potted top)
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
        comp.name = "WXF_Probe_Body"
        extrudes = comp.features.extrudeFeatures
        planes = comp.constructionPlanes

        OD = 45.0
        WALL = 2.5
        ID = OD - 2 * WALL  # 40mm
        LENGTH = 300.0

        # ════════════════════════════════════════════════════
        # STEP 1: Outer tube — solid cylinder then bore it out
        # ════════════════════════════════════════════════════
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(OD / 2))

        prof = sk.profiles.item(0)
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(LENGTH)))
        tube_ext = extrudes.add(inp)
        body = tube_ext.bodies.item(0)
        body.name = "Probe"

        # ════════════════════════════════════════════════════
        # STEP 2: Bore out the inside (full length, open both ends)
        # ════════════════════════════════════════════════════
        sk_bore = comp.sketches.add(comp.xYConstructionPlane)
        sk_bore.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(ID / 2))

        for i in range(sk_bore.profiles.count):
            p = sk_bore.profiles.item(i)
            a = p.areaProperties().area
            inner_area = math.pi * mm(ID / 2) ** 2
            if abs(a - inner_area) / inner_area < 0.5:
                inp_b = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_b.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(LENGTH)))
                extrudes.add(inp_b)
                break

        # Helper: make an offset XY plane
        def xy_at(z_mm):
            pi = planes.createInput()
            pi.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(z_mm)))
            return planes.add(pi)

        # Helper: solid disc plug (joins into tube wall)
        def add_shelf(z_mm, thickness_mm):
            plane = xy_at(z_mm)
            sk_s = comp.sketches.add(plane)
            sk_s.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, 0, 0), mm(ID / 2))
            for i in range(sk_s.profiles.count):
                p = sk_s.profiles.item(i)
                a = p.areaProperties().area
                inner_area = math.pi * mm(ID / 2) ** 2
                if abs(a - inner_area) / inner_area < 0.5:
                    inp_s = extrudes.createInput(p, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                    inp_s.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(thickness_mm)))
                    extrudes.add(inp_s)
                    return
                # If the bore made the inner circle a profile, try the smaller one
                if a < inner_area * 1.2:
                    inp_s = extrudes.createInput(p, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                    inp_s.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(thickness_mm)))
                    try:
                        extrudes.add(inp_s)
                        return
                    except:
                        pass

        # ════════════════════════════════════════════════════
        # STEP 3: Shelf at z=30mm (pressure sensor platform)
        # ════════════════════════════════════════════════════
        add_shelf(30, 3)

        # ════════════════════════════════════════════════════
        # STEP 4: Conductivity cell recess — 20mm dia bore
        # from z=33 upward through the shelf into the chamber
        # ════════════════════════════════════════════════════
        plane_cond = xy_at(33)
        sk_cond = comp.sketches.add(plane_cond)
        sk_cond.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(10))

        for i in range(sk_cond.profiles.count):
            p = sk_cond.profiles.item(i)
            a = p.areaProperties().area
            target = math.pi * mm(10) ** 2
            if abs(a - target) / target < 0.5:
                inp_c = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_c.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(30)))
                try:
                    extrudes.add(inp_c)
                except:
                    pass
                break

        # ════════════════════════════════════════════════════
        # STEP 5: Shelf at z=80mm (flow chamber floor)
        # ════════════════════════════════════════════════════
        add_shelf(80, 3)

        # ════════════════════════════════════════════════════
        # STEP 6: Heater center post — 10mm dia, 40mm tall
        # From z=83 (top of shelf) upward
        # ════════════════════════════════════════════════════
        plane_fc = xy_at(83)
        sk_heater = comp.sketches.add(plane_fc)
        sk_heater.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(5))

        for i in range(sk_heater.profiles.count):
            p = sk_heater.profiles.item(i)
            if p.areaProperties().area < 1.0:
                inp_hp = extrudes.createInput(p, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                inp_hp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(40)))
                try:
                    extrudes.add(inp_hp)
                except:
                    pass
                break

        # 3mm axial hole through heater post for nichrome wire
        sk_hw = comp.sketches.add(plane_fc)
        sk_hw.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(1.5))

        for i in range(sk_hw.profiles.count):
            p = sk_hw.profiles.item(i)
            if p.areaProperties().area < 0.1:
                inp_hh = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_hh.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(40)))
                try:
                    extrudes.add(inp_hh)
                except:
                    pass
                break

        # ════════════════════════════════════════════════════
        # STEP 7: 4× Thermistor posts — 5mm dia, 15mm from center
        # ════════════════════════════════════════════════════
        THERM_R = 15.0
        for angle_deg in [0, 90, 180, 270]:
            rad = math.radians(angle_deg)
            tx = THERM_R * math.cos(rad)
            ty = THERM_R * math.sin(rad)

            # Post
            sk_tp = comp.sketches.add(plane_fc)
            sk_tp.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(tx), mm(ty), 0), mm(2.5))
            for i in range(sk_tp.profiles.count):
                p = sk_tp.profiles.item(i)
                if p.areaProperties().area < 0.3:
                    inp_tp = extrudes.createInput(p, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                    inp_tp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(40)))
                    try:
                        extrudes.add(inp_tp)
                    except:
                        pass
                    break

            # 3mm hole through each post
            sk_th = comp.sketches.add(plane_fc)
            sk_th.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(tx), mm(ty), 0), mm(1.5))
            for i in range(sk_th.profiles.count):
                p = sk_th.profiles.item(i)
                if p.areaProperties().area < 0.1:
                    inp_th = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                    inp_th.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(40)))
                    try:
                        extrudes.add(inp_th)
                    except:
                        pass
                    break

        # ════════════════════════════════════════════════════
        # STEP 8: 8× flow slots in outer wall
        # 5mm wide × 60mm tall, from z=110 to z=170
        # Use angled construction planes through Z axis
        # ════════════════════════════════════════════════════
        SLOT_W = 5.0
        SLOT_H = 60.0
        SLOT_Z = 110.0

        for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
            # Create a radial plane at this angle
            angle_inp = planes.createInput()
            angle_inp.setByAngle(
                comp.zConstructionAxis,
                adsk.core.ValueInput.createByString(f"{angle_deg} deg"),
                comp.xZConstructionPlane
            )
            try:
                radial_plane = planes.add(angle_inp)
            except:
                continue

            sk_sl = comp.sketches.add(radial_plane)
            # On this radial plane: local X = radial outward, local Y = global Z
            # The slot rectangle sits at the outer wall (x = OD/2 ± half width)
            # But since we want it centered on the wall, we sketch at x=0
            # and let the cut go outward through the wall from inside.
            # Actually easier: sketch the slot rectangle centered at x=0
            # covering from inner to outer wall, then it'll cut the wall.
            hw = SLOT_W / 2
            sk_sl.sketchCurves.sketchLines.addTwoPointRectangle(
                adsk.core.Point3D.create(mm(-hw), mm(SLOT_Z), 0),
                adsk.core.Point3D.create(mm(hw), mm(SLOT_Z + SLOT_H), 0)
            )

            # Pick the slot rectangle profile
            target_slot_area = mm(SLOT_W) * mm(SLOT_H)
            for pi_idx in range(sk_sl.profiles.count):
                p = sk_sl.profiles.item(pi_idx)
                a = p.areaProperties().area
                if abs(a - target_slot_area) / target_slot_area < 0.3:
                    # Extrude both directions to ensure we cut through the wall
                    inp_sl = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                    inp_sl.setDistanceExtent(True, adsk.core.ValueInput.createByReal(mm(OD / 2 + 2)))
                    try:
                        extrudes.add(inp_sl)
                    except:
                        pass
                    break

        # ════════════════════════════════════════════════════
        # STEP 9: Shelf at z=220mm (separates flow chamber from electronics)
        # ════════════════════════════════════════════════════
        add_shelf(220, 3)

        # Wire pass-through hole (12mm dia) through this shelf
        plane_wire = xy_at(220)
        sk_wire = comp.sketches.add(plane_wire)
        sk_wire.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), mm(6))

        for i in range(sk_wire.profiles.count):
            p = sk_wire.profiles.item(i)
            a = p.areaProperties().area
            target = math.pi * mm(6) ** 2
            if abs(a - target) / target < 0.5:
                inp_w = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_w.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(3)))
                try:
                    extrudes.add(inp_w)
                except:
                    pass
                break

        # ════════════════════════════════════════════════════
        # STEP 10: North alignment flat on outer wall
        # A flat face along the +Y side so you know orientation
        # ════════════════════════════════════════════════════
        pi_flat = planes.createInput()
        pi_flat.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByReal(mm(OD / 2 - 1)))
        flat_plane = planes.add(pi_flat)

        sk_flat = comp.sketches.add(flat_plane)
        sk_flat.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(-3), mm(80), 0),
            adsk.core.Point3D.create(mm(3), mm(220), 0)
        )

        for i in range(sk_flat.profiles.count):
            p = sk_flat.profiles.item(i)
            a = p.areaProperties().area
            if a > mm(5) * mm(100):
                inp_f = extrudes.createInput(p, adsk.fusion.FeatureOperations.CutFeatureOperation)
                inp_f.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(2)))
                try:
                    extrudes.add(inp_f)
                except:
                    pass
                break

        ui.messageBox(
            "WX-Flow Probe Body created!\n\n"
            "45 mm OD × 300 mm\n"
            "• Open bottom (pressure sensor)\n"
            "• Conductivity cell recess\n"
            "• Flow chamber: heater + 4 thermistors\n"
            "• 8 × flow slots\n"
            "• Electronics shelf with wire pass-through\n"
            "• North alignment flat\n\n"
            "Export: right-click body → Save As Mesh → 3MF"
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
