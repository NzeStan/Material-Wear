# clothing_image_orders/__init__.py
"""
Clothing Image Orders App

This Django app handles bulk clothing orders with image upload support.

Features:
- Individual participant registration with image uploads
- Cloudinary integration for image storage
- Size selection and custom name printing
- Payment processing via Paystack
- Coupon code system
- Admin document generation (PDF, Word, Excel)
- Organized image download by size

Models:
- ClothingImageOrder: Main order entity
- ClothingOrderParticipant: Individual participants
- ClothingCouponCode: Discount coupons

Key Difference from bulk_orders:
- Image upload support (optional or required)
- Admin generates complete packages with images organized by size
- Images stored in Cloudinary folders by order and size
"""

default_app_config = 'clothing_image_orders.apps.ClothingImageOrdersConfig'