# users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('auth/signup/', views.SignupView.as_view(), name='signup'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('user/me/', views.UserProfileView.as_view(), name='user-profile'),
    path('user/addresses/', views.UserAddressListView.as_view(), name='user-addresses'),
    path('user/addresses/<int:id>/', views.UserAddressDetailView.as_view(), name='user-address-detail'),
    path('user/addresses/<int:id>/default/', views.SetDefaultAddressView.as_view(), name='set-default-address'),
]