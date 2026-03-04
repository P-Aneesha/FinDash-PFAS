from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    # Create gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw white circle
    margin = size // 8
    draw.ellipse([margin, margin, size-margin, size-margin], fill='white')
    
    # Draw rupee symbol
    try:
        font = ImageFont.truetype('arial.ttf', size//3)
    except:
        try:
            font = ImageFont.truetype('C:\\Windows\\Fonts\\arial.ttf', size//3)
        except:
            font = ImageFont.load_default()
    
    text = '₹'
    draw.text((size//2, size//2), text, fill='#667eea', font=font, anchor='mm')
    
    img.save(f'static/{filename}')
    print(f'✅ Created {filename}')

print('Creating app icons...')
create_icon(192, 'icon-192.png')
create_icon(512, 'icon-512.png')
print('✅ All icons created!')