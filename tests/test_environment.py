"""
Environment verification tests for ATS system
"""
import sys
from pathlib import Path

def test_environment_verification():
    """Test basic environment setup"""
    print("=== Environment Verification Test ===")
    
    # Test Python version
    python_version = sys.version_info
    print(f"✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Test virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment is active")
    else:
        print("✗ Virtual environment not detected")
    
    # Test core imports
    try:
        import ccxt
        import pandas
        import numpy
        print("✓ Core dependencies (ccxt, pandas, numpy) imported successfully")
    except ImportError as e:
        print(f"✗ Core dependencies import failed: {e}")
        return False
    
    # Test ML dependencies
    try:
        import sklearn
        import lightgbm
        import xgboost
        print("✓ ML dependencies (sklearn, lightgbm, xgboost) imported successfully")
    except ImportError as e:
        print(f"✗ ML dependencies import failed: {e}")
        return False
    
    # Test web dependencies
    try:
        import fastapi
        import uvicorn
        print("✓ Web dependencies (fastapi, uvicorn) imported successfully")
    except ImportError as e:
        print(f"✗ Web dependencies import failed: {e}")
        return False
    
    return True

def test_project_structure():
    """Test project directory structure"""
    print("\n=== Project Structure Test ===")
    
    required_dirs = [
        "src", "src/data", "src/algorithms", "src/risk", "src/ml", 
        "src/database", "src/trading", "src/monitoring",
        "config", "tests", "logs", "data"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def test_logging_system():
    """Test logging system setup"""
    print("\n=== Logging System Test ===")
    
    try:
        # Add current directory to Python path
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path.cwd()))
        
        from config.logging_config import setup_logging, get_logger
        
        # Initialize logging
        logger = setup_logging()
        
        # Test different log levels
        logger.info("Environment setup test - INFO level")
        logger.warning("Environment setup test - WARNING level")
        logger.error("Environment setup test - ERROR level")
        
        # Test named logger
        test_logger = get_logger("test_module")
        test_logger.info("Named logger test")
        
        # Check if log files are created
        logs_dir = Path("logs")
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            if log_files:
                print(f"✓ Log files created: {[f.name for f in log_files]}")
            else:
                print("✓ Logs directory exists (files will be created on first log)")
        else:
            print("✗ Logs directory not found")
            return False
        
        print("✓ Logging system working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Logging system test failed: {e}")
        return False

def main():
    """Run all environment tests"""
    print("Starting ATS Environment Verification Tests...\n")
    
    tests = [
        test_environment_verification,
        test_project_structure,
        test_logging_system
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All environment tests passed! Task 1 completed successfully.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    main()
