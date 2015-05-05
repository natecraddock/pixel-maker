"""
Easy Audio Visualizer - Blender Audio Visualizer
Copyright (C) 2014 Nathan Craddock

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

bl_info = {
    "name": "Pixel Maker",
    "author": "Nathan Craddock",
    "version": (1, 0, 0),
    "blender": (2, 7, 4),
    "location": "Object Mode >> Tool Shelf >> Tools Tab",
    "description": "Converts each pixel of an image to a cube of the same color, with some options.",
    "tracker_url": "https://docs.google.com/forms/d/1dOvU7ZuXsDousyM8tiZlN-HCeKyn2ygI8cRX2aLgnKg/viewform?usp=send_form",
    "category": "Object"
}

import bpy
import bmesh
import random

class pixelMakerPanel(bpy.types.Panel):
    """Pixel Maker Panel"""
    bl_category = "Tools"
    bl_idname = "PIXEL_MAKER"
    bl_context = "objectmode"
    bl_label = "Pixel Maker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.prop(context.scene, "pixel_img_path", icon = 'FILE_IMAGE')
        row = layout.row()
        row.prop(context.scene, "pixel_object_type")
        layout.separator()

        split = layout.split()
        
        # Column 1
        col = split.column(align = True)
        col.label(text = "Height Mapping:")
        col.prop(context.scene, "pixel_color_height")
        col.prop(context.scene, "pixel_color_height_amount")
        col.prop(context.scene, "pixel_z_var")
        layout.separator()
        
        # Column 2
        col = split.column(align = True)
        col.label(text = "Other:")
        col.prop(context.scene, "pixel_join_cubes")
        col.prop(context.scene, "pixel_z_depth")
        layout.separator()
        
        row = layout.row()
        row.operator("object.make_pixel")
        
class pixelMaker(bpy.types.Operator):
    """Run the Pixel Maker Addon"""
    bl_idname = "object.make_pixel"
    bl_label = "Run"
    bl_options = {'REGISTER', 'UNDO'}
    cyclesMaterialMap = dict()
    internalMaterialMap = dict()
    
    def execute(self, context):        
        importedImage = context.scene.pixel_img_path
        variation = context.scene.pixel_z_var
        colorMapping = context.scene.pixel_color_height
        colorAmount = context.scene.pixel_color_height_amount
        joinCubes = context.scene.pixel_join_cubes        
    
        # Create an object to start from
        if(context.scene.pixel_object_type == 'cube'):
            bpy.ops.mesh.primitive_cube_add()
            originalObject = bpy.context.scene.objects.active.name
        elif(context.scene.pixel_object_type == 'cylinder_6'):
            bpy.ops.mesh.primitive_cylinder_add(vertices = 6)
            originalObject = bpy.context.scene.objects.active.name
        elif(context.scene.pixel_object_type == 'cylinder_8'):
            bpy.ops.mesh.primitive_cylinder_add(vertices = 8)
            originalObject = bpy.context.scene.objects.active.name 
        elif(context.scene.pixel_object_type == 'cylinder'):
            bpy.ops.mesh.primitive_cylinder_add()
            originalObject = bpy.context.scene.objects.active.name
        
        obs = []
        ob = bpy.context.object
            
        
        def setup(path):                        
            # Load the image from the users chosen file path into Blender. Also assign to a var.
            image = bpy.data.images.load(path)
            
            # Accessing some data from the chosen image
            pixels = image.pixels[:]
            width = image.size[0]
            height = image.size[1]
            numberPix = len(image.pixels)
            
            # Loops through the width and height of the image            
            for y in range(0, height):
                for x in range(0, width):
                    currentCube = (y * width) + x
                    color = []
                    
                    # Gets the RGBA values for that pixel
                    for colorRGBA in range(0, 4):
                        RGBA = (currentCube * 4) + colorRGBA
                        color.append(pixels[RGBA])
                    
                    # Calls the createCubes Function with information from the loops and pixel color
                    createCubes(x * 2, y * 2, color)
            
            # This links all the objects that were created to the scene.           
            for ob in obs:
                bpy.context.scene.objects.link(ob)
            bpy.context.scene.update()
            
            bpy.ops.object.select_all(action = 'DESELECT')
            bpy.data.objects[originalObject].select = True
            bpy.ops.object.delete()
            
            if joinCubes:
                for ob in obs:
                    name = ob.name
                    bpy.data.objects[name].select = True
                
                bpy.context.scene.objects.active = obs[0]
                
                bpy.ops.object.join()
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='TOGGLE')

                TOL = 0.05

                obj = bpy.context.active_object
                mesh = obj.data
                bm = bmesh.from_edit_mesh(mesh)

                faces = [(face.calc_center_median(), face) 
                            for face in bm.faces]

                #yay, key instead of cmp... 
                #no tolerance, precision problems -> round
                faces.sort(key=lambda t: round(t[0].x, 1))
                faces.sort(key=lambda t: round(t[0].y, 1)) 
                faces.sort(key=lambda t: round(t[0].z, 1)) 

                #find double faces
                for index in range(1, len(faces)):
                    prev = faces[index - 1]
                    current = faces[index]
                    if all(abs(prev[0][j] - current[0][j]) < TOL for j in range(3)):
                        current[1].select = True
                        prev[1].select = True

                bmesh.update_edit_mesh(mesh, False, False)
                bpy.ops.mesh.delete(type = 'FACE')
                bpy.ops.mesh.select_all(action='TOGGLE')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.transform.resize(value = (1, 1, context.scene.pixel_z_depth))
                
                bpy.ops.object.editmode_toggle()
                
                bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
                
                bpy.ops.view3d.snap_cursor_to_center()

                bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)

        
        def createCubes(x, y, col):
            # Sets the alpha variable to the alpha of the color.
            r, g, b, a = col
            
            # Checks to see whether or not the pixel is transparent. If not, then it creates a material and creates the cube.
            if a == 1:
                # This calls the makeMaterial function with the color as a parameter.
                material = makeMaterial(col)            
                
                copy = ob.copy()
                copy.data = ob.data.copy()
                copy.data.materials.append(material)
                
                # It has a z in the name in order to place all objects at the bottom of the list
                copy.name = "z.cube"
                copy.location.x = x - 1
                copy.location.y = y - 1
                copy.location.z = 0
                
                # Z-Scale functions
                if variation != 0 and colorMapping:
                    copy.scale.z = (((2.126 * r) + (7.152 * g) + (0.722 * b)) * colorAmount) + 1

                    copy.scale.z += random.uniform((variation * -1), variation)
                    if copy.scale.z == 0:
                        copy.scale.z = 1
                
                elif colorMapping:
                    copy.scale.z = (((2.126 * r) + (7.152 * g) + (0.722 * b)) * colorAmount) + 1

                elif variation != 0:
                    copy.scale.z = random.uniform((variation * -1), variation)
                    if copy.scale.z == 0:
                        copy.scale.z = 1
                
                else:
                    copy.scale.z = 1

                obs.append(copy)
            
        def makeMaterial(color):
            # This first checks whether it is in Blender Internal or Blender Cycles.
            # Then it creates materials for whatever engine it is in.
            
            if bpy.context.scene.render.engine == 'CYCLES':
                # Make a Cycles material
                key = repr(color)
                if key in self.cyclesMaterialMap:
                    return self.cyclesMaterialMap[key]
                
                alpha = 1.0
                red, green, blue, alpha = color
                colorName = "pixel_material_cycles"
                
                material = bpy.data.materials.new(colorName)
                material.use_nodes = True
                Diffuse_BSDF = material.node_tree.nodes['Diffuse BSDF']
                Diffuse_BSDF.inputs[0].default_value = [red, green, blue, alpha]
                material.diffuse_color = [red, green, blue]
                
                self.cyclesMaterialMap[key] = material
                return material
            
            elif bpy.context.scene.render.engine == 'BLENDER_RENDER':
                # Make a Blender Internal material
                key = repr(color)
                if key in self.internalMaterialMap:
                    return self.internalMaterialMap[key]
                
                alpha = 1.0
                red, green, blue, alpha = color
                colorName = "pixel_material_internal"
                
                material = bpy.data.materials.new(colorName)
                material.diffuse_color = [red, green, blue]
                
                self.internalMaterialMap[key] = material
                return material                

        setup(importedImage)
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(pixelMaker)
    bpy.utils.register_class(pixelMakerPanel)
    bpy.types.Scene.pixel_join_cubes = bpy.props.BoolProperty(name = "Join Objects", description = "Join the cubes?", default = False)
    bpy.types.Scene.pixel_object_type = bpy.props.EnumProperty(name = "Object", items = [("cube", "Cube", "Make it a cube"), ("cylinder", "Cylinder", "Make it a default cylinder"), ("cylinder_6", "Cylinder 6 Vertices", "Make it a 6 vertex cylinder"), ("cylinder_8", "Cylinder 8 Vertices", "Make it an 8 vertex cylinder")], default = "cube")
    bpy.types.Scene.pixel_color_height = bpy.props.BoolProperty(name = "Color Height Mapping", description = "Convert pixel color to height", default = False)
    bpy.types.Scene.pixel_color_height_amount = bpy.props.IntProperty(name = "Amount", description = "How much to effect the height based on color", default = 2, min = 1, max = 16)
    bpy.types.Scene.pixel_z_var = bpy.props.IntProperty(name = "Height Variation", description = "How much to vary the height. (0 = none)", default = 0, min = 0, max = 100)
    bpy.types.Scene.pixel_img_path = bpy.props.StringProperty(name="Image", default = "", description = "Navigate to an image file.", subtype = 'FILE_PATH')
    bpy.types.Scene.pixel_z_depth = bpy.props.IntProperty(name = "Z Depth", description = "How tall", default = 1)

def unregister():
    bpy.utils.unregister_class(pixelMaker)
    bpy.utils.unregister_class(pixelMakerPanel)
    del bpy.types.Scene.pixel_join_cubes
    del bpy.types.Scene.pixel_object_type
    del bpy.types.Scene.pixel_color_height
    del bpy.types.Scene.pixel_color_height_amount
    del bpy.types.Scene.pixel_z_var
    del bpy.types.Scene.pixel_img_path