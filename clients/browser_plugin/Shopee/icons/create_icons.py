# สร้าง icon สำหรับ Chrome Extension
from PIL import Image, ImageDraw

def create_icon(size, filename):
    # สร้างรูปพื้นหลังไล่สี
    img = Image.new('RGB', (size, size), '#667eea')
    draw = ImageDraw.Draw(img)
    
    # วาดวงกลมสีม่วง
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#764ba2')
    
    # วาดสามเหลี่ยม play
    center_x, center_y = size // 2, size // 2
    triangle_size = size // 3
    points = [
        (center_x - triangle_size // 3, center_y - triangle_size // 2),
        (center_x - triangle_size // 3, center_y + triangle_size // 2),
        (center_x + triangle_size // 2, center_y)
    ]
    draw.polygon(points, fill='white')
    
    img.save(filename)
    print(f"Created {filename}")

# สร้าง icons ทุกขนาด
create_icon(16, 'icon16.png')
create_icon(48, 'icon48.png')
create_icon(128, 'icon128.png')

print("Done!")
