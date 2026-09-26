from django.contrib import admin
from .models import Zone, Ride, Visitor, Booking, BookingItem

admin.site.register(Zone)
admin.site.register(Ride)
admin.site.register(Visitor)
admin.site.register(Booking)
admin.site.register(BookingItem)