#pragma once
class AccelStepper {
 long remaining=0,position=0;
public:
 bool outputsEnabled=false;
 float maxSpeed=0;
 enum { HALF4WIRE=8 };
 AccelStepper(int,int,int,int,int,bool) {}
 void setMaxSpeed(float speed) { maxSpeed=speed; } void setAcceleration(float) {}
 void disableOutputs() { outputsEnabled=false; } void enableOutputs() { outputsEnabled=true; }
 void setCurrentPosition(long value) { position=value; remaining=0; }
 long currentPosition() { return position; }
 void move(long steps) { remaining=steps; }
 void run() { if(remaining>0) { --remaining; ++position; } else if(remaining<0) { ++remaining; --position; } }
 long distanceToGo() { return remaining; }
};
