/*
 * MCP Button Monitor - Arduino Sketch
 * 
 * This sketch implements the button monitoring functionality for the MCP demonstration project.
 * It reads button state and communicates with the Python MCP server via serial.
 * 
 * Hardware Setup:
 * - Button connected to pin 2 with internal pull-up resistor
 * - Button connects pin 2 to ground when pressed
 * 
 * Serial Commands:
 * - STATE\n     -> Returns current button state (0 or 1)
 * - SUBSCRIBE\n -> Starts streaming button edge events
 * - UNSUBSCRIBE\n -> Stops streaming events
 * 
 * Event Format:
 * - RISING\n   -> Button pressed (0->1 transition)
 * - FALLING\n  -> Button released (1->0 transition)
 */

// Pin configuration
const int BUTTON_PIN = 2;
const int DEBOUNCE_DELAY = 50; // milliseconds

// Button state variables
int buttonState = HIGH;        // Current button state (HIGH = not pressed due to pull-up)
int lastButtonState = HIGH;    // Previous button state
int lastDebounceTime = 0;     // Last time button state changed
bool streaming = false;        // Whether we're streaming events

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Configure button pin with internal pull-up resistor
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Initial button state
  buttonState = digitalRead(BUTTON_PIN);
  lastButtonState = buttonState;
}

void loop() {
  // Read button state
  int reading = digitalRead(BUTTON_PIN);
  
  // Check if button state has changed
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  // Wait for debounce period to end
  if ((millis() - lastDebounceTime) > DEBOUNCE_DELAY) {
    // Button state has been stable for debounce period
    if (reading != buttonState) {
      buttonState = reading;
      
      // If streaming is enabled, send edge events
      if (streaming) {
        if (buttonState == LOW) {  // Button pressed (HIGH -> LOW due to pull-up)
          Serial.println("RISING");
        } else {                    // Button released (LOW -> HIGH due to pull-up)
          Serial.println("FALLING");
        }
      }
    }
  }
  
  // Store button state for next comparison
  lastButtonState = reading;
  
  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "STATE") {
      // Return current button state (inverted due to pull-up logic)
      Serial.println(buttonState == LOW ? "1" : "0");
    }
    else if (command == "SUBSCRIBE") {
      streaming = true;
      Serial.println("OK");
    }
    else if (command == "UNSUBSCRIBE") {
      streaming = false;
      Serial.println("OK");
    }
  }
}
