import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from core.models import Product, Category, ProductImage
print('=== Products ===')
for p in Product.objects.all()[:15]:
    print(p.name, '| featured:', p.featured, '| avail:', p.available, '| image:', p.image)
print()
print('=== Categories ===')
for c in Category.objects.all()[:10]:
    print(c.name, '| image:', c.image)
print()
print('=== ProductImages ===')
print('Count:', ProductImage.objects.count())
for pi in ProductImage.objects.all()[:10]:
    print(pi, '| image:', pi.image)