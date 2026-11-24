#pragma once
#include "config.h"
#include "protocol.h"
class SerialProtocol {
public:
 using Handler=void (*)(const Request&);
 void begin(Handler handler); void update(); void flushOutput();
 void reply(uint32_t id,const __FlashStringHelper* status,Error error=Error::NONE,uint8_t position=0);
 void telemetry(uint32_t id,SortingState state,uint8_t position,uint16_t mm,BinStatus bin,bool homed,Error error);
 void color(uint32_t id,uint16_t r,uint16_t g,uint16_t b,uint16_t c,uint8_t position,bool healthy);
 void stateChange(uint32_t id,SortingState from,SortingState to);
 void motionDiagnostics(uint32_t id,const MotionDiagnostics& diagnostics);
 void weight(uint32_t id,const ScaleReading& reading);
 uint32_t lastContact() const { return lastContact_; }
 bool overflowed() const { return overflow_; }
 void clearOverflow() { overflow_=false; }
private:
 Handler handler_=nullptr;
 char rx_[Config::RX_SIZE]={},tx_[Config::TX_SIZE]={};
 uint8_t used_=0; bool dropping_=false,overflow_=false;
 uint16_t head_=0,tail_=0;
 uint32_t lastByte_=0,lastContact_=0;
 uint16_t freeSpace() const;
 void enqueue(const char* data,bool optional=false); void parse();
 bool startFrame(uint16_t bound,bool optional=false,uint16_t reserve=0);
 void append(const __FlashStringHelper* text); void appendUnsigned(uint32_t number);
 void appendChar(char value);
 void appendSigned(int32_t number); void appendFloat(float number);
};
