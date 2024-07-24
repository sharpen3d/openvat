import bpy
import os
import time

# Specify the directory to save rendered frames
output_directory = "D:/GitHub/openvat/source/"
# Ensure the directory exists
os.makedirs(output_directory, exist_ok=True)

# Define the frame range to render
start_frame = 1
end_frame = 24

# Loop through the specified frame range
for frame in range(start_frame, end_frame + 1):
    # Set current frame
    bpy.context.scene.frame_set(frame)
    
    # Reload all images
    for img in bpy.data.images:
        img.reload()
    
    # Set output path for the current frame
    bpy.context.scene.render.filepath = os.path.join(output_directory, f"alphie2VAT.png")
    
    # Render the frame
    bpy.ops.render.render(write_still=True)  # 'write_still' to ensure the image is saved
    
    print(f"Rendered frame {frame}")
    
for img in bpy.data.images:
    img.reload()
    
print("Rendering completed.")
