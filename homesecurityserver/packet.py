from abc import ABC
from struct import pack, unpack
from time import time


class Packet(ABC):
    pass


class ClientRegistrationPacket(Packet):
    def __init__(self, bytes_pkt):
        self.pkt_type = 0x00
        msg = unpack("!xIBI", bytes_pkt[:10])
        self.source_id = msg[0]     # always 0x00 because no ID assigned yet
        self.pkt_number = msg[1]    # unused
        self.info_length = msg[2]
        self.packet_length = 10 + self.info_length
        self.info = unpack("!{0}s".format(self.info_length),
                           bytes_pkt[10:self.packet_length])[0].decode()

    @staticmethod
    def to_bytes(source_id, battery_level, info):
        return pack("!BIBI{0}s".format(len(info)),
                    0x00,
                    source_id,
                    battery_level,
                    len(info),
                    info.encode())


class ServerAckPacket(Packet):
    def __init__(self, bytes_pkt):
        self.pkt_type = 0x01
        msg = unpack("!xBI", bytes_pkt)
        self.assigned_id = msg[0]   # non-zero is success
        self.current_time = msg[1]  # time in seconds, truncated decimal
        self.packet_length = 6

    @staticmethod
    def to_bytes(assigned_id):
        return pack("!BBI", 0x01, assigned_id, int(time()))


class StatusUpdatePacket(Packet):
    def __init__(self, bytes_pkt):
        self.pkt_type = 0x02
        msg = unpack("!xIBI", bytes_pkt[:10])
        self.source_id = msg[0]         # ignore content if this is zero
        self.priority_lvl = msg[1]      # priority of the event
        self.content_length = msg[2]    # event details or heartbeat
        self.packet_length = 10 + self.content_length
        self.content = unpack("!{0}s".format(self.content_length),
                              bytes_pkt[10:self.packet_length])[0].decode()

    @staticmethod
    def to_bytes(source_id, priority_lvl, content):
        return pack("!BIBI{0}s".format(len(content)),
                    0x02,
                    source_id,
                    priority_lvl,
                    len(content),
                    content.encode())


class ImagePacket(Packet):
    def __init__(self, bytes_pkt):
        pass

    @staticmethod
    def to_bytes(source_id, info):
        pass


class PacketParser():
    """Utility class for parsing packets."""

    @staticmethod
    def parse(bytes_pkt):
        payload = bytes_pkt
        messages = []
        while (len(payload) > 0):
            pkt = None
            code = payload[0]
            if code == 0x00:
                pkt = ClientRegistrationPacket(payload)
            elif code == 0x01:
                pkt = ServerAckPacket(payload)
            elif code == 0x02:
                pkt = StatusUpdatePacket(payload)
            elif code == 0x03:
                pkt = ImagePacket(payload)

            if pkt:
                messages.append(pkt)
                payload = payload[pkt.packet_length:]
            else:
                raise Exception("Unknown packet type")

        return messages
