# Better Test Data for Bin-Xray Tool Validation

## Overview

Created a **realistic ADAS (Advanced Driver Assistance System) camera processing pipeline** to properly test the tool's efficiency with complex, real-world embedded systems.

## Project Structure

```
adas_camera/
├── Hardware Abstraction Layer (HAL)
│   ├── hal_gpio.c      - GPIO control functions
│   ├── hal_i2c.c       - I2C communication (camera sensor)
│   └── hal_spi.c       - SPI communication
│   → Static library: libhal.a (3 object files)
│
├── Driver Layer
│   ├── driver_camera.c - OV5640 camera sensor driver
│   └── driver_can.c    - CAN bus communication
│   → Static library: libdrivers.a (2 object files)
│
├── Algorithm Layer
│   ├── image_processing.c  - Gaussian blur, Sobel edge detection
│   ├── lane_detection.c    - Hough transform, lane finding
│   └── object_detection.c  - CNN-based object detection
│   → Static library: libalgorithms.a (3 object files)
│
└── Application Layer
    ├── vehicle_control.c - Steering, braking, CAN messaging
    └── main_adas.c       - Main application loop
    → Linked with all libraries above
```

## Complexity Comparison

### Old Test Data (multi-module)
- **3 source files**: main.c, utils.c, math_ops.c
- **Simple functions**: vector_magnitude, calculate_distance
- **5 symbol dependencies total**
- **No libraries, no layering**
- **Toy example** - not realistic for automotive SDKs

### New Test Data (adas_camera)
- **10 source files** organized in 4 layers
- **3 static libraries** (.a archives)
- **Realistic ADAS functions**:
  - Hardware abstraction (GPIO, I2C, SPI)
  - Camera sensor control
  - Image processing pipeline
  - Lane detection algorithms
  - Object detection (vehicles, pedestrians)
  - Vehicle control (steering, braking)
  - CAN bus communication
- **50+ function symbols**
- **Multi-layer dependencies**:
  ```
  Application → Algorithms → Drivers → HAL
  ```

## Symbol Dependencies to Visualize

### HAL Layer Dependencies
```
hal_i2c.c    --[HAL_GPIO_Init]-->        hal_gpio.c
hal_spi.c    --[HAL_GPIO_Init]-->        hal_gpio.c
hal_spi.c    --[HAL_GPIO_WritePin]-->    hal_gpio.c
```

### Driver Layer Dependencies
```
driver_camera.c --[HAL_I2C_Init]-->      hal_i2c.o (in libhal.a)
driver_camera.c --[HAL_I2C_Write]-->     hal_i2c.o
driver_camera.c --[HAL_I2C_Read]-->      hal_i2c.o
driver_camera.c --[HAL_GPIO_WritePin]--> hal_gpio.o
driver_can.c    --[HAL_GPIO_Init]-->     hal_gpio.o
```

### Algorithm Layer Dependencies
```
image_processing.c  --[Camera_CaptureFrame]--> driver_camera.o (in libdrivers.a)
lane_detection.c    --[Image_ProcessFrame]-->  image_processing.o (in libalgorithms.a)
object_detection.c  --[Image_GaussianBlur]-->  image_processing.o
```

### Application Layer Dependencies
```
main_adas.c      --[Camera_Init]-->                driver_camera.o
main_adas.c      --[CAN_Init]-->                   driver_can.o
main_adas.c      --[Image_ProcessFrame]-->         image_processing.o
main_adas.c      --[LaneDetection_FindLanes]-->    lane_detection.o
main_adas.c      --[ObjectDetection_Detect...]-->  object_detection.o

vehicle_control.c --[CAN_Send]-->                  driver_can.o
vehicle_control.c --[LaneDetection_GetWarning...] lane_detection.o
```

## Expected Graph Features

### Multi-Layer Visualization
The graph should clearly show the **4-layer architecture**:
1. Application tier (top)
2. Algorithm tier
3. Driver tier
4. HAL tier (bottom)

### Library Containment
Should show:
- `libhal.a` contains `hal_gpio.o`, `hal_i2c.o`, `hal_spi.o`
- `libdrivers.a` contains `driver_camera.o`, `driver_can.o`
- `libalgorithms.a` contains `image_processing.o`, `lane_detection.o`, `object_detection.o`

### Cross-Layer Symbol References
With "Show Symbol Dependencies" enabled, should display:
- Function names on edges between layers
- Dashed teal edges for symbol references
- Example: `main_adas.o --[Camera_Init]--> driver_camera.o`

## Build Instructions

```bash
cd /home/uic27619/Working/Bin-xray/test_binaries/adas_camera
./build.sh
```

This will create:
- `libhal.a` (12 KB)
- `libdrivers.a` (8 KB)
- `libalgorithms.a` (16 KB)
- `adas_camera.elf` (24 KB)
- `adas_camera.map` (450+ KB with cross-references)

## How to Test with Bin-Xray

1. **Launch GUI:**
   ```bash
   python3 /home/uic27619/Working/Bin-xray/run.py \
   ```

2. **Load Files:**
   - Binary: `test_binaries/adas_camera/adas_camera.elf`
   - Map File: `test_binaries/adas_camera/adas_camera.map`
   - Library Dir: `test_binaries/adas_camera/` (contains *.a files and *.o files)

3. **Configure Options:**
   - ✓ Check "Show Symbol Dependencies"
   - Set Layout: "hierarchical" (best for layered architecture)
   - Max Depth: 6

4. **Analyze:**
   - Click "Analyze & Generate Graph"
   - Wait for complex dependency analysis

## Expected Results

### Tool Efficiency Validation

✅ **Parser Performance:**
- Should parse 10 source files
- Extract symbols from 3 static archives
- Handle 50+ function symbols
- Process 450+ KB map file with cross-references

✅ **Graph Construction:**
- Create multi-layer directed graph
- Match undefined symbols across libraries
- Show containment relationships (library→objects)
- Display symbol-level dependencies

✅ **Visualization Quality:**
- Clear layer separation (hierarchical layout)
- Distinguishable edge types (dynamic, symbol_ref, contains)
- Readable symbol labels on edges
- Proper node coloring by type

✅ **Automotive SDK Representation:**
- Realistic embedded systems structure
- Hardware abstraction patterns
- Driver/middleware/application layers
- Safety-critical functionality (ADAS)

## Comparison with Other Tools

### vs. `ldd`
- ldd: Only shows dynamic library dependencies
- Bin-Xray: Shows static libs, object files, and symbol-level deps

### vs. `nm`
- nm: Lists symbols per file (no relationships)
- Bin-Xray: Visualizes which symbols connect which modules

### vs. `objdump`
- objdump: Low-level disassembly
- Bin-Xray: High-level architecture visualization

### vs. Graphviz DOT files
- DOT: Manual creation required
- Bin-Xray: Automatic extraction from binaries/maps

## Real-World Use Cases Demonstrated

1. **Layer Violation Detection**: Can you identify if application directly calls HAL (bypassing drivers)?
2. **Circular Dependency Detection**: Are there any circular refs between modules?
3. **Dead Code Identification**: Which library symbols are never referenced?
4. **API Surface Analysis**: What functions are exposed vs. internal?
5. **Refactoring Impact**: If you change a HAL function, what layers are affected?

## Conclusion

This ADAS camera test dataset provides a **realistic embedded automotive system** that properly tests Bin-Xray's ability to:
- Parse complex multi-layer builds
- Extract symbol dependencies from static libraries
- Visualize architecture at scale
- Handle real-world SDK patterns

It replaces the simple 3-file toy example with a production-quality test case that demonstrates the tool's value for automotive/ADAS development teams.
