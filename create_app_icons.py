from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw white circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='white')
    
    # Draw rupee symbol
    try:
        # Try to find Arial font
        font = ImageFont.truetype('arial.ttf', size//3)
    except:
        try:
            # Windows font path
            font = ImageFont.truetype('C:\\Windows\\Fonts\\arial.ttf', size//3)
        except:
            # Fallback to default
            font = ImageFont.load_default()
    
    # Draw rupee symbol in center
    text = '₹'
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size//10
    
    draw.text((x, y), text, fill='#667eea', font=font)
    
    # Save
    img.save(f'static/{filename}')
    print(f'✅ Created {filename} ({size}x{size})')

# Make sure static folder exists
if not os.path.exists('static'):
    os.makedirs('static')

# Create icons
print('Creating app icons...')
create_icon(192, 'icon-192.png')
create_icon(512, 'icon-512.png')
print('✅ All icons created successfully!')