#!/usr/bin/env python3
"""
Setup verification script - ensures all components are ready
Run this after installation to verify everything works
"""

import os
import sys
import subprocess
from pathlib import Path

class Verification:
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.base_path = Path(__file__).parent
    
    def print_header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def check_mark(self, condition, message):
        if condition:
            print(f"✓ {message}")
            self.checks_passed += 1
        else:
            print(f"✗ {message}")
            self.checks_failed += 1
        return condition
    
    def verify_file_structure(self):
        """Verify all required files exist"""
        self.print_header("1. File Structure")
        
        files_to_check = {
            "app/main.py": "Main API file (updated)",
            "app/preprocess.py": "Preprocessing layer (NEW)",
            "app/frontend.html": "Web frontend (NEW)",
            "app/inference.py": "Model inference",
            "app/risk_engine.py": "Risk computation",
            "models/mlp_model.keras": "ML model",
            "models/shap_background.npy": "SHAP background",
            "requirements.txt": "Dependencies",
            "README.md": "Documentation (updated)",
            "QUICKSTART.md": "Quick start guide (NEW)",
            "FRONTEND_USAGE.md": "Detailed usage guide (NEW)",
            "test_risk_engine.py": "API tests (NEW)",
            "verify_integration.py": "Integration tests (NEW)",
        }
        
        for file_path, description in files_to_check.items():
            full_path = self.base_path / file_path
            exists = full_path.exists()
            self.check_mark(exists, f"{file_path:30} - {description}")
    
    def verify_python_imports(self):
        """Verify Python dependencies"""
        self.print_header("2. Python Dependencies")
        
        dependencies = {
            "fastapi": "FastAPI framework",
            "uvicorn": "ASGI server",
            "tensorflow": "TensorFlow/Keras",
            "numpy": "NumPy",
            "shap": "SHAP explainability",
        }
        
        for module, description in dependencies.items():
            try:
                __import__(module)
                self.check_mark(True, f"{module:20} - {description}")
            except ImportError:
                self.check_mark(False, f"{module:20} - {description} (INSTALL NEEDED)")
    
    def verify_preprocessing_module(self):
        """Verify preprocessing layer works"""
        self.print_header("3. Preprocessing Layer")
        
        try:
            sys.path.insert(0, str(self.base_path))
            from app.preprocess import preprocess_user_input, FeatureDeriver
            self.check_mark(True, "Preprocessing module imports successfully")
            
            # Test derivation
            test_input = {
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
            
            result = preprocess_user_input(test_input)
            
            # Check all required features
            required_features = {
                "proto", "service", "state", "attack_cat",
                "sbytes", "dbytes", "dur", "rate", "sload", "dload"
            }
            
            has_all = all(f in result for f in required_features)
            self.check_mark(has_all, f"Feature derivation works (11→{len(result)} features)")
            
        except Exception as e:
            self.check_mark(False, f"Preprocessing test failed: {str(e)}")
    
    def verify_model_files(self):
        """Verify model files can be loaded"""
        self.print_header("4. Model Files")
        
        model_dir = self.base_path / "models"
        
        self.check_mark(
            model_dir.exists(),
            "models/ directory exists"
        )
        
        model_files = {
            "mlp_model.keras": "MLP model",
            "ae_model.keras": "AutoEncoder model",
            "shap_background.npy": "SHAP background data"
        }
        
        for filename, description in model_files.items():
            file_path = model_dir / filename
            exists = file_path.exists()
            size_str = ""
            if exists:
                size_mb = file_path.stat().st_size / (1024*1024)
                size_str = f" ({size_mb:.1f}MB)"
            self.check_mark(
                exists,
                f"{filename:25} - {description}{size_str}"
            )
    
    def verify_frontend(self):
        """Verify frontend HTML"""
        self.print_header("5. Frontend")
        
        frontend_path = self.base_path / "app" / "frontend.html"
        if frontend_path.exists():
            with open(frontend_path, 'r') as f:
                content = f.read()
                has_form = "flowForm" in content
                has_api = "http://localhost:8000/predict" in content
                has_styles = "<style>" in content
                
                self.check_mark(has_form, "Frontend has form (flowForm)")
                self.check_mark(has_api, "Frontend has API endpoint")
                self.check_mark(has_styles, "Frontend has styling")
        else:
            self.check_mark(False, "frontend.html not found")
    
    def verify_api_structure(self):
        """Verify API structure"""
        self.print_header("6. API Structure")
        
        main_path = self.base_path / "app" / "main.py"
        if main_path.exists():
            with open(main_path, 'r') as f:
                content = f.read()
                has_cors = "CORSMiddleware" in content
                has_predict = "@app.post(\"/predict\")" in content
                has_preprocess = "preprocess_user_input" in content
                
                self.check_mark(has_cors, "API has CORS support")
                self.check_mark(has_predict, "API has /predict endpoint")
                self.check_mark(has_preprocess, "API uses preprocessing layer")
        else:
            self.check_mark(False, "main.py not found")
    
    def verify_documentation(self):
        """Verify documentation"""
        self.print_header("7. Documentation")
        
        docs = {
            "README.md": "Main README",
            "QUICKSTART.md": "Quick start guide",
            "FRONTEND_USAGE.md": "Detailed usage guide"
        }
        
        for filename, description in docs.items():
            path = self.base_path / filename
            exists = path.exists()
            if exists:
                lines = len(path.read_text().split('\n'))
                self.check_mark(
                    exists,
                    f"{filename:20} - {description} ({lines} lines)"
                )
            else:
                self.check_mark(False, f"{filename:20} - {description}")
    
    def run_all_checks(self):
        """Run all verification checks"""
        self.print_header("Zero Trust Risk Engine - Setup Verification")
        
        print(f"Base Path: {self.base_path}\n")
        
        self.verify_file_structure()
        self.verify_python_imports()
        self.verify_preprocessing_module()
        self.verify_model_files()
        self.verify_frontend()
        self.verify_api_structure()
        self.verify_documentation()
        
        # Summary
        self.print_header("Summary")
        
        total = self.checks_passed + self.checks_failed
        percentage = (self.checks_passed / total * 100) if total > 0 else 0
        
        print(f"Checks passed: {self.checks_passed}/{total} ({percentage:.0f}%)")
        print()
        
        if self.checks_failed == 0:
            print("✓ All checks passed! System is ready to use.\n")
            print("Next steps:")
            print("1. Run: uvicorn app.main:app --reload")
            print("2. Open: http://localhost:8000")
            print("3. Or run: python test_risk_engine.py")
            print()
            return True
        else:
            print(f"✗ {self.checks_failed} checks failed. Review above.\n")
            print("Common fixes:")
            print("- Install missing packages: pip install -r requirements.txt")
            print("- Check model files exist in ./models/")
            print("- Verify Python version: python --version")
            print()
            return False
    
    def print_system_info(self):
        """Print system information"""
        print(f"\nSystem Information:")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Platform: {sys.platform}")
        print(f"  Working Dir: {self.base_path}")
        print()

def main():
    verifier = Verification()
    verifier.print_system_info()
    success = verifier.run_all_checks()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
