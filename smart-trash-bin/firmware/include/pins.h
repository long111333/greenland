#pragma once
#include <Arduino.h>
namespace Pins {
constexpr uint8_t SERVO_1=6, SERVO_2=7;
constexpr uint8_t IN1=8, IN2=9, IN3=10, IN4=11;
constexpr uint8_t TRIG=2, ECHO=3, COLOR_SDA=A4, COLOR_SCL=A5;
constexpr uint8_t HX711_DOUT=4, HX711_SCK=5;
constexpr bool loadCellPinFree(uint8_t pin) {
 return pin>1 && pin<20 && pin!=SERVO_1 && pin!=SERVO_2 && pin!=IN1 && pin!=IN2 && pin!=IN3 && pin!=IN4 && pin!=TRIG && pin!=ECHO && pin!=COLOR_SDA && pin!=COLOR_SCL;
}
static_assert(HX711_DOUT!=HX711_SCK && loadCellPinFree(HX711_DOUT) && loadCellPinFree(HX711_SCK), "HX711 conflicts with existing hardware pins");
}
