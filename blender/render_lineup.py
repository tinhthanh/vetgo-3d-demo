import bpy, sys, os, math
models = sys.argv[sys.argv.index("--")+1]; out = sys.argv[sys.argv.index("--")+2]
bpy.ops.wm.read_factory_settings(use_empty=True)
xs = {"human":-2.2,"dog":-0.9,"cat":0.2,"rabbit":1.1,"carrier":2.0}
for n,x in xs.items():
    bpy.ops.import_scene.gltf(filepath=os.path.join(models,n+".glb"))
    for o in bpy.context.selected_objects:
        if o.parent is None: o.location.x = x
# floor
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
pl=bpy.context.object; m=bpy.data.materials.new("fl"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.9,.92,.94,1); pl.data.materials.append(m)
bpy.ops.object.light_add(type='SUN', location=(4,4,8)); s=bpy.context.object; s.data.energy=4; s.rotation_euler=(math.radians(50),0,math.radians(145)); s.data.angle=math.radians(8)
bpy.ops.object.light_add(type='AREA', location=(-4,4,4)); a=bpy.context.object; a.data.energy=400; a.data.size=5; a.rotation_euler=(math.radians(60),0,math.radians(-135))
bpy.ops.object.camera_add(location=(0,7.5,3.2), rotation=(math.radians(70),0,math.radians(180))); cam=bpy.context.object; cam.data.lens=45
bpy.context.scene.camera=cam
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE' if hasattr(bpy.types,'SceneEEVEE') else 'BLENDER_WORKBENCH'
try:
    sc.render.engine='BLENDER_EEVEE'
except Exception: sc.render.engine='BLENDER_WORKBENCH'
sc.render.resolution_x=1600; sc.render.resolution_y=700; sc.render.filepath=out
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(.85,.9,.92,1); w.node_tree.nodes["Background"].inputs[1].default_value=.8
bpy.ops.render.render(write_still=True); print("RENDERED", out, sc.render.engine)
