// This target links the real pinned AccelStepper, not the simple state-test mock.
#include <cassert>
#include <cstdio>
#include "controllers/StepperController.h"
#include "config.h"
#include "pins.h"
uint32_t fakeMillis=0,fakeMicros=0;
uint8_t fakePins[32]={};
FakeSerialPort Serial;
uint8_t phase() {
 return fakePins[Pins::IN1] | (fakePins[Pins::IN2]<<1) | (fakePins[Pins::IN3]<<2) | (fakePins[Pins::IN4]<<3);
}
void advance(StepperController& motor,uint32_t budgetUs,bool work) {
 uint32_t start=fakeMicros;
 uint32_t calls=0;
 uint8_t previous=phase();
 while(motor.isMoving() && fakeMicros-start<budgetUs) {
  fakeMicros+=100;
  if(work) {
   ++calls;
   if(calls%2000==0) fakeMicros+=2000; // Representative I2C/main-loop pause.
   if(calls%125==0) fakeMicros+=350; // Representative HX711 read at the faster ADC rate.
  }
  fakeMillis=fakeMicros/1000;
  motor.update();
  uint8_t next=phase();
  if(previous && next!=previous) {
   uint8_t changed=previous^next;
   assert(changed && !(changed&(changed-1))); // Exactly one coil-bit per half-step.
  }
  previous=next;
 }
}
int main() {
 StepperController motor;
 motor.begin(); motor.setReady(true); motor.testMove();
 advance(motor,Config::TEST_STEPPER_TIMEOUT_MS*1000UL,true);
 assert(!motor.isMoving() && !motor.timedOut());
 auto diagnostics=motor.diagnostics();
 assert(diagnostics.emittedSteps==1000 && diagnostics.maxRunGapUs==2450);
 assert(phase()!=0); // Hold at completion.

 motor.setReady(true); motor.setHoming(true); motor.moveSteps(1000);
 advance(motor,12000000UL,true);
 assert(!motor.isMoving() && motor.diagnostics().emittedSteps==1000);

 motor.setReady(true); motor.setHoming(false); motor.moveSteps(1000);
 while(motor.diagnostics().emittedSteps<31) {
  fakeMicros+=100; fakeMillis=fakeMicros/1000; motor.update();
 }
 uint8_t held=phase(); motor.haltAndHold(); assert(phase()==held);
 motor.setReady(true); motor.moveSteps(-40);
 advance(motor,2000000UL,false);
 assert(!motor.isMoving() && motor.diagnostics().emittedSteps==40);
 motor.stop(); assert(phase()==0);
 puts("Real AccelStepper: 1000/700 baseline, loaded polling, half-step phase and reverse resume passed");
}
