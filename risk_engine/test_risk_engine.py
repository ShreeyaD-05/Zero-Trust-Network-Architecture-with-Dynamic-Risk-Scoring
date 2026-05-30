#!/usr/bin/env python3
"""
Test script for Zero Trust Risk Engine
Demonstrates preprocessing layer and API usage
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000/predict"
TIMEOUT = 10

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_result(title: str, result: Dict[str, Any]):
    """Print formatted results."""
    print(f"{Colors.BOLD}{Colors.CYAN}{title}{Colors.ENDC}")
    print(json.dumps(result, indent=2))
    print()

def get_risk_color(risk_level: str) -> str:
    """Get color based on risk level."""
    colors = {
        "LOW": Colors.GREEN,
        "MEDIUM": Colors.YELLOW,
        "HIGH": Colors.YELLOW,
        "CRITICAL": Colors.RED
    }
    return colors.get(risk_level, Colors.ENDC)

def print_risk_score(result: Dict[str, Any]):
    """Print risk score with color coding."""
    mlp_score = result.get("mlp_score", 0)
    risk_score, risk_level = result.get("risk_score", [0, "UNKNOWN"])
    
    color = get_risk_color(risk_level)
    print(f"{Colors.BOLD}Risk Assessment:{Colors.ENDC}")
    print(f"  Model Score:  {mlp_score:.4f} ({mlp_score*100:.2f}%)")
    print(f"  Risk Score:   {color}{risk_score}/100 - {risk_level}{Colors.ENDC}")
    print()

def test_case(name: str, flow_data: Dict[str, Any], description: str = ""):
    """Run a single test case."""
    print_header(f"Test: {name}")
    if description:
        print(f"{Colors.CYAN}Description:{Colors.ENDC} {description}\n")
    
    print(f"{Colors.CYAN}Input Data:{Colors.ENDC}")
    print(json.dumps(flow_data, indent=2))
    print()
    
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=flow_data, timeout=TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Time: {elapsed:.3f}s\n")
            print_risk_score(result)
            
            # Show derived features
            if "derived_features" in result:
                print(f"{Colors.CYAN}Key Derived Features:{Colors.ENDC}")
                features = result["derived_features"]
                for key in ["dur", "rate", "sload", "dload", "sjit", "djit"]:
                    if key in features:
                        print(f"  {key}: {features[key]:.4f}")
            print()
        else:
            print(f"{Colors.RED}Error: {response.status_code}{Colors.ENDC}")
            print(response.text)
            print()
    except requests.exceptions.ConnectionError:
        print(f"{Colors.RED}ERROR: Could not connect to API at {API_URL}{Colors.ENDC}")
        print("Make sure the server is running: uvicorn app.main:app --reload\n")
    except Exception as e:
        print(f"{Colors.RED}ERROR: {str(e)}{Colors.ENDC}\n")

def main():
    """Run all test cases."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}Zero Trust Risk Engine - Test Suite{Colors.ENDC}\n")
    print(f"API Endpoint: {API_URL}")
    print(f"Timeout: {TIMEOUT}s\n")
    
    # Test Case 1: Normal HTTP Traffic
    test_case(
        "Normal HTTP Traffic",
        {
            "protocol": "tcp",
            "service": "http",
            "state": "SF",
            "attack_cat": "Normal",
            "src_bytes": 800,
            "dst_bytes": 600,
            "src_packets": 6,
            "dst_packets": 5,
            "duration": 0.8,
            "src_loss": 0,
            "dst_loss": 0
        },
        "Expected: LOW risk - Normal web traffic"
    )
    
    # Test Case 2: Potential DDoS/DoS Attack
    test_case(
        "Potential DDoS Attack",
        {
            "protocol": "tcp",
            "service": "http",
            "state": "SYN",
            "attack_cat": "DoS",
            "src_bytes": 8000,
            "dst_bytes": 2500,
            "src_packets": 800,
            "dst_packets": 205,
            "duration": 0.2,
            "src_loss": 5,
            "dst_loss": 3
        },
        "Expected: CRITICAL risk - High packet rate, many SYN, connection loss"
    )
    
    # Test Case 3: SSH Connection with Suspicious Activity
    test_case(
        "SSH Reconnaissance Activity",
        {
            "protocol": "tcp",
            "service": "ssh",
            "state": "SYN",
            "attack_cat": "Reconnaissance",
            "src_bytes": 15000,
            "dst_bytes": 500,
            "src_packets": 200,
            "dst_packets": 5,
            "duration": 0.05,
            "src_loss": 10,
            "dst_loss": 8
        },
        "Expected: MEDIUM-HIGH risk - Excessive src packets, high loss, SSH"
    )
    
    # Test Case 4: FTP Login Attempt
    test_case(
        "FTP Connection (Low Activity)",
        {
            "protocol": "tcp",
            "service": "ftp",
            "state": "SF",
            "attack_cat": "Normal",
            "src_bytes": 200,
            "dst_bytes": 1500,
            "src_packets": 3,
            "dst_packets": 4,
            "duration": 2.5,
            "src_loss": 0,
            "dst_loss": 0,
            "flags": "LOGIN"
        },
        "Expected: LOW risk - Normal FTP login attempt"
    )
    
    # Test Case 5: Backdoor/Exploitation
    test_case(
        "Potential Backdoor Activity",
        {
            "protocol": "tcp",
            "service": "http",
            "state": "FIN",
            "attack_cat": "Backdoor",
            "src_bytes": 5000,
            "dst_bytes": 3000,
            "src_packets": 100,
            "dst_packets": 95,
            "duration": 0.15,
            "src_loss": 2,
            "dst_loss": 1
        },
        "Expected: HIGH risk - Backdoor category, significant data transfer"
    )
    
    # Test Case 6: DNS Query
    test_case(
        "DNS Query",
        {
            "protocol": "udp",
            "service": "dns",
            "state": "SF",
            "attack_cat": "Normal",
            "src_bytes": 50,
            "dst_bytes": 150,
            "src_packets": 1,
            "dst_packets": 1,
            "duration": 0.01,
            "src_loss": 0,
            "dst_loss": 0
        },
        "Expected: LOW risk - Normal DNS resolution"
    )
    
    # Test Case 7: Full-Featured Input (Direct Model Format)
    test_case(
        "Full Feature Vector Input",
        {
            "proto": "tcp",
            "service": "http",
            "state": "FIN",
            "attack_cat": "Exploits",
            "sbytes": 800,
            "dbytes": 600,
            "stcpb": 20000,
            "dtcpb": 18000,
            "response_body_len": 400,
            "sloss": 0,
            "dloss": 0,
            "spkts": 6,
            "dpkts": 5,
            "swin": 255,
            "dwin": 255,
            "dmean": 150,
            "ct_src_dport_ltm": 1,
            "ct_dst_sport_ltm": 1,
            "trans_depth": 0,
            "ct_ftp_cmd": 0,
            "ct_flw_http_mthd": 1,
            "is_ftp_login": 0,
            "is_sm_ips_ports": 0,
            "dur": 0.8,
            "rate": 200,
            "sload": 900,
            "dload": 700,
            "sinpkt": 0.15,
            "dinpkt": 0.18,
            "sjit": 0.01,
            "djit": 0.02,
            "tcprtt": 0.03,
            "synack": 0.01,
            "ackdat": 0.02
        },
        "Expected: Test data from Data-test.txt - Direct model format"
    )
    
    print_header("Test Suite Complete")
    print(f"{Colors.GREEN}✓ All tests executed{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
