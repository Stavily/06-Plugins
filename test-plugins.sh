#!/bin/bash

# Test script for Stavily plugins
# Tests all plugins in demo mode to verify they work correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}🔌 Stavily Plugin Test Suite${NC}"
echo "=================================="
echo

# Ensure demo mode is enabled
export STAVILY_DEMO_MODE=true

# Function to test a plugin
test_plugin() {
    local plugin_path="$1"
    local plugin_name="$2"
    local plugin_type="$3"
    
    echo -e "${YELLOW}Testing $plugin_name ($plugin_type)...${NC}"
    
    if [ ! -f "$plugin_path" ]; then
        echo -e "${RED}❌ Plugin file not found: $plugin_path${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    # Test get_info
    local info_result
    info_result=$(echo '{"action": "get_info"}' | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$info_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ get_info${NC}"
    else
        echo -e "  ${RED}✗ get_info failed${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    # Test initialize
    local init_result
    init_result=$(echo '{"action": "initialize", "config": {}}' | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$init_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ initialize${NC}"
    else
        echo -e "  ${RED}✗ initialize failed${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    # Test start
    local start_result
    start_result=$(echo '{"action": "start"}' | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$start_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ start${NC}"
    else
        echo -e "  ${RED}✗ start failed${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    # Test get_health
    local health_result
    health_result=$(echo '{"action": "get_health"}' | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$health_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ get_health${NC}"
    else
        echo -e "  ${RED}✗ get_health failed${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    # Type-specific tests
    if [ "$plugin_type" = "trigger" ]; then
        # Test detect_triggers
        local triggers_result
        triggers_result=$(echo '{"action": "detect_triggers"}' | python3 "$plugin_path" 2>/dev/null)
        
        if [[ $? -eq 0 && "$triggers_result" == *"\"success\": true"* ]]; then
            echo -e "  ${GREEN}✓ detect_triggers${NC}"
        else
            echo -e "  ${RED}✗ detect_triggers failed${NC}"
            ((TESTS_FAILED++))
            return
        fi
        
        # Test get_trigger_config
        local config_result
        config_result=$(echo '{"action": "get_trigger_config"}' | python3 "$plugin_path" 2>/dev/null)
        
        if [[ $? -eq 0 && "$config_result" == *"\"success\": true"* ]]; then
            echo -e "  ${GREEN}✓ get_trigger_config${NC}"
        else
            echo -e "  ${RED}✗ get_trigger_config failed${NC}"
            ((TESTS_FAILED++))
            return
        fi
        
    elif [ "$plugin_type" = "action" ]; then
        # Test get_action_config
        local config_result
        config_result=$(echo '{"action": "get_action_config"}' | python3 "$plugin_path" 2>/dev/null)
        
        if [[ $? -eq 0 && "$config_result" == *"\"success\": true"* ]]; then
            echo -e "  ${GREEN}✓ get_action_config${NC}"
        else
            echo -e "  ${RED}✗ get_action_config failed${NC}"
            ((TESTS_FAILED++))
            return
        fi
    fi
    
    # Test stop
    local stop_result
    stop_result=$(echo '{"action": "stop"}' | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$stop_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ stop${NC}"
    else
        echo -e "  ${RED}✗ stop failed${NC}"
        ((TESTS_FAILED++))
        return
    fi
    
    echo -e "  ${GREEN}✅ All tests passed for $plugin_name${NC}"
    ((TESTS_PASSED++))
    echo
}

# Function to test action execution
test_action_execution() {
    local plugin_path="$1"
    local plugin_name="$2"
    local test_request="$3"
    
    echo -e "${YELLOW}Testing $plugin_name action execution...${NC}"
    
    # Initialize and start plugin first
    echo '{"action": "initialize", "config": {}}' | python3 "$plugin_path" >/dev/null 2>&1
    echo '{"action": "start"}' | python3 "$plugin_path" >/dev/null 2>&1
    
    # Test action execution
    local exec_result
    exec_result=$(echo "$test_request" | python3 "$plugin_path" 2>/dev/null)
    
    if [[ $? -eq 0 && "$exec_result" == *"\"success\": true"* ]]; then
        echo -e "  ${GREEN}✓ Action execution${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "  ${RED}✗ Action execution failed${NC}"
        echo "  Result: $exec_result"
        ((TESTS_FAILED++))
    fi
    echo
}

echo -e "${BLUE}Testing Trigger Plugins${NC}"
echo "------------------------"

# Test Memory Monitor
test_plugin "triggers/memory-monitor/memory_monitor.py" "Memory Monitor" "trigger"

# Test Disk Space Monitor  
test_plugin "triggers/disk-space-monitor/disk_space_monitor.py" "Disk Space Monitor" "trigger"

echo -e "${BLUE}Testing Action Plugins${NC}"
echo "-----------------------"

# Test Email Notification
test_plugin "actions/email-notification/email_notification.py" "Email Notification" "action"

# Test Shell Command
test_plugin "actions/shell-command/shell_command.py" "Shell Command" "action"

echo -e "${BLUE}Testing Action Executions${NC}"
echo "--------------------------"

# Test email action execution
test_action_execution "actions/email-notification/email_notification.py" "Email Notification" '{
    "action": "execute_action",
    "action_request": {
        "id": "test-email-001",
        "parameters": {
            "to": "admin@example.com",
            "subject": "Test Alert",
            "body": "This is a test email from Stavily plugins"
        }
    }
}'

# Test shell command execution
test_action_execution "actions/shell-command/shell_command.py" "Shell Command" '{
    "action": "execute_action", 
    "action_request": {
        "id": "test-cmd-001",
        "parameters": {
            "command": "ls -la",
            "working_dir": "/tmp"
        }
    }
}'

echo -e "${BLUE}Test Summary${NC}"
echo "============="
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All plugin tests passed!${NC}"
    echo -e "${GREEN}✅ All plugins are working correctly in demo mode${NC}"
    exit 0
else
    echo -e "${RED}❌ Some plugin tests failed${NC}"
    echo -e "${YELLOW}💡 Check plugin implementations and dependencies${NC}"
    exit 1
fi 