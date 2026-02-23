# feed/management/commands/upload_images.py
"""
Management command to upload images to feed from CSV file

CSV Format:
-----------
image_url,active
https://example.com/image1.jpg,true
https://example.com/image2.jpg,false
https://res.cloudinary.com/demo/image/upload/feed_images/banner.jpg,true

Supported URLs:
--------------
✅ External URLs (http/https): Downloaded and uploaded to Cloudinary
✅ Cloudinary URLs: Reused by public_id (NO duplication!)

Usage:
------
python manage.py upload_images path/to/images.csv
python manage.py upload_images path/to/images.csv --dry-run
"""

import csv
import requests
import logging
import re
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from feed.models import Image

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Upload images from CSV file to feed app"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving to database",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        dry_run = options["dry_run"]

        # Header
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("  MATERIAL ACCESSORIES - IMAGE UPLOAD"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"CSV File: {self.style.WARNING(csv_file)}")
        if dry_run:
            self.stdout.write(
                self.style.NOTICE("MODE: DRY RUN (No changes will be saved)\n")
            )

        try:
            # Read CSV
            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            if not rows:
                raise CommandError("CSV file is empty")

            self.stdout.write(f"Found {len(rows)} images to process\n")

            # Validate headers
            self._validate_headers(reader.fieldnames)

            # Process images
            success_count = error_count = 0
            errors = []

            for idx, row in enumerate(rows, start=1):
                image_url = row.get("image_url", "").strip()
                self.stdout.write(f"\n[{idx}/{len(rows)}] {image_url[:60]}...")

                try:
                    with transaction.atomic():
                        result = self._process_image(row, dry_run)

                        if result == "success":
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS("  ✓ Uploaded"))

                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {idx}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))

            # Summary
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("UPLOAD SUMMARY"))
            self.stdout.write("=" * 80)
            self.stdout.write(f"Total Processed: {len(rows)}")
            self.stdout.write(self.style.SUCCESS(f"✓ Successful: {success_count}"))
            if error_count:
                self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
                self.stdout.write("\nError Details:")
                for err in errors:
                    self.stdout.write(self.style.ERROR(f"  • {err}"))

            self.stdout.write("=" * 80 + "\n")

            if dry_run:
                self.stdout.write(
                    self.style.NOTICE(
                        "DRY RUN COMPLETE - No changes were saved to the database"
                    )
                )
            elif error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS("✓ Upload completed successfully!")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠ Upload completed with some errors")
                )

        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {csv_file}")
        except UnicodeDecodeError:
            raise CommandError("CSV file encoding error. Ensure file is UTF-8 encoded")
        except Exception as e:
            raise CommandError(f"Unexpected error: {str(e)}")

    def _validate_headers(self, headers):
        """Validate CSV headers"""
        required_headers = {"image_url"}
        optional_headers = {"active"}

        if not headers:
            raise CommandError("CSV file has no headers")

        header_set = set(headers)
        missing = required_headers - header_set

        if missing:
            raise CommandError(f"Missing required columns: {', '.join(missing)}")

        self.stdout.write(self.style.SUCCESS("✓ CSV headers validated"))

    def _process_image(self, row, dry_run):
        """Process a single image row"""
        image_url = row["image_url"].strip()

        if not image_url:
            raise ValueError("image_url cannot be empty")

        # Get active status (default to True)
        active = self._str_to_bool(row.get("active", "True"))

        if dry_run:
            self.stdout.write(f"    Would upload: {image_url} (active={active})")
            return "success"

        # Download/get image (returns File object OR string public_id)
        image_file = self._download_image(image_url)
        if not image_file:
            raise ValueError(f"Failed to download image from: {image_url}")

        # Create new image
        image = Image(active=active)

        # Cloudinary's ImageField accepts both:
        # - String (public_id) → references existing Cloudinary image (no duplicate!)
        # - File object → uploads new image to Cloudinary
        image.url = image_file

        image.save()

        return "success"

    def _download_image(self, url):
        """
        Download image from URL and return File object, or return Cloudinary public_id if it's a Cloudinary URL

        Returns:
            - String (public_id) for Cloudinary URLs (reuses existing image)
            - File object for regular URLs (will be uploaded to Cloudinary)
            - None if download fails
        """
        if not url or not url.strip():
            return None

        url = url.strip()

        # Check if it's a Cloudinary URL - if so, just return the public_id as a string
        if self._is_cloudinary_url(url):
            public_id = self._extract_cloudinary_public_id(url)
            if public_id:
                self.stdout.write(
                    self.style.NOTICE(
                        f"    ↻ Using existing Cloudinary image: {public_id}"
                    )
                )
                return public_id  # Return as string, not File object
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "    ⚠ Invalid Cloudinary URL format, downloading instead"
                    )
                )
                # Fall through to normal download

        # Validate URL length
        if len(url) > 500:
            self.stdout.write(
                self.style.WARNING(
                    f"    ⚠ URL too long (>{500} chars), skipping download"
                )
            )
            return None

        try:
            self.stdout.write(f"    → Downloading from: {url[:60]}...")

            # Download with timeout
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Validate content type
            content_type = response.headers.get("content-type", "").lower()
            if "image" not in content_type:
                self.stdout.write(
                    self.style.WARNING(
                        f"    ⚠ Not an image (content-type: {content_type})"
                    )
                )
                return None

            # Validate file size (max 10MB)
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > 10 * 1024 * 1024:
                self.stdout.write(self.style.WARNING("    ⚠ Image too large (>10MB)"))
                return None

            # Extract filename from URL
            filename = url.split("/")[-1].split("?")[0]
            if not filename or "." not in filename:
                filename = "image.jpg"

            # Create temporary file
            img_temp = NamedTemporaryFile(delete=True)

            # Download in chunks
            for chunk in response.iter_content(chunk_size=8192):
                img_temp.write(chunk)

            img_temp.flush()
            img_temp.seek(0)

            self.stdout.write(self.style.SUCCESS(f"    ✓ Downloaded successfully"))

            return File(img_temp, name=filename)

        except requests.Timeout:
            self.stdout.write(self.style.WARNING("    ⚠ Download timeout"))
            return None
        except requests.RequestException as e:
            self.stdout.write(self.style.WARNING(f"    ⚠ Download failed: {str(e)}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    ⚠ Unexpected error: {str(e)}"))
            return None

    def _is_cloudinary_url(self, url):
        """Check if URL is a Cloudinary URL"""
        if not url:
            return False
        return "cloudinary.com" in url.lower() and "/image/upload/" in url

    def _extract_cloudinary_public_id(self, url):
        """
        Extract public_id from Cloudinary URL

        Cloudinary URL formats:
        - https://res.cloudinary.com/{cloud_name}/image/upload/v{version}/{public_id}.{format}
        - https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/v{version}/{public_id}.{format}
        - https://res.cloudinary.com/{cloud_name}/image/upload/{public_id}.{format}

        Returns: public_id with extension (e.g., "feed_images/banner.jpg")
        """
        try:
            # Split by /image/upload/
            parts = url.split("/image/upload/")
            if len(parts) != 2:
                return None

            # Get everything after /image/upload/
            after_upload = parts[1]

            # Remove query parameters
            after_upload = after_upload.split("?")[0]

            # Split by / to get segments
            segments = after_upload.split("/")

            # Remove version (starts with 'v' followed by numbers)
            segments = [s for s in segments if not re.match(r"^v\d+$", s)]

            # Remove transformations (contains underscore, comma, or common transform prefixes)
            transform_patterns = [r"w_", r"h_", r"c_", r"q_", r"f_", r"dpr_", r"ar_"]
            segments = [
                s
                for s in segments
                if not any(pattern in s for pattern in transform_patterns)
            ]

            # What's left should be the public_id path (could be folder/filename.ext)
            public_id = "/".join(segments)

            return public_id

        except Exception as e:
            logger.error(f"Error extracting Cloudinary public_id: {str(e)}")
            return None

    def _str_to_bool(self, value):
        """
        Convert string to boolean

        True values: 'true', '1', 'yes', 'y', True
        False values: 'false', '0', 'no', 'n', False
        Empty/None: defaults to True
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return True

        if isinstance(value, bool):
            return value

        value_str = str(value).strip().lower()

        if value_str in ("true", "1", "yes", "y"):
            return True
        elif value_str in ("false", "0", "no", "n"):
            return False
        else:
            # Default to False for invalid values
            return False
