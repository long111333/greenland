#include "SafetyManager.h"
void SafetyManager::update(SortingController& sorter,ServoController& gate,StepperController& stepper,ColorSensor& color,SerialProtocol& serial) {
 if(sorter.state()==SortingState::ERROR) return;
 Error error=Error::NONE;
 if(serial.overflowed()) error=Error::TX_OVERFLOW;
 else if((sorter.busy() || sorter.homed()) && millis()-serial.lastContact()>=Config::LINK_TIMEOUT_MS) error=Error::LINK_LOST;
 else if(stepper.isMoving() && !gate.isClosed()) error=Error::GATE_UNSAFE;
 else if(stepper.timedOut()) error=sorter.state()==SortingState::HOMING ? Error::HOME_TIMEOUT : Error::POSITION_TIMEOUT;
 else if(sorter.needsColor() && !color.isSensorHealthy()) error=Error::COLOR_SENSOR;
 if(error!=Error::NONE) sorter.fault(error);
}
