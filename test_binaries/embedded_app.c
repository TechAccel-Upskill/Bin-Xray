#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Simulating embedded system modules
void init_hardware(void) {
    printf("Hardware initialized\n");
}

void init_drivers(void) {
    printf("Drivers initialized\n");
}

int process_data(int *buffer, size_t len) {
    int sum = 0;
    for (size_t i = 0; i < len; i++) {
        sum += buffer[i];
    }
    return sum;
}

double calculate_value(double x) {
    return sin(x) * cos(x) + sqrt(x);
}

int main(int argc, char *argv[]) {
    init_hardware();
    init_drivers();
    
    int data[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};
    int result = process_data(data, 10);
    
    printf("Result: %d\n", result);
    printf("Calculation: %f\n", calculate_value(5.0));
    
    return 0;
}
