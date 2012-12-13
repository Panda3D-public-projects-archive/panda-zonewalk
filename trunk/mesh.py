'''
mesh.py

The mesh class 
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




from panda3d.core import  Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter

from polygroup import PolyGroup
              
        
class Mesh():

    def __init__(self, name):
        self.name = name
        self.poly_groups = []
        
        # GeomVertexFormats
        #
        # GeomVertexFormat.getV3cpt2()  - vertex, color, uv
        # GeomVertexFormat.getV3t2()    - vertex, uv
        # GeomVertexFormat.getV3cp()    - vertex, color
        # GeomVertexFormat.getV3n3t2()  - vertex, normal, uv
        # GeomVertexFormat.getV3n3cpt2()- vertex, normal, rgba, uv
        
        # textured
        self.vdata = GeomVertexData(name, GeomVertexFormat.getV3n3cpt2(), Geom.UHStatic)
        
        # plain color filled polys
        # self.vdata = GeomVertexData(name, GeomVertexFormat.getV3cp(), Geom.UHStatic)
        
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.vnormal = GeomVertexWriter(self.vdata, 'normal')
        self.color = GeomVertexWriter(self.vdata, 'color')
        self.texcoord = GeomVertexWriter(self.vdata, 'texcoord')
        
        
    # f is a 0x36 mesh fragment (see fragment.py for reference)
    def buildFromFragment(self, f, wld_container):
        
        # write vertex coordinates
        for v in f.vertexList:
            self.vertex.addData3f(v[0], v[1], v[2])

        # write vertex colors
        for rgba in f.vertexColorsList:
            '''
            r = (rgba & 0xff000000) >> 24
            g = (rgba & 0x00ff0000) >> 16
            b = (rgba & 0x0000ff00) >> 8
            a = (rgba & 0x000000ff)
            if a != 0:
                print 'vertex color has alpha component, r:0x%x g:0x%x b:0x%x a:0x%x ' % (r, g, b, a)
            '''    
            self.color.addData1f(rgba)

        # write vertex normals
        for v in f.vertexNormalsList:
            self.vnormal.addData3f(v[0], v[1], v[2])
            
        # write texture uv
        for uv in f.uvList:
            self.texcoord.addData2f(uv[0], uv[1])
            
        # Build PolyGroups
        # each polyTexList is a tuple containing a polygon count and the texture index for those polys        
        # we create a PolyGroup for each of these
        # the PolyGroup creates all Polygons sharing a texture and adds them under a NodePath
        poly_idx = 0
        for pt in f.polyTexList:
            n_polys = pt[0]
            tex_idx = pt[1]

            pg = PolyGroup(self.vdata, tex_idx)
                        
            # pass fragment so that it can access the SPRITES
            if pg.build(wld_container, f, poly_idx, n_polys, tex_idx) == 1:
                self.poly_groups.append(pg)

            poly_idx += n_polys            
        
        if poly_idx != f.polyCount or poly_idx != len(f.polyList):
            print 'ERROR: polycount mismatch'
