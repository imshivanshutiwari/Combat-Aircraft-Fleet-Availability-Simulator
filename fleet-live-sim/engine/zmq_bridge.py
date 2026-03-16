"""
ZeroMQ High-Speed Bridge - Socket Communication Utility.
Replaces slow JSON file polling with nanosecond IPC.
"""

import zmq

# ZMQ Port for the Fleet Bridge
BRIDGE_PORT = 5555

class CommandSubscriber:
    """Pygame side: Subscribes to commands from Streamlit."""
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://localhost:{BRIDGE_PORT}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all
        
        # Make the socket non-blocking
        self.socket.setsockopt(zmq.RCVTIMEO, 0)
        
    def check_for_command(self):
        """Non-blocking check for new messages."""
        try:
            msg = self.socket.recv_string()
            cmd, timestamp = msg.split(':')
            return cmd, float(timestamp)
        except zmq.Again:
            return None, None
        except Exception:
            return None, None
