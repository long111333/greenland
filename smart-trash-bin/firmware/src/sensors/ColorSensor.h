#pragma once
#include <Arduino.h>
#include "config.h"
struct ColorReading { uint16_t r=0,g=0,b=0,c=0; };
class ColorSensor {
public:
 void begin(); void update();
 uint8_t getDetectedPosition() const { return isPositionStable() ? detected_ : 0; }
 // A fresh classified sample is only a brake trigger; never permission to open.
 uint8_t getInstantPosition() const { return isSensorHealthy() ? instant_ : 0; }
 uint16_t sampleSequence() const { return sampleSequence_; }
 bool isPositionStable() const;
 bool isSensorHealthy() const;
 void resetStability();
 void setTracking(bool tracking);
 const ColorReading& raw() const { return raw_; }
private:
 ColorReading raw_;
 uint8_t detected_=0, history_[Config::COLOR_HISTORY_SIZE]={}, index_=0, count_=0;
 uint8_t instant_=0;
 uint16_t sampleSequence_=0;
 bool healthy_=false;
 bool tracking_=false;
 uint32_t lastPoll_=0,lastGood_=0,lastVote_=0;
 bool readRaw();
 uint8_t classify() const;
 void addSample(uint8_t position);
};
