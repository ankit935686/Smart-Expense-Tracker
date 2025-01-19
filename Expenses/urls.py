from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('add-expense/', views.add_expense, name='add_expense'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('update-category-budget/<int:category_id>/', views.update_category_budget, name='update_category_budget'),
    path('set-budget/', views.set_budget, name='set_budget'),
    path('expense-list/', views.expense_list, name='expense_list'),
    
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('categories/', views.category_list, name='categories'),
    path('category/add/', views.add_category, name='add_category'),
    path('category/<int:category_id>/edit/', views.edit_category, name='edit_category'),
    path('category/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    path('profile/', views.profile, name='profile'),
    path('insights/', views.get_insights, name='get_insights'),
    path('insights/generate/', views.generate_insights, name='generate_insights'),
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='expenses/password_change.html',
        success_url='/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='expenses/password_change_done.html'
    ), name='password_change_done'),
    path('export-expenses/', views.export_expenses, name='export_expenses'),
    path('api/daily-spending/<str:period>/', views.daily_spending, name='daily_spending'),
    path('api/generate-insights/', views.generate_insights, name='generate_insights'),
]