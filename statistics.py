#!/usr/bin/env python3
"""
Statistics tracking for signal broadcasting
"""

from datetime import datetime


class Statistics:
    def __init__(self):
        self.total_signals = 0
        self.successful_sends = 0
        self.failed_sends = 0
        self.signals_by_trend = {"call": 0, "put": 0}
        self.start_time = datetime.now()
        self.devices_reached = set()
        self.user_sends = 0
        self.admin_sends = 0
    
    def log_signal(self, trend: str, success: bool, identifier: str = None, user_type: str = "user"):
        """Log a signal send attempt"""
        self.total_signals += 1
        if success:
            self.successful_sends += 1
            if identifier:
                self.devices_reached.add(identifier)
            if "admin" in user_type.lower():
                self.admin_sends += 1
            else:
                self.user_sends += 1
        else:
            self.failed_sends += 1
        
        if trend in self.signals_by_trend:
            self.signals_by_trend[trend] += 1
    
    def get_summary(self) -> dict:
        """Get statistics summary"""
        uptime = datetime.now() - self.start_time
        return {
            "uptime_seconds": int(uptime.total_seconds()),
            "total_signals": self.total_signals,
            "successful": self.successful_sends,
            "failed": self.failed_sends,
            "success_rate": f"{(self.successful_sends / max(self.total_signals, 1) * 100):.1f}%",
            "calls": self.signals_by_trend["call"],
            "puts": self.signals_by_trend["put"],
            "unique_devices": len(self.devices_reached),
            "user_sends": self.user_sends,
            "admin_sends": self.admin_sends
        }
    
    def print_summary(self):
        """Print statistics summary"""
        summary = self.get_summary()
        print("\n📊 Statistics Summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")
    
    def reset(self):
        """Reset all statistics"""
        self.__init__()


# Global statistics instance
stats = Statistics()