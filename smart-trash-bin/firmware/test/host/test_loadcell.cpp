#include <cassert>
#include <cstdio>
#include <cmath>
#include <EEPROM.h>
#include <avr/eeprom.h>
#include "sensors/LoadCellSensor.h"
#include "config.h"
#include "pins.h"
uint32_t fakeMillis=0,fakeMicros=0;
uint8_t fakePins[32]={};
FakeSerialPort Serial;
static uint32_t adcBits=0,highStarted=0,maxHigh=0;
static uint8_t pulses=0;
static bool ready=false;
static bool clockHigh=false;
int readPin(uint8_t pin) {
 if(pin!=Pins::HX711_DOUT) return fakePins[pin];
 if(!ready) return HIGH;
 if(pulses==0) return LOW;
 if(pulses<=24) return (adcBits>>(24-pulses))&1;
 return HIGH;
}
void writePin(uint8_t pin,uint8_t value) {
 if(pin!=Pins::HX711_SCK) return;
 if(value==HIGH) { ++pulses; highStarted=fakeMicros; clockHigh=true; }
 else if(clockHigh) { uint32_t width=fakeMicros-highStarted; if(width>maxHigh) maxHigh=width; clockHigh=false; }
}
void feed(LoadCellSensor& scale,int32_t raw) {
 fakeMillis+=100; fakeMicros=fakeMillis*1000UL;
 adcBits=static_cast<uint32_t>(raw)&0xFFFFFF; pulses=0; ready=true;
 scale.update(); ready=false;
 assert(pulses==25 && maxHigh<60);
}
void finish(LoadCellSensor& scale) {
 for(int i=0;i<30 && scale.busy();i++) { fakeMillis+=4; scale.update(); }
 assert(!scale.busy() && scale.operationError()==Error::NONE);
}
int main() {
 fakeReadHook=readPin; fakeWriteHook=writePin;
 EEPROM.reset();
 LoadCellSensor scale; scale.begin();
 assert(!scale.reading().healthy);
 feed(scale,-123456); assert(scale.reading().raw==-123456 && scale.reading().healthy);
 feed(scale,8388607); assert(!scale.reading().healthy);
 feed(scale,-8388608); assert(!scale.reading().healthy);
 feed(scale,123456); fakeMillis+=Config::SCALE_STALE_MS; assert(!scale.reading().healthy);
 assert(!scale.setCalibration(NAN,0)); assert(!scale.setCalibration(1,0)); assert(!scale.setCalibration(10000,8388608));
 assert(scale.setCalibration(-100000,1000)); finish(scale);
 for(int i=0;i<30;i++) feed(scale,-19000);
 assert(scale.reading().calibrated && fabs(scale.reading().weightKg-0.2f)<0.001f);
 LoadCellSensor reboot; reboot.begin(); assert(reboot.reading().factor==-100000 && reboot.reading().offset==1000);
 assert(reboot.startTare());
 for(int i=0;i<Config::SCALE_TARE_SAMPLES;i++) feed(reboot,2000);
 finish(reboot); assert(reboot.reading().offset==2000);
 LoadCellSensor afterTare; afterTare.begin(); assert(afterTare.reading().offset==2000);
 assert(afterTare.startTare()); fakeMillis+=Config::SCALE_TARE_TIMEOUT_MS; afterTare.update();
 assert(!afterTare.busy() && afterTare.operationError()==Error::SCALE_TIMEOUT);
 // Interrupted update cannot invalidate the previous slot.
 assert(afterTare.setCalibration(500000,100));
 afterTare.update(); afterTare.update(); afterTare.cancel();
 LoadCellSensor afterInterrupted; afterInterrupted.begin(); assert(afterInterrupted.reading().offset==2000);
 // A not-ready EEPROM must not block the main loop or issue a byte write.
 assert(afterInterrupted.setCalibration(500000,100)); fakeEEPROMReady=false; unsigned oldWrites=EEPROM.writes;
 afterInterrupted.update(); assert(afterInterrupted.busy() && EEPROM.writes==oldWrites);
 fakeEEPROMReady=true; finish(afterInterrupted);
 // Corrupt newest slot -> valid older slot is used.
 EEPROM.bytes[Config::SCALE_EEPROM_ADDRESS+16]^=1;
 LoadCellSensor older; older.begin(); assert(older.reading().offset==2000);
 EEPROM.bytes[Config::SCALE_EEPROM_ADDRESS+18+16]^=1;
 LoadCellSensor corrupt; corrupt.begin(); assert(corrupt.reading().calibrated==Config::SCALE_CALIBRATED);
 puts("HX711 signed ADC/25 pulses/stale/tare/negative factor/EEPROM journal and failure tests passed");
}
