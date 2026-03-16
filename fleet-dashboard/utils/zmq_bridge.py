"""
ZeroMQ High-Speed Bridge - Socket Communication Utility.
Replaces slow JSON file polling with nanosecond IPC.
"""

try:
    import zmq
    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False
import time

# ZMQ Port for the Fleet Bridge
BRIDGE_PORT = 5555

class CommandPublisher:
    """Streamlit side: Publishes commands (Surge, Pause, etc.)"""
    def __init__(self):
        if not ZMQ_AVAILABLE:
            self.socket = None
            return
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        # Publisher connects to avoid Streamlit Address In Use bugs on hot reload
        self.socket.connect(f"tcp://localhost:{BRIDGE_PORT}")
        
    def send_command(self, cmd_type):
        """Broadcast command to all tactical displays."""
        if not self.socket:
            return
        payload = f"{cmd_type}:{time.time()}"
        self.socket.send_string(payload)

class CommandSubscriber:
    """Pygame side: Subscribes to commands from Streamlit."""
    def __init__(self):
        if not ZMQ_AVAILABLE:
            self.socket = None
            return
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        # Subscriber binds so the persistent Pygame window owns the port
        self.socket.bind(f"tcp://*:{BRIDGE_PORT}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all
        
        # Make the socket non-blocking
        self.socket.setsockopt(zmq.RCVTIMEO, 0)
        
    def check_for_command(self):
        """Non-blocking check for new messages."""
        if not self.socket:
            return None, None
        try:
            msg = self.socket.recv_string()
            cmd, timestamp = msg.split(':')
            return cmd, float(timestamp)
        except (Exception, NameError):
            return None, None
