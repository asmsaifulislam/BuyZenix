import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from core.models import Product
Product.objects.filter(featured=True).update(featured=False)
Product.objects.filter(name__icontains='JIAYOU').update(featured=True)
Product.objects.filter(name__icontains='OLAX M200').update(featured=True)
Product.objects.filter(name__icontains='OLAX M100').update(featured=True)
f = Product.objects.filter(featured=True)
print('New featured:', f.count())
for p in f:
    print(' ', p.name, '| image:', bool(p.image))