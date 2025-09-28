import cloudinary
import cloudinary.uploader
import cloudinary.api
from django.conf import settings

# Initialize Cloudinary (should be called in Django settings, but safe here for utility)
cloudinary.config(
    cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
    api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
    api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
    secure=True
)

def upload_image_to_cloudinary(file, folder='products'):
    """
    Uploads an image file to Cloudinary and returns the URL.
    """
    result = cloudinary.uploader.upload(file, folder=folder)
    return result.get('secure_url')
