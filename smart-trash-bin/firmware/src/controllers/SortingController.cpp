#include "SortingController.h"
void SortingController::begin() { enter(SortingState::INIT); }
void SortingController::enter(SortingState state) {
 SortingState previous=state_;
 state_=state; entered_=millis();
 if(previous!=state) serial_.stateChange(active_.id,previous,state);
}
void SortingController::report(uint32_t id) {
 serial_.telemetry(id,state_,position_,bin_.distanceMm(),bin_.status(),homed_,error_);
}
void SortingController::fault(Error error) {
 // STOP detaches PWM and releases stepper coils; no unverified automatic closing.
 stepper_.stop(); gate_.stop(); homed_=false; position_=0; error_=error;
 color_.setTracking(false);
 if(scale_ && scale_->busy()) scale_->cancel();
 if(busy()) {
  cached_=active_; cacheDone_=true; cachedError_=error; cachedPosition_=0;
  serial_.reply(active_.id,F("ERROR"),error); active_=Request{};
 }
 enter(SortingState::ERROR);
}
void SortingController::finish() {
 color_.setTracking(false);
 cached_=active_; cacheDone_=true; cachedError_=Error::NONE; cachedPosition_=position_;
 serial_.reply(active_.id,F("COMPLETE"),Error::NONE,position_); active_=Request{};
 enter(homed_ ? SortingState::IDLE : SortingState::INIT);
}
void SortingController::handle(const Request& r) {
 // STOP bypasses readiness, BUSY and stale-ID interlocks, including retransmissions.
 if(r.cmd==Command::STOP) {
  serial_.reply(r.id,F("ACCEPTED")); fault(Error::STOPPED);
  if(r.id>highestId_) highestId_=r.id;
  serial_.reply(r.id,F("COMPLETE")); return;
 }
 if(cached_.id==r.id) {
  if(cached_.cmd!=r.cmd || cached_.target!=r.target || (r.cmd==Command::SET_SCALE && (cached_.factor!=r.factor || cached_.offset!=r.offset))) { reject(r,Error::ID_CONFLICT); return; }
  serial_.reply(r.id,cacheDone_ ? (cachedError_==Error::NONE ? F("COMPLETE") : F("ERROR")) : F("ACCEPTED"),cachedError_,cachedPosition_); return;
 }
 if(r.id<=highestId_) { reject(r,Error::STALE_ID); return; }
 highestId_=r.id;
 if(r.cmd==Command::GET_STATUS) { report(r.id); return; }
 if(r.cmd==Command::GET_WEIGHT) {
  if(!scale_) { reject(r,Error::NOT_READY); return; }
  serial_.weight(r.id,scale_->reading()); return;
 }
 if(r.cmd==Command::GET_MOTION_DIAG) { serial_.motionDiagnostics(r.id,stepper_.diagnostics()); return; }
 if(r.cmd==Command::GET_COLOR) {
  const ColorReading& raw=color_.raw();
  serial_.color(r.id,raw.r,raw.g,raw.b,raw.c,color_.getDetectedPosition(),color_.isSensorHealthy()); return;
 }
 if(busy()) { reject(r,Error::BUSY); return; }
 if(r.cmd==Command::RESET_ERROR) {
  if(state_!=SortingState::ERROR || stepper_.isMoving() || gate_.isMoving()) { reject(r,Error::NOT_READY); return; }
  // Recovery only clears the latch; it never resumes motion or restores homed.
  serial_.clearOverflow(); color_.begin(); stepper_.begin(); error_=Error::NONE;
  enter(SortingState::INIT); serial_.reply(r.id,F("ACCEPTED")); serial_.reply(r.id,F("COMPLETE")); return;
 }
 if(state_==SortingState::ERROR) { reject(r,Error::NOT_READY); return; }
 if(r.cmd==Command::TARE_WEIGHT || r.cmd==Command::SET_SCALE) {
  if(!scale_ || stepper_.isMoving() || gate_.isMoving() || scale_->busy()) { reject(r,Error::NOT_READY); return; }
  bool accepted=r.cmd==Command::TARE_WEIGHT ? scale_->startTare() : scale_->setCalibration(r.factor,r.offset);
  if(!accepted) { reject(r,Error::INVALID_SCALE); return; }
 }
 if(r.cmd==Command::HOME && !gate_.isClosed()) { reject(r,Error::GATE_UNSAFE); return; }
 if(r.cmd==Command::TEST_STEPPER && !gate_.isClosed()) { reject(r,Error::GATE_UNSAFE); return; }
 if((r.cmd==Command::HOME || r.cmd==Command::SORT || r.cmd==Command::OPEN_GATE) && !color_.isSensorHealthy()) { reject(r,Error::COLOR_SENSOR); return; }
 if(r.cmd==Command::SORT || r.cmd==Command::OPEN_GATE) {
  if(!homed_ || state_!=SortingState::IDLE) { reject(r,Error::NOT_READY); return; }
  if(!gate_.isClosed()) { reject(r,Error::GATE_UNSAFE); return; }
 }
 if(r.cmd==Command::SORT && r.target==Config::MONITORED_BIN) {
  if(Config::REJECT_FULL && bin_.status()==BinStatus::FULL) { reject(r,Error::BIN_FULL); return; }
  if(Config::REJECT_UNKNOWN_BIN && bin_.status()==BinStatus::UNKNOWN) { reject(r,Error::BIN_UNKNOWN); return; }
 }
 active_=cached_=r; cachedError_=Error::NONE; cacheDone_=false; cachedPosition_=0;
 serial_.reply(r.id,F("ACCEPTED"));
 if(r.cmd==Command::TARE_WEIGHT || r.cmd==Command::SET_SCALE) enter(SortingState::CALIBRATING);
 else if(r.cmd==Command::CLOSE_GATE) { gate_.close(); enter(SortingState::CLOSING); }
 else if(r.cmd==Command::TEST_STEPPER) {
  // Bounded baseline test with all other modules active, but no color-based stop.
  homed_=false; position_=0; stepper_.setReady(true); stepper_.testMove(); enter(SortingState::ROTATING);
 }
 else if(r.cmd==Command::HOME) {
  homed_=false; position_=0; target_=Config::HOME_POSITION;
  captures_=0; searchRemaining_=Config::SEARCH_STEPS; searchStarted_=millis();
  // Already at RED? Establish HOME from fresh stationary samples first.
  // If not RED within VERIFY_MS, verify() starts the bounded continuous search.
  color_.setTracking(false); color_.resetStability(); enter(SortingState::VERIFY_POSITION);
 } else if(r.cmd==Command::SORT) {
  target_=r.target; captures_=0;
  searchRemaining_=Config::SEARCH_STEPS; searchStarted_=millis();
  if(target_==position_) {
   // Already at the requested marker: verify fresh samples without a full revolution.
   color_.resetStability(); enter(SortingState::VERIFY_POSITION);
  } else { position_=0; resumeSearch(); }
 } else if(r.cmd==Command::OPEN_GATE) {
  // Fresh samples while stationary are required even for a manual opening.
  target_=position_; color_.resetStability();
  enter(SortingState::VERIFY_POSITION);
 }
}
bool SortingController::searchExpired() const {
 uint32_t limit=active_.cmd==Command::HOME ? Config::HOME_TIMEOUT_MS : Config::ROTATE_TIMEOUT_MS;
 return millis()-searchStarted_>=limit;
}
void SortingController::resumeSearch() {
 Error timeout=active_.cmd==Command::HOME ? Error::HOME_TIMEOUT : Error::POSITION_TIMEOUT;
 if(searchExpired() || searchRemaining_<=0 || captures_>=Config::MAX_TARGET_CAPTURES) { fault(timeout); return; }
 position_=0;
 color_.setTracking(true);
 color_.resetStability(); lastColorSample_=color_.sampleSequence();
 stepper_.setReady(true); stepper_.setHoming(active_.cmd==Command::HOME);
 int8_t direction=active_.cmd==Command::HOME ? Config::HOME_DIRECTION : Config::SORT_DIRECTION;
 stepper_.moveSteps(direction*searchRemaining_);
 enter(active_.cmd==Command::HOME ? SortingState::HOMING : SortingState::ROTATING);
}
bool SortingController::captureTarget() {
 uint16_t sequence=color_.sampleSequence();
 if(sequence==lastColorSample_) return false; // Never brake twice on a cached sample.
 lastColorSample_=sequence;
 if(color_.getInstantPosition()!=target_) return false;
 ++captures_;
 // Only actual emitted steps consume the common budget, including false captures.
 searchRemaining_-=stepper_.stepsTaken();
 stepper_.haltAndHold();
 color_.setTracking(false);
 color_.resetStability();
 enter(SortingState::VERIFY_POSITION);
 return true;
}
void SortingController::verify() {
 if(active_.cmd!=Command::OPEN_GATE && searchExpired()) {
  fault(active_.cmd==Command::HOME ? Error::HOME_TIMEOUT : Error::POSITION_TIMEOUT); return;
 }
 if(color_.isPositionStable() && color_.getDetectedPosition()==target_) {
  position_=target_;
  // A marker must still be present after the motor has stopped and samples renewed.
  if(active_.cmd==Command::HOME) { homed_=true; enter(SortingState::COMPLETE); }
  else { gate_.open(); enter(SortingState::OPENING); }
 } else if(millis()-entered_>=Config::VERIFY_MS) {
  if(active_.cmd==Command::OPEN_GATE) { fault(Error::POSITION_TIMEOUT); return; }
  // False candidate: continue the same search direction, without resetting limits.
  resumeSearch();
 }
}
void SortingController::update() {
 uint32_t elapsed=millis()-entered_;
 switch(state_) {
 case SortingState::CALIBRATING:
  if(scale_ && !scale_->busy()) {
   Error result=scale_->operationError();
   if(result==Error::NONE) enter(SortingState::COMPLETE);
   else {
    cached_=active_; cachedError_=result; cachedPosition_=position_; cacheDone_=true;
    serial_.reply(active_.id,F("ERROR"),result); active_=Request{};
    enter(homed_ ? SortingState::IDLE : SortingState::INIT);
   }
  }
  break;
 case SortingState::HOMING:
 case SortingState::ROTATING:
  if(active_.cmd==Command::TEST_STEPPER) {
   if(elapsed>=Config::TEST_STEPPER_TIMEOUT_MS) fault(Error::POSITION_TIMEOUT);
   else if(!stepper_.isMoving()) enter(SortingState::COMPLETE);
   break;
  }
  if(searchExpired()) { fault(active_.cmd==Command::HOME ? Error::HOME_TIMEOUT : Error::POSITION_TIMEOUT); break; }
  if(captureTarget()) break;
  if(!stepper_.isMoving()) fault(active_.cmd==Command::HOME ? Error::HOME_TIMEOUT : Error::POSITION_TIMEOUT);
  break;
 case SortingState::VERIFY_POSITION: verify(); break;
 case SortingState::OPENING:
  if(elapsed>=Config::GATE_TIMEOUT_MS) { fault(Error::STATE_TIMEOUT); break; }
  if(gate_.isOpen()) {
   if(active_.cmd==Command::OPEN_GATE) enter(SortingState::COMPLETE);
   else enter(SortingState::HOLDING);
  } break;
 case SortingState::HOLDING:
  if(elapsed>=Config::HOLD_MS) { gate_.close(); enter(SortingState::CLOSING); } break;
 case SortingState::CLOSING:
  if(elapsed>=Config::GATE_TIMEOUT_MS) { fault(Error::STATE_TIMEOUT); break; }
  if(gate_.isClosed()) enter(SortingState::COMPLETE);
  break;
 case SortingState::COMPLETE: finish(); break;
 default: break; // INIT/IDLE wait for explicit commands; ERROR is latched.
 }
}
