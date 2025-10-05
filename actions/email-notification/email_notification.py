#!/usr/bin/env python3
"""
Email Notification Action Plugin for Stavily Action Agents

Sends email notifications for alerts, reports, and automation updates.
"""

import json
import os
import sys
import smtplib
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Email modules
try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
    from email.mime.base import MIMEBase as MimeBase
    from email import encoders
except ImportError:
    # Fallback for older Python versions
    from email.MIMEText import MIMEText as MimeText
    from email.MIMEMultipart import MIMEMultipart as MimeMultipart
    from email.MIMEBase import MIMEBase as MimeBase
    from email import Encoders as encoders

class EmailNotificationPlugin:
    """Email Notification action plugin implementation."""
    
    def __init__(self):
        self.config = {}
        self.smtp_server = ""
        self.smtp_port = 587
        self.username = ""
        self.password = ""
        self.from_email = ""
        self.use_tls = True
        self.running = False
        self.status = "stopped"
        self.start_time = None
        self.logger = self._setup_logging()
        self.demo_mode = os.getenv("STAVILY_DEMO_MODE", "true").lower() == "true"
    
    def _setup_logging(self) -> logging.Logger:
        """Setup plugin logging."""
        logger = logging.getLogger('email_notification')
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
            "id": "email-notification",
            "name": "Email Notification",
            "description": "Sends email notifications for alerts, reports, and automation updates",
            "version": "1.0.0",
            "author": "Stavily Team",
            "license": "MIT",
            "type": "action",
            "tags": ["notification", "email", "alert", "communication"],
            "categories": ["communication"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        try:
            self.config = config
            
            # SMTP configuration
            self.smtp_server = config.get("smtp_server", "")
            self.smtp_port = int(config.get("smtp_port", 587))
            self.username = config.get("username", "")
            self.password = config.get("password", "")
            self.from_email = config.get("from_email", self.username)
            self.use_tls = config.get("use_tls", True)
            
            # Validate required configuration in non-demo mode
            if not self.demo_mode:
                if not all([self.smtp_server, self.username, self.password, self.from_email]):
                    raise ValueError("SMTP server, username, password, and from_email are required")
            
            self.status = "initialized"
            self.logger.info(f"Email Notification initialized (demo_mode={self.demo_mode})")
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
            self.logger.info("Email Notification plugin started")
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
            self.logger.info("Email Notification plugin stopped")
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
                "smtp_server": self.smtp_server if not self.demo_mode else "demo-smtp-server",
                "smtp_port": self.smtp_port,
                "from_email": self.from_email if not self.demo_mode else "demo@example.com"
            }
        }
        
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            health["uptime"] = uptime
            
        return health
    
    def execute_action(self, action_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an email notification action."""
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
                "plugin_id": "email-notification",
                "plugin_version": "1.0.0",
                "execution_host": os.uname().nodename
            }
        }
        
        try:
            # Extract email parameters
            to_emails = parameters.get("to", [])
            cc_emails = parameters.get("cc", [])
            bcc_emails = parameters.get("bcc", [])
            subject = parameters.get("subject", "Stavily Notification")
            body = parameters.get("body", "")
            html_body = parameters.get("html_body", "")
            attachments = parameters.get("attachments", [])
            
            # Validate parameters
            if not to_emails:
                return self._create_error_result(action_id, "At least one recipient email is required", start_time)
            
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            if isinstance(cc_emails, str):
                cc_emails = [cc_emails]
            if isinstance(bcc_emails, str):
                bcc_emails = [bcc_emails]
            
            # Send email
            if self.demo_mode:
                email_result = self._simulate_email_send(to_emails, cc_emails, bcc_emails, subject, body, html_body, attachments)
            else:
                email_result = self._send_email(to_emails, cc_emails, bcc_emails, subject, body, html_body, attachments)
            
            if email_result["success"]:
                result.update({
                    "status": "completed",
                    "data": {
                        "recipients": to_emails,
                        "cc": cc_emails,
                        "bcc": bcc_emails,
                        "subject": subject,
                        "message_id": email_result.get("message_id"),
                        "attachments_count": len(attachments),
                        "demo_mode": self.demo_mode
                    }
                })
                self.logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            else:
                result.update({
                    "status": "failed",
                    "error": email_result["error"],
                    "data": {
                        "recipients": to_emails,
                        "subject": subject
                    }
                })
                self.logger.error(f"Failed to send email: {email_result['error']}")
            
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
                "to": {
                    "type": ["string", "array"],
                    "description": "Recipient email address(es)",
                    "required": True,
                    "examples": ["user@example.com", ["user1@example.com", "user2@example.com"]]
                },
                "cc": {
                    "type": ["string", "array"],
                    "description": "CC email address(es)",
                    "required": False,
                    "examples": ["cc@example.com"]
                },
                "bcc": {
                    "type": ["string", "array"],
                    "description": "BCC email address(es)",
                    "required": False,
                    "examples": ["bcc@example.com"]
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                    "required": True,
                    "max_length": 200,
                    "examples": ["Alert: High CPU Usage", "System Maintenance Complete"]
                },
                "body": {
                    "type": "string",
                    "description": "Plain text email body",
                    "required": False,
                    "examples": ["CPU usage has exceeded 90% on server-01"]
                },
                "html_body": {
                    "type": "string",
                    "description": "HTML email body (optional)",
                    "required": False,
                    "examples": ["<h1>Alert</h1><p>CPU usage high</p>"]
                },
                "attachments": {
                    "type": "array",
                    "description": "List of file paths to attach",
                    "required": False,
                    "items": {"type": "string"},
                    "examples": [["/tmp/report.pdf", "/tmp/logs.txt"]]
                }
            },
            "required": ["to", "subject"],
            "examples": [
                {
                    "to": "admin@example.com",
                    "subject": "High Memory Usage Alert",
                    "body": "Memory usage on server-01 has exceeded 85%"
                },
                {
                    "to": ["admin@example.com", "ops@example.com"],
                    "cc": "manager@example.com",
                    "subject": "System Maintenance Report",
                    "html_body": "<h2>Maintenance Complete</h2><p>All systems operational</p>",
                    "attachments": ["/tmp/maintenance-report.pdf"]
                }
            ],
            "description": "Email notification configuration",
            "timeout": 60
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
                "plugin_id": "email-notification",
                "plugin_version": "1.0.0"
            }
        }
    
    def _send_email(self, to_emails: list, cc_emails: list, bcc_emails: list, 
                   subject: str, body: str, html_body: str, attachments: list) -> Dict[str, Any]:
        """Send actual email via SMTP."""
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            msg['Subject'] = subject
            
            # Add text body
            if body:
                text_part = MimeText(body, 'plain')
                msg.attach(text_part)
            
            # Add HTML body
            if html_body:
                html_part = MimeText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            for attachment_path in attachments:
                if os.path.isfile(attachment_path):
                    with open(attachment_path, "rb") as attachment:
                        part = MimeBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(attachment_path)}'
                        )
                        msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            
            all_recipients = to_emails + cc_emails + bcc_emails
            text = msg.as_string()
            server.sendmail(self.from_email, all_recipients, text)
            server.quit()
            
            return {
                "success": True,
                "message_id": msg.get('Message-ID', '')
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _simulate_email_send(self, to_emails: list, cc_emails: list, bcc_emails: list,
                           subject: str, body: str, html_body: str, attachments: list) -> Dict[str, Any]:
        """Simulate email sending for demo mode."""
        import time
        time.sleep(0.5)  # Simulate network delay
        
        # Simulate occasional failure for testing
        import random
        if random.random() < 0.05:  # 5% failure rate
            return {
                "success": False,
                "error": "Simulated SMTP connection timeout (demo mode)"
            }
        
        message_id = f"<demo-{int(time.time())}-{random.randint(1000, 9999)}@stavily-demo>"
        
        self.logger.info(f"DEMO: Email would be sent:")
        self.logger.info(f"  To: {', '.join(to_emails)}")
        if cc_emails:
            self.logger.info(f"  CC: {', '.join(cc_emails)}")
        if bcc_emails:
            self.logger.info(f"  BCC: {', '.join(bcc_emails)}")
        self.logger.info(f"  Subject: {subject}")
        self.logger.info(f"  Body length: {len(body)} chars")
        if html_body:
            self.logger.info(f"  HTML body length: {len(html_body)} chars")
        if attachments:
            self.logger.info(f"  Attachments: {len(attachments)} files")
        
        return {
            "success": True,
            "message_id": message_id
        }


def main():
    """Main plugin entry point."""
    plugin = EmailNotificationPlugin()
    
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
    print("this has worked")
    print(f"Executed at {datetime.now()}")
    return(0)
    main() 
