# app/preprocess.py
"""
Feature Preprocessing Layer
Takes minimal user input and derives all required features for the risk engine model.
"""

import numpy as np
from typing import Dict, Any


class FeatureDeriver:
    """
    Derives complex features from basic network flow information.
    
    Primary inputs:
    - protocol: TCP/UDP
    - service: HTTP, HTTPS, SSH, FTP, DNS, etc.
    - src_bytes, dst_bytes: Data transferred in each direction
    - src_packets, dst_packets: Number of packets in each direction
    - duration: Connection duration in seconds
    - attack_cat: Normal or attack category
    
    Derived features:
    - Window sizes, packet rates, loads, jitter, latencies
    """
    
    # Service categorization for enhanced context
    SERVICE_MAPPING = {
        "http": "http",
        "https": "https",
        "ssh": "ssh",
        "ftp": "ftp",
        "smtp": "smtp",
        "dns": "dns",
        "telnet": "telnet",
        "irc": "irc",
        "P2P": "P2P",
        "unknown": "unknown"
    }
    
    STATE_MAPPING = {
        "FIN": "FIN",
        "SYN": "SYN",
        "RST": "RST",
        "RSTO": "RSTO",
        "RSTR": "RSTR",
        "RSTOS0": "RSTOS0",
        "RSTRH": "RSTRH",
        "SH": "SH",
        "SHR": "SHR",
        "OTH": "OTH",
        "SF": "SF"
    }
    
    def __init__(self):
        """Initialize the feature deriver with default scaling parameters."""
        pass
    
    def derive_features(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Take user-provided basic information and derive all model features.
        
        Args:
            user_input: Dictionary with keys:
                - protocol: "tcp" or "udp"
                - service: Service name (http, ssh, etc.)
                - state: Connection state (SYN, FIN, SF, etc.)
                - src_bytes, dst_bytes: Bytes transferred
                - src_packets, dst_packets: Packet counts
                - duration: Connection duration in seconds
                - attack_cat: "Normal" or attack type
                - [optional] src_loss, dst_loss: Packet loss counts
                - [optional] flags: Connection flags (for FTP, HTTP, etc.)
        
        Returns:
            Dictionary with all 45 required features formatted for model input
        """
        
        # Extract and validate primary inputs
        protocol = user_input.get("protocol", "tcp").lower()
        service = user_input.get("service", "http").lower()
        state = user_input.get("state", "SF").upper()
        attack_cat = user_input.get("attack_cat", "Normal")
        
        src_bytes = float(user_input.get("src_bytes", 0))
        dst_bytes = float(user_input.get("dst_bytes", 0))
        src_packets = float(user_input.get("src_packets", 1))
        dst_packets = float(user_input.get("dst_packets", 1))
        duration = float(user_input.get("duration", 0.1))
        
        src_loss = float(user_input.get("src_loss", 0))
        dst_loss = float(user_input.get("dst_loss", 0))
        
        # Avoid division by zero
        duration = max(duration, 0.01)
        src_packets = max(src_packets, 1)
        dst_packets = max(dst_packets, 1)
        
        # ==================== ROBUST FEATURES ====================
        # These are byte/data related features that need robust scaling
        sbytes = src_bytes  # Source bytes
        dbytes = dst_bytes  # Destination bytes
        
        # TCP Buffer estimates (based on typical window sizes and data flow)
        stcpb = self._estimate_tcp_buffer(src_bytes, src_packets)  # Src TCP buffer
        dtcpb = self._estimate_tcp_buffer(dst_bytes, dst_packets)  # Dst TCP buffer
        
        # Response body length (estimate from dst bytes for HTTP-like services)
        response_body_len = self._estimate_response_length(service, dst_bytes)
        
        # Packet loss
        sloss = src_loss
        dloss = dst_loss
        
        robust_features = {
            "sbytes": sbytes,
            "dbytes": dbytes,
            "stcpb": stcpb,
            "dtcpb": dtcpb,
            "response_body_len": response_body_len,
            "sloss": sloss,
            "dloss": dloss
        }
        
        # ==================== STANDARD FEATURES ====================
        # Packet counts and connection state features
        spkts = src_packets
        dpkts = dst_packets
        
        # Window sizes (based on packet counts and loss)
        swin = self._estimate_window_size(src_packets, sloss)
        dwin = self._estimate_window_size(dst_packets, dloss)
        
        # Data mean per packet
        dmean = (src_bytes + dst_bytes) / (src_packets + dst_packets) if (src_packets + dst_packets) > 0 else 0
        
        # Connection tuple features (simplified based on service)
        ct_src_dport_ltm = self._compute_src_dport_count(service)
        ct_dst_sport_ltm = self._compute_dst_sport_count(service)
        
        # Transaction depth (protocol layers)
        trans_depth = 1 if protocol == "tcp" else 0
        
        # Protocol-specific counts
        ct_ftp_cmd = 1 if service == "ftp" and "CMD" in str(user_input.get("flags", "")) else 0
        ct_flw_http_mthd = 1 if service == "http" or service == "https" else 0
        
        standard_features = {
            "spkts": spkts,
            "dpkts": dpkts,
            "swin": swin,
            "dwin": dwin,
            "dmean": dmean,
            "ct_src_dport_ltm": ct_src_dport_ltm,
            "ct_dst_sport_ltm": ct_dst_sport_ltm,
            "trans_depth": trans_depth,
            "ct_ftp_cmd": ct_ftp_cmd,
            "ct_flw_http_mthd": ct_flw_http_mthd
        }
        
        # ==================== BINARY FEATURES ====================
        is_ftp_login = 1 if service == "ftp" and "LOGIN" in str(user_input.get("flags", "")) else 0
        is_sm_ips_ports = 1 if self._is_suspicious_port(user_input.get("src_port", 0), 
                                                        user_input.get("dst_port", 0)) else 0
        
        binary_features = {
            "is_ftp_login": is_ftp_login,
            "is_sm_ips_ports": is_sm_ips_ports
        }
        
        # ==================== FLOW FEATURES ====================
        # Traffic rate and timing features
        rate = (src_bytes + dst_bytes) / duration if duration > 0 else 0
        sload = src_bytes / duration if duration > 0 else 0  # Source load
        dload = dst_bytes / duration if duration > 0 else 0  # Dest load
        
        # Inter-packet times (derived from packet count and duration)
        sinpkt = duration / src_packets if src_packets > 0 else duration
        dinpkt = duration / dst_packets if dst_packets > 0 else duration
        
        # Jitter estimates (packet timing variance, estimated from loss)
        sjit = self._estimate_jitter(src_packets, sloss)
        djit = self._estimate_jitter(dst_packets, dloss)
        
        # RTT and ACK timing (based on state and protocol)
        tcprtt = self._estimate_rtt(protocol, state)
        synack = self._estimate_synack_time(state)
        ackdat = self._estimate_ack_time(state)
        
        flow_features = {
            "dur": duration,
            "rate": rate,
            "sload": sload,
            "dload": dload,
            "sinpkt": sinpkt,
            "dinpkt": dinpkt,
            "sjit": sjit,
            "djit": djit,
            "tcprtt": tcprtt,
            "synack": synack,
            "ackdat": ackdat
        }
        
        # ==================== CATEGORICAL FEATURES ====================
        categorical_features = {
            "proto": protocol,
            "service": service,
            "state": state,
            "attack_cat": attack_cat
        }
        
        # Combine all features
        all_features = {
            **categorical_features,
            **robust_features,
            **standard_features,
            **binary_features,
            **flow_features
        }
        
        return all_features
    
    def _estimate_tcp_buffer(self, bytes_val: float, packets: float) -> float:
        """Estimate TCP buffer size based on bytes and packet count."""
        if packets == 0:
            return 0
        avg_pkt_size = bytes_val / packets
        # Typical TCP window: 65535 bytes max, but varies
        buffer = max(min(avg_pkt_size * packets * 2, 1000000), avg_pkt_size * 10)
        return buffer
    
    def _estimate_response_length(self, service: str, dst_bytes: float) -> float:
        """Estimate response body length based on service type."""
        if service in ["http", "https"]:
            # HTTP responses often include headers
            return max(dst_bytes - 500, dst_bytes * 0.8)  # Subtract approx headers
        elif service == "ssh":
            return max(dst_bytes - 100, dst_bytes * 0.9)
        elif service == "dns":
            return dst_bytes  # DNS responses are mostly data
        return dst_bytes
    
    def _estimate_window_size(self, packets: float, loss: float) -> float:
        """Estimate TCP window size based on packets and loss."""
        base_window = max(128, min(packets * 32, 255))  # 128-255 typical range
        # Reduce window if there's loss (flow control)
        if loss > 0:
            base_window = max(64, base_window * (1 - loss / 100))
        return base_window
    
    def _compute_src_dport_count(self, service: str) -> float:
        """Estimate count of source connections to destination port."""
        # Services that often have multiple connections
        if service in ["http", "https"]:
            return 3  # Typical HTTP might have multiple connections
        elif service == "ftp":
            return 2  # FTP control + data
        elif service == "ssh":
            return 1  # SSH typically single connection
        return 1
    
    def _compute_dst_sport_count(self, service: str) -> float:
        """Estimate count of destination source port connections."""
        if service in ["http", "https"]:
            return 2
        elif service == "dns":
            return 5  # DNS might have multiple queries
        return 1
    
    def _is_suspicious_port(self, src_port: int, dst_port: int) -> int:
        """Detect if ports are suspicious (same IPs/ports)."""
        if src_port == dst_port and src_port > 0:
            return 1
        return 0
    
    def _estimate_jitter(self, packets: float, loss: float) -> float:
        """Estimate jitter (timing variance) based on packets and loss."""
        base_jitter = 0.001 + (1 / max(packets, 1)) * 0.01
        jitter_from_loss = loss * 0.001 if loss > 0 else 0
        return min(base_jitter + jitter_from_loss, 0.1)
    
    def _estimate_rtt(self, protocol: str, state: str) -> float:
        """Estimate RTT based on protocol and state."""
        if protocol == "udp":
            return 0.001
        # TCP RTT varies by state
        rtt_map = {
            "SYN": 0.05,
            "SF": 0.02,
            "FIN": 0.03,
            "RST": 0.01,
        }
        return rtt_map.get(state, 0.015)
    
    def _estimate_synack_time(self, state: str) -> float:
        """Estimate SYN-ACK time based on connection state."""
        if state in ["SYN", "RSTO", "RSTR", "RSTOS0", "RSTRH"]:
            return 0.01
        return 0.005
    
    def _estimate_ack_time(self, state: str) -> float:
        """Estimate ACK timing based on connection state."""
        if state in ["SYN", "RSTOS0", "RSTRH"]:
            return 0.02
        elif state in ["FIN", "RST"]:
            return 0.01
        return 0.005


# Singleton instance
_deriver = None


def get_feature_deriver() -> FeatureDeriver:
    """Get or create the feature deriver singleton."""
    global _deriver
    if _deriver is None:
        _deriver = FeatureDeriver()
    return _deriver


def preprocess_user_input(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to preprocess user input.
    
    Takes basic user input and returns all derived features ready for the model.
    """
    deriver = get_feature_deriver()
    return deriver.derive_features(user_input)
