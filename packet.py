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

    def send(self, port, pack):
        a_socket = socket(AF_INET, SOCK_DGRAM)
        a_socket.sendto(pack, ("localhost", port))

    def format_field(self, format, len_bytes, name=None):
        self.byte_format += format
        if name:
            self.field_names.append(str(name))
            self.len_bytes += len_bytes

    def format_padding(self, len_bytes):
        self.format_field(str(len_bytes)+'x', len_bytes)

    def format_int8(self, name):
        self.format_field('b', 1, name)

    def format_int16(self, name):
        self.format_field('h', 2, name)

    def format_int32(self, name):
        self.format_field('i', 4, name)

class RIPPacket(Packet):

    def __init__(self, byte_data=None):
        super().__init__()
        self.from_router_id = None
        self.entries = []
        self.num_entries = 0
        self.entry_size = 20
        self.header_size = 4
        self.command = 2
        self.version = 2
        self.format_int8('command')
        self.format_int8('version')
        self.format_int16('from_router_id')

        if byte_data:
            self.unpack(byte_data)

    def add_entry(self, router_id, cost):
        self.entries.append({
            'afi': 2,
            'router_id': router_id,
            'cost': cost,
        })

    def format_entry(self):
        self.format_int16('afi_'+str(self.num_entries))
        self.format_padding(2)
        self.format_int32('router_id_'+str(self.num_entries))
        self.format_padding(8)
        self.format_int32('cost_'+str(self.num_entries))

    def unpack(self, byte_data):
        entries = (len(byte_data) - self.header_size) // self.entry_size
        while self.num_entries < entries:
            self.format_entry()
            self.num_entries += 1

        super().unpack(byte_data)
        for i in range(self.num_entries):
            i = str(i)
            self.entries.append({
                'afi': getattr(self, 'afi_'+i),
                'router_id': getattr(self, 'router_id_'+i),
                'cost': getattr(self, 'cost_'+i),
            })

    def pack(self):
        entries = len(self.entries)
        while self.num_entries < entries:
            self.format_entry()
            self.num_entries += 1

        values = [self.command, self.version, self.from_router_id]
        for entry in self.entries:
            values.append(entry['afi'])
            values.append(entry['router_id'])
            values.append(entry['cost'])

        return super().pack(values)

    def send(self, port, from_router_id):
        setattr(self, 'from_router_id', from_router_id)
        return super().send(port, self.pack())