from database import LocalDatabase
from datetime import datetime
from packet import PacketParser, ServerAckPacket
import selectors    # non-blocking setup
import signal       # safely handle interrupts
import socket       # tcp connections

GREY = '\033[90m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[95m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'


class Device():
    """ Base class for connected components.

    All components need a write buffer to store packets addressed to them.
    After their details become known, this is converted to a more specific
    class for the component type.

    At the moment, there are only security devices. This design allows for
    other types of dedicated sensors such as weather and plant monitoring.
    """

    def __init__(self):
        self.write_buf = b''


class ValidatedDevice(Device):
    def __init__(self, id, info):
        super(ValidatedDevice, self).__init__()
        self.id = id
        self.info = info


class BaseStation():
    """ Basic IoT TCP server """
    DEFAULT_NAME = "RaspberryPi-Server"
    DEFAULT_DB = "smarthome.db"
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, server_port, server_name=DEFAULT_NAME, db=DEFAULT_DB):
        self.server_name = server_name
        self.host_name = socket.gethostname()
        self.ip_addr = socket.gethostbyname(self.host_name)
        self.sel = selectors.DefaultSelector()
        self.devices = {}
        self.initial_dev_id = 10
        self.port = server_port
        self.shutdown = False
        self.message_handlers = {
            0x00: self.handle_client_registration,
            # this is unused unless multiple servers are present
            0x01: self.handle_server_ack,
            0x02: self.handle_client_status_update
        }
        self.db = LocalDatabase(db)

        # handle resource cleanup on user interrupt
        signal.signal(signal.SIGINT, self.sighandler)

    def sighandler(self, signum, frame):
        self.print_info(RED + "Shutting down server..." + END)
        self.cleanup()
        exit(0)

    def run(self):
        self.print_info(BLUE + "Launching server..." + END)
        self.setup_server_socket()

        # Begin listening for client messages
        self.check_for_messages()

    def print_info(self, msg, alert=0):
        BaseStation.print_event(self.server_name, msg, alert)

    @staticmethod
    def print_event(host, msg, alert=0):
        color = END
        if host == BaseStation.DEFAULT_NAME:
            color = GREY
        else:
            color = CYAN

        priority = END
        if alert == 1:
            priority = GREEN
        elif alert == 2:
            priority = YELLOW
        elif alert == 3:
            priority = RED

        display_name = f"[{color}{host.upper():^20}{END}]"
        display_time = f"{datetime.now().strftime(BaseStation.TIME_FORMAT)}"
        display_msg = f"{priority}{msg}{END}"
        print(f"{display_name}\t{display_time}\t{display_msg}")

    def setup_server_socket(self):
        self.my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_sock.bind(('', self.port))
        self.my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        my_info = ValidatedDevice(99, "RaspberryPi Base Station")
        self.sel.register(self.my_sock, selectors.EVENT_READ, my_info)
        self.my_sock.listen()
        self.my_sock.setblocking(False)

    def check_for_messages(self):
        self.print_info(BLUE + f"Listening for new connections on port \
            {self.port}" + END)
        while not self.shutdown:
            devices_rdy = self.sel.select(0.1)
            for device, event_mask in devices_rdy:
                if device.fileobj is self.my_sock:
                    self.accept_new_connection(device)
                else:
                    self.handle_device_events(device, event_mask)

        self.cleanup()

    def cleanup(self):
        self.my_sock.close()
        devs = list(self.sel._fd_to_key.values())
        for id in devs:
            client = id.fileobj
            client.close
            self.sel.unregister(client)

        self.sel.close()
        self.db.shutdown()

    def accept_new_connection(self, device):
        dev_sock, dev_addr = device.fileobj.accept()
        dev_sock.setblocking(False)
        dev_data = Device()
        self.sel.register(dev_sock,
                          selectors.EVENT_READ | selectors.EVENT_WRITE,
                          dev_data)

    def handle_device_events(self, device, event_mask):
        sock = device.fileobj
        device_obj = device.data
        if event_mask & selectors.EVENT_READ:
            try:
                rcv_data = sock.recv(2048)
                if rcv_data:
                    self.handle_messages(device, rcv_data)
                elif not device_obj.write_buf:
                    self.sel.unregister(sock)
                    sock.close()
            except Exception as e:
                print(e)

        if event_mask & selectors.EVENT_WRITE:
            if device_obj.write_buf:
                try:
                    sent = sock.send(device_obj.write_buf)
                    device_obj.write_buf = device_obj.write_buf[sent:]
                except Exception as e:
                    print(e)

    def handle_messages(self, device, payload):
        messages = PacketParser.parse(payload)

        for msg in messages:
            if msg.pkt_type in self.message_handlers:
                self.print_info(f"Received packet from device \
                    [{msg.source_id}]")
                self.message_handlers[msg.pkt_type](device, msg)
            else:
                raise Exception("Invalid message: " + msg)

    #################################################################
    #                                                               #
    #                       Message Handlers                        #
    #                                                               #
    #################################################################
    def handle_client_registration(self, device, msg):
        # duplicate registration from potential power failure
        if msg.source_id != 0 or msg.source_id in self.devices:
            self.print_info(f"Duplicate registration from device \
                            {msg.source_id}")
            self.send_server_ack_packet(device, msg.source_id)
            return

        REGISTRATION_PRIORITY_LVL = 1
        BaseStation.print_event(msg.info, "Request to join the network")
        assigned_id = self.initial_dev_id
        self.initial_dev_id += 1
        client_data_obj = ValidatedDevice(assigned_id, msg.info)
        self.devices[assigned_id] = client_data_obj
        self.sel.modify(device.fileobj,
                        selectors.EVENT_READ | selectors.EVENT_WRITE,
                        client_data_obj)
        self.print_info(f"Welcome to the network, [{msg.info}]!",
                        alert=REGISTRATION_PRIORITY_LVL)
        self.print_info(f"assigned id #{assigned_id} to device [{msg.info}]",
                        alert=REGISTRATION_PRIORITY_LVL)
        time = datetime.now().strftime(BaseStation.TIME_FORMAT)
        self.db.insert_event(
            time,
            assigned_id,
            msg.info,
            REGISTRATION_PRIORITY_LVL,
            "Joined the network")
        self.send_server_ack_packet(device, assigned_id)

    def handle_client_status_update(self, device, msg):
        BaseStation.print_event(self.devices[device.data.id].info, msg.content,
                                msg.priority_lvl)
        time = datetime.now().strftime(BaseStation.TIME_FORMAT)
        self.db.insert_event(
            time,
            device.data.id,
            self.devices[device.data.id].info,
            msg.priority_lvl,
            msg.content)
        pass

    def handle_client_img_attached(self, device, msg):
        pass

    def handle_server_ack(self, msg):
        pass

    def send_msg_to_host(self, dest_id, msg):
        if dest_id in self.devices:
            self.print_info(f"Sending message to host #{dest_id} \
                [{self.devices[dest_id].info}]")
            self.devices[dest_id].write_buf += msg

    def send_server_ack_packet(self, device, assigned_id):
        pkt = ServerAckPacket.to_bytes(assigned_id)
        self.send_msg_to_host(assigned_id, pkt)
