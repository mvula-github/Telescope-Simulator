#!/usr/bin/env python3
"""
Enhanced display menu system for Telescope Simulator
Provides interactive data viewing and display configuration options
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from core.data_display import data_display_manager, DisplayFormat, DataCategory
from core.access_control import access_control_manager

class DisplayMenuManager:
    """Manages the enhanced display menu system"""
    
    def __init__(self):
        self.data_manager = data_display_manager
        self.current_filters = {}
        self.current_format = None
    
    def show_display_options_menu(self, user: Dict[str, Any]) -> None:
        """Show the main display options menu"""
        while True:
            print(f"\n{'='*60}")
            print("📊 DISPLAY DATA OPTIONS")
            print(f"{'='*60}")
            print(f"Current User: {user['username']} ({user.get('role', 'operator')})")
            print(f"Current Format: {self.current_format or self.data_manager.display_config['default_format']}")
            print(f"Current Filters: {self.current_filters if self.current_filters else 'None'}")
            print(f"{'='*60}")
            
            menu_options = [
                "1. View Telescope Data",
                "2. View System Logs", 
                "3. View User Activity",
                "4. View Celestial Objects",
                "5. View System Status",
                "6. Configure Display Options",
                "7. Set Data Filters",
                "8. Export Data",
                "9. Quick Reports",
                "10. Back to Main Menu"
            ]
            
            for option in menu_options:
                print(option)
            
            try:
                choice = int(input("\nEnter your choice: "))
                
                if choice == 1:
                    self._view_telescope_data(user)
                elif choice == 2:
                    self._view_system_logs(user)
                elif choice == 3:
                    self._view_user_activity(user)
                elif choice == 4:
                    self._view_celestial_objects(user)
                elif choice == 5:
                    self._view_system_status(user)
                elif choice == 6:
                    self._configure_display_options()
                elif choice == 7:
                    self._set_data_filters()
                elif choice == 8:
                    self._export_data_menu(user)
                elif choice == 9:
                    self._quick_reports_menu(user)
                elif choice == 10:
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n\nExiting display menu...")
                break
    
    def _view_telescope_data(self, user: Dict[str, Any] = None) -> None:
        """View telescope operational data"""
        print(f"\n{'='*50}")
        print("🔭 TELESCOPE DATA VIEWER")
        print(f"{'='*50}")
        
        # Get format choice
        format_choice = self._get_format_choice()
        if not format_choice:
            return
        
        # Get data
        data_output = self.data_manager.display_telescope_data(format_choice, self.current_filters, user)
        print(data_output)
        
        # Ask if user wants to save
        self._ask_save_data("telescope", format_choice)
    
    def _view_system_logs(self, user: Dict[str, Any] = None) -> None:
        """View system logs"""
        print(f"\n{'='*50}")
        print("📋 SYSTEM LOGS VIEWER")
        print(f"{'='*50}")
        
        # Get format choice
        format_choice = self._get_format_choice()
        if not format_choice:
            return
        
        # Get data
        data_output = self.data_manager.display_system_logs(format_choice, self.current_filters, user)
        print(data_output)
        
        # Ask if user wants to save
        self._ask_save_data("logs", format_choice)
    
    def _view_user_activity(self, user: Dict[str, Any] = None) -> None:
        """View user activity summary"""
        print(f"\n{'='*50}")
        print("👥 USER ACTIVITY VIEWER")
        print(f"{'='*50}")
        
        # Get format choice
        format_choice = self._get_format_choice()
        if not format_choice:
            return
        
        # Get data
        data_output = self.data_manager.display_user_activity(format_choice, self.current_filters, user)
        print(data_output)
        
        # Ask if user wants to save
        self._ask_save_data("users", format_choice)
    
    def _view_celestial_objects(self, user: Dict[str, Any] = None) -> None:
        """View celestial objects data"""
        print(f"\n{'='*50}")
        print("🌟 CELESTIAL OBJECTS VIEWER")
        print(f"{'='*50}")
        
        # Get format choice
        format_choice = self._get_format_choice()
        if not format_choice:
            return
        
        # Get data
        data_output = self.data_manager.display_celestial_objects(format_choice, self.current_filters, user)
        print(data_output)
        
        # Ask if user wants to save
        self._ask_save_data("objects", format_choice)
    
    def _view_system_status(self, user: Dict[str, Any] = None) -> None:
        """View system status"""
        print(f"\n{'='*50}")
        print("⚙️ SYSTEM STATUS VIEWER")
        print(f"{'='*50}")
        
        # Get format choice
        format_choice = self._get_format_choice()
        if not format_choice:
            return
        
        # Get data
        data_output = self.data_manager.display_system_status(format_choice, user)
        print(data_output)
        
        # Ask if user wants to save
        self._ask_save_data("system", format_choice)
    
    def _configure_display_options(self) -> None:
        """Configure display options"""
        print(f"\n{'='*50}")
        print("⚙️ DISPLAY CONFIGURATION")
        print(f"{'='*50}")
        
        current_config = self.data_manager.get_display_options()
        
        while True:
            print(f"\nCurrent Configuration:")
            for key, value in current_config.items():
                if key != "filters":  # Show filters separately
                    print(f"  {key}: {value}")
            
            print(f"\nConfiguration Options:")
            print("1. Change default format")
            print("2. Change table style")
            print("3. Change max rows")
            print("4. Toggle timestamps")
            print("5. Change date format")
            print("6. Toggle color output")
            print("7. Toggle compact mode")
            print("8. Change export path")
            print("9. Reset to defaults")
            print("10. Back")
            
            try:
                choice = int(input("\nEnter your choice: "))
                
                if choice == 1:
                    self._change_default_format()
                elif choice == 2:
                    self._change_table_style()
                elif choice == 3:
                    self._change_max_rows()
                elif choice == 4:
                    self._toggle_timestamps()
                elif choice == 5:
                    self._change_date_format()
                elif choice == 6:
                    self._toggle_color_output()
                elif choice == 7:
                    self._toggle_compact_mode()
                elif choice == 8:
                    self._change_export_path()
                elif choice == 9:
                    self._reset_to_defaults()
                elif choice == 10:
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
    
    def _set_data_filters(self) -> None:
        """Set data filters"""
        print(f"\n{'='*50}")
        print("🔍 DATA FILTERS")
        print(f"{'='*50}")
        
        while True:
            print(f"\nCurrent Filters: {self.current_filters if self.current_filters else 'None'}")
            print(f"\nFilter Options:")
            print("1. Set timeframe (hours)")
            print("2. Filter by user")
            print("3. Filter by log level")
            print("4. Filter by command")
            print("5. Filter by object name")
            print("6. Clear all filters")
            print("7. Back")
            
            try:
                choice = int(input("\nEnter your choice: "))
                
                if choice == 1:
                    self._set_timeframe_filter()
                elif choice == 2:
                    self._set_user_filter()
                elif choice == 3:
                    self._set_level_filter()
                elif choice == 4:
                    self._set_command_filter()
                elif choice == 5:
                    self._set_object_name_filter()
                elif choice == 6:
                    self.current_filters = {}
                    print("✅ All filters cleared")
                elif choice == 7:
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
    
    def _export_data_menu(self, user: Dict[str, Any] = None) -> None:
        """Export data menu"""
        print(f"\n{'='*50}")
        print("📁 EXPORT DATA")
        print(f"{'='*50}")
        
        data_types = self.data_manager.get_available_data_types()
        formats = self.data_manager.get_available_formats()
        
        print(f"\nAvailable data types: {', '.join(data_types)}")
        print(f"Available formats: {', '.join(formats)}")
        
        try:
            data_type = input("\nEnter data type to export: ").strip()
            if data_type not in data_types:
                print(f"❌ Invalid data type. Available: {', '.join(data_types)}")
                return
            
            format_type = input("Enter export format: ").strip()
            if format_type not in formats:
                print(f"❌ Invalid format. Available: {', '.join(formats)}")
                return
            
            filename = input("Enter filename (or press Enter for auto-generated): ").strip()
            if not filename:
                filename = None
            
            result = self.data_manager.export_data(data_type, format_type, filename, self.current_filters, user)
            print(result)
            
        except KeyboardInterrupt:
            print("\nExport cancelled.")
    
    def _quick_reports_menu(self, user: Dict[str, Any] = None) -> None:
        """Quick reports menu"""
        print(f"\n{'='*50}")
        print("📊 QUICK REPORTS")
        print(f"{'='*50}")
        
        while True:
            print(f"\nQuick Report Options:")
            print("1. Daily Activity Summary")
            print("2. Error Analysis")
            print("3. Telescope Usage Stats")
            print("4. User Performance Report")
            print("5. System Health Check")
            print("6. Back")
            
            try:
                choice = int(input("\nEnter your choice: "))
                
                if choice == 1:
                    self._generate_daily_summary(user)
                elif choice == 2:
                    self._generate_error_analysis(user)
                elif choice == 3:
                    self._generate_telescope_stats(user)
                elif choice == 4:
                    self._generate_user_performance(user)
                elif choice == 5:
                    self._generate_system_health(user)
                elif choice == 6:
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter a number.")
    
    def _get_format_choice(self) -> Optional[str]:
        """Get format choice from user"""
        formats = self.data_manager.get_available_formats()
        
        print(f"\nAvailable formats: {', '.join(formats)}")
        format_choice = input(f"Enter format (or press Enter for '{self.data_manager.display_config['default_format']}'): ").strip()
        
        if not format_choice:
            return self.data_manager.display_config['default_format']
        
        if format_choice in formats:
            return format_choice
        else:
            print(f"❌ Invalid format. Using default: {self.data_manager.display_config['default_format']}")
            return self.data_manager.display_config['default_format']
    
    def _ask_save_data(self, data_type: str, format_type: str) -> None:
        """Ask user if they want to save the displayed data"""
        try:
            save = input(f"\nSave this {data_type} data? (y/n): ").strip().lower()
            if save in ['y', 'yes']:
                filename = input("Enter filename (or press Enter for auto-generated): ").strip()
                if not filename:
                    filename = None
                
                result = self.data_manager.export_data(data_type, format_type, filename, self.current_filters, user)
                print(result)
        except KeyboardInterrupt:
            print("\nSave cancelled.")
    
    # Configuration methods
    def _change_default_format(self) -> None:
        """Change default display format"""
        formats = self.data_manager.get_available_formats()
        print(f"Available formats: {', '.join(formats)}")
        
        new_format = input("Enter new default format: ").strip()
        if new_format in formats:
            self.data_manager.update_display_option("default_format", new_format)
        else:
            print(f"❌ Invalid format. Available: {', '.join(formats)}")
    
    def _change_table_style(self) -> None:
        """Change table style"""
        styles = ["github", "grid", "fancy_grid", "pipe", "orgtbl", "rst", "mediawiki", "html", "latex"]
        print(f"Available styles: {', '.join(styles)}")
        
        new_style = input("Enter new table style: ").strip()
        if new_style in styles:
            self.data_manager.update_display_option("table_style", new_style)
        else:
            print(f"❌ Invalid style. Available: {', '.join(styles)}")
    
    def _change_max_rows(self) -> None:
        """Change maximum rows to display"""
        try:
            new_max = int(input("Enter new maximum rows (10-1000): "))
            if 10 <= new_max <= 1000:
                self.data_manager.update_display_option("max_rows", new_max)
            else:
                print("❌ Maximum rows must be between 10 and 1000")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    def _toggle_timestamps(self) -> None:
        """Toggle timestamp display"""
        current = self.data_manager.display_config["show_timestamps"]
        new_value = not current
        self.data_manager.update_display_option("show_timestamps", new_value)
        print(f"✅ Timestamps {'enabled' if new_value else 'disabled'}")
    
    def _change_date_format(self) -> None:
        """Change date format"""
        print("Common formats:")
        print("  %Y-%m-%d %H:%M:%S (2024-01-15 14:30:25)")
        print("  %d/%m/%Y %H:%M (15/01/2024 14:30)")
        print("  %m/%d/%Y (01/15/2024)")
        
        new_format = input("Enter new date format: ").strip()
        if new_format:
            self.data_manager.update_display_option("date_format", new_format)
    
    def _toggle_color_output(self) -> None:
        """Toggle color output"""
        current = self.data_manager.display_config["color_output"]
        new_value = not current
        self.data_manager.update_display_option("color_output", new_value)
        print(f"✅ Color output {'enabled' if new_value else 'disabled'}")
    
    def _toggle_compact_mode(self) -> None:
        """Toggle compact mode"""
        current = self.data_manager.display_config["compact_mode"]
        new_value = not current
        self.data_manager.update_display_option("compact_mode", new_value)
        print(f"✅ Compact mode {'enabled' if new_value else 'disabled'}")
    
    def _change_export_path(self) -> None:
        """Change export path"""
        new_path = input("Enter new export path: ").strip()
        if new_path:
            # Ensure path ends with separator
            if not new_path.endswith(os.sep):
                new_path += os.sep
            self.data_manager.update_display_option("export_path", new_path)
    
    def _reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        confirm = input("Are you sure you want to reset to defaults? (yes/no): ").strip().lower()
        if confirm == 'yes':
            # Reset to default configuration
            default_config = {
                "default_format": "table",
                "table_style": "github",
                "max_rows": 100,
                "show_timestamps": True,
                "date_format": "%Y-%m-%d %H:%M:%S",
                "auto_refresh": False,
                "refresh_interval": 30,
                "color_output": True,
                "compact_mode": False,
                "show_headers": True,
                "export_path": "exports/",
                "filters": {
                    "default_timeframe": 24,
                    "default_levels": ["success", "error", "warning"],
                    "default_categories": ["telescope", "system", "logs"]
                }
            }
            
            for key, value in default_config.items():
                self.data_manager.update_display_option(key, value)
            
            print("✅ Configuration reset to defaults")
    
    # Filter methods
    def _set_timeframe_filter(self) -> None:
        """Set timeframe filter"""
        try:
            hours = int(input("Enter timeframe in hours (1-168): "))
            if 1 <= hours <= 168:
                self.current_filters["timeframe"] = hours
                print(f"✅ Timeframe set to {hours} hours")
            else:
                print("❌ Timeframe must be between 1 and 168 hours")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
    
    def _set_user_filter(self) -> None:
        """Set user filter"""
        user = input("Enter username to filter by (or 'clear' to remove): ").strip()
        if user.lower() == 'clear':
            self.current_filters.pop("user", None)
            print("✅ User filter cleared")
        elif user:
            self.current_filters["user"] = user
            print(f"✅ User filter set to: {user}")
    
    def _set_level_filter(self) -> None:
        """Set log level filter"""
        levels = ["success", "error", "warning", "info", "critical"]
        print(f"Available levels: {', '.join(levels)}")
        
        level_input = input("Enter levels (comma-separated, or 'clear' to remove): ").strip()
        if level_input.lower() == 'clear':
            self.current_filters.pop("level", None)
            print("✅ Level filter cleared")
        elif level_input:
            selected_levels = [level.strip() for level in level_input.split(',')]
            valid_levels = [level for level in selected_levels if level in levels]
            if valid_levels:
                self.current_filters["level"] = valid_levels
                print(f"✅ Level filter set to: {', '.join(valid_levels)}")
            else:
                print(f"❌ Invalid levels. Available: {', '.join(levels)}")
    
    def _set_command_filter(self) -> None:
        """Set command filter"""
        command = input("Enter command pattern to filter by (or 'clear' to remove): ").strip()
        if command.lower() == 'clear':
            self.current_filters.pop("command", None)
            print("✅ Command filter cleared")
        elif command:
            self.current_filters["command"] = command
            print(f"✅ Command filter set to: {command}")
    
    def _set_object_name_filter(self) -> None:
        """Set object name filter"""
        name = input("Enter object name pattern to filter by (or 'clear' to remove): ").strip()
        if name.lower() == 'clear':
            self.current_filters.pop("name", None)
            print("✅ Object name filter cleared")
        elif name:
            self.current_filters["name"] = name
            print(f"✅ Object name filter set to: {name}")
    
    # Quick report methods
    def _generate_daily_summary(self, user: Dict[str, Any] = None) -> None:
        """Generate daily activity summary"""
        print(f"\n{'='*60}")
        print("📊 DAILY ACTIVITY SUMMARY")
        print(f"{'='*60}")
        
        # Set timeframe to 24 hours for daily summary
        filters = self.current_filters.copy()
        filters["timeframe"] = 24
        
        # Get user activity
        user_data = self.data_manager.display_user_activity("summary", filters, user)
        print(user_data)
        
        # Get telescope usage
        telescope_data = self.data_manager.display_telescope_data("summary", filters, user)
        print(telescope_data)
    
    def _generate_error_analysis(self, user: Dict[str, Any] = None) -> None:
        """Generate error analysis report"""
        print(f"\n{'='*60}")
        print("❌ ERROR ANALYSIS REPORT")
        print(f"{'='*60}")
        
        # Set filters for errors only
        filters = self.current_filters.copy()
        filters["level"] = ["error", "critical"]
        
        error_data = self.data_manager.display_system_logs("detailed", filters, user)
        print(error_data)
    
    def _generate_telescope_stats(self, user: Dict[str, Any] = None) -> None:
        """Generate telescope usage statistics"""
        print(f"\n{'='*60}")
        print("🔭 TELESCOPE USAGE STATISTICS")
        print(f"{'='*60}")
        
        telescope_data = self.data_manager.display_telescope_data("summary", self.current_filters, user)
        print(telescope_data)
    
    def _generate_user_performance(self, user: Dict[str, Any] = None) -> None:
        """Generate user performance report"""
        print(f"\n{'='*60}")
        print("👥 USER PERFORMANCE REPORT")
        print(f"{'='*60}")
        
        user_data = self.data_manager.display_user_activity("detailed", self.current_filters, user)
        print(user_data)
    
    def _generate_system_health(self, user: Dict[str, Any] = None) -> None:
        """Generate system health check"""
        print(f"\n{'='*60}")
        print("⚙️ SYSTEM HEALTH CHECK")
        print(f"{'='*60}")
        
        system_data = self.data_manager.display_system_status("detailed", user)
        print(system_data)

# Global instance
display_menu_manager = DisplayMenuManager()
