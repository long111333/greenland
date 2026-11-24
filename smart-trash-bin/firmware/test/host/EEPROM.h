#pragma once
#include <stdint.h>
#include <cstring>
class FakeEEPROM {
public:
 uint8_t bytes[1024];
 unsigned writes=0;
 FakeEEPROM() { reset(); }
 void reset() { memset(bytes,0xFF,sizeof(bytes)); writes=0; }
 uint8_t read(int address) { return bytes[address]; }
 void update(int address,uint8_t value) { if(bytes[address]!=value) { bytes[address]=value; ++writes; } }
};
inline FakeEEPROM EEPROM;
