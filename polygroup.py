'''
polygroup.py

PolyGroups organize meshes into groups that share a common texture
(c) gsk 2012


Copyright (c) 2012, Gedolian Soft Kram
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided 
that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions 
    and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions 
    and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the <ORGANIZATION> nor the names of its contributors may be used to endorse or 
    promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR 
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY 
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



'''



from panda3d.core import Geom, GeomTriangles, GeomNode, CullFaceAttrib
from panda3d.core import PandaNode, NodePath, TextureAttrib, TransparencyAttrib, ColorAttrib


# The PolyGroup defines a submesh in which all polygons use the same texture
# Each PolyGroup is mapped directly to a Panda3D NodePath which gets the texture assigned
class PolyGroup():
    
    # vdata is the Panda3D vertex data object created by the main Mesh
    def __init__(self, vdata, tex_idx):
        self.vdata = vdata      # vertex data, passed in from parent mesh
        
        self.name = 'PolyGroup_'+str(tex_idx)
        self.geom = Geom(self.vdata)
        self.primitives = GeomTriangles(Geom.UHStatic)
        self.geom.addPrimitive(self.primitives)
        
    # called by the sprite animation code to let us know we need to change our texture image
    def animFrameChange(self, t):
        return 
        # print 'POLYGROUP ANIMATION UPDATE'
        self.nodePath.setTexture(t, 1)
            
                
    # Parameters:
    # wld_container - WldContainer parent object
    # f             - the f36 fragment we are based on
    # start_index   - index of our first poly in the fragment's polyList polygon list
    # n_polys       - numer of polys to build
    # tex_idx       - index of the texture that all our polys share
    def build(self, wld_container, f, start_index, n_polys, tex_idx):

        zone = wld_container.zone
        sprite = wld_container.getSprite(tex_idx)
            
        polyList = f.polyList
        poly_idx = start_index
        for poly in range(0, n_polys):
            p = polyList[poly_idx]
            poly_idx += 1
            self.primitives.addVertices(p[0], p[1], p[2])

        self.node = GeomNode(self.name)
        self.node.addGeom(self.geom)
        
        # attach all our nodes under the zone's geometry root node
        self.nodePath = zone.rootNode.attachNewNode(self.node)
        
        # self.nodePath.setRenderModeWireframe()
        # self.nodePath.setRenderModeFilled()
        # self.nodePath.showBounds()
        
        self.nodePath.setPos(f.centerX, f.centerY,f.centerZ)    # translate to correct world position
        
        self.nodePath.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullCounterClockwise))
        # self.nodePath.setAttrib(CullFaceAttrib.make(CullFaceAttrib.MCullClockwise))

        # Texture setup
        if sprite != None:
            # sprite.dump()
            if sprite.numtex > 0:   
                t = sprite.textures[0]
                self.nodePath.setTexture(t)
        else:
            print 'Error: texture (idx=%i) not found. PolyGroup will be rendered untextured' % (tex_idx)

        return 1
        
              
