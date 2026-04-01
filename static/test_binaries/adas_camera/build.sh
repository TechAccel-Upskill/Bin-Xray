#!/bin/bash
cd "$(dirname "$0")"

echo "Compiling ADAS Camera System..."
echo "================================"

# Compile HAL layer
echo "1. Compiling HAL layer..."
gcc -c hal_gpio.c -o hal_gpio.o -Wall || exit 1
gcc -c hal_i2c.c -o hal_i2c.o -Wall || exit 1
gcc -c hal_spi.c -o hal_spi.o -Wall || exit 1
ar rcs libhal.a hal_gpio.o hal_i2c.o hal_spi.o
echo "   ✓ libhal.a created"

# Compile Driver layer
echo "2. Compiling Driver layer..."
gcc -c driver_camera.c -o driver_camera.o -Wall || exit 1
gcc -c driver_can.c -o driver_can.o -Wall || exit 1
ar rcs libdrivers.a driver_camera.o driver_can.o
echo "   ✓ libdrivers.a created"

# Compile Algorithm layer
echo "3. Compiling Algorithm layer..."
gcc -c image_processing.c -o image_processing.o -Wall || exit 1
gcc -c lane_detection.c -o lane_detection.o -Wall || exit 1
gcc -c object_detection.c -o object_detection.o -Wall || exit 1
ar rcs libalgorithms.a image_processing.o lane_detection.o object_detection.o
echo "   ✓ libalgorithms.a created"

# Compile demo-only unused library to show optimization opportunities in Bin-Xray
echo "3b. Compiling unused demo library..."
gcc -c unused_diag.c -o unused_diag.o -Wall || exit 1
gcc -c unused_telemetry.c -o unused_telemetry.o -Wall || exit 1
ar rcs libunused_demo.a unused_diag.o unused_telemetry.o
echo "   ✓ libunused_demo.a created (intentionally not linked)"

# Compile Application layer
echo "4. Compiling Application layer..."
gcc -c vehicle_control.c -o vehicle_control.o -Wall || exit 1
gcc -c main_adas.c -o main_adas.o -Wall || exit 1
echo "   ✓ Application objects created"

# Link everything
echo "5. Linking final binary..."
gcc main_adas.o vehicle_control.o -L. -lalgorithms -ldrivers -lhal -lm \
    -Wl,-Map=adas_camera.map,--cref -o adas_camera.elf || exit 1
echo "   ✓ adas_camera.elf created"

echo ""
echo "Build Summary:"
echo "=============="
ls -lh lib*.a adas_camera.elf adas_camera.map 2>/dev/null | awk '{print "  " $9 "  (" $5 ")"}'

echo ""
echo "Dependency Structure:"
echo "  main_adas.o → vehicle_control.o → libalgorithms.a → libdrivers.a → libhal.a"

echo ""
echo "Object files in each library:"
ar t libhal.a | sed 's/^/  libhal.a: /'
ar t libdrivers.a | sed 's/^/  libdrivers.a: /'
ar t libalgorithms.a | sed 's/^/  libalgorithms.a: /'
ar t libunused_demo.a | sed 's/^/  libunused_demo.a: /'

echo ""
echo "✅ ADAS Camera System build complete!"
