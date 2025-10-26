#!/usr/bin/env python3
"""
Log analysis and reporting tools for Telescope Simulator
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from tabulate import tabulate
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class LogAnalyzer:
    """Advanced log analysis and reporting"""
    
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self._init_mongodb()
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            DB_NAME = os.getenv('DB_NAME', 'celestiCodeServerDB')
            
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_client.admin.command('ping')
            self.mongo_db = self.mongo_client[DB_NAME]
            self.mongo_collection = self.mongo_db['enhanced_logs']
            print("Log analyzer connected to MongoDB")
        except Exception as e:
            print(f"Log analyzer MongoDB connection failed: {e}")
            self.mongo_client = None
            self.mongo_db = None
            self.mongo_collection = None
    
    def get_logs_by_timeframe(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get logs from the last N hours"""
        if not self.mongo_collection:
            return []
        
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            logs = list(self.mongo_collection.find({
                'timestamp': {'$gte': start_time}
            }).sort('timestamp', -1))
            return logs
        except PyMongoError as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def get_user_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get user activity summary"""
        logs = self.get_logs_by_timeframe(hours)
        
        user_stats = defaultdict(lambda: {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'commands': Counter(),
            'categories': Counter(),
            'last_activity': None
        })
        
        for log in logs:
            user = log.get('user', 'unknown')
            level = log.get('level', 'unknown')
            command = log.get('command', 'unknown')
            category = log.get('category', 'unknown')
            timestamp = log.get('timestamp')
            
            user_stats[user]['total_actions'] += 1
            user_stats[user]['commands'][command] += 1
            user_stats[user]['categories'][category] += 1
            
            if level in ['success', 'info']:
                user_stats[user]['successful_actions'] += 1
            elif level in ['error', 'critical']:
                user_stats[user]['failed_actions'] += 1
            
            if not user_stats[user]['last_activity'] or timestamp > user_stats[user]['last_activity']:
                user_stats[user]['last_activity'] = timestamp
        
        return dict(user_stats)
    
    def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns"""
        logs = self.get_logs_by_timeframe(hours)
        error_logs = [log for log in logs if log.get('level') in ['error', 'critical']]
        
        error_stats = {
            'total_errors': len(error_logs),
            'errors_by_category': Counter(),
            'errors_by_user': Counter(),
            'errors_by_command': Counter(),
            'common_error_messages': Counter(),
            'recent_errors': error_logs[:10]  # Last 10 errors
        }
        
        for log in error_logs:
            error_stats['errors_by_category'][log.get('category', 'unknown')] += 1
            error_stats['errors_by_user'][log.get('user', 'unknown')] += 1
            error_stats['errors_by_command'][log.get('command', 'unknown')] += 1
            error_stats['common_error_messages'][log.get('message', 'unknown')] += 1
        
        return error_stats
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security-related events"""
        if not self.mongo_collection:
            return []
        
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            security_logs = list(self.mongo_collection.find({
                'timestamp': {'$gte': start_time},
                '$or': [
                    {'level': 'security'},
                    {'category': 'security'},
                    {'category': 'auth'},
                    {'message': {'$regex': 'login|auth|security|failed|attempt', '$options': 'i'}}
                ]
            }).sort('timestamp', -1))
            return security_logs
        except PyMongoError as e:
            print(f"Error fetching security logs: {e}")
            return []
    
    def get_telescope_usage_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get telescope usage statistics"""
        logs = self.get_logs_by_timeframe(hours)
        telescope_logs = [log for log in logs if log.get('category') == 'telescope']
        
        stats = {
            'total_movements': len(telescope_logs),
            'movements_by_user': Counter(),
            'movements_by_command': Counter(),
            'coordinate_ranges': {
                'altitude': {'min': 90, 'max': 0},
                'azimuth': {'min': 360, 'max': 0}
            },
            'success_rate': 0
        }
        
        successful_movements = 0
        for log in telescope_logs:
            user = log.get('user', 'unknown')
            command = log.get('command', 'unknown')
            level = log.get('level', 'unknown')
            extra_data = log.get('extra_data', {})
            
            stats['movements_by_user'][user] += 1
            stats['movements_by_command'][command] += 1
            
            if level in ['success', 'info']:
                successful_movements += 1
            
            # Extract coordinate information
            coordinates = extra_data.get('coordinates', {})
            if 'alt' in coordinates:
                alt = coordinates['alt']
                stats['coordinate_ranges']['altitude']['min'] = min(stats['coordinate_ranges']['altitude']['min'], alt)
                stats['coordinate_ranges']['altitude']['max'] = max(stats['coordinate_ranges']['altitude']['max'], alt)
            
            if 'az' in coordinates:
                az = coordinates['az']
                stats['coordinate_ranges']['azimuth']['min'] = min(stats['coordinate_ranges']['azimuth']['min'], az)
                stats['coordinate_ranges']['azimuth']['max'] = max(stats['coordinate_ranges']['azimuth']['max'], az)
        
        if stats['total_movements'] > 0:
            stats['success_rate'] = (successful_movements / stats['total_movements']) * 100
        
        return stats
    
    def generate_daily_report(self) -> str:
        """Generate a comprehensive daily report"""
        report = []
        report.append("🔭 TELESCOPE SIMULATOR - DAILY REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # User Activity Summary
        user_stats = self.get_user_activity_summary(24)
        if user_stats:
            report.append("USER ACTIVITY (Last 24 Hours)")
            report.append("-" * 30)
            
            table_data = []
            for user, stats in user_stats.items():
                success_rate = (stats['successful_actions'] / stats['total_actions'] * 100) if stats['total_actions'] > 0 else 0
                table_data.append([
                    user,
                    stats['total_actions'],
                    stats['successful_actions'],
                    stats['failed_actions'],
                    f"{success_rate:.1f}%",
                    stats['last_activity'].strftime('%H:%M:%S') if stats['last_activity'] else 'N/A'
                ])
            
            headers = ["User", "Total Actions", "Successful", "Failed", "Success Rate", "Last Activity"]
            report.append(tabulate(table_data, headers=headers, tablefmt="github"))
            report.append("")
        
        # Error Analysis
        error_stats = self.get_error_analysis(24)
        if error_stats['total_errors'] > 0:
            report.append("ERROR ANALYSIS (Last 24 Hours)")
            report.append("-" * 30)
            report.append(f"Total Errors: {error_stats['total_errors']}")
            report.append("")
            
            if error_stats['errors_by_category']:
                report.append("Errors by Category:")
                for category, count in error_stats['errors_by_category'].most_common(5):
                    report.append(f"  {category}: {count}")
                report.append("")
            
            if error_stats['common_error_messages']:
                report.append("Most Common Error Messages:")
                for message, count in error_stats['common_error_messages'].most_common(3):
                    report.append(f"  {message}: {count}")
                report.append("")
        
        # Security Events
        security_events = self.get_security_events(24)
        if security_events:
            report.append("SECURITY EVENTS (Last 24 Hours)")
            report.append("-" * 30)
            report.append(f"Total Security Events: {len(security_events)}")
            
            for event in security_events[:5]:  # Show last 5 events
                timestamp = event.get('timestamp', datetime.now()).strftime('%H:%M:%S')
                user = event.get('user', 'unknown')
                message = event.get('message', 'No message')
                report.append(f"  {timestamp} - {user}: {message}")
            report.append("")
        
        # Telescope Usage
        telescope_stats = self.get_telescope_usage_stats(24)
        if telescope_stats['total_movements'] > 0:
            report.append("TELESCOPE USAGE (Last 24 Hours)")
            report.append("-" * 30)
            report.append(f"Total Movements: {telescope_stats['total_movements']}")
            report.append(f"Success Rate: {telescope_stats['success_rate']:.1f}%")
            
            if telescope_stats['coordinate_ranges']['altitude']['min'] != 90:
                report.append(f"Altitude Range: {telescope_stats['coordinate_ranges']['altitude']['min']:.1f}° - {telescope_stats['coordinate_ranges']['altitude']['max']:.1f}°")
            
            if telescope_stats['coordinate_ranges']['azimuth']['min'] != 360:
                report.append(f"Azimuth Range: {telescope_stats['coordinate_ranges']['azimuth']['min']:.1f}° - {telescope_stats['coordinate_ranges']['azimuth']['max']:.1f}°")
            report.append("")
        
        return "\n".join(report)
    
    def export_logs_to_csv(self, hours: int = 24, filename: Optional[str] = None) -> str:
        """Export logs to CSV format"""
        import csv
        
        if not filename:
            filename = f"telescope_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        logs = self.get_logs_by_timeframe(hours)
        
        if not logs:
            return "No logs to export"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'level', 'category', 'user', 'command', 'message', 'extra_data']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for log in logs:
                    # Convert extra_data to string for CSV
                    log_copy = log.copy()
                    if 'extra_data' in log_copy and log_copy['extra_data']:
                        log_copy['extra_data'] = str(log_copy['extra_data'])
                    else:
                        log_copy['extra_data'] = ''
                    
                    # Remove MongoDB _id field
                    log_copy.pop('_id', None)
                    
                    writer.writerow(log_copy)
            
            return f"Logs exported to {filename}"
        except Exception as e:
            return f"Export failed: {e}"

def main():
    """Test the log analyzer"""
    analyzer = LogAnalyzer()
    
    if analyzer.mongo_collection:
        print("Testing Log Analyzer...")
        
        # Generate daily report
        report = analyzer.generate_daily_report()
        print(report)
        
        # Test CSV export
        result = analyzer.export_logs_to_csv(24)
        print(f"\n{result}")
    else:
        print("Log analyzer not available - MongoDB connection failed")

if __name__ == "__main__":
    main()
