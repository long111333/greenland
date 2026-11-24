#include "LoadCellSensor.h"
#include "config.h"
#include "pins.h"
#include <EEPROM.h>
#include <avr/eeprom.h>
#include <util/atomic.h>
#include <math.h>
#include <string.h>
static_assert(sizeof(float)==4, "Calibration record requires IEEE-754 binary32");
#ifdef __AVR__
static_assert(Config::SCALE_EEPROM_ADDRESS+36<=E2END+1, "Calibration journal exceeds EEPROM");
#endif

static uint32_t decode32(const uint8_t* p) {
 return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);
}
static void encode32(uint8_t* p,uint32_t value) {
 for(uint8_t i=0;i<4;i++) { p[i]=value&255; value>>=8; }
}
uint16_t LoadCellSensor::crc(const uint8_t* data,uint8_t length) {
 uint16_t value=0xFFFF;
 while(length--) {
  value^=uint16_t(*data++)<<8;
  for(uint8_t bit=0;bit<8;bit++) value=value&0x8000 ? (value<<1)^0x1021 : value<<1;
 }
 return value;
}
bool LoadCellSensor::validCalibration(float factor,int32_t offset) {
 return isfinite(factor) && fabsf(factor)>1 && fabsf(factor)<=Config::SCALE_FACTOR_LIMIT && offset>=-8388608L && offset<=8388607L;
}
bool LoadCellSensor::load(uint8_t slot,bool apply) {
 uint8_t bytes[RECORD_SIZE];
 for(uint8_t i=0;i<RECORD_SIZE;i++) bytes[i]=EEPROM.read(Config::SCALE_EEPROM_ADDRESS+slot*RECORD_SIZE+i);
 if(decode32(bytes)!=Config::SCALE_MAGIC || bytes[4]!=1 || bytes[5]>1) return false;
 uint16_t checksum=uint16_t(bytes[16])|(uint16_t(bytes[17])<<8);
 if(crc(bytes+4,12)!=checksum) return false;
 float factor; memcpy(&factor,bytes+8,4);
 int32_t offset=static_cast<int32_t>(decode32(bytes+12));
 if(bytes[5] && !validCalibration(factor,offset)) return false;
 if(!isfinite(factor) || offset<-8388608L || offset>8388607L) return false;
 uint16_t generation=uint16_t(bytes[6])|(uint16_t(bytes[7])<<8);
 if(apply) { factor_=factor; offset_=offset; calibrated_=bytes[5]; generation_=generation; slot_=slot; }
 return true;
}
void LoadCellSensor::begin() {
 pinMode(Pins::HX711_SCK,OUTPUT); digitalWrite(Pins::HX711_SCK,LOW);
 pinMode(Pins::HX711_DOUT,INPUT_PULLUP);
 operation_=Operation::IDLE; operationError_=Error::NONE;
 received_=false; sequence_=0; raw_=filtered_=0;
 factor_=Config::SCALE_FACTOR; offset_=Config::SCALE_OFFSET;
 calibrated_=Config::SCALE_CALIBRATED && validCalibration(factor_,offset_);
 slot_=1; generation_=0;
 bool first=load(0,true); uint16_t firstGeneration=generation_;
 if(load(1,false)) {
  uint16_t secondGeneration=EEPROM.read(Config::SCALE_EEPROM_ADDRESS+RECORD_SIZE+6);
  secondGeneration|=uint16_t(EEPROM.read(Config::SCALE_EEPROM_ADDRESS+RECORD_SIZE+7))<<8;
  if(!first || int16_t(secondGeneration-firstGeneration)>0) load(1,true);
 }
 // No automatic tare: an object present at boot must not silently become zero.
}
bool LoadCellSensor::readAdc(int32_t& value) {
 uint32_t bits=0;
 for(uint8_t bit=0;bit<24;bit++) {
  // An ISR must never extend SCK high beyond HX711's power-down threshold.
  // Interrupts remain enabled between bits while SCK is LOW, keeping Servo/UART live.
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
   digitalWrite(Pins::HX711_SCK,HIGH); delayMicroseconds(Config::SCALE_CLOCK_US);
   bits=(bits<<1)|(digitalRead(Pins::HX711_DOUT) ? 1UL : 0UL);
   digitalWrite(Pins::HX711_SCK,LOW);
  }
  delayMicroseconds(Config::SCALE_CLOCK_US);
 }
 // Pulse 25 selects channel A / gain 128 for the next conversion.
 ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
  digitalWrite(Pins::HX711_SCK,HIGH); delayMicroseconds(Config::SCALE_CLOCK_US);
  digitalWrite(Pins::HX711_SCK,LOW);
 }
 if(digitalRead(Pins::HX711_DOUT)==LOW) return false; // Stuck-low/missing clock is not a valid conversion.
 if(bits&0x800000UL) bits|=0xFF000000UL;
 value=static_cast<int32_t>(bits); return true;
}
ScaleReading LoadCellSensor::reading() const {
 ScaleReading result;
 result.raw=raw_; result.sequence=sequence_; result.factor=factor_; result.offset=offset_;
 result.healthy=received_ && millis()-lastSample_<Config::SCALE_STALE_MS;
 result.calibrated=calibrated_; result.busy=busy();
 if(result.healthy && calibrated_) {
  result.weightKg=float(filtered_-offset_)/factor_;
  if(fabsf(result.weightKg)<Config::SCALE_DEADBAND_KG) result.weightKg=0;
 }
 return result;
}
bool LoadCellSensor::startTare() {
 if(busy()) return false;
 operation_=Operation::TARE; operationStarted_=millis(); sum_=0; tareCount_=0; operationError_=Error::NONE;
 return true;
}
bool LoadCellSensor::setCalibration(float factor,int32_t offset) {
 if(busy() || !validCalibration(factor,offset)) return false;
 operationError_=Error::NONE; save(factor,offset,true); return true;
}
void LoadCellSensor::save(float factor,int32_t offset,bool calibrated) {
 memset(record_,0,RECORD_SIZE);
 encode32(record_,Config::SCALE_MAGIC); record_[4]=1; record_[5]=calibrated;
 uint16_t next=generation_+1; record_[6]=next&255; record_[7]=next>>8;
 memcpy(record_+8,&factor,4); encode32(record_+12,static_cast<uint32_t>(offset));
 uint16_t checksum=crc(record_+4,12); record_[16]=checksum&255; record_[17]=checksum>>8;
 saveIndex_=0; operationStarted_=millis(); operation_=Operation::SAVE;
}
void LoadCellSensor::updateSave() {
 // Two-slot journal keeps the previous calibration valid during power loss.
 if(!eeprom_is_ready()) return;
 uint8_t target=slot_^1;
 if(saveIndex_<=RECORD_SIZE) {
  uint8_t index=saveIndex_==RECORD_SIZE ? 0 : saveIndex_;
  uint8_t value=saveIndex_==0 ? 0 : record_[index];
  // update() has no EEPROM wait here because readiness was checked above.
  EEPROM.update(Config::SCALE_EEPROM_ADDRESS+target*RECORD_SIZE+index,value);
  ++saveIndex_; return;
 }
 if(!load(target,true)) operationError_=Error::EEPROM_ERROR;
 operation_=Operation::IDLE;
}
void LoadCellSensor::cancel() {
 // Current byte may finish electrically; the previous journal slot remains valid.
 operation_=Operation::IDLE; operationError_=Error::STOPPED;
}
void LoadCellSensor::update() {
 if(operation_==Operation::SAVE) {
  if(millis()-operationStarted_>=Config::SCALE_TARE_TIMEOUT_MS) { operationError_=Error::EEPROM_ERROR; operation_=Operation::IDLE; }
  else updateSave();
 }
 if(operation_==Operation::TARE && millis()-operationStarted_>=Config::SCALE_TARE_TIMEOUT_MS) {
  operationError_=Error::SCALE_TIMEOUT; operation_=Operation::IDLE;
 }
 if(digitalRead(Pins::HX711_DOUT)!=LOW) return; // Never wait for an ADC conversion.
 int32_t value;
 if(!readAdc(value)) { received_=false; return; }
 ++sequence_; raw_=value;
 if(value==-8388608L || value==8388607L) { received_=false; return; }
 bool fresh=received_ && millis()-lastSample_<Config::SCALE_STALE_MS;
 filtered_=fresh ? filtered_+(value-filtered_)/Config::SCALE_FILTER_DIVISOR : value;
 received_=true; lastSample_=millis();
 if(operation_==Operation::TARE) {
  sum_+=value;
  if(++tareCount_>=Config::SCALE_TARE_SAMPLES) {
   int32_t offset=sum_/Config::SCALE_TARE_SAMPLES;
   save(factor_,offset,calibrated_);
  }
 }
}
