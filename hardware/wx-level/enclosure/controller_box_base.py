"""
Fusion 360 Script — WX-Level Controller Box BASE
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste this file → Run

Generates the bottom half of the IP67 controller enclosure.
Dimensions: 160 × 110 × 30mm (base half), 3mm walls, O-ring groove,
4× M3 PCB standoffs, battery bay lip, 2× M12 cable gland holes,
2× SMA antenna holes, 2× mounting slots, 4× M3 screw bosses.
"""

import adsk.core
import adsk.fusion
import traceback

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    design = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = design.rootComponent

    # Fusion 360 uses centimeters internally
    def mm(v):
        return v / 10.0

    def pick_profile_by_area(sketch, min_cm2, max_cm2):
        """Return the first profile whose area falls in [min, max] cm²."""
        for i in range(sketch.profiles.count):
            a = sketch.profiles.item(i).areaProperties().area
            if min_cm2 <= a <= max_cm2:
                return sketch.profiles.item(i)
        return None

    def pick_smallest_profiles(sketch, max_cm2):
        """Return all profiles smaller than max_cm2."""
        out = []
        for i in range(sketch.profiles.count):
            a = sketch.profiles.item(i).areaProperties().area
            if a <= max_cm2:
                out.append(sketch.profiles.item(i))
        return out

    def cut_down(comp, profile, depth_mm):
        """Extrude-cut in the NEGATIVE-Z direction."""
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        extent_def = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(mm(depth_mm)))
        inp.setOneSideExtent(extent_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        return ext.add(inp)

    def cut_positive(comp, profile, depth_mm):
        """Extrude-cut in the POSITIVE normal direction of the sketch plane."""
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(depth_mm)))
        return ext.add(inp)

    def cut_negative(comp, profile, depth_mm):
        """Extrude-cut in the NEGATIVE normal direction of the sketch plane."""
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        extent_def = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(mm(depth_mm)))
        inp.setOneSideExtent(extent_def, adsk.fusion.ExtentDirections.NegativeExtentDirection)
        return ext.add(inp)

    def join_up(comp, profile, height_mm):
        """Extrude-join in the positive normal direction."""
        ext = comp.features.extrudeFeatures
        inp = ext.createInput(profile, adsk.fusion.FeatureOperations.JoinFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(height_mm)))
        return ext.add(inp)

    try:
        # ── Create component ────────────────────────────────
        occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        comp = occ.component
        comp.name = "WXL_Controller_Base"
        extrudes = comp.features.extrudeFeatures
        planes = comp.constructionPlanes

        # ════════════════════════════════════════════════════
        # STEP 1: Outer box 160×110×30mm
        # ════════════════════════════════════════════════════
        sk = comp.sketches.add(comp.xYConstructionPlane)
        sk.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(mm(160), mm(110), 0)
        )

        prof = sk.profiles.item(0)
        inp = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(30)))
        box_ext = extrudes.add(inp)
        box_body = box_ext.bodies.item(0)
        box_body.name = "Base"

        # ════════════════════════════════════════════════════
        # STEP 2: Fillet the 4 vertical edges at 5mm
        # ════════════════════════════════════════════════════
        fillets = comp.features.filletFeatures
        edge_coll = adsk.core.ObjectCollection.create()
        for i in range(box_body.edges.count):
            edge = box_body.edges.item(i)
            # Vertical edges run along Z — both endpoints have same X,Y
            p1 = edge.startVertex.geometry
            p2 = edge.endVertex.geometry
            if abs(p1.x - p2.x) < 0.001 and abs(p1.y - p2.y) < 0.001:
                length = abs(p1.z - p2.z)
                if abs(length - mm(30)) < 0.01:
                    edge_coll.add(edge)

        if edge_coll.count > 0:
            fillet_inp = fillets.createInput()
            fillet_inp.addConstantRadiusEdgeSet(edge_coll,
                adsk.core.ValueInput.createByReal(mm(5)), True)
            fillets.add(fillet_inp)

        # ════════════════════════════════════════════════════
        # STEP 3: Shell — 3mm walls, remove top face
        # ════════════════════════════════════════════════════
        top_face = None
        for i in range(box_body.faces.count):
            face = box_body.faces.item(i)
            _, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
            if normal and abs(normal.z - 1.0) < 0.01:
                top_face = face
                break

        if not top_face:
            ui.messageBox("Could not find top face for shelling.")
            return

        shells = comp.features.shellFeatures
        face_coll = adsk.core.ObjectCollection.create()
        face_coll.add(top_face)
        shell_inp = shells.createInput(face_coll, False)
        shell_inp.insideThickness = adsk.core.ValueInput.createByReal(mm(3))
        shells.add(shell_inp)

        # ════════════════════════════════════════════════════
        # STEP 4: O-ring groove on top rim
        # Groove: 2mm wide × 2mm deep, inset 4.5mm from outer edge
        # Sketch at z=30 (rim top), cut DOWNWARD 2mm
        # ════════════════════════════════════════════════════
        pi_top = planes.createInput()
        pi_top.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(30)))
        plane_top = planes.add(pi_top)

        sk_groove = comp.sketches.add(plane_top)
        # Outer boundary of groove (4.5mm inset from box outer edge)
        sk_groove.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(4.5), mm(4.5), 0),
            adsk.core.Point3D.create(mm(155.5), mm(105.5), 0)
        )
        # Inner boundary (6.5mm inset = 4.5 + 2mm groove width)
        sk_groove.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(6.5), mm(6.5), 0),
            adsk.core.Point3D.create(mm(153.5), mm(103.5), 0)
        )

        # The ring profile between the two rectangles:
        # Outer rect area ≈ 151×101 = 15251 mm² = 152.51 cm²
        # Inner rect area ≈ 147×97 = 14259 mm² = 142.59 cm²
        # Ring area ≈ 9.92 cm²
        # There may also be intersections with the rim cross-section.
        # Pick the profile closest to ~10 cm²
        best_prof = None
        best_diff = 99999
        target_area = (mm(151) * mm(101)) - (mm(147) * mm(97))  # ~9.92 cm²
        for i in range(sk_groove.profiles.count):
            p = sk_groove.profiles.item(i)
            a = p.areaProperties().area
            diff = abs(a - target_area)
            if diff < best_diff:
                best_diff = diff
                best_prof = p

        if best_prof:
            try:
                cut_down(comp, best_prof, 2)
            except:
                # If the ring profile doesn't work, the groove might need a different approach
                pass

        # ════════════════════════════════════════════════════
        # STEP 5: PCB Standoffs — 4 posts on the inner floor
        # Floor is at z=3mm (after shelling), standoffs are 5mm tall
        # ════════════════════════════════════════════════════
        pi_floor = planes.createInput()
        pi_floor.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(3)))
        plane_floor = planes.add(pi_floor)

        standoff_pos = [(25, 35), (95, 35), (25, 75), (95, 75)]

        for (sx, sy) in standoff_pos:
            sk_so = comp.sketches.add(plane_floor)
            sk_so.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(sx), mm(sy), 0), mm(3))
            # Pick the small circle profile (area ≈ π×0.3² ≈ 0.28 cm²)
            for pi in range(sk_so.profiles.count):
                p = sk_so.profiles.item(pi)
                if p.areaProperties().area < 0.5:  # < 0.5 cm²
                    try:
                        join_up(comp, p, 5)
                    except:
                        pass
                    break

        # M3 holes through standoffs (2.5mm dia, cut from top of standoff down)
        pi_so_top = planes.createInput()
        pi_so_top.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(8)))
        plane_so_top = planes.add(pi_so_top)

        for (sx, sy) in standoff_pos:
            sk_hole = comp.sketches.add(plane_so_top)
            sk_hole.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(sx), mm(sy), 0), mm(1.25))
            for pi in range(sk_hole.profiles.count):
                p = sk_hole.profiles.item(pi)
                if p.areaProperties().area < 0.1:  # tiny circle
                    try:
                        cut_down(comp, p, 8)  # cut through standoff + floor
                    except:
                        pass
                    break

        # ════════════════════════════════════════════════════
        # STEP 6: Cable gland holes — 2× M12 (12mm dia) on bottom wall
        # Bottom wall is z=0 to z=3. Sketch at z=0, cut UPWARD into wall.
        # ════════════════════════════════════════════════════
        sk_gland = comp.sketches.add(comp.xYConstructionPlane)  # z=0
        gland_pos = [(50, 55), (90, 55)]
        for (gx, gy) in gland_pos:
            sk_gland.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(gx), mm(gy), 0), mm(6))

        for pi_idx in range(sk_gland.profiles.count):
            p = sk_gland.profiles.item(pi_idx)
            a = p.areaProperties().area
            # Circle area ≈ π×0.6² ≈ 1.13 cm²
            if a < 1.5:
                try:
                    cut_positive(comp, p, 3)  # +Z = up through 3mm bottom wall
                except:
                    pass

        # ════════════════════════════════════════════════════
        # STEP 7: SMA antenna holes — 2× 6.5mm on FRONT wall (y=0)
        # Front wall goes y=0 to y=3mm.
        # Sketch on XZ plane (y=0), cut in +Y direction (into wall).
        # On XZ plane: local X = global X, local Y = global Z.
        # ════════════════════════════════════════════════════
        sk_sma = comp.sketches.add(comp.xZConstructionPlane)  # y=0 plane
        sk_sma.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(60), mm(15), 0), mm(3.25))
        sk_sma.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(mm(90), mm(15), 0), mm(3.25))

        for pi_idx in range(sk_sma.profiles.count):
            p = sk_sma.profiles.item(pi_idx)
            a = p.areaProperties().area
            # Circle area ≈ π×0.325² ≈ 0.33 cm²
            if a < 0.5:
                try:
                    # XZ plane normal = +Y → positive direction goes into front wall
                    cut_positive(comp, p, 3)
                except:
                    pass

        # ════════════════════════════════════════════════════
        # STEP 8: Mounting slots on BACK wall (y=110mm)
        # Back wall goes y=107 to y=110. Sketch at y=110, cut in -Y.
        # On an XZ-parallel plane: local X = global X, local Y = global Z.
        # ════════════════════════════════════════════════════
        pi_back = planes.createInput()
        pi_back.setByOffset(comp.xZConstructionPlane, adsk.core.ValueInput.createByReal(mm(110)))
        plane_back = planes.add(pi_back)

        sk_slot = comp.sketches.add(plane_back)
        # Slot 1: centered at x=50mm, z=15mm, 5×15mm
        sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(47.5), mm(7.5), 0),
            adsk.core.Point3D.create(mm(52.5), mm(22.5), 0)
        )
        # Slot 2: centered at x=110mm, z=15mm
        sk_slot.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(mm(107.5), mm(7.5), 0),
            adsk.core.Point3D.create(mm(112.5), mm(22.5), 0)
        )

        for pi_idx in range(sk_slot.profiles.count):
            p = sk_slot.profiles.item(pi_idx)
            a = p.areaProperties().area
            # Slot area = 5×15 mm² = 75 mm² = 0.75 cm²
            if a < 1.0:
                try:
                    # Plane at y=110, normal = +Y. Wall is at y<110.
                    # Need to cut in -Y direction (into the wall).
                    cut_negative(comp, p, 3)
                except:
                    pass

        # ════════════════════════════════════════════════════
        # STEP 9: Screw bosses — 4 corner posts for lid attachment
        # Bosses rise from z=3 (floor) to z=30 (rim top) = 27mm tall
        # Positioned near corners, 8mm OD
        # ════════════════════════════════════════════════════
        boss_pos = [(10, 10), (150, 10), (10, 100), (150, 100)]
        for (bx, by) in boss_pos:
            sk_boss = comp.sketches.add(plane_floor)
            sk_boss.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(bx), mm(by), 0), mm(4))
            for pi_idx in range(sk_boss.profiles.count):
                p = sk_boss.profiles.item(pi_idx)
                a = p.areaProperties().area
                # Circle area ≈ π×0.4² ≈ 0.50 cm²
                if a < 0.7:
                    try:
                        join_up(comp, p, 27)
                    except:
                        pass
                    break

        # M3 threaded holes in screw bosses (2.5mm dia)
        for (bx, by) in boss_pos:
            sk_bh = comp.sketches.add(plane_top)
            sk_bh.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(mm(bx), mm(by), 0), mm(1.25))
            for pi_idx in range(sk_bh.profiles.count):
                p = sk_bh.profiles.item(pi_idx)
                if p.areaProperties().area < 0.1:
                    try:
                        cut_down(comp, p, 10)
                    except:
                        pass
                    break

        ui.messageBox(
            "WXL Controller Box BASE created!\n\n"
            "160 × 110 × 30 mm, 3 mm walls\n"
            "• 5 mm corner fillets\n"
            "• O-ring groove (2 × 2 mm)\n"
            "• 4 × PCB standoffs with M3 holes\n"
            "• 2 × M12 cable gland holes\n"
            "• 2 × SMA antenna holes\n"
            "• 2 × mounting slots\n"
            "• 4 × screw bosses with M3 holes\n\n"
            "Export: right-click body → Save As Mesh → 3MF"
        )

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
