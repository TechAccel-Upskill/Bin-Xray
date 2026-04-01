#include <stdint.h>

// Demo-only helper that is intentionally not linked into the final ELF.
uint32_t unused_diag_checksum(const uint8_t *buf, uint32_t len) {
    uint32_t sum = 0;
    for (uint32_t i = 0; i < len; ++i) {
        sum += buf[i];
    }
    return sum;
}
