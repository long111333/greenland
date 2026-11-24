#include "StepperController.h"
#include "config.h"
#include "pins.h"
StepperController::StepperController():motor_(AccelStepper::HALF4WIRE,Pins::IN1,Pins::IN3,Pins::IN2,Pins::IN4,false) {}
void StepperController::begin() {
 ready_=moving_=homing_=timedOut_=false;
 motor_.setMaxSpeed(Config::STEPPER_SPEED); motor_.setAcceleration(Config::STEPPER_ACCEL);
 motor_.disableOutputs();
 diagnostics_=MotionDiagnostics{};
}
void StepperController::setHoming(bool homing) {
 homing_=homing; motor_.setMaxSpeed(homing ? Config::HOME_SPEED : Config::TARGET_SEARCH_SPEED);
 diagnostics_.nominalIntervalUs=1000000UL/(homing ? Config::HOME_SPEED : Config::TARGET_SEARCH_SPEED);
}
void StepperController::moveSteps(long steps) {
 if (!ready_ || moving_ || steps>Config::SEARCH_STEPS || steps < -Config::SEARCH_STEPS) return;
 timedOut_=false;
 // Rebase without changing the half-step phase; avoid a phase jump on resume.
 motor_.setCurrentPosition(motor_.currentPosition() & 7L);
 startedPosition_=motor_.currentPosition(); motor_.move(steps);
 motor_.enableOutputs(); started_=millis(); moving_=steps!=0;
 diagnostics_.runCalls=diagnostics_.emittedSteps=diagnostics_.maxRunGapUs=0;
 diagnostics_.moving=moving_; lastRunCall_=micros();
}
void StepperController::testMove() {
 homing_=false;
 motor_.setMaxSpeed(Config::STEPPER_SPEED);
 diagnostics_.nominalIntervalUs=1000000UL/Config::STEPPER_SPEED;
 moveSteps(Config::TEST_STEPPER_STEPS);
}
void StepperController::rotateToPosition(uint8_t target) {
 if (target<1 || target>4) return;
 // Search a bounded arc, independent of marker spacing/order. The color sensor
 // stops this move at the target; the controller must still verify while stopped.
 setHoming(false);
 moveSteps(Config::SORT_DIRECTION*Config::SEARCH_STEPS);
}
void StepperController::update() {
 if (!moving_) return;
 uint32_t now=micros();
 uint32_t gap=now-lastRunCall_; lastRunCall_=now;
 if(gap>diagnostics_.maxRunGapUs) diagnostics_.maxRunGapUs=gap;
 uint32_t limit=homing_ ? Config::HOME_TIMEOUT_MS : Config::ROTATE_TIMEOUT_MS;
 if (millis()-started_>=limit) { stop(); timedOut_=true; return; }
 ++diagnostics_.runCalls;
 long before=motor_.currentPosition();
 motor_.run();
 if(motor_.currentPosition()!=before) ++diagnostics_.emittedSteps;
 if (!motor_.distanceToGo()) moving_=false; // Keep phase energized until STOP/fault.
 diagnostics_.moving=moving_;
}
long StepperController::stepsTaken() { return labs(motor_.currentPosition()-startedPosition_); }
void StepperController::haltAndHold() {
 // No new steps, no phase reset and no coil release during stationary verification.
 motor_.setCurrentPosition(motor_.currentPosition()); moving_=false; ready_=false;
 diagnostics_.moving=false;
}
void StepperController::stop() {
 motor_.setCurrentPosition(0); motor_.disableOutputs(); moving_=false; ready_=false;
 diagnostics_.moving=false;
}
