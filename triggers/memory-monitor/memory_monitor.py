#!/usr/bin/env python3
"""
Memory Monitor Trigger Plugin for Stavily Sensor Agents

Monitors RAM and swap usage, triggering alerts when thresholds are exceeded.
"""

import json
import os
import sys
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class MemoryMonitorPlugin:
    """Memory Monitor trigger plugin implementation."""
    
    def __init__(self):
        self.config = {}
        self.memory_threshold = 85.0
        self.swap_threshold = 90.0
        self.interval = 60
        self.running = False
        self.status = "stopped"
        self.start_time = None
        self.logger = self._setup_logging()
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between same type alerts
    
    def _setup_logging(self) -> logging.Logger:
        """Setup plugin logging."""
        logger = logging.getLogger('memory_monitor')
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
            "id": "memory-monitor",
            "name": "Memory Monitor",
            "description": "Monitors RAM and swap usage with configurable thresholds",
            "version": "1.0.0",
            "author": "Stavily Team",
            "license": "MIT",
            "type": "trigger",
            "tags": ["system", "monitoring", "memory", "ram", "swap"],
            "categories": ["system-monitoring"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            self.memory_threshold = float(config.get("memory_threshold", 85.0))
            self.swap_threshold = float(config.get("swap_threshold", 90.0))
            self.interval = int(config.get("interval", 60))
            self.alert_cooldown = int(config.get("alert_cooldown", 300))
            
            # Validate configuration
            if not (0 <= self.memory_threshold <= 100):
                raise ValueError("Memory threshold must be between 0 and 100")
            if not (0 <= self.swap_threshold <= 100):
                raise ValueError("Swap threshold must be between 0 and 100")
            if self.interval < 1:
                raise ValueError("Interval must be at least 1 second")
                
            self.status = "initialized"
            self.logger.info(f"Memory Monitor initialized: memory={self.memory_threshold}%, swap={self.swap_threshold}%, interval={self.interval}s")
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
            self.logger.info("Memory Monitor plugin started")
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
            self.logger.info("Memory Monitor plugin stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop plugin: {e}")
            return False
    
    def get_status(self) -> str:
        """Return the current plugin status."""
        return self.status
    
    def get_health(self) -> Dict[str, Any]:
        """Return plugin health information."""
        memory_info = self._get_memory_info()
        
        health = {
            "status": "healthy" if self.running else "unhealthy",
            "message": "Plugin is running normally" if self.running else "Plugin is not running",
            "last_check": datetime.now().isoformat(),
            "uptime": 0,
            "error_count": 0,
            "metrics": {
                "current_memory_percent": memory_info["memory_percent"],
                "current_swap_percent": memory_info["swap_percent"],
                "memory_threshold": self.memory_threshold,
                "swap_threshold": self.swap_threshold,
                "total_memory_gb": round(memory_info["total_memory"] / (1024**3), 2),
                "available_memory_gb": round(memory_info["available_memory"] / (1024**3), 2)
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
            memory_info = self._get_memory_info()
            now = datetime.now()
            
            # Check memory threshold
            if memory_info["memory_percent"] > self.memory_threshold:
                if self._should_alert("memory", now):
                    event = self._create_memory_event(memory_info, "memory")
                    self.last_alert_time["memory"] = now
                    return event
            
            # Check swap threshold
            if memory_info["swap_percent"] > self.swap_threshold:
                if self._should_alert("swap", now):
                    event = self._create_memory_event(memory_info, "swap")
                    self.last_alert_time["swap"] = now
                    return event
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting triggers: {e}")
            return None
    
    def get_trigger_config(self) -> Dict[str, Any]:
        """Return the trigger configuration schema."""
        return {
            "schema": {
                "memory_threshold": {
                    "type": "number",
                    "description": "Memory usage threshold percentage (0-100)",
                    "default": 85.0,
                    "required": False,
                    "minimum": 0.0,
                    "maximum": 100.0
                },
                "swap_threshold": {
                    "type": "number",
                    "description": "Swap usage threshold percentage (0-100)",
                    "default": 90.0,
                    "required": False,
                    "minimum": 0.0,
                    "maximum": 100.0
                },
                "interval": {
                    "type": "integer",
                    "description": "Monitoring interval in seconds",
                    "default": 60,
                    "required": False,
                    "minimum": 1,
                    "examples": [30, 60, 300]
                },
                "alert_cooldown": {
                    "type": "integer",
                    "description": "Cooldown period between alerts of same type (seconds)",
                    "default": 300,
                    "required": False,
                    "minimum": 60
                }
            },
            "required": [],
            "examples": [
                {
                    "memory_threshold": 85.0,
                    "swap_threshold": 90.0,
                    "interval": 60
                },
                {
                    "memory_threshold": 90.0,
                    "swap_threshold": 95.0,
                    "interval": 30,
                    "alert_cooldown": 600
                }
            ],
            "description": "Memory monitoring configuration"
        }
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "memory_percent": memory.percent,
            "total_memory": memory.total,
            "available_memory": memory.available,
            "used_memory": memory.used,
            "swap_percent": swap.percent,
            "total_swap": swap.total,
            "used_swap": swap.used,
            "free_swap": swap.free
        }
    
    def _should_alert(self, alert_type: str, current_time: datetime) -> bool:
        """Check if we should send an alert based on cooldown period."""
        if alert_type not in self.last_alert_time:
            return True
            
        time_since_last = (current_time - self.last_alert_time[alert_type]).total_seconds()
        return time_since_last >= self.alert_cooldown
    
    def _create_memory_event(self, memory_info: Dict[str, Any], alert_type: str) -> Dict[str, Any]:
        """Create memory trigger event."""
        event_id = f"memory-{alert_type}-{int(time.time())}"
        
        if alert_type == "memory":
            usage = memory_info["memory_percent"]
            threshold = self.memory_threshold
            event_type = "memory.high"
            severity = "critical" if usage > 95 else "high" if usage > 90 else "medium"
        else:  # swap
            usage = memory_info["swap_percent"]
            threshold = self.swap_threshold
            event_type = "swap.high"
            severity = "critical" if usage > 95 else "high"
        
        return {
            "id": event_id,
            "type": event_type,
            "source": "memory-monitor",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "alert_type": alert_type,
                "usage_percent": usage,
                "threshold": threshold,
                "memory_info": memory_info,
                "system_info": {
                    "hostname": os.uname().nodename,
                    "platform": os.uname().sysname,
                    "architecture": os.uname().machine
                }
            },
            "metadata": {
                "plugin_id": "memory-monitor",
                "plugin_version": "1.0.0",
                "hostname": os.uname().nodename
            },
            "tags": ["system", "memory", alert_type, "alert"],
            "severity": severity
        }


def main():
    """Main plugin entry point."""
    plugin = MemoryMonitorPlugin()
    
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