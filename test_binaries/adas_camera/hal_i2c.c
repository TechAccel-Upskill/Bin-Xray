// Hardware Abstraction Layer - I2C
#include <stdint.h>

extern void HAL_GPIO_Init(uint8_t port, uint8_t pin, uint8_t mode);

volatile uint32_t* I2C_BASE = (volatile uint32_t*)0x40005400;

void HAL_I2C_Init(uint8_t instance, uint32_t speed) {
    // Configure I2C pins
    HAL_GPIO_Init(1, 6, 0x02); // SCL
    HAL_GPIO_Init(1, 7, 0x02); // SDA
    
    I2C_BASE[instance * 8] = speed;
}

int HAL_I2C_Write(uint8_t instance, uint8_t addr, uint8_t* data, uint16_t len) {
    I2C_BASE[instance * 8 + 1] = addr;
    for (uint16_t i = 0; i < len; i++) {
        I2C_BASE[instance * 8 + 2] = data[i];
    }
    return 0;
}

int HAL_I2C_Read(uint8_t instance, uint8_t addr, uint8_t* data, uint16_t len) {
    I2C_BASE[instance * 8 + 1] = addr | 0x01;
    for (uint16_t i = 0; i < len; i++) {
        data[i] = I2C_BASE[instance * 8 + 2];
    }
    return 0;
}
