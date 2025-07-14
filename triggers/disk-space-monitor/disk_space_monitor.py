#!/usr/bin/env python3
"""
Disk Space Monitor Trigger Plugin for Stavily Sensor Agents

Monitors disk usage across filesystems and triggers alerts when thresholds are exceeded.
"""

import json
import os
import sys
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

class DiskSpaceMonitorPlugin:
    """Disk Space Monitor trigger plugin implementation."""
    
    def __init__(self):
        self.config = {}
        self.threshold = 85.0
        self.critical_threshold = 95.0
        self.interval = 300  # 5 minutes default
        self.monitored_paths = ["/", "/var", "/tmp", "/home"]
        self.exclude_types = ["tmpfs", "devtmpfs", "proc", "sysfs"]
        self.running = False
        self.status = "stopped"
        self.start_time = None
        self.logger = self._setup_logging()
        self.last_alert_time = {}
        self.alert_cooldown = 600  # 10 minutes between same filesystem alerts
    
    def _setup_logging(self) -> logging.Logger:
        """Setup plugin logging."""
        logger = logging.getLogger('disk_space_monitor')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def get_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "id": "disk-space-monitor",
            "name": "Disk Space Monitor",
            "description": "Monitors disk usage across filesystems with configurable thresholds",
            "version": "1.0.0",
            "author": "Stavily Team",
            "license": "MIT",
            "type": "trigger",
            "tags": ["system", "monitoring", "disk", "storage", "filesystem"],
            "categories": ["system-monitoring"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            self.threshold = float(config.get("threshold", 85.0))
            self.critical_threshold = float(config.get("critical_threshold", 95.0))
            self.interval = int(config.get("interval", 300))
            self.alert_cooldown = int(config.get("alert_cooldown", 600))
            
            # Handle monitored paths
            if "monitored_paths" in config:
                self.monitored_paths = config["monitored_paths"]
            if "exclude_types" in config:
                self.exclude_types = config["exclude_types"]
            
            # Validate configuration
            if not (0 <= self.threshold <= 100):
                raise ValueError("Threshold must be between 0 and 100")
            if not (0 <= self.critical_threshold <= 100):
                raise ValueError("Critical threshold must be between 0 and 100")
            if self.threshold >= self.critical_threshold:
                raise ValueError("Critical threshold must be higher than regular threshold")
            if self.interval < 1:
                raise ValueError("Interval must be at least 1 second")
                
            self.status = "initialized"
            self.logger.info(f"Disk Space Monitor initialized: threshold={self.threshold}%, critical={self.critical_threshold}%, interval={self.interval}s")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin: {e}")
            self.status = "error"
            return False
    
    def start(self) -> bool:
        """Start the plugin execution."""
        try:
            if self.running:
                self.logger.warning("Plugin is already running")
                return True
                
            self.running = True
            self.status = "running"
            self.start_time = datetime.now()
            self.logger.info("Disk Space Monitor plugin started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start plugin: {e}")
            self.status = "error"
            return False
    
    def stop(self) -> bool:
        """Stop the plugin execution."""
        try:
            self.running = False
            self.status = "stopped"
            self.logger.info("Disk Space Monitor plugin stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop plugin: {e}")
            return False
    
    def get_status(self) -> str:
        """Return the current plugin status."""
        return self.status
    
    def get_health(self) -> Dict[str, Any]:
        """Return plugin health information."""
        disk_info = self._get_disk_info()
        
        health = {
            "status": "healthy" if self.running else "unhealthy",
            "message": "Plugin is running normally" if self.running else "Plugin is not running",
            "last_check": datetime.now().isoformat(),
            "uptime": 0,
            "error_count": 0,
            "metrics": {
                "monitored_filesystems": len(disk_info),
                "threshold": self.threshold,
                "critical_threshold": self.critical_threshold,
                "highest_usage": max([fs["percent"] for fs in disk_info] + [0]),
                "filesystems": disk_info
            }
        }
        
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            health["uptime"] = uptime
            
        return health
    
    def detect_triggers(self) -> Optional[Dict[str, Any]]:
        """Detect and return trigger events."""
        if not self.running:
            return None
            
        try:
            disk_info = self._get_disk_info()
            now = datetime.now()
            
            for filesystem in disk_info:
                mountpoint = filesystem["mountpoint"]
                usage = filesystem["percent"]
                
                # Determine alert level
                if usage >= self.critical_threshold:
                    alert_level = "critical"
                    threshold = self.critical_threshold
                elif usage >= self.threshold:
                    alert_level = "warning"
                    threshold = self.threshold
                else:
                    continue
                
                # Check cooldown
                alert_key = f"{mountpoint}_{alert_level}"
                if self._should_alert(alert_key, now):
                    event = self._create_disk_event(filesystem, alert_level, threshold)
                    self.last_alert_time[alert_key] = now
                    self.logger.warning(f"Disk usage alert: {mountpoint} at {usage:.1f}% (threshold: {threshold}%)")
                    return event
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting triggers: {e}")
            return None
    
    def get_trigger_config(self) -> Dict[str, Any]:
        """Return the trigger configuration schema."""
        return {
            "schema": {
                "threshold": {
                    "type": "number",
                    "description": "Disk usage threshold percentage (0-100)",
                    "default": 85.0,
                    "required": False,
                    "minimum": 0.0,
                    "maximum": 100.0
                },
                "critical_threshold": {
                    "type": "number",
                    "description": "Critical disk usage threshold percentage (0-100)",
                    "default": 95.0,
                    "required": False,
                    "minimum": 0.0,
                    "maximum": 100.0
                },
                "interval": {
                    "type": "integer",
                    "description": "Monitoring interval in seconds",
                    "default": 300,
                    "required": False,
                    "minimum": 1,
                    "examples": [60, 300, 600]
                },
                "monitored_paths": {
                    "type": "array",
                    "description": "List of filesystem paths to monitor",
                    "default": ["/", "/var", "/tmp", "/home"],
                    "required": False,
                    "items": {"type": "string"}
                },
                "exclude_types": {
                    "type": "array",
                    "description": "Filesystem types to exclude from monitoring",
                    "default": ["tmpfs", "devtmpfs", "proc", "sysfs"],
                    "required": False,
                    "items": {"type": "string"}
                },
                "alert_cooldown": {
                    "type": "integer",
                    "description": "Cooldown period between alerts for same filesystem (seconds)",
                    "default": 600,
                    "required": False,
                    "minimum": 60
                }
            },
            "required": [],
            "examples": [
                {
                    "threshold": 85.0,
                    "critical_threshold": 95.0,
                    "interval": 300,
                    "monitored_paths": ["/", "/var"]
                },
                {
                    "threshold": 90.0,
                    "critical_threshold": 98.0,
                    "interval": 600,
                    "exclude_types": ["tmpfs", "devtmpfs"]
                }
            ],
            "description": "Disk space monitoring configuration"
        }
    
    def _get_disk_info(self) -> List[Dict[str, Any]]:
        """Get disk usage information for monitored filesystems."""
        disk_info = []
        
        try:
            # Get all mounted filesystems
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                # Skip if filesystem type is excluded
                if partition.fstype.lower() in [ft.lower() for ft in self.exclude_types]:
                    continue
                
                # Skip if not in monitored paths (if specific paths are configured)
                if self.monitored_paths and not any(
                    partition.mountpoint.startswith(path) for path in self.monitored_paths
                ):
                    continue
                
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    percent = (usage.used / usage.total) * 100
                    
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round(percent, 2),
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2)
                    })
                    
                except (PermissionError, OSError) as e:
                    self.logger.warning(f"Cannot access {partition.mountpoint}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error getting disk info: {e}")
            
        return disk_info
    
    def _should_alert(self, alert_key: str, current_time: datetime) -> bool:
        """Check if we should send an alert based on cooldown period."""
        if alert_key not in self.last_alert_time:
            return True
            
        time_since_last = (current_time - self.last_alert_time[alert_key]).total_seconds()
        return time_since_last >= self.alert_cooldown
    
    def _create_disk_event(self, filesystem: Dict[str, Any], alert_level: str, threshold: float) -> Dict[str, Any]:
        """Create disk space trigger event."""
        event_id = f"disk-{alert_level}-{filesystem['mountpoint'].replace('/', '_')}-{int(time.time())}"
        
        return {
            "id": event_id,
            "type": f"disk.space.{alert_level}",
            "source": "disk-space-monitor",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "alert_level": alert_level,
                "filesystem": filesystem,
                "threshold": threshold,
                "usage_percent": filesystem["percent"],
                "free_space_gb": filesystem["free_gb"],
                "system_info": {
                    "hostname": os.uname().nodename,
                    "platform": os.uname().sysname
                }
            },
            "metadata": {
                "plugin_id": "disk-space-monitor",
                "plugin_version": "1.0.0",
                "hostname": os.uname().nodename
            },
            "tags": ["system", "disk", "storage", "filesystem", alert_level],
            "severity": "critical" if alert_level == "critical" else "high"
        }


def main():
    """Main plugin entry point."""
    plugin = DiskSpaceMonitorPlugin()
    
    # Plugin communication protocol
    while True:
        try:
            # Read command from stdin
            line = sys.stdin.readline().strip()
            if not line:
                break
                
            try:
                command = json.loads(line)
            except json.JSONDecodeError:
                response = {"error": "Invalid JSON command"}
                print(json.dumps(response))
                continue
            
            action = command.get("action")
            response = {"action": action, "success": False}
            
            if action == "get_info":
                response["data"] = plugin.get_info()
                response["success"] = True
                
            elif action == "initialize":
                config = command.get("config", {})
                response["success"] = plugin.initialize(config)
                
            elif action == "start":
                response["success"] = plugin.start()
                
            elif action == "stop":
                response["success"] = plugin.stop()
                
            elif action == "get_status":
                response["data"] = plugin.get_status()
                response["success"] = True
                
            elif action == "get_health":
                response["data"] = plugin.get_health()
                response["success"] = True
                
            elif action == "detect_triggers":
                trigger_event = plugin.detect_triggers()
                response["data"] = trigger_event
                response["success"] = True
                
            elif action == "get_trigger_config":
                response["data"] = plugin.get_trigger_config()
                response["success"] = True
                
            else:
                response["error"] = f"Unknown action: {action}"
            
            print(json.dumps(response))
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            response = {"error": f"Plugin error: {str(e)}"}
            print(json.dumps(response))


if __name__ == "__main__":
    main() 