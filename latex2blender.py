bl_info = {
    "name": "latex2blender",
    "description": "Enables user to write Latex in Blender.",
    "author": "Peter K. Johnson and George H. Seelinger",
    "version": (1, 0, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar",
    "warning": "",
    "wiki_url": "https://github.com/ghseeli/latex2blender/wiki",
    "support": "COMMUNITY",
    "category": "Add Mesh"
}


import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       PointerProperty
                       )

from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup
                       )

from bl_operators.presets import AddPresetBase

from bl_ui.utils import PresetPanel

import os
import glob
import subprocess
import tempfile
import shutil
import math


# Various settings.
class Settings(PropertyGroup):

    latex_code: StringProperty(
        name="Latex",
        description="Enter Latex Code",
        default="",
    )

    text_scale: FloatProperty(
        name="Scale",
        description="Set size of text",
        default=1.0,
    )

    x_loc: FloatProperty(
        name="X",
        description="Set x position",
        default=0.0,
    )

    y_loc: FloatProperty(
        name="Y",
        description="Set y position",
        default=0.0,
    )

    z_loc: FloatProperty(
        name="Z",
        description="Set z position",
        default=0.0,
    )

    x_rot: FloatProperty(
        name="X",
        description="Set x rotation",
        default=0.0,
    )

    y_rot: FloatProperty(
        name="Y",
        description="Set y rotation",
        default=0.0,
    )

    z_rot: FloatProperty(
        name="Z",
        description="Set z rotation",
        default=0.0,
    )

    custom_preamble_bool: BoolProperty(
        name="Use Custom Preamble",
        description="Use a custom preamble",
        default=False
    )

    preamble_path: StringProperty(
        name="Preamble",
        description="Choose a .tex file for the preamble",
        default="",
        subtype='FILE_PATH'
    )


def ErrorMessageBox(message, title):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')


# Imports compiled latex code into blender given chosen settings.
def import_latex(self, context, latex_code, text_scale, x_loc, y_loc, z_loc, x_rot, y_rot, z_rot, custom_preamble_bool,
                 temp_dir, preamble_path=None):

    # Set current directory to temp_directory
    current_dir = os.getcwd()
    os.chdir(temp_dir)

    # Create temp latex file with specified preamble.
    temp_file_name = temp_dir + os.sep + 'temp'
    if custom_preamble_bool:
        shutil.copy(preamble_path, temp_file_name + '.tex')
        temp = open(temp_file_name + '.tex', "a")
    else:
        temp = open(temp_file_name + '.tex', "a")
        default_preamble = '\\documentclass{amsart}\n\\usepackage{amssymb,amsfonts}\n\\usepackage{tikz}' \
                           '\n\\usepackage{tikz-cd}\n\\pagestyle{empty}\n\\thispagestyle{empty}'
        temp.write(default_preamble)

    # Add latex code to temp.tex and close the file.
    temp.write('\n\\begin{document}\n' + latex_code + '\n\\end{document}')
    temp.close()

    # Try to compile temp.tex and create an svg file
    try:
        # Updates 'PATH' to include reference to folder containing latex and dvisvgm executable files.
        # This only matters when running on MacOS. It is unnecessary for Linux and Windows.
        latex_exec_path = '/Library/TeX/texbin'
        local_env = os.environ.copy()
        local_env['PATH'] = (latex_exec_path + os.pathsep + local_env['PATH'])

        subprocess.call(["latex", "-interaction=batchmode", temp_file_name + ".tex"], env=local_env)
        subprocess.call(["dvisvgm", "--no-fonts", temp_file_name + ".dvi"], env=local_env)

        objects_before_import = bpy.data.objects[:]

        bpy.ops.object.select_all(action='DESELECT')


        svg_file_list = glob.glob("*.svg")

        if len(svg_file_list) == 0:
            ErrorMessageBox("Please check your latex code for errors and that latex and dvisvgm are properly "
                            "installed. Also, if using a custom preamble, check that it is formatted correctly.",
                            "Compilation Error")
        else:
            # Import svg into blender as curve
            svg_file_path = temp_dir + os.sep + svg_file_list[0]
            bpy.ops.import_curve.svg(filepath=svg_file_path)

            # Select imported objects
            imported_curve = [x for x in bpy.data.objects if x not in objects_before_import]
            active_obj = imported_curve[0]
            context.view_layer.objects.active = active_obj
            for x in imported_curve:
                x.select_set(True)

            # Convert to Mesh
            bpy.ops.object.convert(target='MESH')

            # Adjust scale, location, and rotation.
            bpy.ops.object.join()
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
            active_obj.scale = (600*text_scale, 600*text_scale, 600*text_scale)
            active_obj.location = (x_loc, y_loc, z_loc)
            active_obj.rotation_euler = (math.radians(x_rot), math.radians(y_rot), math.radians(z_rot))
            # Move mesh to scene collection and delete the temp.svg collection. Then rename mesh.
            temp_svg_collection = active_obj.users_collection[0]
            bpy.ops.object.move_to_collection(collection_index=0)
            bpy.data.collections.remove(temp_svg_collection)
            active_obj.name = 'Latex Figure'
    except FileNotFoundError as e:
        ErrorMessageBox("Please check that LaTeX is installed on your system.", "Compilation Error")
    except subprocess.CalledProcessError:
        ErrorMessageBox("Please check your latex code for errors and that latex and dvisvgm are properly installed. "
                        "Also, if using a custom preamble, check that it is formatted correctly.", "Compilation Error")
    finally:
        os.chdir(current_dir)
        print("Finished trying to compile latex and create an svg file.")


class LATEX2BLENDER_MT_Presets(Menu):
    bl_idname = 'LATEX2BLENDER_MT_Presets'
    bl_label = 'Presets'
    preset_subdir = 'latex2blender_presets'
    preset_operator = 'script.execute_preset'
    draw = Menu.draw_preset


class OBJECT_OT_add_latex_preset(AddPresetBase, Operator):
    bl_idname = 'object.add_latex_preset'
    bl_label = 'Create a new preset with below settings'
    preset_menu = 'LATEX2BLENDER_MT_Presets'

    preset_defines = ['t = bpy.context.scene.my_tool']

    preset_values = [
        't.text_scale',
        't.x_loc',
        't.y_loc',
        't.z_loc',
        't.x_rot',
        't.y_rot',
        't.z_rot',
        't.custom_preamble_bool',
        't.preamble_path'
    ]

    preset_subdir = 'latex2blender_presets'


# Display into an existing panel
def panel_func(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.menu(LATEX2BLENDER_MT_Presets.__name__, text=LATEX2BLENDER_MT_Presets.bl_label)
    row.operator(OBJECT_OT_add_latex_preset.bl_idname, text="", icon='ADD')
    row.operator(OBJECT_OT_add_latex_preset.bl_idname, text="", icon='REMOVE').remove_active = True


# Compile latex.
class WM_OT_compile(Operator):
    bl_idname = "wm.compile"
    bl_label = "Compile Latex Code"

    def execute(self, context):
        scene = context.scene
        t = scene.my_tool
        if t.latex_code == '' and t.custom_preamble_bool \
                and t.preamble_path == '':
            ErrorMessageBox("No Latex code has been entered and no preamble file has been chosen. Please enter some "
                            "latex code and choose a .tex file for the preamble", "Multiple Errors")
        elif t.latex_code == '':
            ErrorMessageBox("No Latex code has been entered. Please enter some Latex code.", "Latex Code Error")
        elif t.custom_preamble_bool and t.preamble_path == '':
            ErrorMessageBox("No preamble file has been chosen. Please choose a file.", "Custom Preamble Error")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                import_latex(self, context, t.latex_code, t.text_scale, t.x_loc, t.y_loc, t.z_loc, t.x_rot, t.y_rot,
                             t.z_rot, t.custom_preamble_bool, temp_dir, t.preamble_path)
        return {'FINISHED'}


class OBJECT_PT_latex2blender_panel(Panel):
    bl_idname = "OBJECT_PT_latex2blender_panel"
    bl_label = "latex2blender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "latex2blender"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        latex2blender_tool = scene.my_tool

        layout.prop(latex2blender_tool, "latex_code")

        layout.separator()

        layout.label(text="Transform Settings")
        layout.prop(latex2blender_tool, "text_scale")

        split = layout.split()

        col = split.column(align=True)
        col.label(text="Location:")
        col.prop(latex2blender_tool, "x_loc")
        col.prop(latex2blender_tool, "y_loc")
        col.prop(latex2blender_tool, "z_loc")

        col = split.column(align=True)
        col.label(text="Rotation:")
        col.prop(latex2blender_tool, "x_rot")
        col.prop(latex2blender_tool, "y_rot")
        col.prop(latex2blender_tool, "z_rot")

        layout.separator()

        layout.prop(latex2blender_tool, "custom_preamble_bool")
        if latex2blender_tool.custom_preamble_bool:
            layout.prop(latex2blender_tool, "preamble_path")

        layout.separator()

        layout.operator("wm.compile")

        layout.separator()


classes = (
    Settings,
    LATEX2BLENDER_MT_Presets,
    OBJECT_OT_add_latex_preset,
    WM_OT_compile,
    OBJECT_PT_latex2blender_panel
)

# Get path of blender scripts directory.
scripts_dir = bpy.utils.user_resource('SCRIPTS')

# Get path of latex2blender_preset directory
l2b_presets = os.path.join(scripts_dir, 'presets', 'latex2blender_presets')


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = PointerProperty(type=Settings)
    OBJECT_PT_latex2blender_panel.prepend(panel_func)

    # Create latex2blender_presets folder if not already created.
    if not os.path.isdir(l2b_presets):
        os.makedirs(l2b_presets)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool
    OBJECT_PT_latex2blender_panel.remove(panel_func)
    shutil.rmtree(l2b_presets)


if __name__ == "__main__":
    register()
