#include "SerialProtocol.h"
#include <ArduinoJson.h>
#include <avr/pgmspace.h>
#include "safety/MemoryMonitor.h"
#include "sensors/LoadCellSensor.h"
#include <math.h>
const __FlashStringHelper* errorName(Error e) {
 switch(e) {
#define E(x) case Error::x: return F(#x)
 E(NONE); E(INVALID_JSON); E(INVALID_COMMAND); E(INVALID_ID); E(INVALID_TARGET);
 E(LINE_TOO_LONG); E(RX_TIMEOUT); E(BUSY); E(NOT_READY); E(GATE_UNSAFE);
 E(BIN_FULL); E(BIN_UNKNOWN); E(HOME_TIMEOUT); E(POSITION_TIMEOUT); E(COLOR_SENSOR);
 E(LINK_LOST); E(STOPPED); E(STATE_TIMEOUT); E(STALE_ID); E(ID_CONFLICT); E(TX_OVERFLOW);
 E(INVALID_SCALE); E(SCALE_TIMEOUT); E(EEPROM_ERROR);
#undef E
 } return F("UNKNOWN");
}
const __FlashStringHelper* stateName(SortingState s) {
 switch(s) {
#define S(x) case SortingState::x: return F(#x)
 S(INIT); S(HOMING); S(IDLE); S(ROTATING); S(VERIFY_POSITION); S(OPENING); S(HOLDING); S(CLOSING); S(COMPLETE); S(ERROR);
 S(CALIBRATING);
#undef S
 } return F("ERROR");
}
const __FlashStringHelper* binName(BinStatus s) {
 if(s==BinStatus::FULL) return F("FULL");
 if(s==BinStatus::NOT_FULL) return F("NOT_FULL");
 return F("UNKNOWN");
}
void SerialProtocol::begin(Handler handler) { handler_=handler; Serial.begin(Config::BAUD); lastContact_=millis(); }
uint16_t SerialProtocol::freeSpace() const { return (tail_+Config::TX_SIZE-head_-1)%Config::TX_SIZE; }
void SerialProtocol::enqueue(const char* data,bool optional) {
 uint16_t length=strlen(data);
 if(length>freeSpace()) { if(!optional) overflow_=true; return; }
 for(uint16_t i=0;i<length;i++) { tx_[head_]=data[i]; head_=(head_+1)%Config::TX_SIZE; }
}
void SerialProtocol::flushOutput() {
 // Never wait for UART space: motor updates and STOP parsing continue under TX load.
 uint8_t budget=Serial.availableForWrite();
 while(budget-- && tail_!=head_) { Serial.write(tx_[tail_]); tail_=(tail_+1)%Config::TX_SIZE; }
}
void SerialProtocol::reply(uint32_t id,const __FlashStringHelper* status,Error error,uint8_t position) {
 if(!startFrame(110)) return;
 append(F("{\"id\":")); appendUnsigned(id); append(F(",\"status\":\"")); append(status);
 if(error!=Error::NONE) { append(F("\",\"error\":\"")); append(errorName(error)); appendChar('"'); }
 else { append(F("\",\"position\":")); appendUnsigned(position); }
 append(F("}\n"));
}
void SerialProtocol::telemetry(uint32_t id,SortingState state,uint8_t position,uint16_t mm,BinStatus bin,bool homed,Error error) {
 if(!startFrame(200,!id,id ? 0 : 100)) return;
 append(F("{\"id\":")); appendUnsigned(id); append(F(",\"type\":\"TELEMETRY\",\"state\":\"")); append(stateName(state));
 append(F("\",\"position\":")); appendUnsigned(position); append(F(",\"distance_cm\":"));
 if(bin==BinStatus::UNKNOWN) append(F("null"));
 else { appendUnsigned(mm/10); appendChar('.'); appendUnsigned(mm%10); }
 append(F(",\"bin_status\":\"")); append(binName(bin)); append(F("\",\"monitored_bin\":")); appendUnsigned(Config::MONITORED_BIN);
 append(F(",\"homed\":")); append(homed ? F("true") : F("false")); append(F(",\"error\":\"")); append(errorName(error)); append(F("\"}\n"));
}
void SerialProtocol::color(uint32_t id,uint16_t r,uint16_t g,uint16_t b,uint16_t c,uint8_t position,bool healthy) {
 if(!startFrame(150,!id,id ? 0 : 100)) return;
 append(F("{\"id\":")); appendUnsigned(id); append(F(",\"type\":\"COLOR\",\"r\":")); appendUnsigned(r);
 append(F(",\"g\":")); appendUnsigned(g); append(F(",\"b\":")); appendUnsigned(b); append(F(",\"clear\":")); appendUnsigned(c);
 append(F(",\"position\":")); appendUnsigned(position); append(F(",\"healthy\":")); append(healthy ? F("true") : F("false")); append(F("}\n"));
}
void SerialProtocol::stateChange(uint32_t id,SortingState from,SortingState to) {
 if(!Config::TRACE_STATES) return;
 if(!startFrame(110,true,128)) return;
 append(F("{\"type\":\"STATE_CHANGE\",\"id\":")); appendUnsigned(id); append(F(",\"from\":\"")); append(stateName(from));
 append(F("\",\"to\":\"")); append(stateName(to)); append(F("\"}\n"));
}
void SerialProtocol::motionDiagnostics(uint32_t id,const MotionDiagnostics& d) {
 if(!startFrame(220)) return;
 append(F("{\"id\":")); appendUnsigned(id); append(F(",\"type\":\"MOTION_DIAG\",\"run_calls\":")); appendUnsigned(d.runCalls);
 append(F(",\"emitted_steps\":")); appendUnsigned(d.emittedSteps); append(F(",\"max_run_gap_us\":")); appendUnsigned(d.maxRunGapUs);
 append(F(",\"nominal_interval_us\":")); appendUnsigned(d.nominalIntervalUs); append(F(",\"moving\":")); append(d.moving ? F("true") : F("false"));
 append(F(",\"min_free_stack\":")); appendUnsigned(MemoryMonitor::minFreeBytes()); append(F("}\n"));
}
bool SerialProtocol::startFrame(uint16_t bound,bool optional,uint16_t reserve) {
 if(!optional && freeSpace()<bound) flushOutput(); // Drain available bytes, never wait.
 if(freeSpace()>=bound+reserve) return true;
 if(!optional) overflow_=true;
 return false;
}
void SerialProtocol::weight(uint32_t id,const ScaleReading& r) {
 if(!startFrame(240)) return;
 append(F("{\"id\":")); appendUnsigned(id); append(F(",\"type\":\"WEIGHT\",\"raw\":")); appendSigned(r.raw);
 append(F(",\"sample_seq\":")); appendUnsigned(r.sequence); append(F(",\"weight_kg\":"));
 if(r.healthy && r.calibrated) appendFloat(r.weightKg); else append(F("null"));
 append(F(",\"healthy\":")); append(r.healthy ? F("true") : F("false"));
 append(F(",\"calibrated\":")); append(r.calibrated ? F("true") : F("false"));
 append(F(",\"factor\":")); appendFloat(r.factor); append(F(",\"offset\":")); appendSigned(r.offset);
 append(F(",\"busy\":")); append(r.busy ? F("true") : F("false")); append(F("}\n"));
}
void SerialProtocol::appendSigned(int32_t number) {
 if(number<0) { appendChar('-'); appendUnsigned(0UL-static_cast<uint32_t>(number)); }
 else appendUnsigned(number);
}
void SerialProtocol::appendFloat(float number) {
 if(!isfinite(number)) { append(F("null")); return; }
 char text[20]; dtostre(number,text,8,0);
 for(const char* p=text;*p;++p) appendChar(*p);
}
void SerialProtocol::appendChar(char value) { tx_[head_]=value; head_=(head_+1)%Config::TX_SIZE; }
void SerialProtocol::append(const __FlashStringHelper* text) {
 const char* cursor=reinterpret_cast<const char*>(text);
 char value;
 while((value=pgm_read_byte(cursor++))!=0) appendChar(value);
}
void SerialProtocol::appendUnsigned(uint32_t number) {
 char digits[10]; uint8_t count=0;
 do { digits[count++]=char('0'+number%10); number/=10; } while(number);
 while(count) appendChar(digits[--count]);
}
void SerialProtocol::parse() {
 // Require exactly one flat object; reject trailing objects and nested JSON.
 bool quoted=false,escape=false; uint8_t closes=0,opens=0;
 for(uint8_t i=0;i<used_;i++) {
  char c=rx_[i];
  if(quoted) { if(escape) escape=false; else if(c=='\\') escape=true; else if(c=='"') quoted=false; }
  else if(c=='"') quoted=true;
  else if(c=='{') { if(++opens!=1 || closes) { reply(0,F("ERROR"),Error::INVALID_JSON); return; } }
  else if(c=='}') ++closes;
  else if(c=='[' || c==']' || (closes && c!=' ' && c!='\t')) { reply(0,F("ERROR"),Error::INVALID_JSON); return; }
 }
 if(opens!=1 || closes!=1 || quoted) { reply(0,F("ERROR"),Error::INVALID_JSON); return; }
 StaticJsonDocument<128> doc;
 if(deserializeJson(doc,rx_) || !doc.is<JsonObject>()) { reply(0,F("ERROR"),Error::INVALID_JSON); return; }
 if(!doc["id"].is<uint32_t>() || !doc["id"].as<uint32_t>() || doc["id"].as<uint32_t>()>2147483647UL) { reply(0,F("ERROR"),Error::INVALID_ID); return; }
 Request request; request.id=doc["id"].as<uint32_t>();
 const char* cmd=doc["cmd"];
 if(!cmd) { reply(request.id,F("ERROR"),Error::INVALID_COMMAND); return; }
#define C(x) if(strcmp_P(cmd,PSTR(#x))==0) request.cmd=Command::x; else
 C(SORT) C(HOME) C(STOP) C(GET_STATUS) C(OPEN_GATE) C(CLOSE_GATE) C(RESET_ERROR) C(GET_COLOR) C(TEST_STEPPER) C(GET_MOTION_DIAG) C(GET_WEIGHT) C(TARE_WEIGHT) C(SET_SCALE)
 { reply(request.id,F("ERROR"),Error::INVALID_COMMAND); return; }
#undef C
 if(request.cmd==Command::SORT) {
  if(!doc["target"].is<uint8_t>() || doc["target"].as<uint8_t>()<1 || doc["target"].as<uint8_t>()>4) { reply(request.id,F("ERROR"),Error::INVALID_TARGET); return; }
  request.target=doc["target"];
 }
 if(request.cmd==Command::SET_SCALE) {
  if(!doc["factor"].is<float>() || !doc["offset"].is<int32_t>()) { reply(request.id,F("ERROR"),Error::INVALID_SCALE); return; }
  request.factor=doc["factor"].as<float>(); request.offset=doc["offset"].as<int32_t>();
  if(!LoadCellSensor::validCalibration(request.factor,request.offset)) { reply(request.id,F("ERROR"),Error::INVALID_SCALE); return; }
 }
 lastContact_=millis(); handler_(request);
}
void SerialProtocol::update() {
 flushOutput();
 if((used_ || dropping_) && millis()-lastByte_>=Config::RX_TIMEOUT_MS) {
  used_=0; dropping_=false; reply(0,F("ERROR"),Error::RX_TIMEOUT);
 }
 uint8_t budget=Config::RX_BUDGET;
 while(budget-- && Serial.available()) {
  char c=Serial.read(); lastByte_=millis();
  if(c=='\r') continue;
  if(c=='\n') {
   if(dropping_) reply(0,F("ERROR"),Error::LINE_TOO_LONG);
   else if(used_) { rx_[used_]=0; parse(); }
   used_=0; dropping_=false;
  } else if(!dropping_) {
   if(c==0 || used_>=Config::RX_SIZE-1) { used_=0; dropping_=true; }
   else rx_[used_++]=c;
  }
 }
}
