"""
Fusion 360 Script — Render WX-Level and WX-Flow from multiple angles
Run inside Fusion 360: Utilities → Scripts and Add-Ins → + → paste → Run

WORKFLOW:
  1. Open a new Fusion doc, run wx_level_full_assembly.py
  2. Then run THIS script — it renders 8 angles for WX-Level
  3. Open another doc, run wx_flow_full_assembly.py
  4. Run THIS script again — it renders 8 angles for WX-Flow

Outputs 1920×1080 PNGs to ~/Desktop/wx_renders/
File naming: {product}_{view}.png
  e.g. wx_level_hero.png, wx_flow_front.png
"""

import adsk.core
import adsk.fusion
import os
import math
import traceback

VIEWS = [
    ("hero",         0.7,  -0.7,  0.5),   # classic 3/4 marketing view
    ("front",        0,    -1,    0.2),
    ("back",         0,     1,    0.2),
    ("top",          0,     0,    1.0),
    ("side_left",   -1,     0,    0.3),
    ("side_right",   1,     0,    0.3),
    ("bottom_3q",    0.5,  -0.5, -0.4),   # shows cable glands / bottom
    ("closeup_3q",   0.5,  -0.4,  0.3),   # tighter framing
]

def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    viewport = app.activeViewport

    out_dir = os.path.expanduser("~/Desktop/wx_renders")
    os.makedirs(out_dir, exist_ok=True)

    ret = ui.inputBox(
        "Product name for filenames:\n"
        "  wx_level  — for the WX-Level assembly\n"
        "  wx_flow   — for the WX-Flow assembly\n"
        "  wx_flow_probe — probe only (hide controller box first)",
        "Render Product", "wx_level"
    )
    if ret[1]:
        return
    product = ret[0].strip().replace(" ", "_")

    try:
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        min_pt = None
        max_pt = None

        # Scan all visible bodies across all occurrences AND root
        def scan_bodies(comp, transform=None):
            nonlocal min_pt, max_pt
            for i in range(comp.bRepBodies.count):
                body = comp.bRepBodies.item(i)
                if body.isVisible:
                    bb = body.boundingBox
                    pts = [bb.minPoint, bb.maxPoint]
                    for pt in pts:
                        if min_pt is None:
                            min_pt = [pt.x, pt.y, pt.z]
                            max_pt = [pt.x, pt.y, pt.z]
                        else:
                            min_pt[0] = min(min_pt[0], pt.x)
                            min_pt[1] = min(min_pt[1], pt.y)
                            min_pt[2] = min(min_pt[2], pt.z)
                            max_pt[0] = max(max_pt[0], pt.x)
                            max_pt[1] = max(max_pt[1], pt.y)
                            max_pt[2] = max(max_pt[2], pt.z)

        scan_bodies(root)
        for occ in root.allOccurrences:
            scan_bodies(occ.component)

        if min_pt is None:
            ui.messageBox("No visible bodies. Make sure your assembly is visible.")
            return

        cx = (min_pt[0] + max_pt[0]) / 2
        cy = (min_pt[1] + max_pt[1]) / 2
        cz = (min_pt[2] + max_pt[2]) / 2
        target = adsk.core.Point3D.create(cx, cy, cz)

        size = max(
            max_pt[0] - min_pt[0],
            max_pt[1] - min_pt[1],
            max_pt[2] - min_pt[2])

        rendered = []

        for (name, ox, oy, oz) in VIEWS:
            length = math.sqrt(ox*ox + oy*oy + oz*oz) or 1

            # closeup uses tighter distance
            dist_mult = 1.8 if "closeup" in name else 2.5
            dist = size * dist_mult

            ex = cx + (ox / length) * dist
            ey = cy + (oy / length) * dist
            ez = cz + (oz / length) * dist

            cam = viewport.camera
            cam.isSmoothTransition = False
            cam.target = target
            cam.eye = adsk.core.Point3D.create(ex, ey, ez)
            cam.upVector = adsk.core.Vector3D.create(0, 0, 1)
            viewport.camera = cam

            adsk.doEvents()
            viewport.refresh()
            adsk.doEvents()
            viewport.fit()
            adsk.doEvents()

            fname = f"{product}_{name}.png"
            fpath = os.path.join(out_dir, fname)
            viewport.saveAsImageFile(fpath, 1920, 1080)
            rendered.append(fname)

        msg = f"Done! {len(rendered)} renders saved to:\n{out_dir}\n\n"
        msg += "\n".join(f"  • {f}" for f in rendered)
        msg += "\n\nFor best quality: Render workspace → In-Canvas Render"
        ui.messageBox(msg)

    except Exception as e:
        ui.messageBox(f"Error: {str(e)}\n\n{traceback.format_exc()}")
