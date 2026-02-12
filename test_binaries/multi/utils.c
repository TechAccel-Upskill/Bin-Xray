#include <math.h>

double vector_magnitude(double x, double y, double z) {
    return sqrt(x*x + y*y + z*z);
}

double calculate_distance(double x1, double y1, double x2, double y2) {
    double dx = x2 - x1;
    double dy = y2 - y1;
    return vector_magnitude(dx, dy, 0.0);
}
