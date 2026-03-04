import urllib.request
import ssl
import os

# Bypass SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context

os.makedirs('static/js/libs', exist_ok=True)

print('Downloading Chart.js via mobile network...')

urls = [
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
    'https://unpkg.com/chart.js@4.4.0/dist/chart.umd.min.js'
]

for url in urls:
    try:
        print(f'Trying: {url}')
        urllib.request.urlretrieve(url, 'static/js/libs/chart.min.js')
        size = os.path.getsize('static/js/libs/chart.min.js')
        print(f'✅ SUCCESS! Downloaded {size} bytes')
        break
    except Exception as e:
        print(f'❌ Failed: {e}')
        continue

if os.path.exists('static/js/libs/chart.min.js'):
    size = os.path.getsize('static/js/libs/chart.min.js')
    if size > 100000:
        print(f'\n✅ Chart.js ready! File size: {size} bytes')
    else:
        print(f'\n❌ File too small ({size} bytes), download failed')
else:
    print('\n❌ Download completely failed')