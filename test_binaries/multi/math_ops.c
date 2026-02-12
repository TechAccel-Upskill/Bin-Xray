#include <math.h>

extern double vector_magnitude(double x, double y, double z);

double sphere_volume(double radius) {
    return (4.0/3.0) * M_PI * pow(radius, 3);
}

double vector_normalize_length(double x, double y, double z) {
    return vector_magnitude(x, y, z);
}
