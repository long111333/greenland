// Compile real controllers against deterministic actuator/time mocks.
#include <cassert>
#include <cstdio>
#include <cstring>
#include <Arduino.h>
#include "pins.h"
#define private public
#include "controllers/SortingController.h"
#include "safety/SafetyManager.h"
#undef private
uint32_t fakeMillis=0,fakeMicros=0;
uint8_t fakePins[32]={};
struct Reply { uint32_t id; Error error; bool complete; } lastReply{};
void SerialProtocol::reply(uint32_t id,const __FlashStringHelper* status,Error error,uint8_t) {
 lastReply={id,error,strcmp(reinterpret_cast<const char*>(status),"COMPLETE")==0};
}
void SerialProtocol::telemetry(uint32_t,SortingState,uint8_t,uint16_t,BinStatus,bool,Error) {}
void SerialProtocol::color(uint32_t,uint16_t,uint16_t,uint16_t,uint16_t,uint8_t,bool) {}
void SerialProtocol::stateChange(uint32_t,SortingState,SortingState) {}
void SerialProtocol::motionDiagnostics(uint32_t,const MotionDiagnostics&) {}
void SerialProtocol::weight(uint32_t,const ScaleReading&) {}
void ColorSensor::begin() { healthy_=true; }
void ColorSensor::resetStability() { detected_=instant_=count_=0; }
void ColorSensor::setTracking(bool tracking) { tracking_=tracking; }
bool ColorSensor::isSensorHealthy() const { return healthy_; }
bool ColorSensor::isPositionStable() const { return healthy_ && detected_ && count_==Config::COLOR_HISTORY_SIZE; }

struct Fixture {
 ServoController gate; StepperController stepper; ColorSensor color;
 UltrasonicSensor bin; SerialProtocol serial;
 LoadCellSensor scale;
 SortingController sorter{gate,stepper,color,bin,serial,&scale};
 SafetyManager safety;
 uint32_t id=0;
 Fixture() { fakeMillis=fakeMicros=0; fakePins[Pins::HX711_DOUT]=HIGH; gate.begin(); stepper.begin(); color.begin(); scale.begin(); sorter.begin(); }
 void command(Command cmd,uint8_t target=0) { sorter.handle(Request{++id,cmd,target}); }
 void tick(uint32_t ms=1) { fakeMillis+=ms; fakeMicros+=ms*1000UL; serial.lastContact_=fakeMillis; gate.update(); stepper.update(); safety.update(sorter,gate,stepper,color,serial); sorter.update(); scale.update(); }
 void mark(uint8_t p) { color.detected_=color.instant_=p; color.count_=Config::COLOR_HISTORY_SIZE; ++color.sampleSequence_; }
 void close() { command(Command::CLOSE_GATE); tick(Config::SERVO_TRAVEL_MS+Config::SERVO_SETTLE_MS); tick(); assert(gate.isClosed()); }
 void home() {
  close(); command(Command::HOME);
  assert(sorter.state()==SortingState::VERIFY_POSITION);
  mark(1); tick(); tick(); assert(sorter.homed());
 }
};
int main() {
 { Fixture f; assert(!f.gate.isClosed()); f.command(Command::HOME); assert(lastReply.error==Error::GATE_UNSAFE); assert(!f.stepper.isMoving()); }
 { Fixture f; f.close(); f.command(Command::HOME); f.tick(Config::HOME_TIMEOUT_MS); assert(f.sorter.state()==SortingState::ERROR); assert(lastReply.error==Error::HOME_TIMEOUT); assert(!f.stepper.isMoving()); }
 { Fixture f; f.home(); f.command(Command::OPEN_GATE); f.mark(1); f.tick(); f.tick(Config::SERVO_TRAVEL_MS+Config::SERVO_SETTLE_MS); f.tick(); assert(f.gate.isOpen()); f.command(Command::SORT,2); assert(lastReply.error==Error::GATE_UNSAFE); }
 { Fixture f; f.home(); f.command(Command::OPEN_GATE); f.mark(1); f.tick(); f.tick(Config::SERVO_TRAVEL_MS+Config::SERVO_SETTLE_MS); f.tick(); f.command(Command::CLOSE_GATE); f.tick(Config::SERVO_TRAVEL_MS/2); assert(f.gate.angle_==90); f.tick(Config::SERVO_TRAVEL_MS/2+Config::SERVO_SETTLE_MS); f.tick(); assert(f.gate.isClosed()); }
 { Fixture f; f.home(); f.command(Command::SORT,2); uint32_t motion=f.id; f.command(Command::SORT,3); assert(lastReply.error==Error::BUSY); f.sorter.handle(Request{motion,Command::SORT,2}); assert(lastReply.error==Error::NONE && !lastReply.complete); f.command(Command::STOP); assert(!f.sorter.homed()); assert(!f.gate.isClosed()); assert(!f.stepper.isMoving()); f.command(Command::RESET_ERROR); assert(f.sorter.state()==SortingState::INIT); }
 { Fixture f; f.home(); f.command(Command::SORT,2); f.mark(3); for(int i=0;i<1500;i++) f.tick(); assert(f.sorter.state()==SortingState::ROTATING); assert(f.stepper.isMoving()); assert(!f.gate.isOpen()); f.tick(Config::ROTATE_TIMEOUT_MS); assert(f.sorter.state()==SortingState::ERROR); assert(lastReply.error==Error::POSITION_TIMEOUT); }
 { Fixture f; f.home(); f.bin.status_=BinStatus::FULL; f.command(Command::SORT,Config::MONITORED_BIN); assert(lastReply.error==Error::BIN_FULL); f.command(Command::SORT,2); assert(f.stepper.isMoving()); f.color.healthy_=false; f.tick(); assert(f.sorter.state()==SortingState::ERROR); assert(lastReply.error==Error::COLOR_SENSOR); }
 { Fixture f; f.home(); fakeMillis+=Config::LINK_TIMEOUT_MS; f.safety.update(f.sorter,f.gate,f.stepper,f.color,f.serial); assert(f.sorter.state()==SortingState::ERROR); assert(!f.sorter.homed()); }
 { Fixture f; f.home(); f.command(Command::SORT,2); f.tick(Config::ROTATE_TIMEOUT_MS); assert(f.sorter.state()==SortingState::ERROR); f.command(Command::RESET_ERROR); f.tick(); assert(f.sorter.state()==SortingState::INIT); assert(!f.stepper.timedOut()); }
 { Fixture f; f.home(); f.command(Command::SORT,2); for(int i=0;i<1025;i++) f.tick(); f.mark(2); f.tick(); assert(f.sorter.state()==SortingState::VERIFY_POSITION); assert(f.gate.isClosed()); assert(f.stepper.motor_.outputsEnabled); f.mark(2); f.tick(); assert(f.sorter.state()==SortingState::OPENING); f.tick(3100); f.tick(Config::HOLD_MS); f.tick(3100); f.tick(); assert(lastReply.complete); uint32_t motion=f.id; f.sorter.handle(Request{motion,Command::SORT,2}); assert(lastReply.complete); assert(!f.stepper.isMoving()); }
 // No periodic pause at the old quarter-turn estimate, regardless of other markers.
 { Fixture f; f.home(); f.command(Command::SORT,4); f.mark(3); for(int i=0;i<2300;i++) { f.tick(); assert(f.sorter.state()==SortingState::ROTATING); } assert(f.stepper.stepsTaken()==2300); }
 // A false target capture resumes with the remaining common budget and same phase.
 { Fixture f; f.home(); f.command(Command::SORT,2); for(int i=0;i<111;i++) f.tick(); f.mark(2); f.tick(); long phase=f.stepper.motor_.currentPosition()&7L; long remaining=f.sorter.searchRemaining_; assert(f.sorter.state()==SortingState::VERIFY_POSITION); f.mark(3); f.tick(Config::VERIFY_MS); assert(f.sorter.state()==SortingState::ROTATING); assert((f.stepper.motor_.currentPosition()&7L)==phase); assert(f.stepper.motor_.distanceToGo()==remaining); f.tick(); assert(f.sorter.state()==SortingState::ROTATING); }
 // Step exhaustion without target fails closed, even before the time deadline.
 { Fixture f; f.home(); f.command(Command::SORT,2); for(long i=0;i<Config::SEARCH_STEPS;i++) f.tick(); assert(f.sorter.state()==SortingState::ERROR); assert(!f.gate.isOpen()); assert(!f.stepper.motor_.outputsEnabled); }
 // An already reached target only verifies; no needless revolution.
 { Fixture f; f.home(); f.bin.status_=BinStatus::NOT_FULL; f.command(Command::SORT,1); assert(f.sorter.state()==SortingState::VERIFY_POSITION); assert(!f.stepper.isMoving()); f.mark(1); f.tick(); assert(f.sorter.state()==SortingState::OPENING); }
 // False-positive retries never reset the command deadline or exceed capture limit.
 { Fixture f; f.home(); f.command(Command::SORT,2); auto started=f.sorter.searchStarted_; for(uint8_t i=0;i<Config::MAX_TARGET_CAPTURES;i++) { f.mark(2); f.tick(); assert(f.sorter.state()==SortingState::VERIFY_POSITION); f.mark(3); f.tick(Config::VERIFY_MS); } assert(f.sorter.state()==SortingState::ERROR); assert(f.sorter.searchStarted_==started); assert(lastReply.error==Error::POSITION_TIMEOUT); }
 // A cached target candidate without a new sensor sample never brakes a move.
 { Fixture f; f.home(); f.command(Command::SORT,2); f.color.instant_=2; for(int i=0;i<20;i++) f.tick(); assert(f.sorter.state()==SortingState::ROTATING); f.mark(2); f.tick(); assert(f.sorter.state()==SortingState::VERIFY_POSITION); }
 // Timeout still expires in stationary verification; it is not restarted at capture.
 { Fixture f; f.home(); f.command(Command::SORT,2); f.tick(Config::ROTATE_TIMEOUT_MS-100); f.mark(2); f.tick(); assert(f.sorter.state()==SortingState::VERIFY_POSITION); f.tick(101); assert(f.sorter.state()==SortingState::ERROR); }
 // OPEN_GATE must never launch a search when its stationary recheck fails.
 { Fixture f; f.home(); f.command(Command::OPEN_GATE); f.mark(3); f.tick(Config::VERIFY_MS); assert(f.sorter.state()==SortingState::ERROR); assert(!f.stepper.isMoving()); }
 // HOME uses the same fresh-sample capture and held-coil stationary verification.
 { Fixture f; f.close(); f.command(Command::HOME); f.tick(Config::VERIFY_MS); assert(f.sorter.state()==SortingState::HOMING); assert(f.stepper.motor_.maxSpeed==Config::HOME_SPEED); assert(f.color.tracking_); f.mark(1); f.tick(); assert(!f.sorter.homed()); assert(!f.color.tracking_); assert(f.stepper.motor_.outputsEnabled); f.mark(3); f.tick(Config::VERIFY_MS); assert(f.sorter.state()==SortingState::HOMING); assert(f.stepper.isMoving()); }
 // STOP while holding a captured marker releases coils and invalidates readiness.
 { Fixture f; f.home(); f.command(Command::SORT,2); assert(f.stepper.motor_.maxSpeed==Config::TARGET_SEARCH_SPEED); f.mark(2); f.tick(); f.command(Command::STOP); assert(!f.stepper.motor_.outputsEnabled); assert(!f.sorter.homed()); assert(f.sorter.state()==SortingState::ERROR); }
 { Fixture f; f.command(Command::TEST_STEPPER); assert(lastReply.error==Error::GATE_UNSAFE); assert(!f.stepper.isMoving()); }
 { Fixture f; f.close(); f.color.healthy_=false; f.command(Command::TEST_STEPPER); assert(f.stepper.motor_.maxSpeed==Config::STEPPER_SPEED); for(long i=0;i<Config::TEST_STEPPER_STEPS;i++) f.tick(); f.tick(); assert(lastReply.complete); assert(f.sorter.state()==SortingState::INIT); assert(!f.sorter.homed()); assert(f.gate.isClosed()); auto d=f.stepper.diagnostics(); assert(d.emittedSteps==Config::TEST_STEPPER_STEPS && !d.moving); assert(d.maxRunGapUs==1000 && d.nominalIntervalUs==static_cast<uint32_t>(1000000UL/Config::STEPPER_SPEED)); }
 { Fixture f; f.close(); f.command(Command::TEST_STEPPER); f.tick(Config::TEST_STEPPER_TIMEOUT_MS); assert(f.sorter.state()==SortingState::ERROR); assert(!f.stepper.isMoving()); }
 { Fixture f; f.close(); f.command(Command::HOME); assert(!f.stepper.isMoving()); f.mark(1); f.tick(); f.tick(); assert(f.sorter.homed()); assert(f.stepper.diagnostics().emittedSteps==0); }
 { Fixture f; f.close(); f.command(Command::HOME); f.mark(4); f.tick(Config::VERIFY_MS); assert(f.sorter.state()==SortingState::HOMING); assert(!f.sorter.homed()); assert(f.stepper.isMoving()); assert(f.color.tracking_); }
 { Fixture f; Request set; set.id=++f.id; set.cmd=Command::SET_SCALE; set.factor=500000; set.offset=1000; f.sorter.handle(set); assert(f.sorter.state()==SortingState::CALIBRATING); f.sorter.handle(set); assert(!lastReply.complete && lastReply.error==Error::NONE); Request conflict=set; conflict.factor=600000; f.sorter.handle(conflict); assert(lastReply.error==Error::ID_CONFLICT); f.command(Command::SORT,2); assert(lastReply.error==Error::BUSY); for(int i=0;i<30;i++) f.tick(4); assert(f.scale.reading().calibrated && f.scale.reading().offset==1000); assert(f.sorter.state()==SortingState::INIT); f.sorter.handle(set); assert(lastReply.complete); }
 { Fixture f; f.command(Command::TARE_WEIGHT); assert(f.sorter.state()==SortingState::CALIBRATING); f.tick(Config::SCALE_TARE_TIMEOUT_MS); f.tick(); assert(lastReply.error==Error::SCALE_TIMEOUT); assert(f.sorter.state()==SortingState::INIT); assert(!f.gate.isMoving() && !f.stepper.isMoving()); }
 { Fixture f; f.command(Command::TARE_WEIGHT); f.command(Command::STOP); assert(!f.scale.busy()); assert(f.sorter.state()==SortingState::ERROR); }
 { Fixture f; f.home(); f.command(Command::SORT,2); f.command(Command::TARE_WEIGHT); assert(lastReply.error==Error::BUSY); }
 puts("29 firmware safety/search/scale scenarios passed");
}
