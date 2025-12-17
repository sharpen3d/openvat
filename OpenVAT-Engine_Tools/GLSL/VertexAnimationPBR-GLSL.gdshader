shader_type spatial;

uniform sampler2D vat_position_texture;
//uniform sampler2D vat_normal_texture; // Assuming normals are packed in this texture
uniform vec3 minValues; // Min values for X, Y, Z
uniform vec3 maxValues; // Max values for X, Y, Z
uniform int FrameCount; // Total number of frames
uniform float Y_resolution; // Resolution along the Y-axis
uniform bool ToggleAnimated; // Toggle for animation control
uniform int frameSelect; // Frame selection when not animated
uniform float Speed; // Animation speed

// PBR Textures
uniform vec4 albedo : source_color;
uniform sampler2D base_color_texture;
uniform sampler2D normal_map_texture;
uniform sampler2D roughness_texture;
uniform float roughness : hint_range(0,1);
uniform vec4 metallic_texture_channel;
uniform float metallic;
uniform sampler2D metallic_texture; 
uniform float specular;

varying vec2 v_vat_uv_offset;

void vertex() {
    // Get the current time and calculate the current frame
    float time = TIME;
	float frameTime;
    int currentFrame;
	int nextFrame;

    if (ToggleAnimated) {
        frameTime = mod(time * Speed, float(FrameCount));
        currentFrame = int(floor(frameTime));
		nextFrame = (currentFrame + 1) % FrameCount;
    } else {
        currentFrame = frameSelect;
		nextFrame = currentFrame;
    }
	
	float blend = fract(frameTime);

    // Calculate the UV offset for the current frame
	float frameStep = 1.0 / Y_resolution;
    vec2 VAT_UV_offset = UV2 + vec2(0.0, float(currentFrame) * frameStep);
	vec2 VAT_UV_offset_next = UV2 + vec2(0.0, float(nextFrame) * frameStep);

    // Pass the UV offset to the fragment shader
    v_vat_uv_offset = VAT_UV_offset;

    // Sample the VAT position texture using UV2
    vec3 VAT_position = texture(vat_position_texture, VAT_UV_offset).rgb;
	vec3 VAT_position_next = texture(vat_position_texture, VAT_UV_offset_next).rgb;
	
	VAT_position = mix(VAT_position, VAT_position_next, blend);

    // Remap each channel of the VAT position to object space individually
    vec3 object_space_position;
    object_space_position.x = minValues.x + VAT_position.x * (maxValues.x - minValues.x);
    object_space_position.z = -1. * (minValues.y + VAT_position.y * (maxValues.y - minValues.y)); //Swap y and z axis from blender. Invert Y axis
    object_space_position.y = minValues.z + VAT_position.z * (maxValues.z - minValues.z);

    // Apply the remapped position to the vertex
    VERTEX += object_space_position;

    //// Sample the VAT normal texture and unpack the normals using UV2
    vec3 VAT_normal = texture(vat_position_texture, VAT_UV_offset + .5f).rbg;
	vec3 VAT_normal_next = texture(vat_position_texture, VAT_UV_offset_next + .5f).rbg;
    VAT_normal = 2.0 * VAT_normal - 1.0; // Unpack the normals from [0, 1] to [-1, 1]
	VAT_normal_next = 2.0 * VAT_normal_next - 1.0; // Unpack the normals from [0, 1] to [-1, 1]
    VAT_normal.b = -VAT_normal.b; // Flip the b channel
    VAT_normal_next.b = -VAT_normal_next.b;

    NORMAL = normalize(mix(VAT_normal,VAT_normal_next, blend));
}

void fragment() {
    vec2 base_uv = UV;
    vec4 albedo_tex = texture(base_color_texture,base_uv);
    ALBEDO = albedo.rgb * albedo_tex.rgb;
    NORMAL_MAP = texture(normal_map_texture, UV).rgb;
    
    float metallic_tex = dot(texture(metallic_texture,base_uv),metallic_texture_channel);
    METALLIC = metallic_tex * metallic;
    vec4 roughness_texture_channel = vec4(1.0,0.0,0.0,0.0);
    float roughness_tex = dot(texture(roughness_texture,base_uv),roughness_texture_channel);
    ROUGHNESS = roughness_tex * roughness;
    SPECULAR = specular;
}
