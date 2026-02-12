#include <stdio.h>

extern double vector_magnitude(double x, double y, double z);
extern double calculate_distance(double x1, double y1, double x2, double y2);
extern double sphere_volume(double radius);
extern double vector_normalize_length(double x, double y, double z);

int main() {
    printf("Vector magnitude: %f\n", vector_magnitude(3.0, 4.0, 0.0));
    printf("Distance: %f\n", calculate_distance(0.0, 0.0, 3.0, 4.0));
    printf("Sphere volume: %f\n", sphere_volume(5.0));
    printf("Normalized length: %f\n", vector_normalize_length(1.0, 2.0, 2.0));
    return 0;
}
