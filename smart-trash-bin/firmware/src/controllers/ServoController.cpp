#include "ServoController.h"
#include "config.h"
#include "pins.h"
void ServoController::begin() { known_=false; moving_=false; }
void ServoController::write(uint8_t angle) {
 angle_=angle>180 ? 180 : angle;
 first_.write(angle_);
 second_.write(Config::SERVO_2_REVERSED ? 180-angle_ : angle_);
}
void ServoController::move(uint8_t target) {
 if (moving_) return;
 // No feedback after boot/STOP: only explicit CLOSE may establish a timed reference.
 if (!known_ && target!=Config::GATE_CLOSED) return;
 if (!attached_) {
  first_.write(target); second_.write(Config::SERVO_2_REVERSED ? 180-target : target);
  first_.attach(Pins::SERVO_1); second_.attach(Pins::SERVO_2); attached_=true;
 }
 from_=known_ ? angle_ : target; target_=target; started_=millis(); moving_=true;
 if (!known_) write(target); // Unknown physical angle: wait full travel + settle.
}
void ServoController::open() { move(Config::GATE_OPEN); }
void ServoController::close() { move(Config::GATE_CLOSED); }
void ServoController::update() {
 if (!moving_) return;
 uint32_t elapsed=millis()-started_;
 uint32_t t=min(elapsed,static_cast<uint32_t>(Config::SERVO_TRAVEL_MS));
 uint8_t next=from_+(static_cast<int32_t>(target_)-from_)*static_cast<int32_t>(t)/Config::SERVO_TRAVEL_MS;
 if (next!=angle_) write(next);
 if (elapsed>=Config::SERVO_TRAVEL_MS+Config::SERVO_SETTLE_MS) { known_=true; moving_=false; }
}
bool ServoController::isOpen() const { return isFinished() && angle_==Config::GATE_OPEN; }
bool ServoController::isClosed() const { return isFinished() && angle_==Config::GATE_CLOSED; }
void ServoController::stop() {
 first_.detach(); second_.detach(); attached_=false; moving_=false; known_=false;
}
