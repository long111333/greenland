#pragma once
#include <Arduino.h>
enum class Command : uint8_t { NONE, SORT, HOME, STOP, GET_STATUS, OPEN_GATE, CLOSE_GATE, RESET_ERROR, GET_COLOR, TEST_STEPPER, GET_MOTION_DIAG, GET_WEIGHT, TARE_WEIGHT, SET_SCALE };
enum class SortingState : uint8_t { INIT, HOMING, IDLE, ROTATING, VERIFY_POSITION, OPENING, HOLDING, CLOSING, COMPLETE, ERROR, CALIBRATING };
enum class BinStatus : uint8_t { NOT_FULL, FULL, UNKNOWN };
enum class Error : uint8_t { NONE, INVALID_JSON, INVALID_COMMAND, INVALID_ID, INVALID_TARGET, LINE_TOO_LONG, RX_TIMEOUT, BUSY, NOT_READY, GATE_UNSAFE, BIN_FULL, BIN_UNKNOWN, HOME_TIMEOUT, POSITION_TIMEOUT, COLOR_SENSOR, LINK_LOST, STOPPED, STATE_TIMEOUT, STALE_ID, ID_CONFLICT, TX_OVERFLOW, INVALID_SCALE, SCALE_TIMEOUT, EEPROM_ERROR };
struct Request { uint32_t id=0; Command cmd=Command::NONE; uint8_t target=0; float factor=0; int32_t offset=0; };
struct ScaleReading {
 int32_t raw=0,offset=0;
 uint16_t sequence=0;
 float factor=1,weightKg=0;
 bool healthy=false,calibrated=false,busy=false;
};
struct MotionDiagnostics {
 uint32_t runCalls=0, emittedSteps=0, maxRunGapUs=0, nominalIntervalUs=0;
 bool moving=false;
};
const __FlashStringHelper* errorName(Error e);
const __FlashStringHelper* stateName(SortingState s);
const __FlashStringHelper* binName(BinStatus s);
