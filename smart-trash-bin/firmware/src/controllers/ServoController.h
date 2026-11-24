#pragma once
#include <Arduino.h>
#include <Servo.h>
class ServoController {
public:
 void begin(); void open(); void close(); void update(); void stop();
 bool isFinished() const { return known_ && !moving_; }
 bool isOpen() const; bool isClosed() const;
 bool isMoving() const { return moving_; }
private:
 Servo first_, second_;
 uint8_t angle_=0, from_=0, target_=0;
 bool known_=false, moving_=false, attached_=false;
 uint32_t started_=0;
 void move(uint8_t target); void write(uint8_t angle);
};
