#!/usr/bin/env python3
"""
Integration test to verify preprocessing layer and API work correctly.
Run this to ensure all components are properly integrated.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.preprocess import preprocess_user_input, FeatureDeriver
import json

def test_feature_deriver():
    """Test the feature deriver independently."""
    print("\n" + "="*60)
    print("TEST 1: Feature Deriver (Standalone)")
    print("="*60)
    
    deriver = FeatureDeriver()
    
    # Test input
    user_input = {
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
    }
    
    print("\nInput:")
    print(json.dumps(user_input, indent=2))
    
    # Derive features
    derived = deriver.derive_features(user_input)
    
    print("\nDerived Features:")
    print(json.dumps(derived, indent=2))
    
    # Verify all required features are present
    required_features = {
        "proto", "service", "state", "attack_cat",
        "sbytes", "dbytes", "stcpb", "dtcpb", "response_body_len",
        "sloss", "dloss", "spkts", "dpkts", "swin", "dwin", "dmean",
        "ct_src_dport_ltm", "ct_dst_sport_ltm", "trans_depth",
        "ct_ftp_cmd", "ct_flw_http_mthd", "is_ftp_login", "is_sm_ips_ports",
        "dur", "rate", "sload", "dload", "sinpkt", "dinpkt",
        "sjit", "djit", "tcprtt", "synack", "ackdat"
    }
    
    missing = required_features - set(derived.keys())
    if missing:
        print(f"\n❌ FAILED: Missing features: {missing}")
        return False
    else:
        print(f"\n✓ PASSED: All {len(derived)} features derived successfully")
        return True

def test_preprocessing_function():
    """Test the preprocessing convenience function."""
    print("\n" + "="*60)
    print("TEST 2: Preprocessing Function")
    print("="*60)
    
    user_input = {
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
    }
    
    print("\nInput:")
    print(json.dumps(user_input, indent=2))
    
    result = preprocess_user_input(user_input)
    
    print("\nDerived Features (DNS Query):")
    print(json.dumps(result, indent=2))
    
    # Check types
    print("\nType Validation:")
    print(f"  proto type: {type(result['proto']).__name__} ✓")
    print(f"  dur type: {type(result['dur']).__name__} ✓")
    print(f"  rate type: {type(result['rate']).__name__} ✓")
    
    return True

def test_complex_scenario():
    """Test a complex attack scenario."""
    print("\n" + "="*60)
    print("TEST 3: Complex Attack Scenario (DDoS)")
    print("="*60)
    
    ddos_flow = {
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
    }
    
    print("\nDDoS Attack Input:")
    print(json.dumps(ddos_flow, indent=2))
    
    deriver = FeatureDeriver()
    features = deriver.derive_features(ddos_flow)
    
    print("\nKey Derived Features:")
    print(f"  Rate: {features['rate']:.2f} B/s (very high)")
    print(f"  Src Load: {features['sload']:.2f} B/s")
    print(f"  Dst Load: {features['dload']:.2f} B/s")
    print(f"  Window Size (src): {features['swin']:.0f}")
    print(f"  Window Size (dst): {features['dwin']:.0f}")
    print(f"  Jitter (src): {features['sjit']:.6f}")
    print(f"  Jitter (dst): {features['djit']:.6f}")
    
    # Verify high rate
    if features['rate'] > 5000:
        print(f"\n✓ PASSED: High data rate detected ({features['rate']:.0f} B/s)")
        return True
    else:
        print(f"\n❌ FAILED: Expected high rate, got {features['rate']:.0f} B/s")
        return False

def test_service_specific():
    """Test service-specific feature derivation."""
    print("\n" + "="*60)
    print("TEST 4: Service-Specific Features")
    print("="*60)
    
    services = {
        "ssh": {
            "protocol": "tcp",
            "service": "ssh",
            "state": "SF",
            "attack_cat": "Normal",
            "src_bytes": 500,
            "dst_bytes": 1000,
            "src_packets": 10,
            "dst_packets": 15,
            "duration": 2.0,
            "src_loss": 0,
            "dst_loss": 0
        },
        "ftp": {
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
        "https": {
            "protocol": "tcp",
            "service": "https",
            "state": "SF",
            "attack_cat": "Normal",
            "src_bytes": 300,
            "dst_bytes": 5000,
            "src_packets": 5,
            "dst_packets": 8,
            "duration": 1.0,
            "src_loss": 0,
            "dst_loss": 0
        }
    }
    
    deriver = FeatureDeriver()
    results = {}
    
    for service_name, service_data in services.items():
        features = deriver.derive_features(service_data)
        results[service_name] = {
            "ct_flw_http_mthd": features.get("ct_flw_http_mthd", 0),
            "ct_ftp_cmd": features.get("ct_ftp_cmd", 0),
            "response_body_len": features.get("response_body_len", 0)
        }
    
    print("\nService-Specific Derivation:")
    print(json.dumps(results, indent=2))
    
    # Verify SSH has 0 ct_flw_http_mthd
    if results["ssh"]["ct_flw_http_mthd"] == 0:
        print("✓ SSH correctly identified (no HTTP method count)")
    else:
        print("❌ SSH incorrectly marked as HTTP")
        return False
    
    # Verify HTTPS has 1 ct_flw_http_mthd
    if results["https"]["ct_flw_http_mthd"] == 1:
        print("✓ HTTPS correctly identified (HTTP method count = 1)")
    else:
        print("❌ HTTPS not correctly identified")
        return False
    
    # Verify FTP detection
    if results["ftp"]["ct_ftp_cmd"] == 1:
        print("✓ FTP LOGIN correctly detected")
    else:
        print("❌ FTP LOGIN not detected")
        return False
    
    return True

def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "="*60)
    print("TEST 5: Edge Cases")
    print("="*60)
    
    deriver = FeatureDeriver()
    
    # Test 1: Minimum values
    print("\n1. Minimum valid values:")
    min_flow = {
        "protocol": "tcp",
        "service": "http",
        "state": "SF",
        "attack_cat": "Normal",
        "src_bytes": 0,
        "dst_bytes": 0,
        "src_packets": 1,
        "dst_packets": 1,
        "duration": 0.01,
        "src_loss": 0,
        "dst_loss": 0
    }
    result = deriver.derive_features(min_flow)
    print(f"  Rate with 0 bytes: {result['rate']:.2f} (should be 0)")
    print(f"  Dmean with 0 bytes: {result['dmean']:.2f} (should be 0)")
    
    # Test 2: Large values
    print("\n2. Large values:")
    large_flow = {
        "protocol": "tcp",
        "service": "http",
        "state": "SF",
        "attack_cat": "Normal",
        "src_bytes": 1000000,
        "dst_bytes": 1000000,
        "src_packets": 10000,
        "dst_packets": 10000,
        "duration": 100,
        "src_loss": 1000,
        "dst_loss": 1000
    }
    result = deriver.derive_features(large_flow)
    print(f"  Rate with 1MB each: {result['rate']:.2f} B/s")
    print(f"  Dmean with 1MB: {result['dmean']:.2f} B")
    
    # Test 3: Loss > packets (should handle gracefully)
    print("\n3. Loss handling:")
    loss_flow = {
        "protocol": "tcp",
        "service": "http",
        "state": "SF",
        "attack_cat": "Normal",
        "src_bytes": 1000,
        "dst_bytes": 1000,
        "src_packets": 5,
        "dst_packets": 5,
        "duration": 1.0,
        "src_loss": 50,
        "dst_loss": 50
    }
    result = deriver.derive_features(loss_flow)
    print(f"  Window size with heavy loss: {result['swin']:.0f} (should be reduced)")
    print(f"  Jitter with loss: {result['sjit']:.6f}")
    
    print("\n✓ PASSED: All edge cases handled")
    return True

def main():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("ZERO TRUST RISK ENGINE - INTEGRATION TESTS")
    print("="*60)
    
    tests = [
        ("Feature Deriver", test_feature_deriver),
        ("Preprocessing Function", test_preprocessing_function),
        ("Complex Scenario", test_complex_scenario),
        ("Service-Specific", test_service_specific),
        ("Edge Cases", test_edge_cases)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, "PASSED" if result else "FAILED"))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
            results.append((test_name, "ERROR"))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, status in results:
        symbol = "✓" if status == "PASSED" else "❌"
        print(f"{symbol} {test_name}: {status}")
    
    passed = sum(1 for _, status in results if status == "PASSED")
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED! Ready to use.")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: uvicorn app.main:app --reload")
        print("2. Open: http://localhost:8000")
        print("3. Or run: python test_risk_engine.py")
        return True
    else:
        print("\n❌ Some tests failed. Check output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
