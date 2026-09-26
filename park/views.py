from django.shortcuts import render, redirect
from .models import Visitor, Zone, Ride, Booking, BookingItem
from django.db.models import Avg


# ---------------- HOME ----------------
def home(request):
    zones = Zone.objects.all()
    rides = Ride.objects.all()
    return render(request, "home.html", {"zones": zones, "rides": rides})


# ---------------- REGISTER ----------------
def register(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Check duplicate username
        if Visitor.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Username already exists"
            })

        Visitor.objects.create(
            name=name,
            email=email,
            phone=phone,
            username=username,
            password=password
        )

        return redirect('login')

    return render(request, "register.html")


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")


        from django.contrib.auth import authenticate

        auth_user = authenticate(request, username=username, password=password)
        if auth_user and auth_user.is_superuser:
            request.session['is_admin'] = True
            return redirect('admin_bookings')

        # Normal visitor login
        user = Visitor.objects.filter(
            username=username,
            password=password
        ).first()

        if user:
            request.session['visitor_id'] = user.id
            request.session['visitor_name'] = user.name
            return redirect('home')
        else:
            return render(request, "login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "login.html")


# ---------------- LOGOUT ----------------
def logout_view(request):
    request.session.flush()
    return redirect('home')


# ---------------- BOOKING ----------------
from django.core.mail import send_mail

def booking(request):
    if not request.session.get('visitor_id'):
        return redirect('login')

    rides = Ride.objects.select_related('zone').all()

    if request.method == "POST":
        visitor = Visitor.objects.get(id=request.session['visitor_id'])

        ride_ids   = request.POST.getlist('ride_ids')
        quantities = request.POST.getlist('quantities')

        if not ride_ids:
            return render(request, 'booking.html', {
                'rides': rides,
                'error': 'Please select at least one ride.'
            })

        visitor_email = request.POST.get('visitor_email')
        visitor_phone = request.POST.get('visitor_phone')
        visit_date    = request.POST.get('visit_date')

        total = 0
        items = []
        for ride_id, qty in zip(ride_ids, quantities):
            try:
                ride = Ride.objects.get(id=int(ride_id))
            except Ride.DoesNotExist:
                continue
            qty = int(qty)
            subtotal = ride.ticket_price * qty
            total += subtotal
            items.append((ride, qty, subtotal))

        b = Booking.objects.create(
            visitor=visitor, total_amount=total, status="Confirmed"
        )
        for ride, qty, subtotal in items:
            BookingItem.objects.create(
                booking=b, ride=ride, quantity=qty, total_price=subtotal
            )

        lines = "\n".join([
            f"  {r.name} ({r.zone.name}) x{q}  →  Rs.{s}"
            for r, q, s in items
        ])

        send_mail(
            subject=f'Booking Confirmed — MysticWorld #{b.id:05d}',
            message=f"""
============================================================
     MYSTICWORLD THEME PARK — BOOKING CONFIRMATION
============================================================

Hi {visitor.name}, your booking is confirmed!

BOOKING REFERENCE   : #{b.id:05d}
Booking Date        : {b.booking_date}
Visit Date          : {visit_date}
Status              : {b.status}

VISITOR DETAILS
Name                : {visitor.name}
Email               : {visitor_email}
Phone               : {visitor_phone}

RIDES BOOKED
{lines}

PAYMENT SUMMARY
Total Paid          : Rs.{total}
Payment             : Card on file

PARK INFO
Location : Fantasy Boulevard, Entertainment City
Hours    : 9 AM - 9 PM Daily
Phone    : +91 98765 43210

Show this email or Booking ID #{b.id:05d} at the gate.

Thank you for choosing MysticWorld!
============================================================
""",
            from_email='yourgmail@gmail.com',
            recipient_list=[visitor_email],
            fail_silently=True,
        )

        return redirect('booking_success', booking_id=b.id)

    return render(request, 'booking.html', {'rides': rides})


def booking_success(request, booking_id):
    booking = Booking.objects.get(id=booking_id)
    return render(request, 'booking_success.html', {'booking': booking})

from django.db.models import Sum, Count

def profile(request):
    if not request.session.get('visitor_id'):
        return redirect('login')
    visitor = Visitor.objects.get(id=request.session['visitor_id'])
    bookings = Booking.objects.filter(visitor=visitor).prefetch_related('bookingitem_set__ride__zone').order_by('-booking_date')
    total_rides = BookingItem.objects.filter(booking__visitor=visitor).aggregate(t=Sum('quantity'))['t'] or 0
    total_spent = Booking.objects.filter(visitor=visitor, status='Confirmed').aggregate(t=Sum('total_amount'))['t'] or 0
    return render(request, 'profile.html', {
        'visitor': visitor,
        'bookings': bookings,
        'total_bookings': bookings.count(),
        'total_rides': total_rides,
        'total_spent': total_spent,
    })

def update_profile(request):
    if not request.session.get('visitor_id'):
        return redirect('login')
    if request.method == 'POST':
        visitor = Visitor.objects.get(id=request.session['visitor_id'])
        visitor.name  = request.POST.get('name')
        visitor.email = request.POST.get('email')
        visitor.phone = request.POST.get('phone')
        visitor.save()
        request.session['visitor_name'] = visitor.name
    return redirect('/profile/?profile_success=1')

def change_password(request):
    if not request.session.get('visitor_id'):
        return redirect('login')
    if request.method == 'POST':
        visitor = Visitor.objects.get(id=request.session['visitor_id'])
        cur = request.POST.get('current_password')
        new = request.POST.get('new_password')
        con = request.POST.get('confirm_password')
        if visitor.password != cur:
            return render(request, 'profile.html', {'pw_error': 'Current password is incorrect.'})
        if new != con:
            return render(request, 'profile.html', {'pw_error': 'New passwords do not match.'})
        visitor.password = new
        visitor.save()
    return redirect('/profile/?pw_success=1')

def cancel_booking(request):
    if request.method == 'POST':
        b = Booking.objects.get(id=request.POST.get('booking_id'))
        b.status = 'Cancelled'
        b.save()
    return redirect('profile')

from .models import Review



def destination_detail(request, id):
    ride = Ride.objects.get(id=id)
    visitor_id = request.session.get('visitor_id')

    if request.method == "POST" and visitor_id:
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        review, created = Review.objects.get_or_create(
            ride=ride,
            visitor_id=visitor_id,
            defaults={'rating': rating, 'comment': comment}
        )

        if not created:
            review.rating = rating
            review.comment = comment
            review.save()

        return redirect('destination_detail', id=id)

    reviews = Review.objects.filter(ride=ride).select_related('visitor').order_by('-created_at')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']

    # Similar rides from the same zone, excluding current ride
    similar_rides = Ride.objects.filter(zone=ride.zone).exclude(id=ride.id)[:4]

    return render(request, 'destination_detail.html', {
        'ride': ride,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'similar_rides': similar_rides,
    })


from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse

def delete_review(request, id):
    if request.method == "POST":
        review = Review.objects.get(id=id)

        if review.visitor_id == request.session.get('visitor_id'):
            review.delete()

    return redirect(request.META.get('HTTP_REFERER'))

def zone_rides(request, id):
    zone = Zone.objects.get(id=id)
    rides = Ride.objects.filter(zone=zone)
    return render(request, 'zone_rides.html', {
        'zone': zone,
        'rides': rides
    })


from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q

# ─── PASTE THESE FUNCTIONS INTO views.py ─────────────────────────────────────

def admin_bookings(request):
    if not request.session.get('is_admin'):
        return redirect('login')

    # --- base queryset (optimised) ---
    qs = (Booking.objects
          .select_related('visitor')
          .prefetch_related('items__ride__zone')
          .order_by('-booking_date'))

    # --- search ---
    search = request.GET.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(visitor__name__icontains=search) |
            Q(visitor__username__icontains=search) |
            Q(visitor__email__icontains=search) |
            Q(id__icontains=search)
        )

    # --- status filter ---
    status = request.GET.get('status', '')
    if status in ('Confirmed', 'Cancelled'):
        qs = qs.filter(status=status)

    # --- date filters ---
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    visit_date = request.GET.get('visit_date')
    if date_from:
        qs = qs.filter(booking_date__gte=date_from)
    if date_to:
        qs = qs.filter(booking_date__lte=date_to)
    if visit_date:
        qs = qs.filter(visit_date=visit_date)

    # --- price range ---
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    if min_amount:
        qs = qs.filter(total_amount__gte=min_amount)
    if max_amount:
        qs = qs.filter(total_amount__lte=max_amount)

    # --- sorting ---
    sort = request.GET.get('sort', '-booking_date')
    allowed_sorts = ['booking_date', '-booking_date', 'total_amount', '-total_amount']
    if sort in allowed_sorts:
        qs = qs.order_by(sort)

    # --- dashboard stats (always full dataset, not filtered) ---
    all_qs = Booking.objects.all()
    total_bookings = all_qs.count()
    total_revenue = all_qs.filter(status='Confirmed').aggregate(t=Sum('total_amount'))['t'] or 0
    cancelled_count = all_qs.filter(status='Cancelled').count()
    total_visitors = Visitor.objects.count()

    # --- pagination ---
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 20)
    page_num = request.GET.get('page', 1)
    bookings = paginator.get_page(page_num)

    # all_bookings for modals (same filtered set, unpaginated)
    all_bookings = qs

    return render(request, 'admin_bookings.html', {
        'bookings': bookings,
        'all_bookings': all_bookings,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'cancelled_count': cancelled_count,
        'total_visitors': total_visitors,
    })


def admin_cancel_booking(request, booking_id):
    if not request.session.get('is_admin'):
        return redirect('login')
    if request.method == 'POST':
        b = Booking.objects.get(id=booking_id)
        b.status = 'Cancelled'
        b.save()
    return redirect('admin_bookings')


def admin_delete_booking(request, booking_id):
    if not request.session.get('is_admin'):
        return redirect('login')
    if request.method == 'POST':
        Booking.objects.filter(id=booking_id).delete()
    return redirect('admin_bookings')


def admin_update_status(request, booking_id):
    if not request.session.get('is_admin'):
        return redirect('login')
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ('Confirmed', 'Cancelled'):
            b = Booking.objects.get(id=booking_id)
            b.status = new_status
            b.save()
    return redirect('admin_bookings')