#pragma once
#include <Arduino.h>
class FakeWire {
 uint8_t reg_=0, writes_=0, remaining_=0;
public:
 uint8_t regs[256]={}; bool fault=false;
 uint8_t lastAddress=0,lastRegister=0,readLength=8;
 bool timeoutFlag=false;
 void begin() {} void setWireTimeout(uint16_t,bool) {}
 void clearWireTimeoutFlag() { timeoutFlag=false; } bool getWireTimeoutFlag() { return timeoutFlag; }
 void beginTransmission(uint8_t address) { writes_=0; lastAddress=address; }
 void write(uint8_t value) { if(!writes_++) lastRegister=reg_=value; else regs[reg_]=value; }
 uint8_t endTransmission(bool=true) { return fault ? 4 : 0; }
 uint8_t requestFrom(uint8_t,uint8_t count) { remaining_=fault ? 0 : std::min(count,readLength); return remaining_; }
 int available() { return remaining_; }
 uint8_t read() { if(remaining_) --remaining_; return regs[reg_++]; }
};
extern FakeWire Wire;
