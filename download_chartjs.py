import urllib.request
import os

os.makedirs('static/js/libs', exist_ok=True)

print('Downloading Chart.js...')
url = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'
urllib.request.urlretrieve(url, 'static/js/libs/chart.min.js')

size = os.path.getsize('static/js/libs/chart.min.js')
print(f'✅ Downloaded! Size: {size} bytes')