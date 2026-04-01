// Hardware Abstraction Layer - GPIO
#include <stdint.h>

volatile uint32_t* GPIO_BASE = (volatile uint32_t*)0x40020000;

void HAL_GPIO_Init(uint8_t port, uint8_t pin, uint8_t mode) {
    GPIO_BASE[port * 16 + pin] = mode;
}

void HAL_GPIO_WritePin(uint8_t port, uint8_t pin, uint8_t state) {
    if (state) {
        GPIO_BASE[port * 16 + pin] |= 0x01;
    } else {
        GPIO_BASE[port * 16 + pin] &= ~0x01;
    }
}

uint8_t HAL_GPIO_ReadPin(uint8_t port, uint8_t pin) {
    return GPIO_BASE[port * 16 + pin] & 0x01;
}

void HAL_GPIO_TogglePin(uint8_t port, uint8_t pin) {
    GPIO_BASE[port * 16 + pin] ^= 0x01;
}
