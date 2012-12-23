'''
texture.py

Implements our texture manager and also some bmp handling support
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

import struct

from panda3d.core import PNMImage, Texture, StringStream
from file.ddsfile import DDSFile

class TextureContainer():

    def __init__(self, name, panda_texture, image_file, type):
        self. name = name
        self.panda_texture = panda_texture
        self.image_file = image_file
        self.image_type = type            # format type of the memory image ('DDS' or 'IMG')
        self.flags = 0x00000000
        
class TextureManager():
    
    def __init__(self):
        self.textures = {}
        
    # force lower case and remove file extension (if any)
    def prepTextureName(self, name):
        n = name.lower()
        i = name.find('.')
        if i != -1:
            n = n[0:i]
            
        return n

    def addTexture(self, name, panda_texture, texture_file, t_type):
        name = self.prepTextureName(name)
        if self.textures.has_key(name):
            print 'WARNING texture %s already exists, overwriting ...' % (name)
        
        self.textures[name] = TextureContainer(name, panda_texture, texture_file, t_type)


    def maskImg(self, img, img_size):
        # print 'SIZE:',img_size
        (top_left_pixel,) = struct.unpack('<i', img[0:4])   # this is our transparent color
        masked_img = ''
        offset = 0
        for i in range(0, img_size):
            (pixel,) = struct.unpack('<i', img[offset:offset+4])
            if pixel == top_left_pixel:
                pixel &= 0x00ffffff     # set alpha to 0
            
            masked_img += struct.pack('<i', pixel)
            offset += 4
            
        return masked_img
        
    # masked textures are a HACK we use to implement the old style transparency for leaves, fire etc.
    # The texture loader turns all bmp textures into 32bit rgba true color images anyway
    # we need to setup the alpha channel of those here in such a way that it masks out 
    # the pixels that are supposed to be transparent
    def createMaskedTexture(self, name):
        name = self.prepTextureName(name)
        original_name = name[len('masked-'):]
        if self.textures.has_key(original_name):
            tc = self.textures[original_name]   # get the original texture
            bm = tc.image_file
            img_type = tc.image_type

            if img_type == 'DDS':
                mtex = TextureContainer(name, tc.panda_texture, tc.image_file, img_type)
                self.textures[name] = mtex
                return mtex
                
            if img_type != 'IMG':
                print 'ERROR in createMaskedTexture(): cant create masked texture from non IMG type image'
                return None
                
            # print type(bm)
            # print len(bm)
            
            # FIXME: this just copies the original right now! Need to implement the alpha-mask bit still
            m_img = self.maskImg(bm, tc.panda_texture.getXSize() * tc.panda_texture.getYSize())

            t = Texture()               # create empty texture object
            component_type = Texture.TUnsignedByte
            format = Texture.FRgba 
            t.setup2dTexture(tc.panda_texture.getXSize(),tc.panda_texture.getYSize(), component_type, format)
            t.setRamImage(m_img)
            
            mtex = TextureContainer(name, t, m_img, img_type)
            self.textures[name] = mtex
            return mtex
        else:
            print 'TextureManager::createMaskedTexture() failed, original texture:%s not found' % (original_name)
            return None
        
        
    # returns the panda_texture for the named texture container (creates it if it does not exist)
    def getMaskedTexture(self, name):
        tex = self.getTexture(name)
        if tex == None:
            # print 'need to create \"masked\" texture:', name
            mtex = self.createMaskedTexture(name)
            return mtex.panda_texture
           
        return tex
        
    # returns the panda_texture for the named texture container (if it exists)
    def getTexture(self, name):
        name = self.prepTextureName(name)
        try:
            return self.textures[name].panda_texture
        except:
            return None

    # check if the named texture has been loaded
    def findTexture(self, name):
        name = self.prepTextureName(name)
        if self.textures.has_key(name):
            return True
            
        return False
        
    # Params
    # container is a WLDContainer object
    def loadTexture(self, texname, container):
        
        # Note that we reference the texture files by name. This works under the 
        # assumption that texture names are unique!
        if self.findTexture(texname) == True:
            return  # texture already loaded before
        
        # print 'loading texture:', texname
        t_type = ''
        s3dentry = container.s3d_file_obj.getFile(texname)            
        if s3dentry != None:
            texfile = s3dentry.data
            (magic,) = struct.unpack('<2s', texfile[0:2])
            if magic == 'BM':
                t_type = 'IMG'      # raw 32 bit rgba (actually argb)
                # Generic BMP file
                # patch up the sometimes irregular bmp headers
                texfile = self.checkBmp(texfile, texname)
                if texfile == None:
                    return
                
                # turn bmp into a 32bit rgba true color image
                # returns a tuple of (img, width, height)
                img = self.createAlphaBMP(texfile, texname)
                texfile = img[0]   # so that the addTexture() at the bottom works
                                    
                t = Texture()               # create empty texture object
                component_type = Texture.TUnsignedByte
                format = Texture.FRgba 
                t.setup2dTexture(img[1], img[2], component_type, format)
                t.setRamImage(img[0])
                #t.load(ti)                  # load texture from pnmimage
                
            elif magic == 'DD':
                t_type = 'DDS'
                # DDS file
                dds = DDSFile(texfile)
                dds.patchHeader()
                # dds.dumpHeader()
                # dds.uncompressToBmp()
                # dds.save(texname+'.dds')
                    
                ts = StringStream(dds.buf)  # turn into an istream                   
                t = Texture()               # create texture object
                t.readDds(ts)               # load texture from dds ram image
            else:
                print 'Error unsupported texture: %s magic:%s referenced in fragment: %i' % (texname, magic, f.id)
                return
        else:
            print 'Error: texture %s not found in s3d archive' % (texname)
            return
            
        # t.setWrapU(Texture.WMClamp)
        # t.setWrapV(Texture.WMClamp)

        self.addTexture(texname, t, texfile, t_type)


    # ================================================================
    # BMP TOOLS
    # ================================================================

    # make a full 32bit rgba image from a palettized 8bit BMP file image
    # name is without an extension
    # Returns the raw image plus width and height as a tuple
    def createAlphaBMP(self, bm, name):
        # self.dumpBMPInfo(bm)
        # unpack the original header (54 bytes)
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])       
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant) = \
        struct.unpack('<iIIhhiiIIii', bm[14:14+40])
        
        # unpack the palette
        if biClrUsed == 0: 
            biClrUsed = 256
            
        if biClrUsed != 256:
            print 'biClrUsed ERROR, biClrImportant:%i offset:%i' % (biClrImportant,offset)
            
        format = '<'+str(biClrUsed)+'i'
        # print format
        palette = struct.unpack(format, bm[54:54+biClrUsed*4])
        # print len(palette)
        # palette = bytearray(palette)
        
        # create 32 bit rgba true color image 
        img = ''
        npixels = biWidth * biHeight
        pixel_index = offset
                
        for i in range(0, npixels):
            (pixel,) = struct.unpack('<b', bm[pixel_index:pixel_index+1])            
            rgba = palette[pixel] | 0xff000000    # set alpha to fully opaque
            img += struct.pack('<i', rgba)
            pixel_index += 1
            
        
        # patch header 
        '''
        offset = 54                 # true color images have no palette, thus just the header size as offset
        biSizeImage = npixels*4
        size = biSizeImage+offset
        biBitCount = 32
        biClrUsed = 0
        biClrImportant = 0

        bm_hdr = struct.pack('<2siii', magic, size, dummy, offset)       
        bm_info_hdr = struct.pack('<iIIhhiiIIii', biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant)
        new_bm_hdr = bm_hdr + bm_info_hdr
        
        bm = new_bm_hdr + img
        self.writeBMPFile(bm, name+'.bmp')
        '''
        
        return (img, biWidth, biHeight)
    
    # dump .bmp file header info
    def dumpBMPInfo(self, bm, name=''):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])
        print 'bmp %s magic:%s size:%i offset:%i' % (name, magic, size, offset)
        
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant) = \
        struct.unpack('<iIIhhiiIIii', bm[14:14+40])
        print 'biSize:%i biWidth:%i biHeight:%i biPlanes:%i biBitcount:%i biCompression:%i biSizeImage:%i biClrUsed:%i biClrImportant:%i' % \
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, biClrUsed, biClrImportant)
        
    # Panda3D's PNImage loader cant deal with bmp files that have limited size palettes
    # it only can process full size palletes (1024 bytes)
    # Here we patch up the Bitmap header of a bmp from a s3d file to prepare it for extending the palette
    # to the full size.
    def patchBmHeader(self, bm, new_offset):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])       
        (biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant) = \
        struct.unpack('<iIIhhiiIIii', bm[14:14+40])

        # patch up header info
        size_diff = offset - new_offset
        new_size = size + size_diff
        biClrUsed = biClrImportant = 256    # adapt to our extended full site palette

        bm_hdr = struct.pack('<2siii', magic, new_size, dummy, new_offset)       
        bm_info_hdr = struct.pack('<iIIhhiiIIii', biSize, biWidth, biHeight, biPlanes, biBitCount, biCompression, biSizeImage, dummy1, dummy2, biClrUsed, biClrImportant)
        new_bm_hdr = bm_hdr + bm_info_hdr
        # self.dumpBMPInfo(new_bm_hdr)
        return new_bm_hdr
        
    # some of the ancient texture files in the old s3d archives even use short color tables
    # (not the standard 256*4 = 1024 bytes). Panda3D's PNImage loader barfs on these. 
    # Patch them up here
    def checkBmp(self, bm, name):
        (magic, size, dummy, offset) = struct.unpack('<2siii', bm[0:14])
        if offset != 1078:  # the "normal" offset for a palletized 8 bit image (1024 palette+54 header)
            # print 'Patching up Panda3D incompatible .bmp texture:', name
    
            color_table = bm[54:offset]     # extract original color table
            image_data = bm[offset:size]    # extract original image data
            
            hdr = self.patchBmHeader(bm, 1078)  # fix up the bitmap header
            new_bm = hdr + color_table + str(bytearray(1078-offset)) + image_data # assemble new bmp
        else:
            new_bm = bm     # leave it as is
            
        
        return new_bm
    
    def writeBMPFile(self, bm, name):
        file = open(name, 'wb')
        file.write(bm)
        file.close()

