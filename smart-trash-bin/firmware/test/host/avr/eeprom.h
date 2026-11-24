#pragma once
inline bool fakeEEPROMReady=true;
inline bool eeprom_is_ready() { return fakeEEPROMReady; }
