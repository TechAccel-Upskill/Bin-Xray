#include <stddef.h>

// Demo-only helper that is intentionally not linked into the final ELF.
int unused_telemetry_encode(const char *label) {
    if (label == NULL) {
        return 0;
    }

    int score = 0;
    for (size_t i = 0; label[i] != '\0'; ++i) {
        score += (int)label[i];
    }
    return score;
}
