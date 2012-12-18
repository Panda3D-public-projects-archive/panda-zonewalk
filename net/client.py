'''
client.py UDP and TCP clients



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


from socket import *
import select
import asyncore

import sys
import select


class UDPClient():
    
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.target = (server, port)
        
        self.client_socket = socket(AF_INET, SOCK_DGRAM)

        self.rlst = (self.client_socket,)
        self.wlst = ()
        self.elst = (self.client_socket,)
        
    def send(self, msg):
        print 'Sending:', msg
        self.client_socket.sendto(msg, self.target)

    def receiveData(self):
        recv_data, addr = self.client_socket.recvfrom(2048)
        print 'receiving from:', addr, ' data:', recv_data
        
    def update(self):
        rlst, wlst, elst =select.select(self.rlst, self.wlst, self.elst, 0)  # with timeout=0 this basically is a poll
        if len(rlst) > 0:
            self.receiveData()
        if len(elst) > 0:
            print 'UDPClient socket error'

    '''
    00 01  -  Session Request (Client -> Server)
SOE Opcode	- Net Byte SHORT	
CRC Length	- Net BYte INT
Connection ID	- Net Byte INT
ClientUDPSize	- Net Byte INT	

The SOE Opcode is just the opcode number to identify the packet.

CRC Length is the amount of length of the CRC checksum to append at the end of a packet. SWG uses 2 bytes. 
Note CRC32 checksums are 32bit, making them 4 bytes, but only 2 are appended.

Connection ID is some type of identification used for the connection. Only other time seen is during a disconnect.

ClientUDPSize is the maximum size allocated for the client's UDP packet buffer. No packet is allowed to exceed this size. 
If it is larger, it must be fragmented. This size is equal to 496 bytes.

Note* This opcode DOES NOT have a footer.




00 02  -  Session Response(Server -> Client)
SOE Opcode	- Net Byte SHORT
Connection ID	- Net Byte INT
CRCSeed		- Net Byte INT
CRCLength	- BYTE
Crypt Flag	- SHORT
ServerUDPSize	- Net Byte INT

Connection ID is replied using the same ID sent by the Session Request.
CRCSeed is a seed value used for the calculation of the CRC32 Checksum.
CRCLength
Crypt Flag is set to 0x0104 (260) to enable the default encryption method. Set to 0x0 and the encryption is completely disabled.
ServerUDPSize is the maximum size allocated for the server's UDP packet buffer. No packet is allowed to exceed this size.
 So far the client has not sent anything large enough to fill this, or be fragmented. This size is equal to 496 bytes.

Note* This opcode DOES NOT have a footer.

    '''

            
class UDPClientStream(UDPClient):
    
    def __init__(self, server, port):
        UDPClient.__init__(self, server, port)
        self.session_state = 0
        
        