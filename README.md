# latex2blender

latex2blender is a [Blender](https://www.blender.org/) extension that enables the user to render [LaTeX](https://www.latex-project.org/) and import it into Blender as a mesh or Grease Pencil object.
In particular, this allows the user to add nicely formatted mathematical text in Blender.

## Requirements

This extension works as a normal Blender extension, but it requires the following be installed on your computer.

1. `latex` -- The extension uses the local LaTeX installation to compile entered LaTeX code.
1. `dvisvgm` -- The extension uses this tool to convert LaTeX outputted .dvi into an .svg file

## Installation

1. If you do not already have [LaTeX](https://www.latex-project.org/) installed on your computer, please [install](https://www.latex-project.org/get/#tex-distributions) it. Note, latex2blender calls the command-line utility [dvisvgm](https://dvisvgm.de/), which comes bundled with most TeX distributions. If after following these installation steps, latex2blender is still not working, then it is probably because the TeX distribution you have installed does not come with dvisvgm (or dvisvgm is not located in the right folder).

2. Navigate to the [latest release](https://github.com/ghseeli/latex2blender/releases) and download `latex2blender.zip`

3. Open Blender. Navigate to `Blender Preferences > Get Extensions`. From the drop-down menu in the upper right, click `Install from disk`. Select downloaded `latex2blender.zip` file. The extension is now enabled in the `Add-ons` tab.

## How to start 

In the 3D Viewport with object mode selected, `latex2blender` appears as a panel in the sidebar. Type `n` to open the sidebar and select `latex2blender` to get started.

### Preambles and Presets

`latex2blender` gives the user the option to use a custom preamble for their LaTeX code in order to load extra packages or user defined LaTeX operators, commands, and macros. This, in combination with the presets functionality, provides the user with high degree of flexibility and reusability. If the user does not opt to use a custom preamble, their code will render using the [default preamble](https://github.com/ghseeli/latex2blender/blob/master/default_preamble.tex). (Note, if using the default preamble, the user does not need to do anything with the default preamble tex file. The link is simply there for reference.)

## License

This code is licensed under GPLv3 in order to be compatible with Blender's licensing. 
