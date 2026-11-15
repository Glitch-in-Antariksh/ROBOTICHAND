
/*
  ROBOTICHAND
  Serial-controlled LED demonstration

  Command 1 -> Red LED (Pin 2)
  Command 2 -> Green LED (Pin 3)
  Command 3 -> Blue LED (Pin 4)

  Baud rate: 9600
*/

const int redLED = 2;
const int greenLED = 3;
const int blueLED = 4;

const int blinkDuration = 300;

// Store the currently selected LED
int activeLED = -1;

void setup() {

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(blueLED, OUTPUT);

  // Initially turn all LEDs OFF
  turnOffAllLEDs();

  // Start serial communication
  Serial.begin(9600);

  Serial.println("ROBOTICHAND READY");
}

void loop() {

  // Check whether Python has sent a command
  if (Serial.available() > 0) {

    char command = Serial.read();

    switch (command) {

      case '1':
        activeLED = redLED;
        Serial.println("OPEN - RED LED");
        break;

      case '2':
        activeLED = greenLED;
        Serial.println("GRIP - GREEN LED");
        break;

      case '3':
        activeLED = blueLED;
        Serial.println("POINT - BLUE LED");
        break;

      default:
        Serial.println("INVALID COMMAND");
        break;
    }
  }

  // Blink the selected LED
  if (activeLED != -1) {

    digitalWrite(activeLED, HIGH);
    delay(blinkDuration);

    digitalWrite(activeLED, LOW);
    delay(blinkDuration);
  }
}

void turnOffAllLEDs() {

  digitalWrite(redLED, LOW);
  digitalWrite(greenLED, LOW);
  digitalWrite(blueLED, LOW);
}
