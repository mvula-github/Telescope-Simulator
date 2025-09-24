#!/usr/bin/env python3
"""
Test script to verify all imports work correctly after package restructuring
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_imports():
    """Test all package imports"""
    print("🧪 Testing package imports...")
    print("=" * 50)
    
    # Test core package imports
    try:
        import core.file_handling
        print("✅ Core file_handling imported successfully")
    except ImportError as e:
        print(f"❌ Core file_handling import failed: {e}")
    
    try:
        import core.telescope_control
        print("✅ Core telescope_control imported successfully")
    except ImportError as e:
        print(f"❌ Core telescope_control import failed: {e}")
    
    try:
        import core.calculations
        print("✅ Core calculations imported successfully")
    except ImportError as e:
        print(f"❌ Core calculations import failed: {e}")
    
    try:
        import core.system_checks
        print("✅ Core system_checks imported successfully")
    except ImportError as e:
        print(f"❌ Core system_checks import failed: {e}")
    
    try:
        from core.system_config import config
        print("✅ Core system_config imported successfully")
    except ImportError as e:
        print(f"❌ Core system_config import failed: {e}")
    
    # Test simulation package imports
    try:
        import simulation.sim_interface
        print("✅ Simulation sim_interface imported successfully")
    except ImportError as e:
        print(f"❌ Simulation sim_interface import failed: {e}")
    
    try:
        import simulation.track_objects
        print("✅ Simulation track_objects imported successfully")
    except ImportError as e:
        print(f"❌ Simulation track_objects import failed: {e}")
    
    try:
        import simulation.sim_const
        print("✅ Simulation sim_const imported successfully")
    except ImportError as e:
        print(f"❌ Simulation sim_const import failed: {e}")
    
    # Test API package imports
    try:
        import api.user_api
        print("✅ API user_api imported successfully")
    except ImportError as e:
        print(f"❌ API user_api import failed: {e}")
    
    # Test users package imports
    try:
        from users.middleware.auth import authenticate_user
        print("✅ Users middleware auth imported successfully")
    except ImportError as e:
        print(f"❌ Users middleware auth import failed: {e}")
    
    print("=" * 50)
    print("🎉 Import testing complete!")

def test_function_calls():
    """Test that key functions can be called"""
    print("\n🔧 Testing function calls...")
    print("=" * 50)
    
    try:
        import core.file_handling as FH
        import core.telescope_control as TM
        import core.calculations as C
        import core.system_checks as SCh
        from core.system_config import config
        
        print("✅ All core modules imported successfully")
        
        # Test config access
        test_config = config.get('latitude', 0.0)
        print(f"✅ Config access works: latitude = {test_config}")
        
        # Test function availability
        if hasattr(TM, 'move_tel'):
            print("✅ TM.move_tel function available")
        else:
            print("❌ TM.move_tel function not found")
        
        if hasattr(FH, 'write_log'):
            print("✅ FH.write_log function available")
        else:
            print("❌ FH.write_log function not found")
        
        if hasattr(C, 'convert_radec_to_altaz'):
            print("✅ C.convert_radec_to_altaz function available")
        else:
            print("❌ C.convert_radec_to_altaz function not found")
        
    except Exception as e:
        print(f"❌ Function call testing failed: {e}")
    
    print("=" * 50)
    print("🎉 Function testing complete!")

if __name__ == "__main__":
    test_imports()
    test_function_calls()
    
    print("\n📋 Summary:")
    print("If all tests passed, your package restructuring is complete!")
    print("You can now run: python main.py")
