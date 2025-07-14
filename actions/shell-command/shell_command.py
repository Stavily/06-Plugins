#!/usr/bin/env python3
"""
Shell Command Action Plugin for Stavily Action Agents

Executes shell commands safely with configurable restrictions and monitoring.
"""

import json
import os
import sys
import subprocess
import logging
import shlex
from datetime import datetime
from typing import Dict, Any, Optional, List

class ShellCommandPlugin:
    """Shell Command action plugin implementation."""
    
    def __init__(self):
        self.config = {}
        self.allowed_commands = []
        self.blocked_commands = ["rm", "rmdir", "dd", "mkfs", "fdisk", "format"]
        self.allowed_paths = ["/tmp", "/var/tmp"]
        self.timeout = 300  # 5 minutes default
        self.max_output_size = 1024 * 1024  # 1MB
        self.running = False
        self.status = "stopped"
        self.start_time = None
        self.logger = self._setup_logging()
        self.demo_mode = os.getenv("STAVILY_DEMO_MODE", "true").lower() == "true"
    
    def _setup_logging(self) -> logging.Logger:
        """Setup plugin logging."""
        logger = logging.getLogger('shell_command')
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
            "id": "shell-command",
            "name": "Shell Command",
            "description": "Executes shell commands safely with configurable restrictions",
            "version": "1.0.0",
            "author": "Stavily Team",
            "license": "MIT",
            "type": "action",
            "tags": ["system", "command", "shell", "automation", "execution"],
            "categories": ["system-management"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            
            # Command restrictions
            if "allowed_commands" in config:
                self.allowed_commands = config["allowed_commands"]
            if "blocked_commands" in config:
                self.blocked_commands = config["blocked_commands"]
            if "allowed_paths" in config:
                self.allowed_paths = config["allowed_paths"]
            
            # Execution limits
            self.timeout = int(config.get("timeout", 300))
            self.max_output_size = int(config.get("max_output_size", 1024 * 1024))
            
            # Validate configuration
            if self.timeout <= 0:
                raise ValueError("Timeout must be positive")
            if self.max_output_size <= 0:
                raise ValueError("Max output size must be positive")
            
            self.status = "initialized"
            self.logger.info(f"Shell Command initialized (demo_mode={self.demo_mode}, timeout={self.timeout}s)")
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
            self.logger.info("Shell Command plugin started")
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
            self.logger.info("Shell Command plugin stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop plugin: {e}")
            return False
    
    def get_status(self) -> str:
        """Return the current plugin status."""
        return self.status
    
    def get_health(self) -> Dict[str, Any]:
        """Return plugin health information."""
        health = {
            "status": "healthy" if self.running else "unhealthy",
            "message": "Plugin is running normally" if self.running else "Plugin is not running",
            "last_check": datetime.now().isoformat(),
            "uptime": 0,
            "error_count": 0,
            "metrics": {
                "demo_mode": self.demo_mode,
                "timeout": self.timeout,
                "max_output_size": self.max_output_size,
                "allowed_commands_count": len(self.allowed_commands),
                "blocked_commands_count": len(self.blocked_commands)
            }
        }
        
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            health["uptime"] = uptime
            
        return health
    
    def execute_action(self, action_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command action."""
        if not self.running:
            return self._create_error_result(action_request["id"], "Plugin is not running")
        
        start_time = datetime.now()
        action_id = action_request["id"]
        parameters = action_request.get("parameters", {})
        
        result = {
            "id": action_id,
            "status": "running",
            "started_at": start_time.isoformat(),
            "metadata": {
                "plugin_id": "shell-command",
                "plugin_version": "1.0.0",
                "execution_host": os.uname().nodename
            }
        }
        
        try:
            # Extract command parameters
            command = parameters.get("command", "")
            working_dir = parameters.get("working_dir", "/tmp")
            env_vars = parameters.get("env_vars", {})
            input_data = parameters.get("input", "")
            timeout = parameters.get("timeout", self.timeout)
            
            # Validate command
            if not command:
                return self._create_error_result(action_id, "Command parameter is required", start_time)
            
            validation_result = self._validate_command(command, working_dir)
            if not validation_result["valid"]:
                return self._create_error_result(action_id, validation_result["error"], start_time)
            
            # Execute command
            if self.demo_mode:
                exec_result = self._simulate_command_execution(command, working_dir, env_vars, input_data, timeout)
            else:
                exec_result = self._execute_command(command, working_dir, env_vars, input_data, timeout)
            
            if exec_result["success"]:
                result.update({
                    "status": "completed",
                    "data": {
                        "command": command,
                        "working_dir": working_dir,
                        "return_code": exec_result["return_code"],
                        "stdout": exec_result["stdout"],
                        "stderr": exec_result["stderr"],
                        "execution_time": exec_result["execution_time"],
                        "demo_mode": self.demo_mode
                    }
                })
                self.logger.info(f"Command executed successfully: {command[:50]}...")
            else:
                result.update({
                    "status": "failed",
                    "error": exec_result["error"],
                    "data": {
                        "command": command,
                        "return_code": exec_result.get("return_code"),
                        "stdout": exec_result.get("stdout", ""),
                        "stderr": exec_result.get("stderr", "")
                    }
                })
                self.logger.error(f"Command execution failed: {exec_result['error']}")
            
        except Exception as e:
            result.update({
                "status": "failed",
                "error": str(e)
            })
            self.logger.error(f"Action execution error: {e}")
        
        # Finalize result
        result.update({
            "completed_at": datetime.now().isoformat(),
            "duration": (datetime.now() - start_time).total_seconds()
        })
        
        return result
    
    def get_action_config(self) -> Dict[str, Any]:
        """Return the action configuration schema."""
        return {
            "schema": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                    "required": True,
                    "examples": ["ls -la", "ps aux | grep nginx", "systemctl status nginx"]
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory for command execution",
                    "default": "/tmp",
                    "required": False,
                    "examples": ["/tmp", "/var/log", "/home/user"]
                },
                "env_vars": {
                    "type": "object",
                    "description": "Environment variables to set",
                    "required": False,
                    "examples": [{"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "en_US.UTF-8"}]
                },
                "input": {
                    "type": "string",
                    "description": "Input data to pass to command via stdin",
                    "required": False,
                    "examples": ["yes\n", "user input data"]
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds",
                    "default": 300,
                    "required": False,
                    "minimum": 1,
                    "maximum": 3600
                }
            },
            "required": ["command"],
            "examples": [
                {
                    "command": "ls -la /var/log",
                    "working_dir": "/tmp"
                },
                {
                    "command": "systemctl status nginx",
                    "timeout": 30
                },
                {
                    "command": "grep ERROR /var/log/application.log | tail -10",
                    "working_dir": "/var/log"
                }
            ],
            "description": "Shell command execution configuration",
            "timeout": 3600
        }
    
    def _create_error_result(self, action_id: str, error: str, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Create an error result."""
        if start_time is None:
            start_time = datetime.now()
            
        return {
            "id": action_id,
            "status": "failed",
            "error": error,
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration": (datetime.now() - start_time).total_seconds(),
            "metadata": {
                "plugin_id": "shell-command",
                "plugin_version": "1.0.0"
            }
        }
    
    def _validate_command(self, command: str, working_dir: str) -> Dict[str, Any]:
        """Validate command against security restrictions."""
        try:
            # Parse command to get the main executable
            try:
                tokens = shlex.split(command)
                if not tokens:
                    return {"valid": False, "error": "Empty command"}
                
                main_command = tokens[0].split("/")[-1]  # Get basename of command
            except ValueError as e:
                return {"valid": False, "error": f"Invalid command syntax: {e}"}
            
            # Check blocked commands
            if main_command in self.blocked_commands:
                return {"valid": False, "error": f"Command '{main_command}' is blocked for security"}
            
            # Check allowed commands (if whitelist is configured)
            if self.allowed_commands and main_command not in self.allowed_commands:
                return {"valid": False, "error": f"Command '{main_command}' is not in allowed list"}
            
            # Check working directory
            if self.allowed_paths:
                allowed = any(working_dir.startswith(path) for path in self.allowed_paths)
                if not allowed:
                    return {"valid": False, "error": f"Working directory '{working_dir}' is not allowed"}
            
            # Additional security checks
            dangerous_patterns = ["rm -rf", ":(){ :|:& };:", "chmod 777", "chown root"]
            for pattern in dangerous_patterns:
                if pattern in command.lower():
                    return {"valid": False, "error": f"Command contains dangerous pattern: {pattern}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {e}"}
    
    def _execute_command(self, command: str, working_dir: str, env_vars: dict, 
                        input_data: str, timeout: int) -> Dict[str, Any]:
        """Execute actual shell command."""
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(env_vars)
            
            # Ensure working directory exists and is accessible
            if not os.path.exists(working_dir):
                return {"success": False, "error": f"Working directory does not exist: {working_dir}"}
            
            if not os.access(working_dir, os.W_OK):
                return {"success": False, "error": f"No write access to working directory: {working_dir}"}
            
            start_time = datetime.now()
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Limit output size
                if len(stdout) > self.max_output_size:
                    stdout = stdout[:self.max_output_size] + "\n... [output truncated]"
                if len(stderr) > self.max_output_size:
                    stderr = stderr[:self.max_output_size] + "\n... [output truncated]"
                
                return {
                    "success": True,
                    "return_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time
                }
                
            except subprocess.TimeoutExpired:
                process.kill()
                return {"success": False, "error": f"Command timed out after {timeout} seconds"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _simulate_command_execution(self, command: str, working_dir: str, env_vars: dict,
                                  input_data: str, timeout: int) -> Dict[str, Any]:
        """Simulate command execution for demo mode."""
        import time
        import random
        
        # Simulate execution time
        sim_time = random.uniform(0.1, 2.0)
        time.sleep(sim_time)
        
        # Generate simulated output based on command
        stdout = ""
        stderr = ""
        return_code = 0
        
        if "ls" in command:
            stdout = "file1.txt\nfile2.log\ndirectory1/\ntotal 4"
        elif "ps" in command:
            stdout = "PID   USER     TIME  COMMAND\n1234  root     0:01  nginx\n5678  app      0:05  python app.py"
        elif "systemctl" in command:
            if "status" in command:
                stdout = "● nginx.service - The nginx HTTP server\n   Loaded: loaded (/lib/systemd/system/nginx.service; enabled)\n   Active: active (running)"
            else:
                stdout = "Service operation completed successfully"
        elif "grep" in command:
            stdout = "2024-01-15 10:30:25 ERROR: Connection timeout\n2024-01-15 10:31:15 ERROR: Database unavailable"
        elif "df" in command:
            stdout = "Filesystem     1K-blocks    Used Available Use%\n/dev/sda1       10485760 5242880   5242880  50% /"
        else:
            stdout = f"Simulated output for command: {command}"
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% error rate
            return_code = 1
            stderr = f"Simulated error for command: {command}"
        
        self.logger.info(f"DEMO: Command executed: {command}")
        self.logger.info(f"DEMO: Working dir: {working_dir}")
        self.logger.info(f"DEMO: Return code: {return_code}")
        if stdout:
            self.logger.info(f"DEMO: STDOUT ({len(stdout)} chars): {stdout[:100]}...")
        if stderr:
            self.logger.info(f"DEMO: STDERR: {stderr}")
        
        return {
            "success": return_code == 0,
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": sim_time,
            "error": stderr if return_code != 0 else ""
        }


def main():
    """Main plugin entry point."""
    plugin = ShellCommandPlugin()
    
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
                
            elif action == "execute_action":
                action_request = command.get("action_request", {})
                response["data"] = plugin.execute_action(action_request)
                response["success"] = True
                
            elif action == "get_action_config":
                response["data"] = plugin.get_action_config()
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