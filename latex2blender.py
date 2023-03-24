bl_info = {
    "name": "latex2blender",
    "description": "Enables user to write LaTeX in Blender.",
    "author": "Peter K. Johnson and George H. Seelinger",
    "version": (1, 0, 6),
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
                       PointerProperty,
                       EnumProperty
                       )

from bpy.types import (Panel,
                       Material,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

from bl_operators.presets import AddPresetBase

from bl_ui.utils import PresetPanel

import os
import glob
import subprocess
import tempfile
import shutil
import math
import functools


def rel_to_abs(sp_name):
    if bpy.context.scene.my_tool[sp_name].startswith('//'):
        abs_path = os.path.abspath(bpy.path.abspath(bpy.context.scene.my_tool[sp_name]))
        bpy.context.scene.my_tool[sp_name] = abs_path

# Various settings.
class Settings(PropertyGroup):

    latex_code: StringProperty(
        name="LaTeX Code",
        description="Enter LaTeX Code",
        default="",
    )

    custom_latex_path: StringProperty(
        name="latex",
        description="""
        Enter the path of the folder containing the latex command
        on your computer. If you are not sure where the latex command is
        located, open your terminal/command prompt and type: \"where latex\" """,
        default = "",
        update  = lambda s,c: rel_to_abs('custom_latex_path'),
        subtype = 'DIR_PATH',
    )

    custom_pdflatex_path: StringProperty(
        name="pdflatex",
        description="""
        Enter the path of the folder containing the pdflatex command
        on your computer. If you are not sure where the pdflatex command is
        located, open your terminal/command prompt and type: \"where pdflatex\" """,
        default = "",
        update  = lambda s,c: rel_to_abs('custom_pdflatex_path'),
        subtype = 'DIR_PATH',
    )

    custom_xelatex_path: StringProperty(
        name="xelatex",
        description="""
        Enter the path of the folder containing the xelatex command
        on your computer. If you are not sure where the xelatex command is
        located, open your terminal/command prompt and type: \"where xelatex\" """,
        default = "",
        update  = lambda s,c: rel_to_abs('custom_xelatex_path'),
        subtype = 'DIR_PATH',
    )

    custom_lualatex_path: StringProperty(
        name="lualatex",
        description="""
        Enter the path of the folder containing the lualatex command
        on your computer. If you are not sure where the lualatex command is
        located, open your terminal/command prompt and type: \"where lualatex\" """,
        default = "",
        update  = lambda s,c: rel_to_abs('custom_lualatex_path'),
        subtype = 'DIR_PATH',
    )

    custom_dvisvgm_path: StringProperty(
        name="dvisvgm",
        description="""
        Enter the path of the folder containing the dvisvgm command
        on your computer. If you are not sure where the dvisvgm command is
        located, open your terminal/command prompt and type: \"where dvisvgm\" """,
        default = "",
        update  = lambda s,c: rel_to_abs('custom_dvisvgm_path'),
        subtype = 'DIR_PATH',
    )

    command_selection: EnumProperty(
        name="Command",
        description="Select the command used to compile LaTeX code",
        items=[
            ('latex', 'latex', 'Use latex command to compile code'),
            ('pdflatex', 'pdflatex', 'Use pdflatex command to compile code'),
            ('xelatex', 'xelatex', 'Use xelatex command to compile code'),
            ('lualatex', 'lualatex', 'Use lualatex command to compile code')
        ]
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

    custom_material_bool: BoolProperty(
        name="Use Custom Material",
        description="Use a custom material",
        default=False
    )

    custom_material_value: PointerProperty(
        type=Material,
        name="Material",
        description="Choose a material"
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
        update  = lambda s,c: rel_to_abs('preamble_path'),
        subtype='FILE_PATH'
    )

    pre_command_bool: BoolProperty(
        name="Use Custom Pre-command",
        description="Use a custom pre-command",
        default=False
    )

    pre_command: StringProperty(
        name="Pre-command",
        description="""
        A custom command that is prepended to the usual latex commands. This allows 
        running the various commands within a docker container for example.
        """,
        default = "",
    )


def ErrorMessageBox(message, title):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon='ERROR')


# Imports compiled latex code into blender given chosen settings.
def import_latex(self, context, latex_code, custom_latex_path,
                 custom_pdflatex_path, custom_xelatex_path, custom_lualatex_path,
                 custom_dvisvgm_path, command_selection, text_scale, x_loc,
                 y_loc, z_loc, x_rot,y_rot, z_rot, custom_preamble_bool,
                 temp_dir, custom_material_bool, custom_material_value,
                 compile_mode, *, preamble_path=None, pre_command):

    # Set current directory to temp_directory
    current_dir = os.getcwd()
    os.chdir(temp_dir)
    temp_dir = os.path.realpath(temp_dir)

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
        latex_exec_path = '/Library/TeX/texbin'
        local_env = os.environ.copy()
        local_env['PATH'] = (latex_exec_path + os.pathsep + local_env['PATH'])

        if custom_latex_path != "" and custom_latex_path != '/Library/TeX/texbin':
            local_env['PATH'] = (custom_latex_path + os.pathsep + local_env['PATH'])
        if (custom_pdflatex_path != "" and custom_pdflatex_path != '/Library/TeX/texbin'
                and custom_pdflatex_path != custom_latex_path):
            local_env['PATH'] = (custom_pdflatex_path + os.pathsep + local_env['PATH'])
        if (custom_xelatex_path != "" and custom_xelatex_path != '/Library/TeX/texbin'
                and custom_xelatex_path != custom_latex_path
                and custom_xelatex_path != custom_pdflatex_path):
            local_env['PATH'] = (custom_xelatex_path + os.pathsep + local_env['PATH'])
        if (custom_lualatex_path != "" and custom_lualatex_path != '/Library/TeX/texbin'
                and custom_lualatex_path != custom_latex_path
                and custom_lualatex_path != custom_pdflatex_path
                and custom_lualatex_path != custom_xelatex_path):
            local_env['PATH'] = (custom_lualatex_path + os.pathsep + local_env['PATH'])
        if (custom_dvisvgm_path != "" and custom_dvisvgm_path != '/Library/TeX/texbin'
                and custom_dvisvgm_path != custom_latex_path
                and custom_dvisvgm_path != custom_pdflatex_path
                and custom_dvisvgm_path != custom_xelatex_path
                and custom_dvisvgm_path != custom_lualatex_path):
            local_env['PATH'] = (custom_dvisvgm_path + os.pathsep + local_env['PATH'])
        fn = functools.partial(subprocess.run,
                               cwd=temp_dir,
                               env=local_env,
                               text=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)

        if command_selection == "latex":
            tex_process = fn([pre_command, "latex", "-interaction=nonstopmode", "temp.tex"])
        elif command_selection == "pdflatex":
            tex_process = fn([pre_command, "pdflatex", "-interaction=nonstopmode", "-output-format=dvi", "temp.tex"])
        elif command_selection == "xelatex":
            tex_process = fn([pre_command, "xelatex", "-interaction=nonstopmode", "-no-pdf", "temp.tex"])
        else:
            tex_process = fn([pre_command, "lualatex", "-interaction=nonstopmode", "-output-format=dvi", "temp.tex"])
        dvisvgm_process = fn([pre_command, "dvisvgm", "--no-fonts", "temp.dvi"])
        svg_file_list = glob.glob("*.svg")
        bpy.ops.object.select_all(action='DESELECT')

        if len(svg_file_list) == 0:
            self.report({"ERROR"},
"Please check your LaTeX code for errors and that LaTeX and dvisvgm are properly "
                             "installed and their paths are specified correctly. Also, if using a custom preamble, check that it is formatted correctly. \n"
                             "Tex return code " + str(tex_process.returncode) + "\n"
                             "dvi2svgm return code " + str(dvisvgm_process.returncode) + "\n"
                             "Tex error message: " + str(tex_process.stdout) + "\n"
                             "dvi2svgm error message: " + str(dvisvgm_process.stdout)
                         )

        else:
            svg_file_path = temp_dir + os.sep + svg_file_list[0]

            objects_before_import = bpy.data.objects[:]
            # Import svg into blender as curve
            bpy.ops.import_curve.svg(filepath=svg_file_path)

            # Select imported objects
            imported_curve = [x for x in bpy.data.objects if x not in objects_before_import]
            active_obj = imported_curve[0]
            context.view_layer.objects.active = active_obj
            for x in imported_curve:
                x.select_set(True)

            # Adjust scale, location, and rotation.
            bpy.ops.object.join()
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
            active_obj.scale = (600*text_scale, 600*text_scale, 600*text_scale)
            bpy.ops.object.transform_apply(location = False, scale = True, rotation = False)
            active_obj.location = (x_loc, y_loc, z_loc)
            active_obj.rotation_euler = (math.radians(x_rot), math.radians(y_rot), math.radians(z_rot))
            # Move curve to scene collection and delete the temp.svg collection. Then rename curve.
            temp_svg_collection = active_obj.users_collection[0]
            bpy.ops.object.move_to_collection(collection_index=0)
            bpy.data.collections.remove(temp_svg_collection)
            active_obj.name = 'LaTeX Figure'

            if custom_material_bool:
                active_obj.material_slots[0].material = custom_material_value

            if compile_mode == "mesh":
                # Convert to mesh
                bpy.ops.object.convert(target='MESH')


            if compile_mode == "grease pencil":
                # Convert to mesh
                bpy.ops.object.convert(target='MESH')
                # Then convert to grease pencil
                bpy.ops.object.convert(target='GPENCIL', angle=0, thickness=1, seams=True, faces=True, offset=0)
                # Moves to scene collection, fixes name.
                bpy.ops.object.move_to_collection(collection_index=0)
                bpy.context.selected_objects[0].name = "LaTeX Figure"
                if custom_material_bool:
                    bpy.context.selected_objects[0].material_slots[0].material = custom_material_value

            # Create custom property that stores typed LaTeX code
            bpy.context.selected_objects[0]["Original LaTeX Code"] = latex_code

    except FileNotFoundError as e:
        ErrorMessageBox("Please check that LaTeX is installed on your system and that its path is specified correctly.", "Compilation Error")
    except subprocess.CalledProcessError as e:
        ErrorMessageBox("Please check your LaTeX code for errors and that LaTeX and dvisvgm are properly "
                        "installed and their paths are specified correctly. Also, if using a custom preamble, check that it is formatted correctly. "
                        "Return code: " + str(e.returncode) + " " + str(e.output),
                        "Compilation Error")
    finally:
        os.chdir(current_dir)
        print("Finished trying to compile LaTeX and create an svg file.")


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
        't.custom_latex_path',
        't.custom_pdflatex_path',
        't.custom_xelatex_path',
        't.custom_lualatex_path',
        't.custom_dvisvgm_path',
        't.command_selection',
        't.text_scale',
        't.x_loc',
        't.y_loc',
        't.z_loc',
        't.x_rot',
        't.y_rot',
        't.z_rot',
        't.custom_preamble_bool',
        't.preamble_path',
        't.pre_command'
    ]

    preset_subdir = 'latex2blender_presets'


# Display into an existing panel
def panel_func(self, context):
    layout = self.layout

    row = layout.row(align=True)
    row.menu(LATEX2BLENDER_MT_Presets.__name__, text=LATEX2BLENDER_MT_Presets.bl_label)
    row.operator(OBJECT_OT_add_latex_preset.bl_idname, text="", icon='ADD')
    row.operator(OBJECT_OT_add_latex_preset.bl_idname, text="", icon='REMOVE').remove_active = True

# Compile latex as curve.
class WM_OT_compile_as_curve(Operator):
    bl_idname = "wm.compile_as_curve"
    bl_label = "Compile as Curve"

    def execute(self, context):
        scene = context.scene
        t = scene.my_tool
        if t.latex_code == '' and t.custom_preamble_bool \
                and t.preamble_path == '':
            ErrorMessageBox("No LaTeX code has been entered and no preamble file has been chosen. Please enter some "
                            "LaTeX code and choose a .tex file for the preamble", "Multiple Errors")
        elif t.custom_material_bool and t.custom_material_value is None:
            ErrorMessageBox("No material has been chosen. Please choose a material.", "Custom Material Error")
        elif t.latex_code == '':
            ErrorMessageBox("No LaTeX code has been entered. Please enter some LaTeX code.", "LaTeX Code Error")
        elif t.custom_preamble_bool and t.preamble_path == '':
            ErrorMessageBox("No preamble file has been chosen. Please choose a file.", "Custom Preamble Error")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                import_latex(self, context, t.latex_code, t.custom_latex_path,
                             t.custom_pdflatex_path, t.custom_xelatex_path,
                             t.custom_lualatex_path, t.custom_dvisvgm_path,
                             t.command_selection, t.text_scale, t.x_loc,
                             t.y_loc, t.z_loc, t.x_rot, t.y_rot, t.z_rot,
                             t.custom_preamble_bool, temp_dir,
                             t.custom_material_bool, t.custom_material_value,
                             'curve',  preamble_path=t.preamble_path, pre_command=t.pre_command)
        return {'FINISHED'}

# Compile latex as mesh.
class WM_OT_compile_as_mesh(Operator):
    bl_idname = "wm.compile_as_mesh"
    bl_label = "Compile as Mesh"

    def execute(self, context):
        scene = context.scene
        t = scene.my_tool
        if t.latex_code == '' and t.custom_preamble_bool \
                and t.preamble_path == '':
            ErrorMessageBox("No LaTeX code has been entered and no preamble file has been chosen. Please enter some "
                            "LaTeX code and choose a .tex file for the preamble", "Multiple Errors")
        elif t.custom_material_bool and t.custom_material_value is None:
            ErrorMessageBox("No material has been chosen. Please choose a material.", "Custom Material Error")
        elif t.latex_code == '':
            ErrorMessageBox("No LaTeX code has been entered. Please enter some LaTeX code.", "LaTeX Code Error")
        elif t.custom_preamble_bool and t.preamble_path == '':
            ErrorMessageBox("No preamble file has been chosen. Please choose a file.", "Custom Preamble Error")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                import_latex(self, context, t.latex_code, t.custom_latex_path,
                             t.custom_pdflatex_path, t.custom_xelatex_path,
                             t.custom_lualatex_path, t.custom_dvisvgm_path,
                             t.command_selection, t.text_scale, t.x_loc,
                             t.y_loc, t.z_loc, t.x_rot, t.y_rot, t.z_rot,
                             t.custom_preamble_bool, temp_dir,
                             t.custom_material_bool, t.custom_material_value,
                             'mesh',  preamble_path=t.preamble_path, pre_command=t.pre_command)
        return {'FINISHED'}

# Compile latex as grease pencil.
class WM_OT_compile_as_grease_pencil(Operator):
    bl_idname = "wm.compile_as_grease_pencil"
    bl_label = "Compile as Grease Pencil"

    def execute(self, context):
        scene = context.scene
        t = scene.my_tool
        if t.latex_code == '' and t.custom_preamble_bool \
                and t.preamble_path == '':
            ErrorMessageBox("No LaTeX code has been entered and no preamble file has been chosen. Please enter some "
                            "LaTeX code and choose a .tex file for the preamble", "Multiple Errors")
        elif t.custom_material_bool and t.custom_material_value is None:
            ErrorMessageBox("No material has been chosen. Please choose a material.", "Custom Material Error")
        elif t.latex_code == '':
            ErrorMessageBox("No LaTeX code has been entered. Please enter some LaTeX code.", "LaTeX Code Error")
        elif t.custom_preamble_bool and t.preamble_path == '':
            ErrorMessageBox("No preamble file has been chosen. Please choose a file.", "Custom Preamble Error")
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                import_latex(self, context, t.latex_code, t.custom_latex_path,
                             t.custom_pdflatex_path, t.custom_xelatex_path,
                             t.custom_lualatex_path, t.custom_dvisvgm_path,
                             t.command_selection, t.text_scale, t.x_loc,
                             t.y_loc, t.z_loc, t.x_rot, t.y_rot, t.z_rot,
                             t.custom_preamble_bool, temp_dir,
                             t.custom_material_bool, t.custom_material_value,
                             'grease pencil', preamble_path=t.preamble_path, pre_command=t.pre_command)
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

        layout.prop(latex2blender_tool, "command_selection")
        layout.separator

        box = layout.box()
        box.label(text="Paths to directories containing commands.")
        row= box.row()
        row.prop(latex2blender_tool, "custom_latex_path")
        row = box.row()
        row.prop(latex2blender_tool, "custom_pdflatex_path")
        row = box.row()
        row.prop(latex2blender_tool, "custom_xelatex_path")
        row = box.row()
        row.prop(latex2blender_tool, "custom_lualatex_path")
        row = box.row()
        row.prop(latex2blender_tool, "custom_dvisvgm_path")

        box = layout.box()
        box.label(text="Transform Settings")
        row = box.row()
        row.prop(latex2blender_tool, "text_scale")

        split = box.split()

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

        layout.prop(latex2blender_tool, "custom_preamble_bool")
        if latex2blender_tool.custom_preamble_bool:
            layout.prop(latex2blender_tool, "preamble_path")

        layout.prop(latex2blender_tool, "pre_command_bool")
        if latex2blender_tool.pre_command_bool:
            layout.prop(latex2blender_tool, "pre_command")

        layout.prop(latex2blender_tool, "custom_material_bool")
        if latex2blender_tool.custom_material_bool:
            layout.prop(latex2blender_tool, "custom_material_value")

        layout.separator()

        box = layout.box()
        row = box.row()
        row.operator("wm.compile_as_curve")
        row = box.row()
        row.operator("wm.compile_as_mesh")
        row = box.row()
        row.operator("wm.compile_as_grease_pencil")

classes = (
    Settings,
    LATEX2BLENDER_MT_Presets,
    OBJECT_OT_add_latex_preset,
    WM_OT_compile_as_curve,
    WM_OT_compile_as_mesh,
    WM_OT_compile_as_grease_pencil,
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

if __name__ == "__main__":
    register()
