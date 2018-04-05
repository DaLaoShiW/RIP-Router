import struct
from socket import *

class Packet:

    def __init__(self):
        self.len_bytes = 0
        self.byte_format = ''
        self.field_names = []

    def __len__(self):
        return self.len_bytes

    def __str__(self):
        out = ""
        for field in self.field_names:
            out += field+": "+str(getattr(self, field))+"\n"
        return out

    def unpack(self, byte_data):
        if len(self.field_names) == 0:
            raise Exception('Missing packet format!')

        values = struct.unpack(self.byte_format, byte_data)
        for i in range(0, len(values)):
            setattr(self, self.field_names[i], values[i])

    def pack(self, values):
        if len(self.field_names) == 0:
            raise Exception('Missing packet format!')

        return struct.pack(self.byte_format, *values)

    def send(self, port, *values):
        a_socket = socket(AF_INET, SOCK_DGRAM)
        a_socket.sendto(self.pack(values), ("localhost", port))

    def add_field(self, format, len_bytes, name=None):
        self.byte_format += format
        if name:
            self.field_names.append(str(name))
            self.len_bytes += len_bytes

    def add_padding(self, len_bytes):
        self.add_field(str(len_bytes)+'x', len_bytes)

    def add_int8(self, name):
        self.add_field('b', 1, name)

    def add_int16(self, name):
        self.add_field('h', 2, name)

    def add_int32(self, name):
        self.add_field('i', 4, name)

class TestPacket(Packet):

    def __init__(self, byte_data=None):
        super().__init__()
        self.add_int8('Test number 1')
        self.add_int8('Test number 2')
        self.add_int8('Test number 3')
        if byte_data:
            self.unpack(byte_data)
