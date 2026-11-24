#include <cassert>
#include <cstdio>
#include <Arduino.h>
#include <Wire.h>
#include "communication/SerialProtocol.h"
#include "sensors/ColorSensor.h"
#include "sensors/UltrasonicSensor.h"
#include "pins.h"
#include "CalibrationSamples.h"
#include <ArduinoJson.h>
uint32_t fakeMillis=0,fakeMicros=0;
uint8_t fakePins[32]={};
FakeSerialPort Serial;
FakeWire Wire;
int handled=0; Request last;
void handle(const Request& request) { ++handled; last=request; }
void drain(SerialProtocol& serial) { for(int i=0;i<20;i++) serial.flushOutput(); }
void send(SerialProtocol& serial,const std::string& input) {
 Serial.output.clear();
 for(char c:input) Serial.input.push_back(c);
 while(Serial.available()) { serial.update(); drain(serial); }
 drain(serial);
}
void raw(uint16_t r,uint16_t g,uint16_t b,uint16_t clear) {
 uint16_t values[]={r,g,b,clear};
 for(int i=0;i<4;i++) { Wire.regs[i*2]=values[i]>>8; Wire.regs[i*2+1]=values[i]&255; }
}
void sample(ColorSensor& color) { fakeMillis+=Config::COLOR_SAMPLE_MS; color.update(); }
void echo(UltrasonicSensor& sensor,uint32_t width) {
 fakeMicros+=Config::ULTRA_PERIOD_US; sensor.update();
 fakeMicros+=10; sensor.update();
 fakePins[Pins::ECHO]=HIGH; sensor.echoInterrupt();
 fakeMicros+=width; fakePins[Pins::ECHO]=LOW; sensor.echoInterrupt(); sensor.update();
}
int main() {
 SerialProtocol protocol; protocol.begin(handle);
 send(protocol,"{\"id\":101,\"cmd\":\"SORT\",\"target\":3}\n"); assert(handled==1 && last.id==101 && last.target==3);
 const char* invalid[]={"{bad}\n","{\"id\":true,\"cmd\":\"STOP\"}\n","{\"id\":-1,\"cmd\":\"STOP\"}\n","{\"id\":1,\"cmd\":\"SORT\",\"target\":0}\n","{\"id\":1,\"cmd\":\"SORT\",\"target\":2.5}\n","{\"id\":1,\"cmd\":\"NOPE\"}\n","{\"id\":1,\"cmd\":\"HOME\"} {}\n","{\"id\":1,\"cmd\":{}}\n"};
 for(const auto input:invalid) { send(protocol,input); assert(handled==1); assert(Serial.output.find("ERROR")!=std::string::npos); }
 send(protocol,std::string(180,'x')+"\n{\"id\":102,\"cmd\":\"STOP\"}\n"); assert(handled==2 && last.cmd==Command::STOP); assert(Serial.output.find("LINE_TOO_LONG")!=std::string::npos);
 send(protocol,"{\"id\":"); fakeMillis+=Config::RX_TIMEOUT_MS; protocol.update(); drain(protocol); assert(Serial.output.find("RX_TIMEOUT")!=std::string::npos);
 send(protocol,"{\"id\":103,\"cmd\":\"HOME\"}\n"); assert(handled==3);
 Serial.output.clear(); protocol.telemetry(104,SortingState::IDLE,3,85,BinStatus::FULL,true,Error::NONE); drain(protocol); assert(Serial.output.find("\"distance_cm\":8.5")!=std::string::npos); assert(Serial.output.find("\"homed\":true")!=std::string::npos);
 Serial.writeSpace=0;
 for(int i=0;i<20;i++) { protocol.reply(i,F("COMPLETE")); }
 assert(protocol.overflowed()); protocol.clearOverflow(); Serial.writeSpace=63; drain(protocol);

 Serial.output.clear(); protocol.stateChange(105,SortingState::ROTATING,SortingState::VERIFY_POSITION); drain(protocol);
 assert(Serial.output.find("STATE_CHANGE")!=std::string::npos);
 assert(Serial.output.find("VERIFY_POSITION")!=std::string::npos);
 Serial.output.clear();
 protocol.telemetry(0,SortingState::IDLE,1,200,BinStatus::NOT_FULL,true,Error::NONE);
 protocol.flushOutput();
 protocol.color(0,506,235,259,1000,1,true);
 drain(protocol);
 assert(Serial.output.find("TELEMETRY")!=std::string::npos && Serial.output.find("COLOR")!=std::string::npos);
 // Exercise the streaming writer at numeric limits and across many ring wraps.
 for(int round=0;round<100;round++) {
  Serial.output.clear();
  protocol.telemetry(2147483647UL,SortingState::VERIFY_POSITION,255,65535,BinStatus::NOT_FULL,false,Error::POSITION_TIMEOUT);
  drain(protocol);
  StaticJsonDocument<768> parsed;
  assert(!deserializeJson(parsed,Serial.output.c_str()));
  assert(parsed["id"].as<uint32_t>()==2147483647UL && parsed["position"].as<int>()==255);
  assert(parsed["homed"].as<bool>()==false);
  Serial.output.clear();
  MotionDiagnostics motion; motion.runCalls=UINT32_MAX; motion.emittedSteps=UINT32_MAX; motion.maxRunGapUs=UINT32_MAX; motion.nominalIntervalUs=UINT32_MAX;
  protocol.motionDiagnostics(2147483647UL,motion); drain(protocol);
  assert(!deserializeJson(parsed,Serial.output.c_str()));
  assert(parsed["emitted_steps"].as<uint32_t>()==UINT32_MAX);
  Serial.output.clear(); protocol.color(2147483647UL,65535,65535,65535,65535,255,false); drain(protocol);
  assert(!deserializeJson(parsed,Serial.output.c_str()));
  assert(parsed["clear"].as<int>()==65535 && parsed["healthy"].as<bool>()==false);
 }
 send(protocol,"{\"id\":104,\"cmd\":\"TEST_STEPPER\"}\n"); assert(last.cmd==Command::TEST_STEPPER);
 send(protocol,"{\"id\":105,\"cmd\":\"GET_MOTION_DIAG\"}\n"); assert(last.cmd==Command::GET_MOTION_DIAG);
 send(protocol,"{\"id\":106,\"cmd\":\"SET_SCALE\",\"factor\":-500000.25,\"offset\":-123456}\n");
 assert(last.cmd==Command::SET_SCALE && last.factor==-500000.25f && last.offset==-123456);
 int beforeInvalid=handled;
 send(protocol,"{\"id\":107,\"cmd\":\"SET_SCALE\",\"factor\":true,\"offset\":0}\n"); assert(handled==beforeInvalid);
 send(protocol,"{\"id\":108,\"cmd\":\"SET_SCALE\",\"factor\":1,\"offset\":0}\n"); assert(handled==beforeInvalid);
 send(protocol,"{\"id\":109,\"cmd\":\"SET_SCALE\",\"factor\":50000,\"offset\":8388608}\n"); assert(handled==beforeInvalid);
 send(protocol,"{\"id\":110,\"cmd\":\"GET_WEIGHT\"}\n"); assert(last.cmd==Command::GET_WEIGHT);
 Serial.output.clear();
 ScaleReading weight; weight.raw=-8388608; weight.offset=-123456; weight.factor=-500000.25f;
 weight.healthy=weight.calibrated=true; weight.weightKg=0.2f;
 protocol.weight(111,weight); drain(protocol);
 StaticJsonDocument<768> weightDoc;
 assert(!deserializeJson(weightDoc,Serial.output.c_str()));
 assert(weightDoc["raw"].as<int32_t>()==-8388608 && weightDoc["offset"].as<int32_t>()==-123456);
 assert(fabs(weightDoc["weight_kg"].as<float>()-0.2f)<0.000001f);
 Serial.output.clear(); weight.healthy=false; protocol.weight(112,weight); drain(protocol);
 assert(!deserializeJson(weightDoc,Serial.output.c_str())); assert(weightDoc["weight_kg"].isNull());

 ColorSensor color; color.begin(); assert(!color.isSensorHealthy());
 raw(769,458,495,1234);
 uint16_t previousSample=color.sampleSequence();
 for(uint8_t i=1;i<Config::COLOR_HISTORY_SIZE;i++) {
  sample(color); assert(!color.isPositionStable());
  assert(color.getInstantPosition()==1 && color.sampleSequence()!=previousSample);
  previousSample=color.sampleSequence();
 }
 sample(color); assert(color.getDetectedPosition()==1);
 assert(Wire.lastAddress==0x5A && Wire.lastRegister==0x00);
 assert(color.raw().r==769 && color.raw().g==458 && color.raw().b==495 && color.raw().c==1234);
 // Brightness scales preserve chromaticity, including RGB sums above 65535.
 raw(44663,26594,28743,50000); sample(color); assert(color.getDetectedPosition()==1);
 // Exactly 4/5 is valid; a second unknown removes the majority.
 raw(1,1,1,99); sample(color); assert(color.getDetectedPosition()==1);
 sample(color); assert(color.getDetectedPosition()==0 && color.isSensorHealthy());
 for(uint8_t p=1;p<=4;p++) {
  color.resetStability();
  raw(uint16_t(Config::COLOR_REFERENCE[p-1][0]*1000+0.5f),uint16_t(Config::COLOR_REFERENCE[p-1][1]*1000+0.5f),uint16_t(Config::COLOR_REFERENCE[p-1][2]*1000+0.5f),p==4 ? 630 : 100);
  for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
  assert(color.getDetectedPosition()==p); // BLACK is position 4, never UNKNOWN.
 }
 color.resetStability(); raw(212,425,363,1000); // Between GREEN and BLACK: ambiguous.
 for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==0);
 raw(1000,0,0,1000); for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==0); // Too far from every reference.
 raw(0,0,0,1000); sample(color); assert(color.getDetectedPosition()==0);
 raw(769,458,495,1000); for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==1);
 fakeMillis+=Config::COLOR_STALE_MS; assert(!color.isSensorHealthy());
 color.update(); assert(!color.isPositionStable()); // Old votes are not reused after a stall.
 for(uint8_t i=1;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==1);
 Wire.fault=true; sample(color); assert(!color.isSensorHealthy()); assert(color.raw().r==0);
 assert(color.getInstantPosition()==0);
 Wire.fault=false; sample(color); assert(color.isSensorHealthy() && !color.isPositionStable());
 Wire.readLength=4; sample(color); assert(!color.isSensorHealthy() && Wire.available()==0);
 Wire.readLength=8;
 for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==1); // Recovery needs a completely fresh history.
 for(const auto& measured:CALIBRATION_SAMPLES) {
  color.resetStability();
  raw(measured.r,measured.g,measured.b,measured.c);
  for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
  assert(color.getDetectedPosition()==measured.position);
 }
 puts("All 48 captured calibration samples recognized by the actual firmware color driver");
 // Real BLACK, falsely accepted backgrounds, and independent RGB/Clear rejection.
 const uint16_t blackCases[][5]={
  {130,235,234,630,4}, {270,445,420,1170,0},
  {244,402,380,630,0}, // Old log's Clear was corrupted; use synthetic in-range Clear.
  {270,445,420,630,0}, // Correct brightness cannot rescue wrong chromaticity.
  {130,235,234,1000,0}, {130,235,234,300,0},
  {130,235,234,450,4}, {130,235,234,850,4},
  {130,235,234,449,0}, {130,235,234,851,0}
 };
 for(const auto& reading:blackCases) {
  color.resetStability(); raw(reading[0],reading[1],reading[2],reading[3]);
  for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
  assert(color.getInstantPosition()==reading[4]);
  assert(color.getDetectedPosition()==reading[4]);
  assert(color.isSensorHealthy()); // UNKNOWN is classification failure, not I2C failure.
 }
 // Tracking polls may brake quickly but cannot fabricate extra stability votes.
 color.resetStability(); color.setTracking(true); raw(769,458,495,1725);
 uint16_t sequenceBefore=color.sampleSequence();
 for(int tick=1;tick<=20;tick++) {
  fakeMillis+=Config::COLOR_TRACK_MS; color.update();
  assert(color.getInstantPosition()==1);
  assert(color.sampleSequence()!=sequenceBefore); sequenceBefore=color.sampleSequence();
  if(tick<20) assert(!color.isPositionStable());
 }
 assert(color.isPositionStable());
 color.setTracking(false); color.resetStability();
 fakeMillis+=Config::COLOR_TRACK_MS; color.update(); assert(!color.isPositionStable());
 for(uint8_t i=0;i<Config::COLOR_HISTORY_SIZE;i++) sample(color);
 assert(color.getDetectedPosition()==1);

 UltrasonicSensor bin; bin.begin(); assert(bin.status()==BinStatus::UNKNOWN);
 for(int i=0;i<3;i++) { echo(bin,580); }
 assert(bin.status()==BinStatus::FULL);
 for(int i=0;i<3;i++) { echo(bin,696); }
 assert(bin.status()==BinStatus::FULL); // hysteresis at 12cm
 for(int i=0;i<3;i++) { echo(bin,1160); }
 assert(bin.status()==BinStatus::NOT_FULL);
 echo(bin,116); echo(bin,1160); echo(bin,1160); assert(bin.distanceMm()==200); // median rejects outlier
 for(int i=0;i<3;i++) { fakeMicros+=Config::ULTRA_PERIOD_US; bin.update(); fakeMicros+=10; bin.update(); fakeMicros+=Config::ULTRA_TIMEOUT_US; bin.update(); }
 assert(bin.status()==BinStatus::UNKNOWN && !bin.healthy());
 puts("Protocol/state events, GY-33 big-endian/4-of-5/Euclidean/fault recovery, ultrasonic tests passed");
}
