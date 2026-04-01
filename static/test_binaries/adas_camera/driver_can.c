// CAN Bus Driver
#include <stdint.h>

extern void HAL_GPIO_Init(uint8_t port, uint8_t pin, uint8_t mode);

volatile uint32_t* CAN_BASE = (volatile uint32_t*)0x40006400;

typedef struct {
    uint32_t id;
    uint8_t data[8];
    uint8_t length;
} CAN_Message;

void CAN_Init(uint8_t instance, uint32_t baudrate) {
    HAL_GPIO_Init(0, 11, 0x09); // CAN_RX
    HAL_GPIO_Init(0, 12, 0x09); // CAN_TX
    
    CAN_BASE[instance * 16] = baudrate;
    CAN_BASE[instance * 16 + 1] = 0x01; // Enable
}

int CAN_Send(uint8_t instance, CAN_Message* msg) {
    if (msg->length > 8) return -1;
    
    CAN_BASE[instance * 16 + 2] = msg->id;
    CAN_BASE[instance * 16 + 3] = msg->length;
    
    for (uint8_t i = 0; i < msg->length; i++) {
        CAN_BASE[instance * 16 + 4 + i] = msg->data[i];
    }
    
    CAN_BASE[instance * 16 + 12] = 0x01; // Transmit
    
    return 0;
}

int CAN_Receive(uint8_t instance, CAN_Message* msg) {
    if (!(CAN_BASE[instance * 16 + 13] & 0x01)) {
        return -1; // No message
    }
    
    msg->id = CAN_BASE[instance * 16 + 2];
    msg->length = CAN_BASE[instance * 16 + 3] & 0x0F;
    
    for (uint8_t i = 0; i < msg->length; i++) {
        msg->data[i] = CAN_BASE[instance * 16 + 4 + i];
    }
    
    return 0;
}
