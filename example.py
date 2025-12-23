#!/usr/bin/env python3
"""
Simple build123d example: Creating a box with a hole
"""
from build123d import *

# Create a box
with BuildPart() as my_part:
    Box(10, 10, 5)
    with Locations((0, 0, 0)):
        Cylinder(2, 10, mode=Mode.SUBTRACT)

# Export to STEP file
export_step(my_part.part, "box_with_hole.step")
print("Created box_with_hole.step")

# Print some info
print(f"Volume: {my_part.part.volume:.2f}")
print(f"Bounding box: {my_part.part.bounding_box()}")
