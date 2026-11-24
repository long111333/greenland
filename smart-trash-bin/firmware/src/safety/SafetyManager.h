#pragma once
#include "controllers/SortingController.h"
class SafetyManager {
public:
 void update(SortingController& sorter,ServoController& gate,StepperController& stepper,ColorSensor& color,SerialProtocol& serial);
};
