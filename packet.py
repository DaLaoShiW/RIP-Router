import struct
from socket import *


class Packet:

    def __init__(self):
        self.len_bytes = 0
        self.byte_format = "" # A format string used by struct to pack and unpack values
        self.field_names = [] # The names of fields in this packet's format

    def __len__(self):
        return self.len_bytes

    def __str__(self):
        out = ""
        for field in self.field_names:
            out += field+": " + str(getattr(self, field)) + "\n"
        return out

    def unpack(self, byte_data):
        """ Unpack byte values and set respective attributes on this packet """
        if len(self.field_names) == 0:
            raise Exception("Missing packet format!")

        values = struct.unpack(self.byte_format, byte_data)
        for i in range(0, len(values)):
            setattr(self, self.field_names[i], values[i])

    def pack(self, values):
        """ Take a list of values and generate a byte string according to the packet format """
        if len(self.field_names) == 0:
            raise Exception("Missing packet format!")

        return struct.pack(self.byte_format, *values)

    def send(self, port, pack):
        """ Send a packed version of this packet to a port on localhost """
        a_socket = socket(AF_INET, SOCK_DGRAM)
        a_socket.sendto(pack, ("localhost", port))

    def format_field(self, _format, len_bytes, name=None):
        """ Add a field to the packet format """
        self.byte_format += _format
        if name:
            self.field_names.append(str(name))
            self.len_bytes += len_bytes

    def format_padding(self, len_bytes):
        """ Add len_bytes of padding to the packet format """
        self.format_field(str(len_bytes) + "x", len_bytes)

    def format_int8(self, name):
        """ Add a signed char field (8-bit) to the packet format """
        self.format_field("b", 1, name)

    def format_int16(self, name):
        """ Add a short field (16-bit) to the packet format """
        self.format_field("h", 2, name)

    def format_int32(self, name):
        """ Add an int field (32-bit) to the packet format """
        self.format_field("i", 4, name)


class RIPPacket(Packet):

    def __init__(self, byte_data=None):
        """ Initialize RIP packet header fields, optionally unpack byte_data """
        super().__init__()
        self.from_router_id = None
        self.entries = []
        self.num_entries = 0
        self.entry_size = 20 # Size in bytes of a RIP entry
        self.header_size = 4 # Size in bytes of RIP header
        self.command = 2 # RIP Command: 2 is 'response'
        self.version = 2 # RIP version

        # Add header fields to packet format
        self.format_int8("command")
        self.format_int8("version")
        self.format_int16("from_router_id")

        if byte_data:
            self.unpack(byte_data)

    def add_entry(self, router_id, cost):
        """ Add a RIP entry to this packet """
        self.entries.append({
            "afi": 2, # AF_INET
            "router_id": router_id,
            "cost": cost,
        })

    def format_entry(self):
        """ Add a RIP entry to the packet format """
        self.format_int16("afi_" + str(self.num_entries))
        self.format_padding(2)
        self.format_int32("router_id_" + str(self.num_entries))
        self.format_padding(8)
        self.format_int32("cost_" + str(self.num_entries))

    def unpack(self, byte_data):
        """ Unpack byte_data to populate this RIP packet """

        # Calculate number of expected entries in this byte_data
        entries = (len(byte_data) - self.header_size) // self.entry_size

        # Add entries to the packet format for unpacking
        while self.num_entries < entries:
            self.format_entry()
            self.num_entries += 1

        # Do the unpacking!
        super().unpack(byte_data)

        # Populate self.entries from unpacked entry values
        for i in range(self.num_entries):
            i = str(i)
            self.entries.append({
                "afi": getattr(self, "afi_" + i),
                "router_id": getattr(self, "router_id_" + i),
                "cost": getattr(self, "cost_" + i),
            })

    def pack(self, values=False):
        """ Format RIP packet values and pack into byte string """

        # Add entries to packet format
        entries = len(self.entries)
        while self.num_entries < entries:
            self.format_entry()
            self.num_entries += 1

        # Add header values if not explicitly set
        if not values:
            values = [self.command, self.version, self.from_router_id]

        # Append RIP entry values to list for packing
        for entry in self.entries:
            values.append(entry["afi"])
            values.append(entry["router_id"])
            values.append(entry["cost"])

        # Do the packing!
        return super().pack(values)

    def send(self, port, from_router_id):
        """ Send the RIP packet from this router_id to localhost:port """
        setattr(self, "from_router_id", from_router_id)
        return super().send(port, self.pack())
