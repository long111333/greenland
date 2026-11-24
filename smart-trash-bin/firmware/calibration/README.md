# GY-33 calibration

`gy33-2026-11-15.json` archives the operator-labeled capture used in `include/config.h`:
12 samples each for RED/HOME, BLUE, GREEN and BLACK. References use RGB divided by
the sum of RGB. Thresholds remain Euclidean distance 0.07, runner-up margin 0.03,
Clear >= 100 and a 4-of-5 vote.

The host I/O test replays all 48 raw samples against the real ColorSensor driver.
This checks the captured training set, not independent validation of backgrounds,
marker edges or different lighting. Keep sensor distance/lighting fixed and verify
new observations on the installed mechanism after uploading firmware.
