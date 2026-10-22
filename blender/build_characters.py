"""Build stylised low-poly characters for the VetGo 3D page and export GLB files.
Run:  Blender -b --python build_characters.py -- <out_dir>
Node names are what the web page animates: Torso, Head, ArmL, ArmR, LegL, LegR,
Coat, Cap (human) and Body, Head, LegFL, LegFR, LegBL, LegBR, Tail (pets).
"""
import bpy, sys, math, os
from mathutils import Matrix, Vector

OUT = os.environ.get("VET_OUT") or (sys.argv[sys.argv.index("--")+1] if "--" in sys.argv else os.getcwd())
LIVE = bool(os.environ.get("VET_LIVE"))   # running inside the user's open Blender: never reset prefs
os.makedirs(OUT, exist_ok=True)
OFFSET = [0.0]

MATS = {}
def reset():
    MATS.clear()
    if LIVE:
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
def clear_scene():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for d in list(coll):
            if d.users == 0: coll.remove(d)

def mat(name, rgb, rough=0.65, metal=0.0, emit=None):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    r,g,bl = [((c/255)/12.92 if c/255<=0.04045 else ((c/255+0.055)/1.055)**2.4) for c in rgb]
    b.inputs["Base Color"].default_value = (r,g,bl,1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (r,g,bl,1)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m; return m

def _ctx(obj):
    return bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj])

def _finish(obj, m, smooth=True, bevel=None, sub=0):
    obj.data.materials.append(m)
    if smooth:
        for p in obj.data.polygons: p.use_smooth = True
    if bevel:
        bv = obj.modifiers.new("bevel","BEVEL"); bv.width = bevel; bv.segments = 3; bv.limit_method='ANGLE'
    if sub:
        s = obj.modifiers.new("sub","SUBSURF"); s.levels = sub; s.render_levels = sub
    with _ctx(obj):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        for md in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    return obj

def sphere(name, r, loc, m, scale=(1,1,1), seg=20, rot=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=max(8,seg//2), location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    return _finish(o, m)

def cyl(name, r, depth, loc, m, rot=(0,0,0), scale=(1,1,1), bevel=0.02, r2=None, verts=20):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts, location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, vertices=verts, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    return _finish(o, m, bevel=bevel)

def cube(name, dims, loc, m, bevel=0.03, rot=(0,0,0), sub=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = dims
    return _finish(o, m, bevel=bevel, sub=sub)

def join(parts, name, pivot, parent=None):
    """Join parts into one object whose origin sits at `pivot` (world)."""
    main = parts[0]
    with bpy.context.temp_override(object=main, active_object=main, selected_objects=parts, selected_editable_objects=parts):
        if len(parts) > 1: bpy.ops.object.join()
    main.name = name
    P = Vector(pivot)
    main.data.transform(Matrix.Translation(main.location - P))
    main.location = P
    if parent:
        main.parent = parent
        main.matrix_parent_inverse = parent.matrix_world.inverted()
    return main

def empty(name, loc, parent=None):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.object; e.name = name
    if parent:
        e.parent = parent; e.matrix_parent_inverse = parent.matrix_world.inverted()
    return e

def export(name):
    root = bpy.data.objects.get("Root")
    objs = [root] + [o for o in bpy.data.objects if o.parent is not None and _top(o) is root]
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = root
    path = os.path.join(OUT, name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True,
                              use_selection=True, export_animations=False, export_lights=False, export_cameras=False,
                              export_materials='EXPORT', export_texcoords=False, export_normals=True)
    print("EXPORTED", path, os.path.getsize(path))
    # keep it visible in the live scene, renamed and moved aside
    root.name = name + "_root"
    for o in objs:
        if o is not root: o.name = name + "." + o.name
    root.location.x = OFFSET[0]; OFFSET[0] += 1.6

def _top(o):
    while o.parent is not None: o = o.parent
    return o

# ---------------------------------------------------------------- Human
def build_human():
    reset()
    skin = mat("Skin", (241,201,165)); hair = mat("Hair", (60,40,30))
    shirt = mat("Shirt", (59,139,234)); pants = mat("Pants", (52,66,86)); shoe = mat("Shoes", (40,40,44))
    coat = mat("Coat", (250,250,252), rough=.5); eye = mat("Eye", (30,30,34), rough=.3); badge = mat("Badge", (31,143,168))
    root = empty("Root", (0,0,0))
    # torso (pivot at hips)
    t = cube("t", (0.50,0.30,0.62), (0,0,1.25), shirt, bevel=0.10, sub=1)
    neck = cyl("n", 0.07, 0.10, (0,0,1.58), skin, bevel=0.01)
    collar = cube("c", (0.26,0.2,0.05), (0,0.02,1.56), shirt, bevel=0.02)
    torso = join([t,neck,collar], "Torso", (0,0,0.95), root)
    # head
    white = mat("EyeWhite", (250,250,250), rough=.25); mouth = mat("Mouth", (170,80,80))
    h = sphere("h", 0.215, (0,0,1.82), skin, scale=(1,0.95,1.05))
    hr = sphere("hr", 0.225, (0,-0.025,1.88), hair, scale=(1,1.0,0.75))
    fringe = cube("f", (0.34,0.09,0.09), (0,0.17,1.93), hair, bevel=0.035)
    nose = sphere("no", 0.03, (0,0.215,1.79), skin, seg=12)
    wL = sphere("wL", 0.038, (-0.08,0.195,1.835), white, seg=12, scale=(1,0.5,1)); wR = sphere("wR", 0.038, (0.08,0.195,1.835), white, seg=12, scale=(1,0.5,1))
    eL = sphere("eL", 0.02, (-0.08,0.212,1.835), eye, seg=10); eR = sphere("eR", 0.02, (0.08,0.212,1.835), eye, seg=10)
    mo = cube("mo", (0.07,0.02,0.015), (0,0.21,1.73), mouth, bevel=0.005)
    earL = sphere("earL", 0.04, (-0.21,0,1.80), skin, seg=12, scale=(0.6,1,1)); earR = sphere("earR", 0.04, (0.21,0,1.80), skin, seg=12, scale=(0.6,1,1))
    head = join([h,hr,fringe,nose,wL,wR,eL,eR,mo,earL,earR], "Head", (0,0,1.60), torso)
    # arms (pivot at shoulder)
    for s,nm in ((-1,"ArmL"),(1,"ArmR")):
        up = cyl("u", 0.065, 0.32, (s*0.30,0,1.36), shirt, rot=(0,s*0.08,0), bevel=0.02)
        lo = cyl("l", 0.055, 0.30, (s*0.32,0,1.06), skin, bevel=0.02)
        hand = sphere("hd", 0.065, (s*0.32,0,0.90), skin, seg=14, scale=(1,0.8,1.1))
        join([up,lo,hand], nm, (s*0.30,0,1.50), torso)
    # legs (pivot at hip)
    for s,nm in ((-1,"LegL"),(1,"LegR")):
        th = cyl("th", 0.095, 0.46, (s*0.12,0,0.70), pants, bevel=0.02)
        sh = cyl("sh", 0.075, 0.40, (s*0.12,0,0.30), pants, bevel=0.02)
        ft = cube("ft", (0.17,0.30,0.11), (s*0.12,0.06,0.055), shoe, bevel=0.035, sub=1)
        join([th,sh,ft], nm, (s*0.12,0,0.93), root)
    # staff coat & cap (toggled from the page)
    ct = cube("ct", (0.56,0.36,0.70), (0,0,1.22), coat, bevel=0.10, sub=1)
    lapL = cube("lp", (0.07,0.05,0.42), (-0.06,0.17,1.40), coat, bevel=0.02); lapR = cube("lp2", (0.07,0.05,0.42), (0.06,0.17,1.40), coat, bevel=0.02)
    bd = cube("bd", (0.10,0.02,0.07), (0.16,0.19,1.30), badge, bevel=0.005)
    steth = mat("Steth", (40,44,52), rough=.4)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.012, location=(0,0.06,1.50), rotation=(math.radians(80),0,0))
    tube = bpy.context.object; tube.name="st"; _finish(tube, steth)
    disc = cyl("sd", 0.045, 0.02, (-0.1,0.2,1.22), mat("StethDisc", (200,205,210), rough=.3, metal=.8), rot=(math.radians(90),0,0), bevel=0.004)
    join([ct,lapL,lapR,bd,tube,disc], "Coat", (0,0,0.95), torso)
    cap = cyl("cap", 0.21, 0.12, (0,0,1.98), badge, bevel=0.03)
    cap = join([cap], "Cap", (0,0,1.60), head)
    export("human")

# ---------------------------------------------------------------- Pets
def pet_common(body_dims, body_z, head_r, head_pos, leg_r, leg_h, leg_dx, leg_dy, fur, fur2, nose_m, eye_m, snout_r, snout_len):
    root = empty("Root", (0,0,0))
    body = sphere("b", 1, (0,0,body_z), fur, scale=body_dims, seg=28)
    chest = sphere("ch", body_dims[2]*0.95, (0,body_dims[1]*0.45,body_z-body_dims[2]*0.1), fur2, seg=20, scale=(0.8,0.7,0.75))
    bodyo = join([body,chest], "Body", (0,0,body_z), root)
    hx,hy,hz = head_pos
    h = sphere("h", head_r, head_pos, fur, seg=24, scale=(1,1,0.95))
    sn = sphere("sn", snout_r, (hx,hy+head_r*0.75,hz-head_r*0.25), fur2, seg=16, scale=(1,snout_len,0.75))
    no = sphere("no", snout_r*0.42, (hx,hy+head_r*0.75+snout_r*snout_len*0.85,hz-head_r*0.18), nose_m, seg=12, scale=(1,0.7,0.8))
    white = mat("EyeWhite", (250,250,250), rough=.25)
    wL = sphere("wL", head_r*0.2, (hx-head_r*0.42,hy+head_r*0.74,hz+head_r*0.18), white, seg=12, scale=(1,0.55,1))
    wR = sphere("wR", head_r*0.2, (hx+head_r*0.42,hy+head_r*0.74,hz+head_r*0.18), white, seg=12, scale=(1,0.55,1))
    eL = sphere("eL", head_r*0.13, (hx-head_r*0.42,hy+head_r*0.84,hz+head_r*0.18), eye_m, seg=10)
    eR = sphere("eR", head_r*0.13, (hx+head_r*0.42,hy+head_r*0.84,hz+head_r*0.18), eye_m, seg=10)
    hl = mat("EyeHL", (255,255,255), rough=.1, emit=0.6)
    gL = sphere("gL", head_r*0.045, (hx-head_r*0.38,hy+head_r*0.96,hz+head_r*0.24), hl, seg=8)
    gR = sphere("gR", head_r*0.045, (hx+head_r*0.46,hy+head_r*0.96,hz+head_r*0.24), hl, seg=8)
    head_parts = [h,sn,no,wL,wR,eL,eR,gL,gR]
    for s,nm in ((-1,"LegFL"),(1,"LegFR"),(-1,"LegBL"),(1,"LegBR")):
        pass
    legs = []
    for s,f,nm in ((-1,1,"LegFL"),(1,1,"LegFR"),(-1,-1,"LegBL"),(1,-1,"LegBR")):
        lg = cyl("lg", leg_r, leg_h, (s*leg_dx, f*leg_dy, leg_h/2+0.02), fur, bevel=0.012)
        paw = sphere("pw", leg_r*1.15, (s*leg_dx, f*leg_dy+leg_r*0.3, leg_r*0.9), fur2, seg=12, scale=(1,1.2,0.7))
        legs.append(join([lg,paw], nm, (s*leg_dx, f*leg_dy, leg_h+0.02), bodyo))
    return root, bodyo, head_parts, head_pos

def tail_chain(start, n, r0, step, curl, m):
    """Smooth tapered tail: a bezier curve with bevel, converted to a mesh."""
    pts=[]; x,y,z=start; n=n*2; step=step*0.5
    for i in range(n):
        pts.append((x,y,z, 1 - i/(n+1)))
        y -= step*math.cos(curl*i/n*1.3); z += step*math.sin(curl*i/n*1.3)
    cu = bpy.data.curves.new("tail", 'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r0; cu.bevel_resolution=4; cu.use_fill_caps=True
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts)-1)
    for bp,(px,py,pz,rad) in zip(sp.bezier_points, pts):
        bp.co=(px,py,pz); bp.handle_left_type=bp.handle_right_type='AUTO'; bp.radius=max(rad,0.18)
    o = bpy.data.objects.new("tl", cu); bpy.context.collection.objects.link(o)
    with _ctx(o):
        bpy.ops.object.convert(target='MESH')
    o.data.materials.append(m)
    for p in o.data.polygons: p.use_smooth=True
    return [o]

def build_dog():
    reset()
    fur = mat("Fur", (200,155,106)); fur2 = mat("FurLight", (245,232,214)); nose = mat("Nose", (30,26,26), rough=.35)
    eye = mat("Eye", (24,22,22), rough=.3); collar = mat("Collar", (226,87,79)); tag = mat("Tag", (240,190,70), rough=.3, metal=.6)
    root, body, hp, (hx,hy,hz) = pet_common((0.24,0.42,0.23), 0.47, 0.19, (0,0.42,0.66), 0.05, 0.31, 0.15, 0.28, fur, fur2, nose, eye, 0.085, 1.5)
    # floppy ears
    for s in (-1,1):
        hp.append(sphere("ear", 0.07, (s*0.17, 0.38, 0.62), fur, seg=14, scale=(0.45,0.8,1.4), rot=(0,s*0.35,0)))
    hp.append(sphere("brow", 0.2, (0,0.42,0.72), fur, seg=18, scale=(0.95,0.9,0.6)))
    head = join(hp, "Head", (0,0.36,0.62), body)
    # collar
    bpy.ops.mesh.primitive_torus_add(major_radius=0.135, minor_radius=0.025, location=(0,0.3,0.57), rotation=(math.radians(100),0,0))
    c = bpy.context.object; c.name="col"; _finish(c, collar)
    t = sphere("tag", 0.03, (0,0.33,0.44), tag, seg=12, scale=(1,0.4,1))
    join([c,t], "Collar", (0,0,0.47), body)
    tail = join(tail_chain((0,-0.40,0.56), 7, 0.045, 0.055, 2.0, fur), "Tail", (0,-0.38,0.55), body)
    export("dog")

def build_cat():
    reset()
    fur = mat("Fur", (154,154,166)); fur2 = mat("FurLight", (236,236,240)); nose = mat("Nose", (230,140,150), rough=.4)
    eye = mat("Eye", (70,160,90), rough=.25); collar = mat("Collar", (59,139,234))
    root, body, hp, (hx,hy,hz) = pet_common((0.18,0.34,0.17), 0.36, 0.15, (0,0.34,0.50), 0.035, 0.24, 0.11, 0.22, fur, fur2, nose, eye, 0.06, 1.1)
    for s in (-1,1):
        hp.append(cyl("ear", 0.055, 0.14, (s*0.09, 0.32, 0.64), fur, r2=0.005, verts=10, bevel=0.005, rot=(0,s*0.25,0)))
        hp.append(cyl("eari", 0.03, 0.09, (s*0.09, 0.335, 0.635), nose, r2=0.003, verts=8, bevel=0, rot=(0,s*0.25,0)))
        hp.append(cyl("wh", 0.003, 0.22, (s*0.14, 0.44, 0.47), fur2, rot=(0,math.radians(90),s*0.15), bevel=0, verts=6))
    head = join(hp, "Head", (0,0.28,0.46), body)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.10, minor_radius=0.018, location=(0,0.24,0.44), rotation=(math.radians(100),0,0))
    c = bpy.context.object; c.name="col"; _finish(c, collar); join([c], "Collar", (0,0,0.36), body)
    tail = join(tail_chain((0,-0.32,0.42), 9, 0.032, 0.06, 3.0, fur), "Tail", (0,-0.30,0.40), body)
    export("cat")

def build_rabbit():
    reset()
    fur = mat("Fur", (242,236,228)); fur2 = mat("FurLight", (255,250,246)); nose = mat("Nose", (230,140,150), rough=.4)
    eye = mat("Eye", (40,30,30), rough=.25); inner = mat("EarInner", (245,180,190))
    root, body, hp, (hx,hy,hz) = pet_common((0.19,0.26,0.19), 0.30, 0.15, (0,0.22,0.47), 0.035, 0.14, 0.11, 0.15, fur, fur2, nose, eye, 0.06, 0.9)
    for s in (-1,1):
        hp.append(sphere("ear", 0.05, (s*0.07, 0.17, 0.74), fur, seg=14, scale=(0.7,0.45,2.6), rot=(0.2,s*0.15,0)))
        hp.append(sphere("eari", 0.035, (s*0.07, 0.19, 0.74), inner, seg=12, scale=(0.6,0.3,2.2), rot=(0.2,s*0.15,0)))
    head = join(hp, "Head", (0,0.16,0.42), body)
    tail = join([sphere("tl", 0.06, (0,-0.26,0.33), fur2, seg=14)], "Tail", (0,-0.24,0.33), body)
    export("rabbit")

def build_carrier():
    reset()
    shell = mat("Shell", (244,246,248), rough=.45); lid = mat("Lid", (59,139,234), rough=.5); grill = mat("Grill", (125,138,150), rough=.4, metal=.3)
    root = empty("Root", (0,0,0))
    b = cube("b", (0.42,0.62,0.34), (0,0,0.17), shell, bevel=0.05, sub=1)
    l = cube("l", (0.40,0.60,0.14), (0,0,0.40), lid, bevel=0.04, sub=1)
    hd = cube("hd", (0.16,0.05,0.07), (0,0,0.50), grill, bevel=0.015)
    parts=[b,l,hd]
    for i in range(5):
        parts.append(cyl("bar", 0.006, 0.26, (-0.12+i*0.06, 0.31, 0.18), grill, bevel=0))
    join(parts, "Body", (0,0,0), root)
    export("carrier")

if LIVE:
    clear_scene()
for fn in (build_human, build_dog, build_cat, build_rabbit, build_carrier):
    fn()
print("ALL DONE")
