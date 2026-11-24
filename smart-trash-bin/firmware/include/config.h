#pragma once
#include <Arduino.h>
#include "loadcell_calibration.h"
namespace Config {
constexpr unsigned long BAUD=115200;
constexpr uint16_t SERVO_TRAVEL_MS=2700, SERVO_SETTLE_MS=400;
constexpr bool SERVO_2_REVERSED=false;
constexpr uint8_t GATE_CLOSED=0, GATE_OPEN=180;
constexpr float STEPPER_SPEED=1200, HOME_SPEED=600, STEPPER_ACCEL=700;
// 600 steps/s x 50ms tracking poll = 30 steps between observations, matching
// the former 150 steps/s x 200ms spacing. Stationary votes remain 200ms apart.
constexpr float TARGET_SEARCH_SPEED=600;
constexpr long TEST_STEPPER_STEPS=1000;
constexpr uint16_t TEST_STEPPER_TIMEOUT_MS=6000;
constexpr uint8_t STACK_MARKER_MARGIN=64;
constexpr long SEARCH_STEPS=15000;
constexpr int8_t HOME_DIRECTION=1;
constexpr int8_t SORT_DIRECTION=1;
constexpr uint8_t HOME_POSITION=1, MAX_TARGET_CAPTURES=3;
// One deadline and step budget for the entire search, including verification/retries.
constexpr uint32_t HOME_TIMEOUT_MS=60000, ROTATE_TIMEOUT_MS=40000;
constexpr uint16_t VERIFY_MS=1500, HOLD_MS=1200, GATE_TIMEOUT_MS=4000;
constexpr uint32_t LINK_TIMEOUT_MS=6000;
constexpr uint16_t TELEMETRY_MS=1000, RX_TIMEOUT_MS=500;
constexpr uint8_t RX_SIZE=128, RX_BUDGET=64;
constexpr uint16_t TX_SIZE=384, FRAME_SIZE=240;
// GY-33 module protocol from the supplied sketch, not the bare TCS34725 bus.
constexpr uint8_t COLOR_ADDRESS=0x5A, COLOR_DATA_REGISTER=0x00;
constexpr uint16_t COLOR_SAMPLE_MS=200, COLOR_STALE_MS=800, COLOR_MIN_CLEAR=100;
constexpr uint16_t COLOR_TRACK_MS=50;
constexpr uint16_t COLOR_LOG_MS=2000;
constexpr float COLOR_MAX_DISTANCE=0.07f, COLOR_MARGIN=0.03f;
// Provisional BLACK-only limits: real marker 130/235/234, Clear=630 (2026-11-24).
// Reject brighter neutral backgrounds; validate again if lighting/distance changes.
constexpr float BLACK_MAX_DISTANCE=0.018f;
constexpr uint16_t BLACK_MIN_CLEAR=450, BLACK_MAX_CLEAR=850;
constexpr uint8_t COLOR_HISTORY_SIZE=5, COLOR_REQUIRED_MATCHES=4;
// channel / (R+G+B); positions 1=RED, 2=BLUE, 3=GREEN, 4=BLACK.
// Measured 2026-11-15, 12 samples/marker; source: calibration/gy33-2026-11-15.json.
constexpr float COLOR_REFERENCE[4][3]={
 {0.446627f,0.265944f,0.287429f}, // RED / HOME
 {0.175560f,0.320092f,0.504347f}, // BLUE
 {0.189267f,0.463051f,0.347682f}, // GREEN
 {0.217028f,0.392321f,0.390651f}  // BLACK: updated 2026-11-24
};
constexpr uint16_t I2C_TIMEOUT_US=1500;
constexpr uint32_t ULTRA_PERIOD_US=100000, ULTRA_TIMEOUT_US=25000;
constexpr uint16_t ULTRA_MIN_PULSE_US=116, ULTRA_TRIGGER_US=10;
constexpr uint8_t ULTRA_WINDOW=3, ULTRA_FAILURE_LIMIT=3;
constexpr uint16_t FULL_MM=100, FULL_HYSTERESIS_MM=30;
constexpr uint8_t MONITORED_BIN=1;
constexpr bool REJECT_FULL=true, REJECT_UNKNOWN_BIN=true;
constexpr bool DEBUG_COLOR=true, TRACE_STATES=true, ENABLE_WATCHDOG=false;
constexpr uint16_t SCALE_STALE_MS=750, SCALE_TARE_TIMEOUT_MS=5000;
constexpr uint8_t SCALE_TARE_SAMPLES=20, SCALE_FILTER_DIVISOR=4, SCALE_CLOCK_US=1;
constexpr uint16_t SCALE_EEPROM_ADDRESS=32;
constexpr uint32_t SCALE_MAGIC=0x48583731UL;
constexpr float SCALE_DEADBAND_KG=0.003f, SCALE_FACTOR_LIMIT=1.0e12f;
constexpr float SCALE_FACTOR=LoadCellCalibration::FACTOR;
constexpr int32_t SCALE_OFFSET=LoadCellCalibration::OFFSET;
constexpr bool SCALE_CALIBRATED=LoadCellCalibration::CALIBRATED;
static_assert(GATE_CLOSED < GATE_OPEN && GATE_OPEN <= 180, "Invalid servo range");
static_assert(HOME_DIRECTION==1 || HOME_DIRECTION==-1, "Invalid direction");
static_assert(SORT_DIRECTION==1 || SORT_DIRECTION==-1, "Invalid sort direction");
static_assert(TARGET_SEARCH_SPEED>0 && TARGET_SEARCH_SPEED<=STEPPER_SPEED, "Invalid search speed");
static_assert(COLOR_REQUIRED_MATCHES>COLOR_HISTORY_SIZE/2 && COLOR_REQUIRED_MATCHES<=COLOR_HISTORY_SIZE, "Invalid color vote");
static_assert(VERIFY_MS>COLOR_SAMPLE_MS*COLOR_HISTORY_SIZE, "Verification must allow a fresh history");
static_assert(COLOR_STALE_MS>COLOR_SAMPLE_MS, "Stale timeout too short");
static_assert(COLOR_TRACK_MS>0 && COLOR_TRACK_MS<=COLOR_SAMPLE_MS, "Invalid tracking poll");
static_assert(GATE_TIMEOUT_MS>SERVO_TRAVEL_MS+SERVO_SETTLE_MS, "Gate timeout too short");
static_assert(MONITORED_BIN>=1 && MONITORED_BIN<=4, "Invalid monitored bin");
static_assert(ULTRA_WINDOW>=3 && ULTRA_WINDOW%2==1, "Median window must be odd");
static_assert(SCALE_TARE_SAMPLES>0 && SCALE_TARE_SAMPLES<=128, "Tare accumulator overflow");
}
