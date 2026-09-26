from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('booking/', views.booking, name='booking'),
    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/password/', views.change_password, name='change_password'),
    path('profile/cancel/', views.cancel_booking, name='cancel_booking'),
    path('destination/<int:id>/', views.destination_detail, name='destination_detail'),
    path('zone/<int:id>/', views.zone_rides, name='zone_rides'),
    path('delete-review/<int:id>/', views.delete_review, name='delete_review'),
    path('manage/bookings/', views.admin_bookings, name='admin_bookings'),
    path('manage/bookings/<int:booking_id>/cancel/', views.admin_cancel_booking, name='admin_cancel_booking'),
    path('manage/bookings/<int:booking_id>/delete/', views.admin_delete_booking, name='admin_delete_booking'),
    path('manage/bookings/<int:booking_id>/status/', views.admin_update_status, name='admin_update_status'),
]