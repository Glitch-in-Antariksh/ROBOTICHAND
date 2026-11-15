# ROBOTICHAND

### Voice-Controlled Robotic Hand

ROBOTICHAND is a voice-controlled robotic hand project that aims to
translate spoken commands into actions for controlling a three-finger
robotic gripper.

The project brings together speech recognition, embedded systems,
mechanical design, and robotic simulation.

## Project Structure

``` text
ROBOTICHAND/
├── Documents/
├── Mechanical/
├── Microcontroller_implementation/
├── Simulations/
└── VoiceIP_SerialCommand/
```

## Work Completed

### Python Voice Recognition

The Python application runs on a laptop and uses the laptop microphone
to capture voice input.

-   Implemented offline speech recognition using **Vosk**.
-   Integrated microphone input using Python.
-   Developed command classification for three commands:
    -   **OPEN** --- Command ID `1`
    -   **GRIP** --- Command ID `2`
    -   **POINT** --- Command ID `3`
-   Successfully tested voice recognition and command classification.

## Current Workflow

1.  Capture voice input through the laptop microphone.
2.  Recognize the spoken command using Vosk.
3.  Classify the recognized text as OPEN, GRIP, or POINT.
4.  Assign the corresponding command ID.

## Next Phase

### Serial Communication with Arduino

The next phase is to implement serial output from the Python application
and transmit the identified command ID to an Arduino microcontroller.

For the initial demonstration, the Arduino will receive the command and
activate the corresponding LED:

-   OPEN --- LED 1
-   GRIP --- LED 2
-   POINT --- LED 3

Servo control and integration with the physical gripper can be developed
in subsequent stages.

## Planned Development

-   **Microcontroller implementation:** Receive serial commands and
    control LEDs, followed by servo actuation.
-   **Mechanical design:** Finalize the three-finger gripper model.
-   **Simulation:** Import the gripper model into MATLAB/Simulink and
    configure its joints and actuators.

## Technology Stack

-   **Python** --- Voice processing and command classification
-   **Vosk** --- Offline speech recognition
-   **Arduino** --- Microcontroller and actuator control
-   **MATLAB / Simulink** --- Robotic modelling and simulation
-   **Git / GitHub** --- Version control

## Project Status

**Completed:** Laptop-based offline voice recognition and classification
of OPEN, GRIP, and POINT commands.

**Next milestone:** Establish serial communication between Python and
Arduino, and demonstrate the three commands using LEDs.

------------------------------------------------------------------------

This repository contains the software, microcontroller implementation,
mechanical design, and simulation components of the ROBOTICHAND project.
