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
import select, sys, struct


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
        rlst, wlst, elst = select.select(self.rlst, self.wlst, self.elst, 0)  # with timeout=0 this basically is a poll
        if len(rlst) > 0:
            self.receiveData()
        if len(elst) > 0:
            print 'UDPClient socket error'

            
class UDPClientStream(UDPClient):
    
    def __init__(self, server, port):
        UDPClient.__init__(self, server, port)
        self.session_state = 0
        
        # session request: 
        # opcode 0x0001, crc_len (the value is a guess), connection id, client udp packet size
        session_request = struct.pack('!hiii', 0x0001, 2, 55, 496)
        self.send(session_request)
 
    def receiveData(self):
        recv_data, addr = self.client_socket.recvfrom(2048)
        print len(recv_data)
        if self.session_state == 0:
            (opcode, cid, crc_seed, crc_len, crypt_flag, udp_size, session_key) = \
                struct.unpack('!hiibhii', recv_data[0:21])
        print 'opcode:0x%x cid:%i crc_seed:%i crc_len:%i crypt_flag:0x%x udp_size:%i session_key:%i' % \
            (opcode, cid, crc_seed, crc_len, crypt_flag, udp_size, session_key)