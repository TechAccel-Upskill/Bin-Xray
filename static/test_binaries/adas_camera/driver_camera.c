// Camera Driver (OV5640 sensor via I2C)
#include <stdint.h>

extern void HAL_I2C_Init(uint8_t instance, uint32_t speed);
extern int HAL_I2C_Write(uint8_t instance, uint8_t addr, uint8_t* data, uint16_t len);
extern int HAL_I2C_Read(uint8_t instance, uint8_t addr, uint8_t* data, uint16_t len);
extern void HAL_GPIO_WritePin(uint8_t port, uint8_t pin, uint8_t state);

#define CAMERA_I2C_ADDR 0x3C
#define CAMERA_WIDTH 1920
#define CAMERA_HEIGHT 1080

static uint8_t camera_initialized = 0;

void Camera_Init(void) {
    HAL_I2C_Init(0, 400000);
    
    // Power on camera
    HAL_GPIO_WritePin(2, 10, 1);
    
    // Reset camera
    HAL_GPIO_WritePin(2, 11, 0);
    for (volatile int i = 0; i < 100000; i++);
    HAL_GPIO_WritePin(2, 11, 1);
    
    camera_initialized = 1;
}

int Camera_Configure(uint16_t width, uint16_t height, uint8_t fps) {
    if (!camera_initialized) return -1;
    
    uint8_t config[4] = {width >> 8, width & 0xFF, height >> 8, height & 0xFF};
    HAL_I2C_Write(0, CAMERA_I2C_ADDR, config, 4);
    
    return 0;
}

int Camera_CaptureFrame(uint8_t* buffer, uint32_t buffer_size) {
    if (!camera_initialized) return -1;
    
    // Trigger frame capture
    uint8_t cmd = 0x01;
    HAL_I2C_Write(0, CAMERA_I2C_ADDR, &cmd, 1);
    
    // Read frame data (simplified)
    uint32_t expected_size = CAMERA_WIDTH * CAMERA_HEIGHT * 2;
    if (buffer_size < expected_size) return -2;
    
    return expected_size;
}

void Camera_SetExposure(uint16_t exposure_ms) {
    uint8_t exp_data[2] = {exposure_ms >> 8, exposure_ms & 0xFF};
    HAL_I2C_Write(0, CAMERA_I2C_ADDR, exp_data, 2);
}

void Camera_SetGain(uint8_t gain) {
    HAL_I2C_Write(0, CAMERA_I2C_ADDR, &gain, 1);
}
