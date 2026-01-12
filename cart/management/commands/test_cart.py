# cart/management/commands/test_cart.py
# Create this file: cart/management/commands/test_cart.py

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from cart.cart import Cart
from products.models import NyscKit, NyscTour, Church
import json


class Command(BaseCommand):
    help = 'Test cart functionality directly'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('CART TEST'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Create mock request with session
        factory = RequestFactory()
        request = factory.get('/')
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        self.stdout.write(f"Session key: {request.session.session_key}")
        self.stdout.write(f"Initial session: {dict(request.session)}")
        
        # Initialize cart
        cart = Cart(request)
        self.stdout.write(f"\nInitial cart length: {len(cart)}")
        self.stdout.write(f"Initial cart.cart: {cart.cart}")
        
        # Get test products
        vest = NyscKit.objects.filter(type='vest').first()
        tour = NyscTour.objects.first()
        church = Church.objects.first()
        
        self.stdout.write(f"\nFound products:")
        self.stdout.write(f"  Vest: {vest}")
        self.stdout.write(f"  Tour: {tour}")
        self.stdout.write(f"  Church: {church}")
        
        if not vest:
            self.stdout.write(self.style.ERROR("No vest product found!"))
            return
        
        # Test 1: Add vest with size
        self.stdout.write(self.style.SUCCESS('\n--- TEST 1: Add Vest ---'))
        self.stdout.write(f"Product can be purchased: {vest.can_be_purchased}")
        
        try:
            cart.add(product=vest, quantity=1, extra_fields={'size': 'M'})
            self.stdout.write(self.style.SUCCESS("✓ cart.add() succeeded"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ cart.add() failed: {e}"))
            import traceback
            traceback.print_exc()
        
        self.stdout.write(f"Cart length after add: {len(cart)}")
        self.stdout.write(f"Cart.cart contents: {json.dumps(cart.cart, indent=2, default=str)}")
        self.stdout.write(f"Session after add: {dict(request.session)}")
        
        # Test 2: Iterate cart
        self.stdout.write(self.style.SUCCESS('\n--- TEST 2: Iterate Cart ---'))
        try:
            items = list(cart)
            self.stdout.write(f"✓ Cart iteration succeeded. Items: {len(items)}")
            for idx, item in enumerate(items):
                self.stdout.write(f"  Item {idx}:")
                self.stdout.write(f"    Product: {item['product']}")
                self.stdout.write(f"    Quantity: {item['quantity']}")
                self.stdout.write(f"    Price: {item['price']}")
                self.stdout.write(f"    Extra: {item.get('extra_fields')}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Cart iteration failed: {e}"))
            import traceback
            traceback.print_exc()
        
        # Test 3: Add another item
        if tour:
            self.stdout.write(self.style.SUCCESS('\n--- TEST 3: Add Tour ---'))
            try:
                cart.add(product=tour, quantity=1, extra_fields={'call_up_number': 'AB/22C/1234'})
                self.stdout.write(self.style.SUCCESS("✓ Added tour"))
                self.stdout.write(f"Cart length: {len(cart)}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Failed to add tour: {e}"))
        
        # Test 4: Get totals
        self.stdout.write(self.style.SUCCESS('\n--- TEST 4: Calculate Totals ---'))
        try:
            total = cart.get_total_price()
            self.stdout.write(f"✓ Total price: {total}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Failed to calculate total: {e}"))
        
        # Test 5: Session persistence
        self.stdout.write(self.style.SUCCESS('\n--- TEST 5: Session Persistence ---'))
        request.session.save()
        self.stdout.write("✓ Session saved")
        
        # Create new cart instance
        cart2 = Cart(request)
        self.stdout.write(f"New cart instance length: {len(cart2)}")
        self.stdout.write(f"New cart instance cart.cart: {json.dumps(cart2.cart, indent=2, default=str)}")
        
        # Final summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f"Final cart length: {len(cart2)}")
        self.stdout.write(f"Total items in session: {len(cart2.cart)}")
        self.stdout.write(f"Session has cart key: {'cart' in request.session}")
        
        if len(cart2) > 0:
            self.stdout.write(self.style.SUCCESS('✓ CART IS WORKING!'))
        else:
            self.stdout.write(self.style.ERROR('✗ CART IS EMPTY - ISSUE DETECTED'))
            self.stdout.write('\nPossible issues:')
            self.stdout.write('  1. Products not available or out of stock')
            self.stdout.write('  2. Cart.add() failing silently')
            self.stdout.write('  3. Session not persisting')
            self.stdout.write('  4. Iterator failing')