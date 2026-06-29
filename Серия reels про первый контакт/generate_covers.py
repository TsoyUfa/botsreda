import os
import shutil
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from rembg import remove

# 1. Directories setup
downloads_dir = "/Users/anton_tsoy/Downloads"
workspace_dir = "/Users/anton_tsoy/Desktop/Обсидиан/Серия reels про первый контакт"
src_dir = os.path.join(workspace_dir, "исходники")
out_dir = os.path.join(workspace_dir, "обложки")

os.makedirs(src_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

# Copy source files from Downloads if not already present in workspace
images = [f"IMG_0{i}.jpg" for i in range(379, 387)]
for img_name in images:
    src_path = os.path.join(downloads_dir, img_name)
    dest_path = os.path.join(src_dir, img_name)
    if os.path.exists(src_path) and not os.path.exists(dest_path):
        shutil.copy(src_path, dest_path)
        print(f"Copied {img_name} to workspace")

# 2. Text configuration according to TZ
covers_data = [
    {
        "file": "IMG_0379.jpg",
        "title": "ПОЧЕМУ ТВОИ\nСДЕЛКИ УПАЛИ?",
        "highlight": "СДЕЛКИ УПАЛИ?",
        "counter": "1 из 8"
    },
    {
        "file": "IMG_0380.jpg",
        "title": "ЗОЛОТОЙ КЛИЕНТ:\nКАК НАЙТИ?",
        "highlight": "ЗОЛОТОЙ КЛИЕНТ:",
        "counter": "2 из 8"
    },
    {
        "file": "IMG_0381.jpg",
        "title": "ПОЧЕМУ КЛИЕНТЫ\nСЛИВАЮТСЯ?",
        "highlight": "СЛИВАЮТСЯ?",
        "counter": "3 из 8"
    },
    {
        "file": "IMG_0382.jpg",
        "title": "ХВАТИТ РАБОТАТЬ\nБЕСПЛАТНО!",
        "highlight": "БЕСПЛАТНО!",
        "counter": "4 из 8"
    },
    {
        "file": "IMG_0383.jpg",
        "title": "4 СПОСОБА КУПИТЬ\nКВАРТИРУ СЕЙЧАС",
        "highlight": "КУПИТЬ КВАРТИРУ",
        "counter": "5 из 8"
    },
    {
        "file": "IMG_0384.jpg",
        "title": "КАК ПРЕЗЕНТОВАТЬ\nЦИФРЫ КЛИЕНТУ?",
        "highlight": "ЦИФРЫ",
        "counter": "6 из 8"
    },
    {
        "file": "IMG_0385.jpg",
        "title": "КЛИЕНТ НЕ ВСЕГДА\nПРАВ!",
        "highlight": "НЕ ВСЕГДА\nПРАВ!",
        "counter": "7 из 8"
    },
    {
        "file": "IMG_0386.jpg",
        "title": "СЕКРЕТ ВЫЯВЛЕНИЯ\nПОТРЕБНОСТЕЙ",
        "highlight": "ПОТРЕБНОСТЕЙ",
        "counter": "8 из 8"
    }
]

# Fonts setup (macOS system fonts)
font_mono = "/System/Library/Fonts/Supplemental/Courier New.ttf"
font_sans_bold = "/System/Library/Fonts/Helvetica.ttc"
font_sans_light = "/System/Library/Fonts/Helvetica.ttc"

# If Helvetica TTC behaves weirdly, fallback to Arial Bold/Narrow
if not os.path.exists(font_sans_bold):
    font_sans_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
if not os.path.exists(font_sans_light):
    font_sans_light = "/System/Library/Fonts/Supplemental/Arial.ttf"

def generate_matrix_rain(width, height, seed, font_path, font_size=24):
    """Generates a matrix code rain overlay image of size (width, height)."""
    random.seed(seed)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        font = ImageFont.load_default()
        
    col_width = font_size
    num_cols = width // col_width
    
    for col in range(num_cols):
        # Randomize drops
        if random.random() > 0.45:
            continue
            
        head_y = random.randint(0, height)
        trail_len = random.randint(12, 28)
        
        for i in range(trail_len):
            curr_y = head_y - i * font_size
            if curr_y < 0 or curr_y >= height:
                continue
                
            # Random characters (Katakana 0x30A0-0x30FF or digits)
            if random.random() > 0.25:
                char = chr(random.randint(0x30A0, 0x30FF))
            else:
                char = chr(random.randint(48, 57))
                
            # Gradient color
            if i == 0:
                color = (200, 255, 220, 210)  # Bright tip
            else:
                ratio = 1.0 - (i / trail_len)
                green = int(255 * ratio)
                alpha = int(190 * ratio)
                color = (0, green, int(60 * ratio), alpha)
                
            x = col * col_width + random.randint(-1, 1)
            draw.text((x, curr_y), char, font=font, fill=color)
            
    # Apply a small blur for glow effect
    overlay = overlay.filter(ImageFilter.GaussianBlur(0.6))
    return overlay

def draw_highlighted_text(draw, text, highlight, font, default_color, highlight_color, start_y, line_spacing=15):
    """Draws multi-line text with highlighted words in another color, centered horizontally."""
    lines = text.split('\n')
    line_widths = []
    line_words_data = []
    
    # Calculate word sizing and positions for horizontal centering
    for line in lines:
        words = line.split(' ')
        words_data = []
        total_width = 0
        for i, word in enumerate(words):
            # Clean punctuation for exact highlight match
            clean_word = word.strip('?!.,:;()')
            clean_highlight = highlight.strip('?!.,:;()')
            is_highlight = clean_word in clean_highlight and clean_word != ""
            
            bbox = draw.textbbox((0, 0), word, font=font)
            word_w = bbox[2] - bbox[0]
            word_h = bbox[3] - bbox[1]
            
            space_bbox = draw.textbbox((0, 0), " ", font=font)
            space_w = space_bbox[2] - space_bbox[0]
            
            words_data.append({
                "text": word,
                "is_highlight": is_highlight,
                "width": word_w,
                "height": word_h
            })
            total_width += word_w
            if i < len(words) - 1:
                total_width += space_w
                
        line_widths.append(total_width)
        line_words_data.append(words_data)
        
    curr_y = start_y
    for line_idx, words_data in enumerate(line_words_data):
        line_w = line_widths[line_idx]
        curr_x = (1080 - line_w) // 2
        max_h = 0
        
        for wd in words_data:
            color = highlight_color if wd["is_highlight"] else default_color
            
            # Shadow offset
            draw.text((curr_x + 3, curr_y + 3), wd["text"], font=font, fill=(0, 0, 0, 200))
            draw.text((curr_x + 1, curr_y + 1), wd["text"], font=font, fill=(0, 0, 0, 220))
            
            # Text
            draw.text((curr_x, curr_y), wd["text"], font=font, fill=color)
            
            space_bbox = draw.textbbox((0, 0), " ", font=font)
            space_w = space_bbox[2] - space_bbox[0]
            curr_x += wd["width"] + space_w
            if wd["height"] > max_h:
                max_h = wd["height"]
                
        curr_y += max_h + line_spacing

def process_cover(data, index):
    img_name = data["file"]
    print(f"Processing cover {index+1}/8: {img_name}...")
    
    # 1. Load source image
    src_path = os.path.join(src_dir, img_name)
    if not os.path.exists(src_path):
        print(f"Error: {src_path} not found!")
        return
        
    original = Image.open(src_path).convert("RGB")
    width, height = original.size
    
    # 2. Extract foreground using rembg
    print("  Removing background...")
    fg = remove(original)
    
    # Get alpha channel mask
    fg_mask = fg.split()[3]
    
    # Make sure workspace (laptop and stand) in the lower left is preserved
    # We create a manual override: we keep pixels in x < 420 and y > 1050 fully in the foreground
    mask_arr = np.array(fg_mask)
    # y coordinates from 1050 to 1920 (which is 1050:1920), x coordinates from 0 to 420
    # Add a soft fade on the override boundary to blend smoothly
    for y in range(1050, height):
        for x in range(0, 420):
            # Calculate distance to edge to feather the manual mask
            dist_x = 420 - x
            dist_y = y - 1050
            feather = min(dist_x / 30.0, dist_y / 30.0, 1.0)
            target_alpha = int(255 * feather)
            if mask_arr[y, x] < target_alpha:
                mask_arr[y, x] = target_alpha
                
    fg_mask = Image.fromarray(mask_arr)
    
    # 3. Generate randomized Matrix rain
    print("  Generating Matrix rain pattern...")
    matrix_rain = generate_matrix_rain(width, height, seed=index + 42, font_path=font_mono, font_size=22)
    
    # Make matrix rain subtle (opacity ~20%)
    matrix_rain_subtle = Image.blend(Image.new("RGBA", matrix_rain.size, (0, 0, 0, 0)), matrix_rain, 0.20)
    
    # 4. Blend background
    print("  Blending background...")
    bg_rgba = original.convert("RGBA")
    # Composite matrix rain onto the background
    blended_bg = Image.alpha_composite(bg_rgba, matrix_rain_subtle)
    
    # 5. Composite foreground on top of blended background using our refined mask
    output = Image.composite(original.convert("RGBA"), blended_bg, fg_mask)
    
    # 6. Add Typography
    print("  Rendering titles...")
    draw = ImageDraw.Draw(output)
    
    # A. Upper Header: ПЕРВЫЙ КОНТАКТ С КЛИЕНТОМ
    header_text = "ПЕРВЫЙ КОНТАКТ С КЛИЕНТОМ"
    try:
        # Load Helvetica Neue Light or regular
        font_header = ImageFont.truetype(font_sans_light, 28)
    except IOError:
        font_header = ImageFont.load_default()
        
    header_bbox = draw.textbbox((0, 0), header_text, font=font_header)
    header_w = header_bbox[2] - header_bbox[0]
    header_x = (width - header_w) // 2
    header_y = 120
    
    # Header shadow
    draw.text((header_x + 2, header_y + 2), header_text, font=font_header, fill=(0, 0, 0, 180))
    # Header main text (electric green / white mix, let's make it a clean white with green dots or pure white)
    draw.text((header_x, header_y), header_text, font=font_header, fill=(240, 240, 240, 255))
    
    # B. Main Title with highlighting
    title_text = data["title"]
    highlight_word = data["highlight"]
    try:
        # Helvetica Bold, font size 62 for massiveness
        # Using index 0 for Helvetica Bold inside Helvetica.ttc
        font_title = ImageFont.truetype(font_sans_bold, 62, index=0)
    except IOError:
        font_title = ImageFont.load_default()
        
    # Positioning in the lower-middle part
    title_start_y = 1240
    electric_green = (0, 255, 70, 255) # Electric green
    draw_highlighted_text(draw, title_text, highlight_word, font_title, (255, 255, 255, 255), electric_green, title_start_y)
    
    # C. Counter: X из 8
    counter_text = data["counter"]
    try:
        font_counter = ImageFont.truetype(font_sans_bold, 34, index=0)
    except IOError:
        font_counter = ImageFont.load_default()
        
    counter_bbox = draw.textbbox((0, 0), counter_text, font=font_counter)
    counter_w = counter_bbox[2] - counter_bbox[0]
    counter_x = 920 - counter_w
    counter_y = 1750
    
    # Counter shadow
    draw.text((counter_x + 2, counter_y + 2), counter_text, font=font_counter, fill=(0, 0, 0, 200))
    # Counter main text
    draw.text((counter_x, counter_y), counter_text, font=font_counter, fill=electric_green)
    
    # Save output
    final_output_path = os.path.join(out_dir, img_name)
    output.convert("RGB").save(final_output_path, "JPEG", quality=95)
    print(f"  Saved to {final_output_path}")

# Run process for all 8 covers
if __name__ == "__main__":
    for i, data in enumerate(covers_data):
        process_cover(data, i)
    print("\nAll 8 covers generated successfully!")
