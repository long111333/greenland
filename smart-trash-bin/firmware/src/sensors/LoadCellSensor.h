#pragma once
#include "protocol.h"
class LoadCellSensor {
public:
 void begin(); void update();
 ScaleReading reading() const;
 bool startTare(); bool setCalibration(float factor,int32_t offset);
 bool busy() const { return operation_!=Operation::IDLE; }
 Error operationError() const { return operationError_; }
 void cancel();
 static bool validCalibration(float factor,int32_t offset);
private:
 enum class Operation : uint8_t { IDLE, TARE, SAVE };
 static constexpr uint8_t RECORD_SIZE=18;
 Operation operation_=Operation::IDLE;
 Error operationError_=Error::NONE;
 int32_t raw_=0,filtered_=0,offset_=0,sum_=0;
 float factor_=1;
 uint32_t lastSample_=0,operationStarted_=0;
 uint16_t sequence_=0,generation_=0;
 uint8_t tareCount_=0,saveIndex_=0,slot_=1,record_[RECORD_SIZE]={};
 bool received_=false,calibrated_=false;
 bool readAdc(int32_t& value); void save(float factor,int32_t offset,bool calibrated);
 void updateSave(); bool load(uint8_t slot,bool apply);
 static uint16_t crc(const uint8_t* data,uint8_t length);
};
