# Nano Banana Pro Scripts

Professional-quality image generation and editing using Google's Gemini 3 Pro Image model (Nano Banana Pro). Gemini remains the default; `generate_image.py --provider atlas` enables optional Atlas Cloud text-to-image generation. All scripts use REST APIs directly for maximum control and compatibility.

## 📚 Script Overview

| Script | Type | Purpose | Input | Output |
|--------|------|---------|-------|--------|
| `gemini_images.py` | Library | Shared functionality for all scripts | N/A | N/A |
| `atlas_images.py` | Library | Optional Atlas Cloud text-to-image generation | Prompt | Image |
| `generate_image.py` | CLI | Text-to-image generation | Text prompt | Image(s) |
| `edit_image.py` | CLI | Image editing with instructions | Image + instruction | Edited image(s) |
| `compose_images.py` | CLI | Multi-image composition | 2-14 images + instruction | Composed image |
| `multi_turn_chat.py` | Interactive | Iterative refinement chat | Prompts/images | Progressive images |
| `test_connection.py` | Utility | API connectivity testing | API key | Success/failure |

---

## 🔧 Core Library

### `gemini_images.py`

**Purpose:** Shared library providing reusable classes and functions for all Nano Banana Pro operations.

**Key Components:**

```python
from gemini_images import NanoBananaProClient, ImageChat

# Main client for API operations
client = NanoBananaProClient(api_key="YOUR_KEY")

# Multi-turn chat for iterative refinement
chat = ImageChat(client)
```

**Classes:**
- `NanoBananaProClient` - High-level API client with methods for generation, editing, and composition
- `ImageChat` - Manages multi-turn conversation history and progressive refinement

**Methods:**
- `generate_image(prompt, aspect_ratio, temperature)` - Text-to-image generation
- `edit_image(instruction, image_path, aspect_ratio, temperature)` - Image editing
- `compose_images(instruction, image_paths, aspect_ratio, temperature)` - Multi-image composition
- `save_response(output_path, response)` - Save API response to file

**When to Use:**
- Building custom workflows or automation
- Integrating Nano Banana Pro into other Python applications
- Batch processing with programmatic control
- Creating your own CLI tools

**Example:**
```python
from gemini_images import NanoBananaProClient

client = NanoBananaProClient()

# Generate
response = client.generate_image("A sunset over mountains", aspect_ratio="16:9")
paths = client.save_response("sunset.png", response)

# Edit
response = client.edit_image("Make the sky more vibrant", "sunset.png")
client.save_response("sunset_edited.png", response)
```

---

## 🎨 Generation Scripts

### `generate_image.py`

**Purpose:** Generate images from text prompts (text-to-image).

**Functionality:**
- Single-shot image generation
- Customizable aspect ratios (1:1, 3:4, 4:3, 9:16, 16:9)
- Temperature control for creativity (0.0-1.0)
- Optional verbose mode for debugging

**Use Cases:**
1. **Marketing Assets**
   ```bash
   python generate_image.py "Professional hero image for tech startup, modern team collaborating, bright office" --aspect-ratio 16:9
   ```

2. **Product Photography**
   ```bash
   python generate_image.py "High-end product photo of luxury watch on marble, dramatic lighting, 4K" --temperature 0.5
   ```

3. **Social Media Content**
   ```bash
   python generate_image.py "Instagram post about productivity, vibrant colors, minimalist" --aspect-ratio 1:1
   ```

4. **Blog Headers**
   ```bash
   python generate_image.py "Blog header about sustainable architecture, green building, modern" --output ./headers/
   ```

5. **Concept Art**
   ```bash
   python generate_image.py "Futuristic cityscape at night, neon lights, cyberpunk style" --temperature 0.9
   ```

**Key Parameters:**
- `--aspect-ratio` - Image dimensions (default: 16:9)
- `--temperature` - Creativity level: 0.3-0.5 (consistent), 0.7 (balanced), 0.8-0.9 (creative)
- `--output` - Output directory
- `--filename` - Base filename
- `--verbose` - Show full API response

**Examples:**
```bash
# Quick generation
python generate_image.py "A red sports car"

# Optional Atlas Cloud provider (requires ATLASCLOUD_API_KEY)
python generate_image.py "A red sports car" --provider atlas --resolution 2k

# Professional headshot
python generate_image.py "Professional headshot, 85mm lens, soft lighting" \
  --temperature 0.4 --aspect-ratio 3:4

# Creative exploration
python generate_image.py "Abstract art with flowing colors" --temperature 0.9
```

---

### `edit_image.py`

**Purpose:** Edit existing images using natural language instructions.

**Functionality:**
- Localized changes (specific elements)
- Atmospheric transformations (time of day, weather, mood)
- Element addition/removal
- Style transfers
- Color corrections

**Use Cases:**

1. **Localized Edits**
   ```bash
   python edit_image.py "Change the car to red" photo.jpg
   python edit_image.py "Add mountains in the background" landscape.jpg
   python edit_image.py "Remove person from left side" group.jpg
   ```

2. **Atmospheric Changes**
   ```bash
   python edit_image.py "Convert to sunset lighting" day_scene.jpg
   python edit_image.py "Make it a night scene with stars" daytime.jpg
   python edit_image.py "Add dramatic storm clouds" clear_sky.jpg
   ```

3. **Enhancement**
   ```bash
   python edit_image.py "Make the sky more vibrant blue" landscape.jpg
   python edit_image.py "Enhance colors for social media" photo.jpg
   python edit_image.py "Increase contrast and saturation" flat_image.jpg
   ```

4. **Element Addition**
   ```bash
   python edit_image.py "Add flying birds in the upper right sky" landscape.jpg
   python edit_image.py "Place a coffee cup on the desk" office.jpg
   python edit_image.py "Add warm street lamps glowing" street.jpg
   ```

5. **Style Transformation**
   ```bash
   python edit_image.py "Apply vintage film look" modern.jpg
   python edit_image.py "Make it look like an oil painting" photo.jpg
   python edit_image.py "Convert to black and white with high contrast" color.jpg
   ```

**Multi-Step Workflow:**
```bash
# Step 1: Change time of day
python edit_image.py "Convert to sunset lighting" day_scene.jpg \
  --output ./step1 --filename sunset

# Step 2: Add elements
python edit_image.py "Add warm street lamps glowing" ./step1/sunset_image_0_0.jpg \
  --output ./step2 --filename with_lamps

# Step 3: Fine-tune atmosphere
python edit_image.py "Make the sky more orange and dramatic" ./step2/with_lamps_image_0_0.jpg \
  --output ./final --filename final
```

**Key Parameters:**
- `prompt` - Edit instruction (required)
- `image` - Input image path (required)
- `--aspect-ratio` - Output aspect ratio
- `--temperature` - Creativity level
- `--output` - Output directory
- `--filename` - Base filename

---

## 🖼️ Composition Script

### `compose_images.py`

**Purpose:** Combine 2-14 reference images into a single cohesive image based on instructions.

**Functionality:**
- Multi-image composition (up to 14 images)
- Group photo creation
- Style transfer between images
- Scene building from elements
- Character/object composition
- Collage generation

**Use Cases:**

1. **Group Photos**
   ```bash
   python compose_images.py "Create a professional group photo in an office setting" \
     person1.png person2.png person3.png person4.png
   ```

2. **Style Transfer**
   ```bash
   # Apply artistic style from reference to photo
   python compose_images.py "Apply the art style from the first image to the scene in the second" \
     art_reference.png photo.png

   # Apply lighting from reference
   python compose_images.py "Use the lighting from image 1 on the subject in image 2" \
     lighting_ref.png subject.png
   ```

3. **Scene Building**
   ```bash
   python compose_images.py "Combine these elements into a cohesive landscape" \
     sky.png mountains.png lake.png trees.png foreground.png
   ```

4. **Character Composition**
   ```bash
   python compose_images.py "Put the cat from the first image on the couch from the second" \
     cat.png couch.png

   python compose_images.py "Place all these people in the same conference room" \
     person1.png person2.png person3.png person4.png person5.png
   ```

5. **Product Showcase**
   ```bash
   python compose_images.py "Arrange these products in a professional catalog layout" \
     product1.png product2.png product3.png product4.png

   python compose_images.py "Create a hero image showing all three products together" \
     product_a.png product_b.png product_c.png
   ```

6. **Collages & Montages**
   ```bash
   python compose_images.py "Create an artistic collage with these travel photos" \
     paris.png tokyo.png newyork.png london.png --aspect-ratio 1:1
   ```

7. **Before/After Comparisons**
   ```bash
   python compose_images.py "Create a side-by-side before and after comparison" \
     before.png after.png --aspect-ratio 16:9
   ```

**Key Parameters:**
- `instruction` - How to combine images (required)
- `images` - 2-14 image paths (required)
- `--output` - Output file path
- `--aspect-ratio` - Output aspect ratio
- `--temperature` - 0.4-0.6 (literal), 0.7 (balanced), 0.8-0.9 (creative)

**Tips:**
- First image often serves as primary reference
- Be specific about spatial relationships ("on the left", "in the background")
- Higher temperature for creative interpretations
- Lower temperature for literal compositions

---

## 💬 Interactive Script

### `multi_turn_chat.py`

**Purpose:** Interactive CLI for iterative image generation and refinement through conversation.

**Functionality:**
- Progressive image refinement
- Multi-turn conversations
- Auto-save after each generation
- Load existing images for editing
- Conversation history tracking
- Manual save with custom filenames

**Commands:**
- `/save [filename]` - Save current image (optional custom name)
- `/load <path>` - Load existing image for editing
- `/clear` - Reset conversation and start fresh
- `/history` - Show conversation history
- `/help` - Display available commands
- `/quit` or `/exit` - Exit program

**Use Cases:**

1. **Logo Design Workflow**
   ```bash
   $ python multi_turn_chat.py --output-dir ./logos

   💬 You: Create a minimalist logo for a coffee shop called 'Daily Grind'
   ✅ Image generated: ./logos/image_1.png

   💬 You: Make the text bolder and use a darker brown
   ✅ Image generated: ./logos/image_2.png

   💬 You: Add a coffee bean icon above the text
   ✅ Image generated: ./logos/image_3.png

   💬 You: Perfect! /save daily_grind_final.png
   ✅ Image saved: ./logos/daily_grind_final.png
   ```

2. **Photo Editing Session**
   ```bash
   $ python multi_turn_chat.py

   💬 You: /load vacation_photo.jpg
   ✅ Loaded: vacation_photo.jpg

   💬 You: Make the sky more vibrant and blue
   ✅ Image generated: ./output/image_1.png

   💬 You: Add some birds flying in the distance
   ✅ Image generated: ./output/image_2.png

   💬 You: Enhance overall colors to make it more dramatic
   ✅ Image generated: ./output/image_3.png
   ```

3. **Marketing Asset Creation**
   ```bash
   💬 You: Create a hero image for a tech startup landing page
   💬 You: Make the colors more vibrant and modern
   💬 You: Add more depth with subtle shadows
   💬 You: /save hero_final_v1.png
   ```

4. **Concept Exploration**
   ```bash
   💬 You: Create a futuristic cityscape
   💬 You: Add neon lights and flying cars
   💬 You: Make it darker and more cyberpunk
   💬 You: Add rain and reflections on the ground
   ```

5. **Product Photography Refinement**
   ```bash
   💬 You: /load product_photo.jpg
   💬 You: Improve the lighting to be more professional
   💬 You: Add a subtle shadow underneath
   💬 You: Change the background to pure white
   ```

**Workflow Tips:**
- Start with a broad concept, then refine progressively
- Use `/history` to review your changes
- Use `/save` with custom names for versions you want to keep
- Use `/clear` to start a new concept
- Be specific with each refinement instruction

**Key Parameters:**
- `--output-dir` - Directory for auto-saved images
- `--aspect-ratio` - Default aspect ratio for all images
- `--temperature` - Default creativity level

**Example Sessions:**

**Session 1: Logo Refinement**
```
You: Create a tech startup logo for "CloudSync"
You: Make it more modern and minimal
You: Use a sans-serif font
You: Add a subtle cloud icon
You: Make the icon smaller and more abstract
You: /save cloudsync_logo_v5.png
```

**Session 2: Photo Enhancement**
```
You: /load portrait.jpg
You: Improve the lighting on the face
You: Blur the background slightly
You: Make the eyes brighter
You: Add a warm color grade
You: /save portrait_enhanced.png
```

---

## 🧪 Utility Script

### `test_connection.py`

**Purpose:** Test API connectivity and verify credentials before generating images.

**Functionality:**
- Validates API key format
- Tests network connectivity
- Verifies API endpoint availability
- Provides clear success/failure feedback
- Optional JSON output for automation

**Use Cases:**

1. **Initial Setup Verification**
   ```bash
   # Test after getting new API key
   python test_connection.py --api-key YOUR_NEW_KEY
   ```

2. **Troubleshooting**
   ```bash
   # Debug connection issues
   python test_connection.py

   # Use JSON output for scripting
   python test_connection.py --json | jq '.success'
   ```

3. **Automated Testing**
   ```bash
   # In CI/CD pipeline
   if python test_connection.py --json | jq -e '.success'; then
     echo "API key valid"
   else
     echo "API key invalid"
     exit 1
   fi
   ```

**Key Parameters:**
- `--api-key` - API key to test (or use GEMINI_API_KEY env var)
- `--json` - Output as JSON for scripting

---

## 🚀 Quick Start Examples

### 1. Generate Your First Image
```bash
export GEMINI_API_KEY="your-api-key"
python generate_image.py "A serene mountain landscape at sunset"
```

### 2. Edit an Existing Photo
```bash
python edit_image.py "Add dramatic clouds" my_photo.jpg --output ./edited
```

### 3. Create a Group Photo
```bash
python compose_images.py "Professional team photo" person1.png person2.png person3.png
```

### 4. Interactive Design Session
```bash
python multi_turn_chat.py --output-dir ./designs
# Then chat to iteratively create your image
```

---

## 📊 Comparison: When to Use Each Script

| Scenario | Best Script | Why |
|----------|-------------|-----|
| Single image from prompt | `generate_image.py` | Simple, fast, one command |
| Edit one image once | `edit_image.py` | Direct, single edit workflow |
| Combine multiple images | `compose_images.py` | Supports up to 14 images |
| Multiple refinements | `multi_turn_chat.py` | Progressive, conversational |
| Batch processing | `gemini_images.py` | Programmatic control |
| Quick test | `test_connection.py` | Fast validation |

---

## 🎯 Common Workflows

### Workflow 1: Marketing Campaign
```bash
# Generate hero image
python generate_image.py "Tech startup hero image, modern team" \
  --aspect-ratio 16:9 --output ./campaign --filename hero

# Create social variant
python edit_image.py "Crop to square, increase contrast" \
  ./campaign/hero_image_0_0.jpg \
  --aspect-ratio 1:1 --output ./campaign --filename social
```

### Workflow 2: Logo Design
```bash
# Interactive refinement
python multi_turn_chat.py --output-dir ./logos
# "Create logo for Daily Grind coffee shop"
# "Make text bolder"
# "Add coffee bean icon"
# "/save final.png"
```

### Workflow 3: Product Showcase
```bash
# Compose product lineup
python compose_images.py "Professional product catalog layout" \
  product1.png product2.png product3.png \
  --aspect-ratio 16:9 --output ./catalog.png
```

### Workflow 4: Photo Enhancement Pipeline
```bash
# Step 1: Basic edit
python edit_image.py "Enhance lighting" original.jpg --output ./step1

# Step 2: Add elements
python edit_image.py "Add clouds" ./step1/edited_image_0_0.jpg --output ./step2

# Step 3: Final touches
python edit_image.py "Increase saturation" ./step2/edited_image_0_0.jpg --output ./final
```

---

## 🔑 Environment Setup

All scripts support API key configuration via:

1. **Environment Variable (Recommended)**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Command Line Flag**
   ```bash
   python generate_image.py "prompt" --api-key YOUR_KEY
   ```

3. **For Development**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export GEMINI_API_KEY="your-api-key-here"
   ```

---

## 📝 Common Parameters

All CLI scripts share these common parameters:

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--api-key` | string | `$GEMINI_API_KEY` | API key |
| `--aspect-ratio` | 1:1, 3:4, 4:3, 9:16, 16:9 | 16:9 | Output dimensions |
| `--temperature` | 0.0-1.0 | 0.7 | Creativity level |
| `--output` | path | `./output` | Output location |
| `--verbose` | flag | false | Show full API response |

---

## 🐛 Troubleshooting

### Import Errors
```bash
# If you see "module not found"
cd /path/to/scripts
python3 -c "from gemini_images import NanoBananaProClient"
```

### API Key Issues
```bash
# Test your API key
python test_connection.py --api-key YOUR_KEY
```

### Rate Limiting
- Free tier: ~100 requests/day, 2-5/minute
- Add delays between requests: `sleep 2`
- See `references/troubleshooting.md` for exponential backoff

### Low Quality Output
- Use more specific prompts
- Lower temperature for consistency (0.5)
- Add quality modifiers: "4K", "professional", "sharp focus"

---

## 💡 Tips & Best Practices

1. **Prompting**
   - Be specific and detailed
   - Use cinematic language (lens, lighting, angle)
   - Include quality modifiers
   - See `references/prompting-guide.md` for examples

2. **Temperature**
   - 0.3-0.5: Product photos, diagrams, consistency
   - 0.7: Balanced (default)
   - 0.8-0.9: Creative exploration, artistic styles

3. **Aspect Ratios**
   - 1:1: Social posts, profile images
   - 16:9: Presentations, website headers
   - 9:16: Mobile stories, vertical video
   - 4:3/3:4: Traditional photography

4. **Batch Processing**
   - Use `gemini_images.py` library for automation
   - Add delays between requests
   - Implement error handling and retries

5. **Version Control**
   - Use descriptive filenames
   - Save intermediate results
   - Use `multi_turn_chat.py` for version tracking

---

## 📚 Additional Resources

- **Prompting Guide**: `../references/prompting-guide.md`
- **API Reference**: `../references/api-reference.md`
- **Troubleshooting**: `../references/troubleshooting.md`
- **Example Prompts**: `../assets/example-prompts.md`
- **Main Skill Docs**: `../skill.md`

---

## 🆘 Getting Help

```bash
# For any script
python script_name.py --help

# Test API connection
python test_connection.py

# Check if library imports
python -c "from gemini_images import NanoBananaProClient"
```

**Need more help?** Check the main skill documentation or troubleshooting guide.
