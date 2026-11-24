#include "UltrasonicSensor.h"
#include "pins.h"
#include <util/atomic.h>
volatile uint32_t UltrasonicSensor::rise_=0,UltrasonicSensor::width_=0;
volatile bool UltrasonicSensor::waiting_=false,UltrasonicSensor::received_=false,UltrasonicSensor::rising_=false;
void UltrasonicSensor::begin() {
 pinMode(Pins::TRIG,OUTPUT); digitalWrite(Pins::TRIG,LOW); pinMode(Pins::ECHO,INPUT);
 attachInterrupt(digitalPinToInterrupt(Pins::ECHO),echoInterrupt,CHANGE);
}
void UltrasonicSensor::echoInterrupt() {
 if(!waiting_) return;
 if(digitalRead(Pins::ECHO)) { rise_=micros(); rising_=true; }
 else if(rising_) { width_=micros()-rise_; received_=true; waiting_=false; rising_=false; }
}
void UltrasonicSensor::finish(bool valid,uint32_t width) {
 phase_=0;
 if(!valid || width<Config::ULTRA_MIN_PULSE_US || width>Config::ULTRA_TIMEOUT_US) {
  if(failures_<255) ++failures_;
  count_=index_=0; status_=BinStatus::UNKNOWN; return;
 }
 failures_=0; samples_[index_]=width*10/58; index_=(index_+1)%Config::ULTRA_WINDOW;
 if(count_<Config::ULTRA_WINDOW) ++count_;
 if(count_<Config::ULTRA_WINDOW) return;
 uint16_t sorted[Config::ULTRA_WINDOW];
 for(uint8_t i=0;i<Config::ULTRA_WINDOW;i++) sorted[i]=samples_[i];
 for(uint8_t i=1;i<Config::ULTRA_WINDOW;i++) for(uint8_t j=i;j && sorted[j]<sorted[j-1];j--) { uint16_t v=sorted[j]; sorted[j]=sorted[j-1]; sorted[j-1]=v; }
 distance_=sorted[Config::ULTRA_WINDOW/2];
 if(distance_<=Config::FULL_MM) status_=BinStatus::FULL;
 else if(distance_>=Config::FULL_MM+Config::FULL_HYSTERESIS_MM) status_=BinStatus::NOT_FULL;
}
void UltrasonicSensor::update() {
 uint32_t now=micros();
 if(!phase_) {
  if(now-lastCycle_<Config::ULTRA_PERIOD_US) return;
  lastCycle_=started_=now; digitalWrite(Pins::TRIG,HIGH); phase_=1; return;
 }
 if(phase_==1) {
  if(now-started_<Config::ULTRA_TRIGGER_US) return;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { received_=false; rising_=false; waiting_=true; }
  digitalWrite(Pins::TRIG,LOW); started_=now; phase_=2; return;
 }
 bool done; uint32_t width;
 ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { done=received_; width=width_; }
 if(done) finish(true,width);
 else if(now-started_>=Config::ULTRA_TIMEOUT_US) {
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) { waiting_=false; }
  finish(false,0);
 }
}
