// Vehicle Control Interface
#include <stdint.h>

extern int CAN_Send(uint8_t instance, void* msg);
extern int LaneDetection_GetWarningLevel(float deviation);
extern float LaneDetection_CalculateDeviation(void* left, void* right);

typedef struct {
    uint32_t id;
    uint8_t data[8];
    uint8_t length;
} CAN_Message;

#define CAN_ID_STEERING 0x100
#define CAN_ID_BRAKE    0x101
#define CAN_ID_THROTTLE 0x102
#define CAN_ID_WARNING  0x200

static float current_speed_kmh = 0.0f;
static float steering_angle_deg = 0.0f;

void VehicleControl_SetSteering(float angle_deg) {
    CAN_Message msg;
    msg.id = CAN_ID_STEERING;
    msg.length = 4;
    
    int16_t angle_int = (int16_t)(angle_deg * 100.0f);
    msg.data[0] = angle_int >> 8;
    msg.data[1] = angle_int & 0xFF;
    
    CAN_Send(0, &msg);
    steering_angle_deg = angle_deg;
}

void VehicleControl_ApplyBrake(uint8_t pressure_percent) {
    CAN_Message msg;
    msg.id = CAN_ID_BRAKE;
    msg.length = 2;
    msg.data[0] = pressure_percent;
    
    CAN_Send(0, &msg);
}

void VehicleControl_SetThrottle(uint8_t percent) {
    CAN_Message msg;
    msg.id = CAN_ID_THROTTLE;
    msg.length = 2;
    msg.data[0] = percent;
    
    CAN_Send(0, &msg);
}

void VehicleControl_SendWarning(uint8_t level, uint8_t type) {
    CAN_Message msg;
    msg.id = CAN_ID_WARNING;
    msg.length = 3;
    msg.data[0] = level;
    msg.data[1] = type;
    
    CAN_Send(0, &msg);
}

void VehicleControl_LaneKeepingAssist(float deviation) {
    int warning_level = LaneDetection_GetWarningLevel(deviation);
    
    if (warning_level == 2) {
        // Critical - apply steering correction
        VehicleControl_SetSteering(-deviation * 5.0f);
        VehicleControl_SendWarning(2, 0x01);
    } else if (warning_level == 1) {
        VehicleControl_SendWarning(1, 0x01);
    }
}

void VehicleControl_EmergencyBrake(uint8_t collision_risk) {
    if (collision_risk > 0) {
        VehicleControl_ApplyBrake(80);
        VehicleControl_SendWarning(2, 0x02);
    }
}
