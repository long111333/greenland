#pragma once
#include "protocol.h"
#include "config.h"
class UltrasonicSensor {
public:
 void begin(); void update();
 BinStatus status() const { return status_; }
 uint16_t distanceMm() const { return status_==BinStatus::UNKNOWN ? 0 : distance_; }
 bool healthy() const { return failures_<Config::ULTRA_FAILURE_LIMIT; }
 static void echoInterrupt();
private:
 static volatile uint32_t rise_,width_;
 static volatile bool waiting_,received_,rising_;
 uint32_t started_=0,lastCycle_=0;
 uint16_t samples_[Config::ULTRA_WINDOW]={},distance_=0;
 uint8_t phase_=0,count_=0,index_=0,failures_=0;
 BinStatus status_=BinStatus::UNKNOWN;
 void finish(bool valid,uint32_t width);
};
