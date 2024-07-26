# openVAT
Open source vertex animated texture encoding and decoding tools based in Blender. Import or create any deforming mesh to generate an optimized and standardized VAT, then use any of the included decoding methods to quickly and simply apply this in distributable context.

# Note (07/26/2024):
I am in the process of creating demo files, tutorials, and additional engine methods for Unreal Engine. Please direct any questions, bug reports, or recommendations to stilson.luke@gmail.com

# Release Notes v1.0.0:

## Released as Blender Extension (Pending Review)

Mesh to encode must maintain consistent domain size (vertex, edge, face count and ordering)

Range finding is rounded for ease of manual engine-shader implementation - may update for better range accuracy, but should not impact quality of encoding.

VAT and VNRM exports are 16 bit PNG exports and have uncapped size. It is recommended to render at a resolution of 4096 or lower - resolution is calculated within the tool when an object is selected.

Linear PNGs can become heavy if not monitored because of the lossless quality. These can be managed after the fact with careful compression (the built-in geometry node decoder can help determine quality loss with compression by re-loading in the compressed image after running your compression of choice.)

Not all animation situations have been tested, but any position/normal information that is accessible in the dependency graph (Geometry Nodes Spreadsheet data) is able to be recorded.