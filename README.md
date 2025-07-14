# 🔌 Stavily Plugins Collection

A comprehensive collection of plugins for Stavily agents, providing monitoring, alerting, and automation capabilities.

## 📋 **Plugin Categories**

### 🔍 **Trigger Plugins** (Sensor Agents)
Monitor system conditions and generate events when thresholds are met.

| Plugin | Description | Use Cases |
|--------|-------------|-----------|
| **Memory Monitor** | Monitors RAM usage and swap utilization | Memory leak detection, capacity planning |
| **Disk Space Monitor** | Tracks disk usage across filesystems | Storage alerts, cleanup automation |
| **File Monitor** | Watches file changes, creation, deletion | Configuration monitoring, security |
| **HTTP Health Check** | Monitors web endpoints and APIs | Service health, uptime monitoring |
| **Process Monitor** | Tracks running processes and resource usage | Application monitoring, zombie detection |
| **Log Monitor** | Scans log files for error patterns | Error detection, security monitoring |

### ⚡ **Action Plugins** (Action Agents)
Perform automated actions in response to triggers.

| Plugin | Description | Use Cases |
|--------|-------------|-----------|
| **Email Notification** | Send email alerts and reports | Incident notifications, reporting |
| **Slack Notification** | Send messages to Slack channels | Team collaboration, real-time alerts |
| **File Operations** | Create, move, delete, backup files | Cleanup automation, backup tasks |
| **Shell Command** | Execute shell commands safely | System maintenance, custom scripts |
| **Docker Management** | Manage Docker containers | Container restart, scaling |
| **Database Operations** | Basic database maintenance tasks | Backups, cleanup, health checks |

## 🚀 **Quick Start**

### **Install Plugin Dependencies**
```bash
# Install common dependencies
pip install -r 06-Plugins/requirements.txt

# Install specific plugin dependencies
pip install -r 06-Plugins/triggers/memory-monitor/requirements.txt
```

### **Test a Plugin**
```bash
# Test memory monitor plugin
echo '{"action": "get_info"}' | python 06-Plugins/triggers/memory-monitor/memory_monitor.py

# Test email notification plugin
echo '{"action": "get_info"}' | python 06-Plugins/actions/email-notification/email_notification.py
```

### **Use in Agent Configuration**
```yaml
plugins:
  directory: "/opt/stavily/agent-sensor-001/data/plugins"
  auto_load: true
  allowed_plugins:
    - "memory-monitor"
    - "disk-space-monitor"
    - "file-monitor"
```

## 📁 **Directory Structure**

```
06-Plugins/
├── README.md                    # This file
├── requirements.txt             # Common dependencies
├── triggers/                    # Sensor agent plugins
│   ├── memory-monitor/          # RAM and swap monitoring
│   ├── disk-space-monitor/      # Disk usage monitoring
│   ├── file-monitor/            # File change detection
│   ├── http-health-check/       # HTTP endpoint monitoring
│   ├── process-monitor/         # Process monitoring
│   └── log-monitor/             # Log file analysis
└── actions/                     # Action agent plugins
    ├── email-notification/      # Email sending
    ├── slack-notification/      # Slack messaging
    ├── file-operations/         # File management
    ├── shell-command/           # Command execution
    ├── docker-management/       # Container management
    └── database-operations/     # Database tasks
```

## 🔧 **Plugin Development**

### **Plugin Interface**
All plugins implement a standard JSON-based communication protocol:

```python
def main():
    plugin = YourPlugin()
    
    while True:
        command = json.loads(sys.stdin.readline().strip())
        action = command.get("action")
        
        if action == "get_info":
            response = {"data": plugin.get_info(), "success": True}
        elif action == "initialize":
            response = {"success": plugin.initialize(command.get("config", {}))}
        # ... handle other actions
        
        print(json.dumps(response))
```

### **Required Methods**
Every plugin must implement:

- **`get_info()`** - Return plugin metadata
- **`initialize(config)`** - Initialize with configuration
- **`start()`** - Start plugin execution
- **`stop()`** - Stop plugin execution
- **`get_status()`** - Return current status
- **`get_health()`** - Return health information

### **Plugin Types**

#### **Trigger Plugins** (Additional Methods)
- **`detect_triggers()`** - Return trigger events
- **`get_trigger_config()`** - Return configuration schema

#### **Action Plugins** (Additional Methods)
- **`execute_action(request)`** - Execute an action
- **`get_action_config()`** - Return action schema

## 🛡️ **Security Features**

### **Sandboxing**
- Resource limits (CPU, memory, execution time)
- Filesystem access controls
- Network access restrictions
- User privilege isolation

### **Validation**
- Input parameter validation
- Configuration schema validation
- Output sanitization
- Error handling and logging

### **Demo Mode**
Most plugins support demo mode for safe testing:
```bash
export STAVILY_DEMO_MODE=true
```

## 📊 **Monitoring & Observability**

### **Health Checks**
```bash
# Check plugin health
echo '{"action": "get_health"}' | python plugin.py
```

### **Metrics**
Plugins expose Prometheus-compatible metrics:
- Execution count and duration
- Error rates and types
- Resource usage
- Custom business metrics

### **Logging**
Structured logging with:
- Timestamp and log level
- Plugin ID and version
- Request correlation IDs
- Error stack traces

## 🔗 **Integration Examples**

### **High CPU Auto-Remediation Workflow**
```yaml
triggers:
  - plugin: "memory-monitor"
    threshold: 90.0
    
actions:
  - plugin: "shell-command"
    command: "systemctl restart high-memory-service"
  - plugin: "slack-notification"
    message: "High memory service restarted"
```

### **Security Monitoring**
```yaml
triggers:
  - plugin: "file-monitor"
    paths: ["/etc/passwd", "/etc/shadow"]
    
actions:
  - plugin: "email-notification"
    subject: "Security Alert: System file modified"
  - plugin: "shell-command"
    command: "backup-system-files.sh"
```

## 📚 **Plugin Reference**

### **Configuration Schema**
Each plugin includes a comprehensive configuration schema with:
- Parameter types and validation rules
- Default values and examples
- Required vs optional parameters
- Human-readable descriptions

### **Error Handling**
Plugins follow consistent error handling patterns:
- Structured error responses
- Error classification (temporary vs permanent)
- Retry guidance
- Debugging information

### **Performance Guidelines**
- Minimize resource usage
- Implement proper cleanup
- Use async operations where appropriate
- Cache expensive operations

## 🤝 **Contributing**

### **Adding New Plugins**
1. Create plugin directory in appropriate category
2. Implement required interface methods
3. Add comprehensive tests
4. Update documentation
5. Follow security guidelines

### **Plugin Standards**
- Use meaningful error messages
- Include comprehensive logging
- Implement graceful degradation
- Support demo/simulation mode

---

**🎯 Ready to automate?** Choose plugins that fit your monitoring and automation needs, or create custom ones following our plugin development guide! 