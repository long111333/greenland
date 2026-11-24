#pragma once
#include <Arduino.h>
#include <AccelStepper.h>
#include "protocol.h"
class StepperController {
public:
 StepperController();
 void begin(); void moveSteps(long steps); void rotateToPosition(uint8_t position);
 void update(); void stop(); bool isMoving() const { return moving_; }
 void haltAndHold();
 long stepsTaken();
 void testMove();
 MotionDiagnostics diagnostics() const { return diagnostics_; }
 void setReady(bool ready) { ready_=ready; }
 void setHoming(bool homing);
 bool timedOut() const { return timedOut_; }
private:
 AccelStepper motor_;
 bool ready_=false, moving_=false, homing_=false, timedOut_=false;
 uint32_t started_=0;
 long startedPosition_=0;
 MotionDiagnostics diagnostics_;
 uint32_t lastRunCall_=0;
};
