#!/usr/bin/env python3
"""
Arduino Connection Manager

This module provides the ArduinoConnectionManager class for handling serial communication
with Arduino devices. It's used by the MCP WebSocket server.
"""

import logging
import serial
import serial.tools.list_ports
import time
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ArduinoConnectionManager:
    """Manages Arduino serial connection and communication."""
    
    def __init__(self):
        self.serial_port: Optional[serial.Serial] = None
        self.connected = False
        self.port_name: Optional[str] = None
        self.baud_rate = 9600
        self.timeout = 1.0
        self.last_heartbeat = 0
        self.heartbeat_interval = 5.0  # seconds
        
    def list_available_ports(self) -> list:
        """List all available serial ports."""
        try:
            ports = list(serial.tools.list_ports.comports())
            logger.info(f"Available serial ports: {[port.device for port in ports]}")
            return ports
        except Exception as e:
            logger.error(f"Error listing serial ports: {e}")
            return []
    
    def auto_detect_arduino(self) -> Optional[str]:
        """Auto-detect Arduino port."""
        ports = self.list_available_ports()
        
        for port in ports:
            # Look for Arduino identifiers
            if any(identifier in port.description.lower() for identifier in 
                   ['arduino', 'mkr', 'wifi', '1010', 'samd', 'usbmodem']):
                logger.info(f"Auto-detected Arduino port: {port.device}")
                return port.device
        
        logger.warning("No Arduino port auto-detected")
        return None
    
    def connect(self, port_name: Optional[str] = None) -> bool:
        """Connect to Arduino on specified or auto-detected port."""
        try:
            if self.connected:
                self.disconnect()
            
            if port_name is None:
                port_name = self.auto_detect_arduino()
            
            if port_name is None:
                logger.error("No Arduino port available")
                return False
            
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )
            
            # Wait for Arduino to reset
            time.sleep(2)
            
            # Test communication
            if self.test_communication():
                self.port_name = port_name
                self.connected = True
                self.last_heartbeat = time.time()
                logger.info(f"Successfully connected to Arduino on {port_name}")
                return True
            else:
                self.disconnect()
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Disconnect from Arduino."""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
        self.connected = False
        self.port_name = None
        logger.info("Disconnected from Arduino")
    
    def test_communication(self) -> bool:
        """Test communication with Arduino."""
        try:
            if not self.serial_port or not self.serial_port.is_open:
                return False
            
            # Send a test command and wait for response
            self.serial_port.write(b"STATE\n")
            time.sleep(0.1)
            
            if self.serial_port.in_waiting > 0:
                response = self.serial_port.readline().decode().strip()
                logger.info(f"Arduino communication test successful")
                return True
            else:
                logger.warning("Arduino communication test failed - no response")
                return False
                
        except Exception as e:
            logger.error(f"Arduino communication test failed: {e}")
            return False
    
    def check_connection_health(self) -> bool:
        """Check if Arduino connection is still healthy."""
        if not self.connected or not self.serial_port or not self.serial_port.is_open:
            return False
        
        current_time = time.time()
        if current_time - self.last_heartbeat > self.heartbeat_interval:
            # Try to get button state as a heartbeat
            if self.send_command("STATE"):
                response = self.read_response()
                if response and response.isdigit():
                    self.last_heartbeat = current_time
                    return True
                else:
                    logger.warning("Arduino heartbeat failed - invalid response")
                    return False
            else:
                logger.warning("Arduino heartbeat failed - command failed")
                return False
        
        return True
    
    def send_command(self, command: str) -> bool:
        """Send a command to Arduino."""
        try:
            if not self.connected or not self.serial_port or not self.serial_port.is_open:
                logger.error("Arduino not connected")
                return False
            
            # Clear any pending input
            self.serial_port.reset_input_buffer()
            
            # Send command with newline
            command_bytes = f"{command}\n".encode()
            self.serial_port.write(command_bytes)
            self.serial_port.flush()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command '{command}': {e}")
            return False
    
    def read_response(self) -> Optional[str]:
        """Read response from Arduino."""
        try:
            if not self.connected or not self.serial_port or not self.serial_port.is_open:
                return None
            
            # Wait for response
            time.sleep(0.1)
            
            if self.serial_port.in_waiting > 0:
                response = self.serial_port.readline().decode().strip()
                return response
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to read response: {e}")
            return None
