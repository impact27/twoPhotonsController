String inputString = "";         // a String to hold incoming data
boolean stringComplete = false;  // whether the string is complete
int ledPin = 13; 

void setup() {
  // initialize serial:
  Serial.begin(9600);
  // reserve 200 bytes for the inputString:
  inputString.reserve(200);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // print the string when a newline arrives:
  if (stringComplete) {
    
    // clear the string:
    inputString = "";
    stringComplete = false;
  }
}

/*
  SerialEvent occurs whenever a new data comes in the hardware serial RX. This
  routine is run between each time loop() runs, so using delay inside loop can
  delay response. Multiple bytes of data may be available.
*/
void serialEvent() {
  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    // add it to the inputString:
    inputString += inChar;
    // if the incoming character is a newline, set a flag so the main loop can
    // do something about it:
    if (inChar == '\n') {
      if (inputString == "ON\n") {
        
          digitalWrite(ledPin, HIGH);
      }
      if (inputString == "OFF\n") {
          digitalWrite(ledPin, LOW);
      }
      stringComplete = true;
    }
  }
}
