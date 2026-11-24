#pragma once
#include "ServoController.h"
#include "StepperController.h"
#include "sensors/ColorSensor.h"
#include "sensors/UltrasonicSensor.h"
#include "communication/SerialProtocol.h"
#include "sensors/LoadCellSensor.h"
class SortingController {
public:
 SortingController(ServoController& gate,StepperController& stepper,ColorSensor& color,UltrasonicSensor& bin,SerialProtocol& serial,LoadCellSensor* scale=nullptr):gate_(gate),stepper_(stepper),color_(color),bin_(bin),serial_(serial),scale_(scale) {}
 void begin(); void update(); void handle(const Request& request); void fault(Error error);
 SortingState state() const { return state_; }
 bool homed() const { return homed_; }
 bool busy() const { return active_.cmd!=Command::NONE; }
 bool needsColor() const { return homed_ || (busy() && active_.cmd!=Command::TEST_STEPPER && state_!=SortingState::CLOSING && state_!=SortingState::CALIBRATING); }
 void report(uint32_t id=0);
private:
 ServoController& gate_; StepperController& stepper_; ColorSensor& color_;
 UltrasonicSensor& bin_; SerialProtocol& serial_;
 LoadCellSensor* scale_;
 SortingState state_=SortingState::INIT;
 bool homed_=false;
 uint8_t position_=0,target_=0,captures_=0;
 long searchRemaining_=0;
 uint32_t searchStarted_=0;
 uint16_t lastColorSample_=0;
 uint32_t entered_=0,highestId_=0;
 Request active_,cached_;
 Error error_=Error::NONE,cachedError_=Error::NONE;
 bool cacheDone_=false;
 uint8_t cachedPosition_=0;
 void enter(SortingState state); void finish(); void verify();
 void resumeSearch(); bool captureTarget(); bool searchExpired() const;
 void reject(const Request& r,Error e) { serial_.reply(r.id,F("ERROR"),e); }
};
