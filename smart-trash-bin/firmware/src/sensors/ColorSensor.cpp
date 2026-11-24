#include "ColorSensor.h"
#include <Wire.h>
#include <math.h>

void ColorSensor::begin() {
 Wire.begin();
 Wire.setWireTimeout(Config::I2C_TIMEOUT_US,true);
 Wire.clearWireTimeoutFlag();
 raw_=ColorReading{};
 healthy_=false;
 tracking_=false;
 sampleSequence_=0;
 lastPoll_=millis();
 resetStability();
 // GY-33 supplies processed RGBC at 0x00. Do not send bare TCS34725
 // ID, power, ATIME, gain or AVALID transactions to this interface.
}

void ColorSensor::resetStability() {
 detected_=instant_=index_=count_=0;
 lastVote_=millis();
 for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) history_[i]=0;
}
void ColorSensor::setTracking(bool tracking) {
 if(tracking_!=tracking) { tracking_=tracking; lastPoll_=millis(); }
}

bool ColorSensor::readRaw() {
 Wire.clearWireTimeoutFlag();
 Wire.beginTransmission(Config::COLOR_ADDRESS);
 Wire.write(Config::COLOR_DATA_REGISTER);
 if(Wire.endTransmission(false)!=0) return false;
 uint8_t length=Wire.requestFrom(Config::COLOR_ADDRESS,static_cast<uint8_t>(8));
 if(length!=8 || Wire.getWireTimeoutFlag()) {
  while(Wire.available()) Wire.read(); // At most Wire's fixed receive buffer.
  return false;
 }
 uint8_t data[8];
 for(uint8_t i=0;i<8;i++) data[i]=Wire.read();
 // GY-33: R,G,B,Clear, each big-endian.
 raw_.r=(uint16_t(data[0])<<8)|data[1];
 raw_.g=(uint16_t(data[2])<<8)|data[3];
 raw_.b=(uint16_t(data[4])<<8)|data[5];
 raw_.c=(uint16_t(data[6])<<8)|data[7];
 return true;
}

uint8_t ColorSensor::classify() const {
 uint32_t total=uint32_t(raw_.r)+raw_.g+raw_.b;
 if(total==0 || raw_.c<Config::COLOR_MIN_CLEAR) return 0;
 float channels[3]={float(raw_.r)/total,float(raw_.g)/total,float(raw_.b)/total};
 float best=999.0f, second=999.0f;
 uint8_t position=0;
 for(uint8_t p=0;p<4;p++) {
  float distanceSquared=0;
  for(uint8_t channel=0;channel<3;channel++) {
   float difference=channels[channel]-Config::COLOR_REFERENCE[p][channel];
   distanceSquared+=difference*difference;
  }
  if(distanceSquared<best) { second=best; best=distanceSquared; position=p+1; }
  else if(distanceSquared<second) second=distanceSquared;
 }
 // Thresholds are actual Euclidean distances, matching the supplied calibration.
 best=sqrtf(best); second=sqrtf(second);
 if(best>Config::COLOR_MAX_DISTANCE || second-best<Config::COLOR_MARGIN) return 0;
 // A rejected BLACK candidate is UNKNOWN, never reassigned to another color.
 // Apply this to instant captures and stationary votes through the same classifier.
 if(position==4 && (best>Config::BLACK_MAX_DISTANCE ||
    raw_.c<Config::BLACK_MIN_CLEAR || raw_.c>Config::BLACK_MAX_CLEAR)) return 0;
 return position;
}

void ColorSensor::addSample(uint8_t position) {
 history_[index_]=position;
 index_=(index_+1)%Config::COLOR_HISTORY_SIZE;
 if(count_<Config::COLOR_HISTORY_SIZE) ++count_;
 detected_=0;
 if(count_<Config::COLOR_HISTORY_SIZE) return;
 uint8_t votes[5]={}; // 0=UNKNOWN, 1=RED, 2=BLUE, 3=GREEN, 4=BLACK.
 for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) ++votes[history_[i]];
 for(uint8_t p=1;p<=4;p++) {
  if(votes[p]>=Config::COLOR_REQUIRED_MATCHES) { detected_=p; break; }
 }
}

bool ColorSensor::isSensorHealthy() const {
 return healthy_ && millis()-lastGood_<Config::COLOR_STALE_MS;
}
bool ColorSensor::isPositionStable() const {
 return isSensorHealthy() && count_==Config::COLOR_HISTORY_SIZE && detected_!=0;
}

void ColorSensor::update() {
 uint32_t now=millis();
 uint16_t period=tracking_ ? Config::COLOR_TRACK_MS : Config::COLOR_SAMPLE_MS;
 if(now-lastPoll_<period) return;
 // Never bridge samples across a long stall into a stale majority.
 if(now-lastPoll_>=Config::COLOR_STALE_MS) {
  resetStability(); lastVote_=now-Config::COLOR_SAMPLE_MS; // First recovered sample may start a fresh history.
 }
 lastPoll_=now;
 if(!readRaw()) {
  healthy_=false; raw_=ColorReading{}; resetStability(); return;
 }
 healthy_=true; lastGood_=now;
 instant_=classify();
 ++sampleSequence_;
 // Faster I2C polling is for candidate capture only. Do not count repeated
 // module frames at 50ms as extra independent samples in the 4-of-5 vote.
 if(now-lastVote_>=Config::COLOR_SAMPLE_MS) { lastVote_=now; addSample(instant_); }
}
