'''
DDSFile

support for dds format image files
    
gsk 6/12/2012

LICENSE:

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




typedef struct {
  DWORD           dwSize;
  DWORD           dwFlags;
  DWORD           dwHeight;
  DWORD           dwWidth;
  DWORD           dwPitchOrLinearSize;
  DWORD           dwDepth;
  DWORD           dwMipMapCount;
  DWORD           dwReserved1[11];
  DDS_PIXELFORMAT ddspf;
  DWORD           dwCaps;
  DWORD           dwCaps2;
  DWORD           dwCaps3;
  DWORD           dwCaps4;
  DWORD           dwReserved2;
} DDS_HEADER;

struct DDS_PIXELFORMAT {
  DWORD dwSize;
  DWORD dwFlags;
  DWORD dwFourCC;
  DWORD dwRGBBitCount;
  DWORD dwRBitMask;
  DWORD dwGBitMask;
  DWORD dwBBitMask;
  DWORD dwABitMask;
};
'''



import struct

class DDSFile():
    
    def __init__(self, rawdata):
        self.buf = rawdata
        
        offset = 0
        
        (magic, dummy, dwSize, dwFlags, dwWidth, dwHeight) = struct.unpack('<3sbiiii', self.buf[offset:offset+20])
        offset += 20   
        (dwPitchOrLinearSize, dwDepth, dwMipMapCount) = struct.unpack('<iii', self.buf[offset:offset+12])
        offset += 12

        self.dds_header_magic = magic
        self.dds_header_dwSize = dwSize
        self.dds_header_dwFlags = dwFlags
        self.dds_header_dwWidth = dwWidth
        self.dds_header_dwHeight = dwHeight
        
        # skip the 11 *4 (44) reserved dwords
        offset += 11*4
        
        (dwSize, dwFlags, dwFourCC, dwRGBBitCount) = struct.unpack('<ii4si', self.buf[offset:offset+16])
        offset += 16
        
        self.dds_pixelformat_dwSize = dwSize
        self.dds_pixelformat_dwFlags = dwFlags
        self.dds_pixelformat_dwFourCC = dwFourCC
        self.dds_pixelformat_dwRGBBitCount = dwRGBBitCount
        
        # skip the remainder of DDS_PIXELFORMAT
        offset += 16
        
        (dwCaps, dwCaps2, dwCaps3, dwCaps4) = struct.unpack('<iiii', self.buf[offset:offset+16])
        offset += 16

        self.dds_header_dwCaps = dwCaps
        self.dds_header_dwCaps2 = dwCaps2
        self.dds_header_dwCaps3 = dwCaps3
        self.dds_header_dwCaps4 = dwCaps4
        
    def decompressBlockDXT1(self, x, y, width, ddsbuf, bufptr, bmpbuf):
        pass
        
    '''    
void DecompressBlockDXT1(unsigned long x, unsigned long y, unsigned long width, const unsigned char *blockStorage, unsigned long *image)
{
	unsigned short color0 = *reinterpret_cast<const unsigned short *>(blockStorage);
	unsigned short color1 = *reinterpret_cast<const unsigned short *>(blockStorage + 2);
 
	unsigned long temp;
 
	temp = (color0 >> 11) * 255 + 16;
	unsigned char r0 = (unsigned char)((temp/32 + temp)/32);
	temp = ((color0 & 0x07E0) >> 5) * 255 + 32;
	unsigned char g0 = (unsigned char)((temp/64 + temp)/64);
	temp = (color0 & 0x001F) * 255 + 16;
	unsigned char b0 = (unsigned char)((temp/32 + temp)/32);
 
	temp = (color1 >> 11) * 255 + 16;
	unsigned char r1 = (unsigned char)((temp/32 + temp)/32);
	temp = ((color1 & 0x07E0) >> 5) * 255 + 32;
	unsigned char g1 = (unsigned char)((temp/64 + temp)/64);
	temp = (color1 & 0x001F) * 255 + 16;
	unsigned char b1 = (unsigned char)((temp/32 + temp)/32);
 
	unsigned long code = *reinterpret_cast<const unsigned long *>t(blockStorage + 4);
 
	for (int j=0; j < 4; j++)
	{
		for (int i=0; i < 4; i++)
		{
			unsigned long finalColor = 0;
			unsigned char positionCode = (code >>  2*(4*j+i)) & 0x03;
 
			if (color0 > color1)
			{
				switch (positionCode)
				{
					case 0:
						finalColor = PackRGBA(r0, g0, b0, 255);
						break;
					case 1:
						finalColor = PackRGBA(r1, g1, b1, 255);
						break;
					case 2:
						finalColor = PackRGBA((2*r0+r1)/3, (2*g0+g1)/3, (2*b0+b1)/3, 255);
						break;
					case 3:
						finalColor = PackRGBA((r0+2*r1)/3, (g0+2*g1)/3, (b0+2*b1)/3, 255);
						break;
				}
			}
			else
			{
				switch (positionCode)
				{
					case 0:
						finalColor = PackRGBA(r0, g0, b0, 255);
						break;
					case 1:
						finalColor = PackRGBA(r1, g1, b1, 255);
						break;
					case 2:
						finalColor = PackRGBA((r0+r1)/2, (g0+g1)/2, (b0+b1)/2, 255);
						break;
					case 3:
						finalColor = PackRGBA(0, 0, 0, 255);
						break;
				}
			}
 
			if (x + i < width)
				image[(y + j)*width + (x + i)] = finalColor;
		}
	}
}        
        
    '''
        
        
    def uncompressToBmp(self):
        ddsbuf = bytearray(self.buf)
        bmpbuf = bytearray(self.dds_header_dwWidth*self.dds_header_dwHeight*4)
        
        blockCountX = (self.dds_header_dwWidth + 3) / 4
        blockCountY = (self.dds_header_dwHeight + 3) / 4
        blockWidth = 4
        blockHeight = 4

        if self.dds_header_dwWidth < 4:
            blockWidth = self.dds_header_dwWidth
            
        if self.dds_header_dwHeight < 4:
            blockHeight = self.dds_header_dwHeight

        print 'uncompressing DXT1 dds texture: blockCountX: %i blockCountY: %i' % (blockCountX, blockCountY) 
 
        bufptr = 0
        for j in range(0, blockCountY):
            for i in range(0, blockCountX):
                self.decompressBlockDXT1(i*4, j*4, self.dds_header_dwWidth, ddsbuf, bufptr, bmpbuf)
                bufptr += 8
                
        
        return bmpbuf
        
        
        
    def save(self, filename):
        file = open(filename, 'wb')
        file.write(self.buf)
        file.close()
   
    # This is a hack to make the EQ DXT1 compressed dds textures readable for Panda3D's loader
    def patchHeader(self):
        # patch caps to not indicate mipmaps anymore 
        dwCaps4 = struct.pack('<i', 0x1000)
        
        # patch up mipmap count
        dwMipMapCount = struct.pack('<i', 1)
             
        # reassemble the header
        self.buf = self.buf[0:28] + dwMipMapCount + self.buf[32:108] + dwCaps4 + self.buf[112:]
        
        
    def dumpHeader(self):
        offset = 0
        (magic, dummy, dwSize, dwFlags, dwWidth, dwHeight) = struct.unpack('<3sbiiii', self.buf[offset:offset+20])
        offset += 20
        print 'DDS_HEADER magic:%s dwSize:%i dwFlags:0x%x dwWidth:%i dwHeight:%i' % (magic, dwSize, dwFlags, dwWidth, dwHeight)
        
        (dwPitchOrLinearSize, dwDepth, dwMipMapCount) = struct.unpack('<iii', self.buf[offset:offset+12])
        offset += 12
        print 'dwPitchOrLinearSize:%i dwDepth:%i dwMipMapCount:%i' % (dwPitchOrLinearSize, dwDepth, dwMipMapCount)

        # skip the 11 *4 (44) reserved dwords
        offset += 11*4
        
        (dwSize, dwFlags, dwFourCC, dwRGBBitCount) = struct.unpack('<ii4si', self.buf[offset:offset+16])
        offset += 16
        print 'DDS_PIXELFORMAT dwSize:%i dwFlags:0x%x dwFourCC:%s dwRGBBitCount:%i' % (dwSize, dwFlags, dwFourCC, dwRGBBitCount)
        
        # skip the remainder of DDS_PIXELFORMAT
        offset += 16
        
        (dwCaps, dwCaps2, dwCaps3, dwCaps4) = struct.unpack('<iiii', self.buf[offset:offset+16])
        offset += 16
        print 'dwCaps:0x%x dwCaps2:0x%x dwCaps3:0x%x dwCaps4:0x%x' % (dwCaps, dwCaps2, dwCaps3, dwCaps4)
        
        




