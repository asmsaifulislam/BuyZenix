import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from core.models import Product
featured = Product.objects.filter(available=True, featured=True)[:8]
print('Featured:', featured.count())
for p in featured:
    print(' ', p.name, '| image:', p.image, '| image.url:', p.image.url if p.image else 'NONE')