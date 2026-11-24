#include "MemoryMonitor.h"
#include "config.h"
#ifdef __AVR__
#include <avr/io.h>
extern char __heap_start;
static uint8_t* markerEnd=nullptr;
void MemoryMonitor::begin() {
 // No heap allocation in this application. Paint unused RAM once, leaving the
 // active startup stack untouched. Later scans measure the deepest overwritten byte.
 markerEnd=reinterpret_cast<uint8_t*>(SP)-Config::STACK_MARKER_MARGIN;
 for(uint8_t* p=reinterpret_cast<uint8_t*>(&__heap_start);p<markerEnd;++p) *p=0xA5;
}
uint16_t MemoryMonitor::minFreeBytes() {
 if(!markerEnd) return 0;
 auto* p=reinterpret_cast<uint8_t*>(&__heap_start);
 uint16_t freeBytes=0;
 while(p<markerEnd && *p==0xA5) { ++p; ++freeBytes; }
 return freeBytes;
}
#else
void MemoryMonitor::begin() {}
uint16_t MemoryMonitor::minFreeBytes() { return 0; }
#endif
