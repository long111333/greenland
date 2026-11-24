#pragma once
class Servo {
public:
 int angle=0; bool attached=false;
 void write(int a) { angle=a; }
 void attach(int) { attached=true; }
 void detach() { attached=false; }
};
