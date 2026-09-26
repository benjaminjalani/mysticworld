from django.db import models


# ---------------- ZONE ----------------
class Zone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


# ---------------- RIDE ----------------
class Ride(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    thrill_level = models.CharField(max_length=50)
    ticket_price = models.IntegerField()
    capacity = models.IntegerField()
    image = models.ImageField(upload_to='rides/')

    def __str__(self):
        return self.name


# ---------------- VISITOR ----------------
class Visitor(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.username


# ---------------- BOOKING MASTER ----------------
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Booking(models.Model):

    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, db_index=True)
    booking_date = models.DateField(auto_now_add=True)
    visit_date = models.DateField(null=True)

    total_amount = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed', db_index=True)

    def __str__(self):
        return f"Booking {self.id}"


class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.IntegerField()


class Review(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE)
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)