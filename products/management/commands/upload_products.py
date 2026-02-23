# products/management/commands/upload_products.py
"""
Management command to upload products from CSV files - PRODUCTION READY VERSION

This comprehensive upload utility handles ALL edge cases and validations.
"""

import csv
import requests
import logging
import re
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import transaction
from django.utils.text import slugify
from cloudinary.uploader import upload
from cloudinary import CloudinaryImage
from products.models import Category, NyscKit, NyscTour, Church
from products.constants import (
    NYSC_KIT_TYPE_CHOICES,
    NYSC_KIT_PRODUCT_NAME,
    STATES,
    CHURCH_PRODUCT_NAME,
    CHURCH_CHOICES,
    CATEGORY_NAME_CHOICES,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Upload products from CSV file with comprehensive validation"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")
        parser.add_argument(
            "--type",
            type=str,
            required=True,
            choices=["nysc_kit", "nysc_tour", "church"],
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--skip-existing", action="store_true")
        parser.add_argument("--update-existing", action="store_true")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        product_type = options["type"]
        dry_run = options["dry_run"]
        skip_existing = options["skip_existing"]
        update_existing = options["update_existing"]

        if skip_existing and update_existing:
            raise CommandError("Cannot use both --skip-existing and --update-existing")

        # Header
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("  MATERIAL ACCESSORIES - PRODUCT UPLOAD"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(f"\nProduct Type: {self.style.WARNING(product_type.upper())}")
        self.stdout.write(f"CSV File: {self.style.WARNING(csv_file)}")
        if dry_run:
            self.stdout.write(self.style.NOTICE("MODE: DRY RUN\n"))

        try:
            # Read CSV
            with open(csv_file, "r", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                rows = list(reader)

            if not rows:
                raise CommandError("CSV file is empty")

            self.stdout.write(f"Found {len(rows)} products\n")

            # Validate
            self._validate_headers(reader.fieldnames, product_type)
            self._check_csv_duplicates(rows)

            # Process
            success_count = error_count = skip_count = update_count = 0
            errors = []

            for idx, row in enumerate(rows, start=1):
                self.stdout.write(f'\n[{idx}/{len(rows)}] {row.get("name", "Unknown")}')

                try:
                    with transaction.atomic():
                        if product_type == "nysc_kit":
                            result = self._process_nysc_kit(
                                row, dry_run, skip_existing, update_existing
                            )
                        elif product_type == "nysc_tour":
                            result = self._process_nysc_tour(
                                row, dry_run, skip_existing, update_existing
                            )
                        else:
                            result = self._process_church(
                                row, dry_run, skip_existing, update_existing
                            )

                        if result == "success":
                            success_count += 1
                            self.stdout.write(self.style.SUCCESS("  ✓ Created"))
                        elif result == "updated":
                            update_count += 1
                            self.stdout.write(self.style.SUCCESS("  ✓ Updated"))
                        elif result == "skipped":
                            skip_count += 1
                            self.stdout.write(self.style.NOTICE("  ⊘ Skipped"))

                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {idx}: {str(e)}")
                    self.stdout.write(self.style.ERROR(f"  ✗ {str(e)}"))

            # Summary
            self.stdout.write("\n" + self.style.SUCCESS("=" * 80))
            self.stdout.write(self.style.SUCCESS("  SUMMARY"))
            self.stdout.write(self.style.SUCCESS("=" * 80))
            self.stdout.write(f"Total: {len(rows)}")
            self.stdout.write(self.style.SUCCESS(f"✓ Created: {success_count}"))
            if update_count:
                self.stdout.write(self.style.SUCCESS(f"✓ Updated: {update_count}"))
            if skip_count:
                self.stdout.write(self.style.NOTICE(f"⊘ Skipped: {skip_count}"))
            if error_count:
                self.stdout.write(self.style.ERROR(f"✗ Errors: {error_count}"))
                for error in errors:
                    self.stdout.write(self.style.ERROR(f"  {error}"))

            if dry_run:
                self.stdout.write(self.style.NOTICE("\nDRY RUN - No changes saved"))

        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_file}")
        except UnicodeDecodeError:
            raise CommandError("Encoding error. Save as UTF-8")
        except csv.Error as e:
            raise CommandError(f"CSV error: {str(e)}")

    def _validate_headers(self, headers, product_type):
        if not headers:
            raise CommandError("No headers found")
        required = ["name", "category", "price", "description"]
        if product_type == "nysc_kit":
            required.append("type")
        if product_type == "church":
            required.append("church")
        missing = set(required) - set(headers)
        if missing:
            raise CommandError(f'Missing columns: {", ".join(missing)}')

    def _check_csv_duplicates(self, rows):
        seen = {}
        dups = []
        for idx, row in enumerate(rows, start=2):
            name = row.get("name", "").strip()
            if name in seen:
                dups.append(f'"{name}" on lines {seen[name]} and {idx}')
            else:
                seen[name] = idx
        if dups:
            raise CommandError("Duplicates:\n" + "\n".join(f"  {d}" for d in dups))

    def _validate_category(self, name, ptype):
        valid = [c[0] for c in CATEGORY_NAME_CHOICES]
        if name not in valid:
            raise ValueError(f'Invalid category. Must be: {", ".join(valid)}')

        cmap = {
            "NYSC KIT": "nysc_kit",
            "NYSC TOUR": "nysc_tour",
            "CHURCH PROGRAMME": "church",
        }
        if cmap.get(name) != ptype:
            raise ValueError(f"Category mismatch for {ptype}")

    def _validate_price(self, price_str):
        try:
            price = Decimal(str(price_str).strip())
            if price <= 0:
                raise ValueError("Price must be > 0")
            if price > 9999999.99:
                raise ValueError("Price too large")
            return price
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid price: {str(e)}")

    def _get_or_create_category(self, name, ptype, desc=None):
        ptype_map = {
            "nysc_kit": "nysc_kit",
            "nysc_tour": "nysc_tour",
            "church": "church",
        }

        if not desc:
            desc_map = {
                "NYSC KIT": "Complete NYSC uniform kit including Kakhi, Vest, and Cap. Premium quality products for serving corps members.",
                "NYSC TOUR": "NYSC tour packages for all 37 Nigerian states. Comprehensive deployment support and orientation services.",
                "CHURCH PROGRAMME": "Quality church merchandise and program materials. Official church shirts, jackets, and polos for various denominations.",
            }
            desc = desc_map.get(name, f"{name} products")

        cat, created = Category.objects.get_or_create(
            name=name,
            defaults={
                "slug": slugify(name),
                "product_type": ptype_map[ptype],
                "description": desc,
            },
        )

        if not created and not cat.description:
            cat.description = desc
            cat.save()

        return cat

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

        Returns: public_id with extension (e.g., "products/kakhi.jpg")
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
            self.stdout.write(
                self.style.WARNING(
                    f"    Warning: Could not parse Cloudinary URL: {str(e)}"
                )
            )
            return None

    def _download_image(self, url):
        """Download image from URL and return File object, or return Cloudinary public_id if it's a Cloudinary URL"""
        if not url or not url.strip():
            return None

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
                        "    Warning: Invalid Cloudinary URL format, downloading instead"
                    )
                )
                # Fall through to normal download

        try:
            if len(url.strip()) > 500:
                self.stdout.write(self.style.WARNING("    URL too long"))
                return None

            resp = requests.get(url.strip(), timeout=30, stream=True)
            resp.raise_for_status()

            ctype = resp.headers.get("content-type", "")
            if not ctype.startswith("image/"):
                self.stdout.write(self.style.WARNING(f"    Not an image ({ctype})"))
                return None

            clen = resp.headers.get("content-length")
            if clen and int(clen) > 10 * 1024 * 1024:
                self.stdout.write(self.style.WARNING("    Image too large (>10MB)"))
                return None

            tmp = NamedTemporaryFile(delete=True)
            for chunk in resp.iter_content(8192):
                tmp.write(chunk)
            tmp.flush()
            tmp.seek(0)  # Reset file pointer to beginning for reading

            fname = url.split("/")[-1].split("?")[0]
            if not any(
                fname.lower().endswith(e)
                for e in [".jpg", ".jpeg", ".png", ".gif", ".webp"]
            ):
                fname += ".jpg"

            return File(tmp, name=fname)

        except requests.Timeout:
            self.stdout.write(self.style.WARNING("    Timeout"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"    Error: {str(e)}"))
        return None

    def _str_to_bool(self, val):
        if isinstance(val, bool):
            return val
        if not val or str(val).strip() == "":
            return True
        return str(val).strip().lower() in ["true", "1", "yes", "y"]

    def _process_nysc_kit(self, row, dry_run, skip_ex, update_ex):
        name = row["name"].strip()
        if not name:
            raise ValueError("Name required")

        cat_name = row["category"].strip()
        self._validate_category(cat_name, "nysc_kit")
        price = self._validate_price(row["price"])

        existing = NyscKit.objects.filter(name=name).first()
        if existing:
            if skip_ex:
                return "skipped"
            if not update_ex:
                raise ValueError("Already exists")

        valid_names = [c[0] for c in NYSC_KIT_PRODUCT_NAME]
        if name not in valid_names:
            raise ValueError(f'Invalid name. Must be one of: {", ".join(valid_names)}')

        kit_type = row["type"].strip().lower()
        valid_types = [c[0] for c in NYSC_KIT_TYPE_CHOICES]
        if kit_type not in valid_types:
            raise ValueError(f'Invalid type: {", ".join(valid_types)}')

        if dry_run:
            self.stdout.write(f"    {name} ({kit_type}) - ₦{price:,.2f}")
            return "success"

        cat_desc = row.get("category_description", "").strip() or None
        category = self._get_or_create_category(cat_name, "nysc_kit", cat_desc)

        data = {
            "name": name,
            "type": kit_type,
            "category": category,
            "price": price,
            "description": row.get("description", "").strip(),
            "available": self._str_to_bool(row.get("available", "True")),
            "out_of_stock": self._str_to_bool(row.get("out_of_stock", "False")),
        }

        if existing and update_ex:
            for k, v in data.items():
                setattr(existing, k, v)
            product = existing
        else:
            product = NyscKit(**data)

        for img in ["image", "image_1", "image_2", "image_3"]:
            if img in row and row[img].strip():
                imgf = self._download_image(row[img])
                if imgf:
                    setattr(product, img, imgf)

        product.save()
        return "updated" if existing and update_ex else "success"

    def _process_nysc_tour(self, row, dry_run, skip_ex, update_ex):
        name = row["name"].strip()
        if not name:
            raise ValueError("Name required")

        cat_name = row["category"].strip()
        self._validate_category(cat_name, "nysc_tour")
        price = self._validate_price(row["price"])

        existing = NyscTour.objects.filter(name=name).first()
        if existing:
            if skip_ex:
                return "skipped"
            if not update_ex:
                raise ValueError("Already exists")

        valid_states = [c[0] for c in STATES if c[0] != ""]
        if name not in valid_states:
            raise ValueError(f"Invalid state")

        if dry_run:
            self.stdout.write(f"    {name} - ₦{price:,.2f}")
            return "success"

        cat_desc = row.get("category_description", "").strip() or None
        category = self._get_or_create_category(cat_name, "nysc_tour", cat_desc)

        data = {
            "name": name,
            "category": category,
            "price": price,
            "description": row.get("description", "").strip(),
            "available": self._str_to_bool(row.get("available", "True")),
            "out_of_stock": self._str_to_bool(row.get("out_of_stock", "False")),
        }

        if existing and update_ex:
            for k, v in data.items():
                setattr(existing, k, v)
            product = existing
        else:
            product = NyscTour(**data)

        for img in ["image", "image_1", "image_2", "image_3"]:
            if img in row and row[img].strip():
                imgf = self._download_image(row[img])
                if imgf:
                    setattr(product, img, imgf)

        product.save()
        return "updated" if existing and update_ex else "success"

    def _process_church(self, row, dry_run, skip_ex, update_ex):
        name = row["name"].strip()
        if not name:
            raise ValueError("Name required")

        cat_name = row["category"].strip()
        self._validate_category(cat_name, "church")
        price = self._validate_price(row["price"])

        existing = Church.objects.filter(name=name).first()
        if existing:
            if skip_ex:
                return "skipped"
            if not update_ex:
                raise ValueError("Already exists")

        valid_names = [c[0] for c in CHURCH_PRODUCT_NAME]
        if name not in valid_names:
            raise ValueError(f'Invalid name. Must be: {", ".join(valid_names)}')

        church = row["church"].strip()
        valid_churches = [c[0] for c in CHURCH_CHOICES if c[0] != ""]
        if church not in valid_churches:
            raise ValueError(f'Invalid church: {", ".join(valid_churches)}')

        if dry_run:
            self.stdout.write(f"    {name} ({church}) - ₦{price:,.2f}")
            return "success"

        cat_desc = row.get("category_description", "").strip() or None
        category = self._get_or_create_category(cat_name, "church", cat_desc)

        data = {
            "name": name,
            "church": church,
            "category": category,
            "price": price,
            "description": row.get("description", "").strip(),
            "available": self._str_to_bool(row.get("available", "True")),
            "out_of_stock": self._str_to_bool(row.get("out_of_stock", "False")),
        }

        if existing and update_ex:
            for k, v in data.items():
                setattr(existing, k, v)
            product = existing
        else:
            product = Church(**data)

        for img in ["image", "image_1", "image_2", "image_3"]:
            if img in row and row[img].strip():
                imgf = self._download_image(row[img])
                if imgf:
                    setattr(product, img, imgf)

        product.save()
        return "updated" if existing and update_ex else "success"
