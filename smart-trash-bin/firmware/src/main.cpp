#include <Arduino.h>
#include <avr/wdt.h>
#include "controllers/SortingController.h"
#include "safety/SafetyManager.h"
#include "safety/MemoryMonitor.h"
// Disable inherited WDT before static initialization (bootloader must also support WDT).
void disableInheritedWatchdog() __attribute__((naked,section(".init3")));
void disableInheritedWatchdog() { MCUSR=0; wdt_disable(); }
ServoController gate;
StepperController stepper;
ColorSensor color;
UltrasonicSensor bin;
LoadCellSensor scale;
SerialProtocol protocol;
SortingController sorter(gate,stepper,color,bin,protocol,&scale);
SafetyManager safety;
void onRequest(const Request& request) { sorter.handle(request); }
void setup() {
 protocol.begin(onRequest); gate.begin(); stepper.begin(); color.begin(); bin.begin(); scale.begin(); sorter.begin();
 if(Config::ENABLE_WATCHDOG) wdt_enable(WDTO_2S);
 MemoryMonitor::begin();
}
void loop() {
 wdt_reset();
 // End the ultrasonic trigger pulse before potentially slower I2C/JSON operations.
 bin.update(); stepper.update(); gate.update(); protocol.update(); bin.update();
 color.update(); safety.update(sorter,gate,stepper,color,protocol); sorter.update();
 stepper.update(); scale.update();
 stepper.update(); protocol.flushOutput();
 static uint32_t lastTelemetry=0;
 if(millis()-lastTelemetry>=Config::TELEMETRY_MS) {
  lastTelemetry=millis(); sorter.report();
 }
 // Telemetry and 2-second color logs can become due together. Release available
 // UART space before optional color enqueue so quiet-link color logs aren't starved.
 protocol.flushOutput();
 static uint32_t lastColorLog=0;
 if(Config::DEBUG_COLOR && millis()-lastColorLog>=Config::COLOR_LOG_MS) {
  lastColorLog=millis();
  const auto& c=color.raw();
  protocol.color(0,c.r,c.g,c.b,c.c,color.getDetectedPosition(),color.isSensorHealthy());
 }
}
