#pragma once
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <string>
#define PSTR(s) (s)
#define strcmp_P strcmp
#define strcpy_P strcpy
#define pgm_read_byte(p) (*reinterpret_cast<const unsigned char*>(p))
inline int snprintf_P(char* dest,size_t size,const char* format,...) {
 std::string converted=format;
 size_t pos=0;
 while((pos=converted.find("%S",pos))!=std::string::npos) { converted.replace(pos,2,"%s"); pos+=2; }
 va_list args; va_start(args,format);
 int result=vsnprintf(dest,size,converted.c_str(),args);
 va_end(args); return result;
}
