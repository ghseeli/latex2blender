bl_info = {
    "name": "latex2blender",
    "author": "Peter Johnson and George H. Seelinger",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Latex Object",
    "description": "Allows user to write Latex in Blender",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
}


import bpy
from bpy.types import Operator
import os
import math
import subprocess
import tempfile


# Imports entered latex code into blender as a mesh with specified options (latex_preamble, size, x_rotation,
# y_rotation, z_rotation, latex_code, temp_directory)
def import_latex(self, context, latex_preamble, size, x_rotation, y_rotation, z_rotation, latex_code, temp_directory):

    # Set current directory to temp_directory
    os.chdir(temp_directory)

    # Create temporary latex file in temp_directory
    temp_file_name = temp_directory + '/temp'
    temp = open(temp_file_name + ".tex", "x")

    # Add latex code to temp.tex
    begin_doc = r"\begin{document}"
    end_doc = r"\end{document}"

    temp.write(latex_preamble+"\n"+begin_doc+"\n"+latex_code+"\n"+end_doc)
    temp.close()

    # Try to compile latex file and create an svg file
    try:
        subprocess.call(["latex", "-interaction=batchmode", temp_file_name + ".tex"])
        subprocess.call(["dvisvgm", "--no-fonts", temp_file_name + ".dvi"])

        objects_before_import = bpy.data.objects[:]

        # Import svg into blender as curve
        bpy.ops.import_curve.svg(filepath=temp_file_name + ".svg")

        # Adjust scale and rotation
        imported_curve = [x for x in bpy.data.objects if x not in objects_before_import]
        for x in imported_curve:
            x.scale = (50 * size, 50 * size, 50 * size)
            x.rotation_euler = (math.radians(x_rotation), math.radians(y_rotation), math.radians(z_rotation))

    except subprocess.CalledProcessError:
        print("Your latex code has an error.")
    finally:
        print("Finished trying to compile latex and create an svg file.")


# Popup menu that displays when Add Latex Button is clicked
# Once user enters data into popup and clicks ok, import latex is called
class LatexPopup(bpy.types.Operator):
    bl_idname = "object.latex_popup"
    bl_label = "Blender Latex"

    preamble_text = r"""\documentclass{standalone}
        \usepackage{amssymb,amsfonts}
        \usepackage{enumerate}
        \usepackage{tikz}
        \usepackage{tikz-cd}
        \usepackage{graphicx}"""
    preamble: bpy.props.StringProperty(name="Preamble", default=preamble_text)
    text_size: bpy.props.FloatProperty(name="Size of Text", default=1.0)
    x_rot: bpy.props.FloatProperty(name="X Rotation", default=90.0)
    y_rot: bpy.props.FloatProperty(name="Y Rotation", default=0.0)
    z_rot: bpy.props.FloatProperty(name="Z Rotation", default=0.0)
    latex_code: bpy.props.StringProperty(name="Latex Code")

    def execute(self, context):
        with tempfile.TemporaryDirectory() as t_directory:
            import_latex(self, context, self.preamble, self.text_size, self.x_rot, self.y_rot, self.z_rot, self.latex_code,
                         t_directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


# Creates a button called "Add Latex" in the "Add Mesh" list.
class OBJECT_OT_add_latex(Operator):
    """Create New Latex Object"""
    bl_idname = "mesh.add_latex"
    bl_label = "Add Latex"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # bpy.utils.register_class(LatexPopup)
        bpy.ops.object.latex_popup('INVOKE_DEFAULT')
        return {'FINISHED'}


# Registration
def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_latex.bl_idname,
        text="Add Latex",
        icon='PLUGIN')


def register():
    bpy.utils.register_class(LatexPopup)
    bpy.utils.register_class(OBJECT_OT_add_latex)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(LatexPopup)
    bpy.utils.unregister_class(OBJECT_OT_add_latex)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()
