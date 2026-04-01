// Object Detection (Vehicles, Pedestrians)
#include <stdint.h>
#include <math.h>

extern void Image_GaussianBlur(uint8_t* input, uint8_t* output, uint16_t width, uint16_t height);

#define MAX_OBJECTS 20

typedef struct {
    uint16_t x, y, width, height;
    uint8_t class_id; // 0=car, 1=pedestrian, 2=bicycle, 3=traffic_sign
    float confidence;
    float distance_m;
} DetectedObject;

static DetectedObject objects[MAX_OBJECTS];
static uint8_t num_objects = 0;

void ObjectDetection_RunCNN(uint8_t* image, DetectedObject* objs, uint8_t* count) {
    // Simplified CNN inference (would normally use TensorFlow Lite or similar)
    *count = 0;
    
    for (uint16_t y = 0; y < 1080 && *count < MAX_OBJECTS; y += 100) {
        for (uint16_t x = 0; x < 1920; x += 100) {
            if (image[y * 1920 + x] > 200) {
                objs[*count].x = x;
                objs[*count].y = y;
                objs[*count].width = 80;
                objs[*count].height = 120;
                objs[*count].class_id = *count % 4;
                objs[*count].confidence = 0.85f;
                objs[*count].distance_m = 10.0f + (*count * 2.0f);
                (*count)++;
            }
        }
    }
}

int ObjectDetection_DetectObjects(uint8_t* frame) {
    uint8_t blurred[1920 * 1080];
    Image_GaussianBlur(frame, blurred, 1920, 1080);
    
    ObjectDetection_RunCNN(blurred, objects, &num_objects);
    
    return num_objects;
}

float ObjectDetection_EstimateDistance(DetectedObject* obj) {
    // Simplified distance estimation based on object size
    float focal_length = 800.0f;
    float real_height = (obj->class_id == 0) ? 1.5f : 1.7f; // car vs pedestrian
    return (focal_length * real_height) / obj->height;
}

int ObjectDetection_TrackCollisions(DetectedObject* objs, uint8_t count) {
    int collision_risk = 0;
    
    for (uint8_t i = 0; i < count; i++) {
        float distance = ObjectDetection_EstimateDistance(&objs[i]);
        if (distance < 5.0f && objs[i].confidence > 0.7f) {
            collision_risk++;
        }
    }
    
    return collision_risk;
}
