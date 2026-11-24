#pragma once
#include <stdint.h>
#include <stdlib.h>
#include <algorithm>
#include <string>
#include <deque>
#include <cstring>
#include <cmath>
#include <cstdio>
using boolean=bool;
using std::max;
extern uint32_t fakeMillis;
inline uint32_t millis() { return fakeMillis; }
extern uint32_t fakeMicros;
inline uint32_t micros() { return fakeMicros; }
inline void delayMicroseconds(unsigned int us) { fakeMicros+=us; }
inline void yield() {}
template<class T> T constrain(T v,int low,int high) { return std::max(T(low),std::min(v,T(high))); }
using std::min;
class __FlashStringHelper;
#define F(x) reinterpret_cast<const __FlashStringHelper*>(x)
constexpr uint8_t A4=18,A5=19;
constexpr uint8_t INPUT=0,OUTPUT=1,LOW=0,HIGH=1,CHANGE=2;
constexpr uint8_t INPUT_PULLUP=2;
inline int (*fakeReadHook)(uint8_t)=nullptr;
inline void (*fakeWriteHook)(uint8_t,uint8_t)=nullptr;
extern uint8_t fakePins[32];
inline void pinMode(uint8_t,uint8_t) {}
inline void digitalWrite(uint8_t pin,uint8_t value) { fakePins[pin]=value; if(fakeWriteHook) fakeWriteHook(pin,value); }
inline int digitalRead(uint8_t pin) { return fakeReadHook ? fakeReadHook(pin) : fakePins[pin]; }
inline char* dtostre(double value,char* output,unsigned char precision,unsigned char) {
 std::snprintf(output,20,"%.*e",int(precision),value); return output;
}
inline int digitalPinToInterrupt(int pin) { return pin; }
inline void attachInterrupt(int,void (*)(),int) {}
class FakeSerialPort {
public:
 std::deque<char> input;
 std::string output;
 int writeSpace=63;
 void begin(unsigned long) {}
 int available() const { return int(input.size()); }
 int availableForWrite() const { return writeSpace; }
 int read() { char c=input.front(); input.pop_front(); return c; }
 void write(char c) { output+=c; }
};
extern FakeSerialPort Serial;
