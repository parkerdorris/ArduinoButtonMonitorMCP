# 🔌 Arduino Setup Guide

Complete guide to setting up your Arduino for button monitoring.

## 📋 Required Components

- **Arduino Board** (Uno, Nano, MKR WiFi 1010, etc.)
- **Push Button** (momentary switch)
- **Breadboard** (optional, for easier wiring)
- **Jumper Wires** (2-3 pieces)
- **USB Cable** (Type A to Type B for Uno, Type C for MKR)

## 🔧 Hardware Connection

### Simple Connection (No Breadboard)
```
Arduino Pin 2 ←→ Button Pin 1
Arduino GND  ←→ Button Pin 2
```

### With Breadboard
```
Arduino Pin 2 → Breadboard → Button Pin 1
Arduino GND  → Breadboard → Button Pin 2
```

### Visual Diagram
```
Arduino Uno
┌─────────────┐
│             │
│  Pin 2 ────┼─── Button Pin 1
│             │    ┌───┐
│  GND   ────┼────┤   ├─── Button Pin 2
│             │    └───┘
└─────────────┘
```

## 💻 Software Setup

### 1. Install Arduino IDE
- Download from [arduino.cc](https://www.arduino.cc/en/software)
- Install for your operating system

### 2. Open the Sketch
- Launch Arduino IDE
- Open `button_monitor.ino`
- Select your board type:
  - **Arduino Uno**: Tools → Board → Arduino AVR Boards → Arduino Uno
  - **Arduino Nano**: Tools → Board → Arduino AVR Boards → Arduino Nano
  - **MKR WiFi 1010**: Tools → Board → Arduino SAMD Boards → Arduino MKR WiFi 1010

### 3. Select Port
- Connect Arduino via USB
- Tools → Port → Select your Arduino port:
  - **Windows**: `COM3`, `COM4`, etc.
  - **macOS**: `/dev/cu.usbmodem*` or `/dev/cu.usbserial*`
  - **Linux**: `/dev/ttyUSB0` or `/dev/ttyACM0`

### 4. Upload Code
- Click the **Upload** button (→) or press `Ctrl+U` (`Cmd+U` on Mac)
- Wait for "Upload complete" message

## 🧪 Testing the Setup

### 1. Open Serial Monitor
- Tools → Serial Monitor
- Set baud rate to **9600**
- You should see initial button state

### 2. Test Button
- Press and release the button
- You should see:
  ```
  RISING
  FALLING
  ```

### 3. Test Commands
Type these commands in Serial Monitor:
- `STATE` → Returns current button state (0 or 1)
- `SUBSCRIBE` → Starts streaming events
- `UNSUBSCRIBE` → Stops streaming events

## 🔍 Troubleshooting

### Button Not Responding?
1. **Check wiring** - Ensure button is connected to pin 2 and GND
2. **Verify pin mode** - Code uses `INPUT_PULLUP` (internal pull-up resistor)
3. **Test continuity** - Use multimeter to check button connections
4. **Try different button** - Some buttons may be faulty

### Serial Communication Issues?
1. **Check baud rate** - Must be 9600
2. **Verify port selection** - Select correct COM port
3. **Restart Arduino IDE** - Sometimes needed after port changes
4. **Check USB cable** - Try different cable

### Upload Fails?
1. **Check board selection** - Must match your Arduino model
2. **Verify port selection** - Arduino must be connected
3. **Check drivers** - Install Arduino drivers if needed
4. **Restart Arduino** - Unplug and reconnect USB

## 🎯 Advanced Configuration

### Change Button Pin
Edit `button_monitor.ino`:
```cpp
// Change from pin 2 to any other digital pin
const int BUTTON_PIN = 3;  // or 4, 5, 6, etc.
```

### Adjust Debounce Delay
```cpp
// Increase for noisy buttons, decrease for faster response
const int DEBOUNCE_DELAY = 100;  // milliseconds
```

### Add LED Indicator
```cpp
const int LED_PIN = 13;  // Built-in LED on most boards

void setup() {
  pinMode(LED_PIN, OUTPUT);
  // ... existing code ...
}

void loop() {
  // ... existing code ...
  
  // Light LED when button is pressed
  digitalWrite(LED_PIN, buttonState == LOW ? HIGH : LOW);
}
```

## 📱 Mobile Testing

### Arduino IoT Remote
- Install "Arduino IoT Remote" app
- Connect to your Arduino
- Monitor button state remotely

### Bluetooth Module (HC-05/HC-06)
- Connect to Arduino's hardware serial
- Monitor button state via Bluetooth
- Requires modified code for dual communication

## 🔒 Safety Notes

- **Voltage**: Arduino operates at 5V - safe for human contact
- **Current**: Limited to 40mA per pin - safe for most components
- **ESD**: Handle Arduino by edges, avoid touching pins
- **Power**: Use USB power or regulated 5V supply

## 📚 Next Steps

1. **Test with Python server** - Run `mcp_websocket_server.py`
2. **Add more sensors** - Temperature, humidity, motion, etc.
3. **Create custom commands** - Add your own serial commands
4. **Build enclosure** - 3D print or build case for your project

---

**Need help? Check the main troubleshooting guide or open an issue! 🆘**
