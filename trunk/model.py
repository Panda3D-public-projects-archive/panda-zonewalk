'''
model.py

The model class is used to implement mobs, players and placeables
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

from wldfile import WLDContainer
from mesh import Mesh


class Model():
    
    def __init__(self, name):
        self.name = name
        self.wld_container = None
        
    # wld_containers : directory of wld container objects
    def load(self, wld_containers):
        print 'loading model:', self.name
        
        # find our 0x14 fragment in any of the "object" wld files in the container
        f14 = None
        for c in wld_containers.values():
            if c.type == 'obj':
                f14 = c.wld_file_obj.getFragmentByName(self.name)
                if f14 != None:
                    self.wld_container = c  # ok , this is "our" wld_file_obj
                    break;
        
        if f14 == None:
            print 'ERROR during model load. Base 0x14 fragment not found. Model:', self.name
            return
        
        wld_file_obj = self.wld_container.wld_file_obj
        
        # note that this will need to be changed when we support animated mob models
        # for those f14.fragRefs does not point to a 0x2d frag but rather to a 0x11 anim track ref
        f2d = wld_file_obj.getFragment(f14.fragRefs3[0])
        # f2d.dump()
                    
        f36 = wld_file_obj.getFragment(f2d.fragRef)
        # f36.dump()
        
        m = Mesh(self.name+'_mesh')
        m.buildFromFragment(f36, self.wld_container)
        
        