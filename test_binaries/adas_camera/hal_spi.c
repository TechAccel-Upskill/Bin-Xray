// Hardware Abstraction Layer - SPI
#include <stdint.h>

extern void HAL_GPIO_Init(uint8_t port, uint8_t pin, uint8_t mode);
extern void HAL_GPIO_WritePin(uint8_t port, uint8_t pin, uint8_t state);

volatile uint32_t* SPI_BASE = (volatile uint32_t*)0x40013000;

void HAL_SPI_Init(uint8_t instance, uint32_t baudrate) {
    HAL_GPIO_Init(0, 5, 0x02); // SCK
    HAL_GPIO_Init(0, 6, 0x02); // MISO
    HAL_GPIO_Init(0, 7, 0x02); // MOSI
    HAL_GPIO_Init(0, 4, 0x01); // CS
    
    SPI_BASE[instance * 8] = baudrate;
}

void HAL_SPI_ChipSelect(uint8_t instance, uint8_t enable) {
    HAL_GPIO_WritePin(0, 4, !enable);
}

uint8_t HAL_SPI_TransferByte(uint8_t instance, uint8_t data) {
    SPI_BASE[instance * 8 + 1] = data;
    while (!(SPI_BASE[instance * 8 + 2] & 0x01));
    return SPI_BASE[instance * 8 + 1];
}

int HAL_SPI_Transfer(uint8_t instance, uint8_t* tx_data, uint8_t* rx_data, uint16_t len) {
    for (uint16_t i = 0; i < len; i++) {
        rx_data[i] = HAL_SPI_TransferByte(instance, tx_data[i]);
    }
    return 0;
}
