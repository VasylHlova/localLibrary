from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible

import os
import hashlib
from io import BytesIO
from PIL import Image, ImageOps


@deconstructible
class GeneratePath:
    def __init__(self, path):
        self.path = path

    def __call__(self, instance, filename):
        hashed_name = hashlib.sha256(filename.encode('utf-8')).hexdigest()

        file_ext = '.webp'
        new_filename = f'{hashed_name}{file_ext}'

        return os.path.join(self.path, new_filename)

def validate_file_size(file):
    limit = 20 * 1024 * 1024

    if file.size > limit :
        raise ValidationError('Exceeded max file size(20MB)')
    
def processing_image(image, max_size=(800, 800)):
    if not image:
        return None
    
    try:
        img = Image.open(image)
        img = ImageOps.exif_transpose(img)

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        

        img = ImageOps.fit(img, max_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

        output = BytesIO()
        img.save(output, format='WEBP', quality=85, optimize=True)
        output.seek(0)

        return ContentFile(output.read())

    except Exception:
        return True    