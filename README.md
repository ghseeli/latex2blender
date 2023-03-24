# latex2blender

[Blender](https://www.blender.org/) add-on to render LaTeX and import it into Blender. See the [wiki](https://github.com/ghseeli/latex2blender/wiki) for more details, including how to install and use.

This Blender add-on is designed to import LaTeX graphics into Blender as mesh objects. In the 3D Viewport with object mode selected, latex2blender appears as a panel in the sidebar. Type "n" to open the sidebar.

## Requirements

This add-on works as a normal Blender add-on. It either requires the following be installed on your computer.

1. `latex` -- The add-on uses the local LaTeX installation to compile entered LaTeX code.
1. `dvisvgm` -- The add-on uses this tool to convert LaTeX outputted .dvi into an .svg file

or the usage of a latex docker image such as [blang/latex](https://github.com/blang/latex-docker) 
via the `pre-command` option.

## License

This code is licensed under GPLv3 in order to be compatible with Blender's licensing. 
