from django.urls import path, include

urlpatterns = [
    path('', include('chat.urls')), # Include your app's URLs
]
