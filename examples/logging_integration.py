#!/usr/bin/env python3
"""
Examples of how to integrate enhanced logging into existing code
"""

from core.enhanced_logging import logger, LogLevel, LogCategory

def example_authentication_logging():
    """Example: Enhanced authentication logging"""
    
    # Login attempt
    logger.log_auth(LogLevel.INFO, "Login attempt started", "admin")
    
    # Successful login
    logger.log_auth(LogLevel.SUCCESS, "User logged in successfully", "admin", success=True)
    
    # Failed login
    logger.log_auth(LogLevel.WARNING, "Invalid password provided", "admin", success=False)
    
    # Security event
    logger.log_security(LogLevel.SECURITY, "Multiple failed login attempts detected", "admin")

def example_telescope_logging():
    """Example: Enhanced telescope movement logging"""
    
    # Telescope movement start
    logger.log_telescope(
        LogLevel.INFO, 
        "Telescope movement initiated", 
        "admin", 
        "move_tel",
        coordinates={"alt": 45.0, "az": 180.0}
    )
    
    # Movement success
    logger.log_telescope(
        LogLevel.SUCCESS, 
        "Telescope reached target position", 
        "admin", 
        "move_tel",
        coordinates={"alt": 45.0, "az": 180.0}
    )
    
    # Movement error
    logger.log_telescope(
        LogLevel.ERROR, 
        "Telescope movement failed - coordinates out of range", 
        "admin", 
        "move_tel",
        coordinates={"alt": 95.0, "az": 180.0}
    )

def example_user_management_logging():
    """Example: Enhanced user management logging"""
    
    # User creation
    logger.log_user_mgmt(
        LogLevel.SUCCESS, 
        "New user created successfully", 
        "admin", 
        target_user="newuser"
    )
    
    # User deletion
    logger.log_user_mgmt(
        LogLevel.WARNING, 
        "User account deleted", 
        "admin", 
        target_user="olduser"
    )
    
    # Permission change
    logger.log_user_mgmt(
        LogLevel.INFO, 
        "User role changed from operator to admin", 
        "admin", 
        target_user="user123"
    )

def example_system_logging():
    """Example: Enhanced system logging"""
    
    # System startup
    logger.log_system(LogLevel.INFO, "Telescope simulator started", "main")
    
    # Configuration change
    logger.log_system(LogLevel.INFO, "Configuration updated", "config_manager")
    
    # Database connection
    logger.log_system(LogLevel.SUCCESS, "Database connection established", "database")
    
    # System error
    logger.log_system(LogLevel.ERROR, "Simulation interface connection failed", "sim_interface")

def example_coordinate_conversion_logging():
    """Example: Enhanced coordinate conversion logging"""
    
    # RA/Dec to Alt/Az conversion
    logger.log(
        LogLevel.INFO,
        LogCategory.COORDINATE_CONVERSION,
        "RA/Dec coordinates converted to Alt/Az",
        "admin",
        "convert_radec_to_altaz",
        extra_data={
            "input": {"ra": "12h34m56s", "dec": "+45°30'15\""},
            "output": {"alt": 45.5, "az": 180.2},
            "location": {"lat": 40.0, "lon": -74.0}
        }
    )

def example_object_tracking_logging():
    """Example: Enhanced object tracking logging"""
    
    # Object selection
    logger.log(
        LogLevel.INFO,
        LogCategory.OBJECT_TRACKING,
        "Astronomical object selected for tracking",
        "admin",
        "select_object",
        extra_data={
            "object_name": "M42 Orion Nebula",
            "coordinates": {"ra": "05h35m17s", "dec": "-05°23'28\""}
        }
    )
    
    # Tracking start
    logger.log(
        LogLevel.SUCCESS,
        LogCategory.OBJECT_TRACKING,
        "Object tracking started",
        "admin",
        "start_tracking",
        extra_data={
            "object_name": "M42 Orion Nebula",
            "tracking_duration": "30 minutes"
        }
    )

def example_error_logging():
    """Example: Enhanced error logging with exceptions"""
    
    try:
        # Some operation that might fail
        result = 1 / 0
    except ZeroDivisionError as e:
        logger.log_error(
            "admin",
            "calculate_position",
            "Division by zero error in position calculation",
            exception=e,
            extra_data={
                "operation": "coordinate_calculation",
                "input_values": {"numerator": 1, "denominator": 0}
            }
        )

def example_audit_logging():
    """Example: Enhanced audit logging"""
    
    # Audit trail for sensitive operations
    logger.log_audit(
        "admin",
        "USER_ROLE_CHANGE",
        "Changed user 'operator1' role from 'operator' to 'admin'"
    )
    
    logger.log_audit(
        "admin",
        "CONFIG_CHANGE",
        "Modified telescope altitude limits from [0,90] to [5,85]"
    )
    
    logger.log_audit(
        "admin",
        "SYSTEM_SHUTDOWN",
        "Telescope simulator shutdown initiated"
    )

if __name__ == "__main__":
    print("🔍 Testing Enhanced Logging Examples...")
    
    example_authentication_logging()
    example_telescope_logging()
    example_user_management_logging()
    example_system_logging()
    example_coordinate_conversion_logging()
    example_object_tracking_logging()
    example_error_logging()
    example_audit_logging()
    
    print("✅ All logging examples completed!")
