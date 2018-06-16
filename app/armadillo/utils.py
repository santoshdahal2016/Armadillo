import qrcode
from PIL import Image
import base64
from io import BytesIO

import os
from django.conf import settings
import collada
import numpy as np
import io

DEF_SIZE_MARKER = 512

def create_qr_from_text(text):
    """
    Creates qr code.
    Args:
      *text* (str) text
    Out:
      PIL Image with QR code
    """
    qr = qrcode.QRCode(
     version=1,
     error_correction=qrcode.constants.ERROR_CORRECT_L,
     box_size=3,
     border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image()
    return img

def put_qr_on_marker(text, marker_in, marker_qr_out = 'markerqr.png'):
    """
    Puts qr code with text on marker image.
    Args:
      *text* (str) text
      *marker_in* - (str) - input png file
      *marker_qr_out* - (str) - output png  file
    """
    img = Image.open(marker_in)

    qr_img = create_qr_from_text(text)

    t_width = img.size[0]
    t_height = img.size[1]
    assert t_height == t_width == DEF_SIZE_MARKER, "marker size does not match ({0}, {0})".format(DEF_SIZE_MARKER)

    new_im = Image.new('RGB', (t_width, t_height), "white")

    new_im.paste(img, (0, 0))
    new_im.paste(qr_img, (60 +  qr_img.size[0], 155))

    buffered = BytesIO()
    new_im.save(buffered, format = "png")
    img_str = base64.b64encode(buffered.getvalue())

    return img_str

def color_func( scalars ):
    smin = np.min(scalars)
    smax = np.max(scalars)
    scalars = (scalars - smin) / smax

    colors = np.zeros((scalars.shape[0],3))
    colors[:,1] += scalars
    colors[:,2] += (1-scalars)

    return colors

def fv_scalar_to_collada(verts,faces,scalars):

    color = color_func(scalars)

    #create collada obj
    mesh = collada.Collada()

    #add shading
    effect = collada.material.Effect("effect0",\
      [], #TEXTURES GO HERE
      "phong", diffuse=(1,1,1), specular=(1,1,1),
      double_sided=True)
    mat = collada.material.Material("material0", "mymaterial", effect)
    mesh.effects.append(effect)
    mesh.materials.append(mat)

    vert_src = collada.source.FloatSource("verts-array", verts, ('X', 'Y', 'Z'))
    color_src = collada.source.FloatSource("colors-array", np.array(color), ('R', 'G', 'B'))

    geom = collada.geometry.Geometry(mesh, "geometry0", "fsave_test",\
      [vert_src,color_src])

    #creates list of inputs for collada DOM obj...so many decorators
    input_list = collada.source.InputList()

    input_list.addInput(0, 'VERTEX', "#verts-array")
    input_list.addInput(1, 'COLOR', "#colors-array")

    #creates faces
    triset = geom.createTriangleSet(
      np.concatenate([faces,faces],axis=1),\
      input_list, "materialref")

    triset.generateNormals()

    geom.primitives.append(triset)
    mesh.geometries.append(geom)

    #creates scene node, which causes display
    matnode = collada.scene.MaterialNode("materialref", mat, inputs=[])
    geomnode = collada.scene.GeometryNode(geom, [matnode])
    node = collada.scene.Node("node0", children=[geomnode])

    #create scene
    myscene = collada.scene.Scene("fs_base_scene", [node])
    mesh.scenes.append(myscene)
    mesh.scene = myscene

    buf = io.BytesIO()
    mesh.write(buf)
    return buf
