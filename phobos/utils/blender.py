#!/usr/bin/python
# coding=utf-8

"""
.. module:: phobos.utils.blender
    :platform: Unix, Windows, Mac
    :synopsis: This module contains functions o manipulate blender objects and interact with blender functionalities

.. moduleauthor:: Kai von Szadowski, Ole Schwiegert

Copyright 2014, University of Bremen & DFKI GmbH Robotics Innovation Center

This file is part of Phobos, a Blender Add-On to edit robot models.

Phobos is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Phobos is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Phobos.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import bpy
import mathutils
import phobos.defs as defs
import phobos.model.materials as materials
from phobos.phoboslog import log
from phobos.phobossystem import getConfigPath
from . import selection as sUtils
from . import naming as nUtils


def update():
    """Forces Blender to update scene contents (i.e. transformations).

    Sometimes when e.g. manipulating internal matrices of Blender objects such as
    matrix_world or matrix_local, Blender will not recalculate all related transforms,
    especially not the visual transform. The bpy.context.scene.update() function often
    named as the solution to this will lead to the matrices being updated, but not the
    visual transforms. This Function runs code (may be updated with new Blender verions)
    that forces Blender to update the visual transforms.

    Returns: None

    """
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_set(0)


def compileEnumPropertyList(iterable):
    return ((a,)*3 for a in iterable)


def getBlenderVersion():
    # DOCU add some docstring
    return bpy.app.version[0] * 100 + bpy.app.version[1]


def getPhobosPreferences():
    return bpy.context.user_preferences.addons["phobos"].preferences


def printMatrices(obj, info=None):
    """This function prints the matrices of an object to the screen.

    Args:
      obj(bpy.types.Object): The object to print the matrices from.
      info(bool, optional): If True the objects name will be included into the printed info. (Default value = None)

    Returns:

    """
    if not info:
        info = obj.name
    print("\n----------------", info, "---------------------\n",
          "local:\n", obj.matrix_local,
          "\n\nworld:\n", obj.matrix_world,
          "\n\nparent_inverse:\n", obj.matrix_parent_inverse,
          "\n\nbasis:\n", obj.matrix_basis)


def createPrimitive(pname, ptype, psize, player=0, pmaterial=None, plocation=(0, 0, 0),
                    protation=(0, 0, 0), phobostype=None):
    """Generates the primitive specified by the input parameters

    Args:
      pname(str): The primitives new name.
      ptype(str): The new primitives type. Can be one of *box, sphere, cylinder, cone, disc*
      psize(float or list): The new primitives size. Depending on the ptype it can be either a single float or a tuple.
      player: The layer bitmask for the new blender object. (Default value = 0)
      pmaterial: The new primitives material. (Default value = None)
      plocation(tuple, optional): The new primitives location. (Default value = (0)
      protation(tuple): The new primitives rotation.
      phobostype(str): phobostype of object to be created
      0:

    Returns:
      bpy.types.Object - the new blender object.

    """
    # TODO: allow placing on currently active layer?
    try:
        n_layer = int(player)
    except ValueError:
        n_layer = defs.layerTypes[player]
    players = defLayers([n_layer])
    # the layer has to be active to prevent problems with object placement
    bpy.context.scene.layers[n_layer] = True
    if ptype == "box":
        bpy.ops.mesh.primitive_cube_add(layers=players, location=plocation, rotation=protation)
        obj = bpy.context.object
        obj.dimensions = psize
    if ptype == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(size=psize, layers=players, location=plocation,
                                             rotation=protation)
    elif ptype == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=psize[0], depth=psize[1],
                                            layers=players, location=plocation, rotation=protation)
    elif ptype == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius=psize[0], depth=psize[1], cap_end=True,
                                        layers=players, location=plocation, rotation=protation)
    elif ptype == 'disc':
        bpy.ops.mesh.primitive_circle_add(vertices=psize[1], radius=psize[0], fill_type='TRIFAN',
                                          location=plocation, rotation=protation, layers=players)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj = bpy.context.object
    if phobostype:
        obj.phobostype = phobostype
    nUtils.safelyName(obj, pname, phobostype)
    if pmaterial:
        materials.assignMaterial(obj, pmaterial)
    return obj


def setObjectLayersActive(obj):
    # DOCU add some docstring
    for l in range(len(obj.layers)):
        bpy.context.scene.layers[l] &= obj.layers[l]


def toggleLayer(index, value=None):
    """This function toggles a specific layer or sets it to a desired value.

    Args:
      index(int): The layer index you want to change.
      value(bool, optional): True if visible, None for toggle. (Default value = None)

    Returns:

    """
    if value:
        bpy.context.scene.layers[index] = value
    else:
        bpy.context.scene.layers[index] = not bpy.context.scene.layers[index]


def defLayers(layerlist):
    """Returns a list of 20 elements encoding the visible layers according to layerlist

    Args:
      layerlist:

    Returns:

    """
    if type(layerlist) is not list:
        layerlist = [layerlist]
    layers = 20 * [False]
    for layer in layerlist:
        layers[layer] = True
    return layers


def updateTextFile(textfilename, newContent):
    """This function updates a blender textfile or creates a new one if it is not existent.

    Args:
      textfilename(str): The blender textfiles file name.
      newContent(str): The textfiles new content.

    Returns:

    """
    try:
        bpy.data.texts.remove(bpy.data.texts[textfilename])
    except KeyError:
        # TODO handle this error somehow
        # Not important. Just create.
        pass
    createNewTextfile(textfilename, newContent)


def readTextFile(textfilename):
    """This function returns the content of a specified text file.

    Args:
      textfilename(str): The blender textfiles name.

    Returns:
      str - the textfiles content.

    """
    try:
        return "\n".join([l.body for l in bpy.data.texts[textfilename].lines])
    except KeyError:
        log("No text file " + textfilename + " found. Setting", "ERROR")
        return ""


def createNewTextfile(textfilename, contents):
    """This function creates a new blender text file with the given content.

    Args:
      textfilename(str): The new blender texts name.
      contents(str): The new textfiles content.

    Returns:

    """
    for text in bpy.data.texts:
        text.tag = True
    bpy.ops.text.new()
    newtext = None
    for text in bpy.data.texts:
        if not text.tag:
            newtext = text
    for text in bpy.data.texts:
        text.tag = False
    newtext.name = textfilename
    bpy.data.texts[textfilename].write(contents)


def openScriptInEditor(scriptname):
    """This function opens a script/textfile in an open blender text window. Nothing happens if there is no
    available text window.

    Args:
      scriptname(str): The scripts name.

    Returns:

    """
    if scriptname in bpy.data.texts:
        for area in bpy.context.screen.areas:
            if area.type == 'TEXT_EDITOR':
                area.spaces.active.text = bpy.data.texts[scriptname]
    else:
        log("There is no script named " + scriptname + "!", "ERROR")


def cleanObjectProperties(props):
    """Cleans a predefined list of Blender-specific or other properties from the dictionary.

    Args:
      props:

    Returns:

    """
    getridof = ['phobostype', '_RNA_UI', 'cycles_visibility', 'startChain', 'endChain', 'masschanged']
    if props:
        for key in getridof:
            if key in props:
                del props[key]
    return props


def cleanScene():
    """Clean up blend file (remove all objects, meshes, materials and lights)"""
    # select all objects
    bpy.ops.object.select_all(action="SELECT")

    # and delete them
    bpy.ops.object.delete()

    # after that we have to clean up all loaded meshes (unfortunately
    # this is not done automatically)
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)

    # and all materials
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)

    # and all lights (aka lamps)
    for lamp in bpy.data.lamps:
        bpy.data.lamps.remove(lamp)


def createPreview(objects, export_path, modelname, render_resolution=256, opengl=False):
    """Creates a thumbnail of the given objects.

    Args:
      objects(list of bpy.types.Object): list of objects for the thumbnail
      export_path(str): folder to export image to
      modelname(str): name of model (used as file name)
      render_resolution(int): side length of resulting image in pixels (Default value = 256)
      opengl(bool): whether to use opengl rendering or not (Default value = False)

    Returns:

    """
    log("Creating thumbnail of model: "+modelname, "INFO")

    # render presets
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.resolution_x = render_resolution
    bpy.context.scene.render.resolution_y = render_resolution
    bpy.context.scene.render.resolution_percentage = 100

    # hide everything that is not supposed to show
    for ob in bpy.data.objects:
        if not (ob in objects):
            ob.hide_render = True
            ob.hide = True

    # render the preview
    if opengl:  # use the viewport representation to create preview
        bpy.ops.view3d.view_selected()
        bpy.ops.render.opengl(view_context=True)
    else:  # use real rendering
        # create camera
        bpy.ops.object.camera_add(view_align=True)
        cam = bpy.context.scene.objects.active
        bpy.data.cameras[cam.data.name].type = 'ORTHO'
        bpy.data.scenes[0].camera = cam  # set camera as active camera

        sUtils.selectObjects(objects, True, 0)
        bpy.ops.view3d.camera_to_view_selected()
        # create light
        bpy.ops.object.lamp_add(type='SUN', radius=1)
        light = bpy.context.scene.objects.active
        light.matrix_world = cam.matrix_world
        # set background
        oldcolor = bpy.data.worlds[0].horizon_color.copy()
        bpy.data.worlds[0].horizon_color = mathutils.Color((1.0, 1.0, 1.0))
        bpy.ops.render.render()
        bpy.data.worlds[0].horizon_color = oldcolor
        sUtils.selectObjects([cam, light], True, 0)
        bpy.ops.object.delete()

    # safe render and reset the scene
    log("Saving model preview to: " + os.path.join(export_path, modelname + '.png'), "INFO")
    bpy.data.images['Render Result'].save_render(os.path.join(export_path, modelname + '.png'))

    # make all objects visible again
    for ob in bpy.data.objects:
        ob.hide_render = False
        ob.hide = False


def toggleTransformLock(obj, setting=None):
    """Toogle transform lock for the referred object"""
    obj.lock_location[0] = setting if setting is not None else not obj.lock_location[0]
    obj.lock_location[1] = setting if setting is not None else not obj.lock_location[1]
    obj.lock_location[2] = setting if setting is not None else not obj.lock_location[2]
    obj.lock_rotation[0] = setting if setting is not None else not obj.lock_rotation[0]
    obj.lock_rotation[1] = setting if setting is not None else not obj.lock_rotation[1]
    obj.lock_rotation[2] = setting if setting is not None else not obj.lock_rotation[2]
    obj.lock_scale[0] = setting if setting is not None else not obj.lock_scale[0]
    obj.lock_scale[1] = setting if setting is not None else not obj.lock_scale[1]
    obj.lock_scale[2] = setting if setting is not None else not obj.lock_scale[2]


def switchToScene(scenename):
    """Switch to Blender scene of the given name"""
    if scenename not in bpy.data.scenes.keys():
        bpy.data.scenes.new(scenename)
    bpy.context.screen.scene = bpy.data.scenes[scenename]
    return bpy.data.scenes[scenename]


def getCombinedDimensions(objects):
    """Returns the dimension of the space the objects passed occupy.

    Args:
        objects(list): list of

    Returns:
        list of floats (x, y, z) of dimensions

    Raises:
        ValueError: If empty object list is passed.

    """
    bbpoints = []
    for o in objects:
        for p in o.bound_box:
            bbpoints.append(o.matrix_world * mathutils.Vector(p))
    mindims = [min([bbpoint[i] for bbpoint in bbpoints]) for i in (0, 1, 2)]
    maxdims = [max([bbpoint[i] for bbpoint in bbpoints]) for i in (0, 1, 2)]
    return [abs(maxdims[i]-mindims[i]) for i in (0, 1, 2)]


def getPhobosConfigPath():
    """Returns the user-defined config path if set or the default-path

    Returns(str): (user-defined) config path
    """
    if bpy.context.user_preferences.addons["phobos"].preferences.configfolder != '':
        return bpy.context.user_preferences.addons["phobos"].preferences.configfolder
    else:  # the following if copied from setup.py, may be imported somehow in the future
        return getConfigPath()
