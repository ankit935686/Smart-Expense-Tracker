from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ExpenseForm, CategoryForm, BudgetForm
from .models import Expense, Category, UserProfile
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
import json
from django.db.models.functions import TruncDate, ExtractMonth
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.db.models import Sum, Avg
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create default categories for new user
            default_categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping']
            for cat in default_categories:
                Category.objects.create(name=cat, user=user)
            
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def send_budget_reminder_email(user):
    """Helper function to send budget reminder email"""
    subject = 'Monthly Budget Reset Reminder'
    message = f"""
    Hello {user.username},

    This is a reminder that your monthly budget has been reset for the new month.
    Please set your new budget to help maintain your financial goals.

    You can set your budget here: {settings.SITE_URL}/expenses/set-budget/

    Best regards,
    Your Expense Tracker Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

@receiver(post_save, sender=UserProfile)
def create_user_profile(sender, instance, created, **kwargs):
    """Signal handler to set initial budget reminder date"""
    if created:
        instance.last_budget_reset = timezone.now()
        instance.save()

def check_and_reset_monthly_budget():
    """Helper function to check and reset monthly budgets"""
    today = timezone.now()
    
    # Get all user profiles
    profiles = UserProfile.objects.all()
    
    for profile in profiles:
        last_reset = profile.last_budget_reset
        
        # Check if it's a new month since last reset
        if (today.year > last_reset.year) or (today.month > last_reset.month):
            # Reset budget
            profile.total_budget = Decimal('0.00')
            profile.last_budget_reset = today
            profile.save()
            
            # Send reminder email
            send_budget_reminder_email(profile.user)

@login_required(login_url='login')
def dashboard(request):
    # Check for monthly budget reset at the start of dashboard view
    check_and_reset_monthly_budget()
    
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get the current month's data
    today = timezone.now()
    start_date = today.replace(day=1)
    
    # Get monthly expenses
    monthly_spend = Expense.get_monthly_total(request.user)
    
    # Calculate remaining budget
    remaining_budget = profile.get_remaining_budget()
    
    # Get expense breakdown by category
    category_expenses = Expense.get_category_breakdown(request.user)
    
    # Get recent transactions
    recent_transactions = Expense.objects.filter(
        user=request.user
    ).select_related('category').order_by('-date')[:5]
    
    # Handle AJAX request for recent transactions
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('partial') == 'recent_transactions':
        transactions_data = [{
            'id': t.id,
            'date': t.date,
            'description': t.description,
            'category_name': t.category.name if t.category else None,
            'amount': str(t.amount)
        } for t in recent_transactions]
        
        return JsonResponse({'transactions': transactions_data})
    
    context = {
        'user': request.user,
        'profile': profile,
        'total_budget': profile.total_budget,
        'remaining_budget': remaining_budget,
        'monthly_spend': monthly_spend,
        'category_expenses': category_expenses,
        'recent_transactions': recent_transactions,
        'budget_percentage': profile.get_budget_percentage(),
    }
    
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(request.user)
    
    return render(request, 'expenses/add_expense.html', {'form': form})

@login_required(login_url='login')
def manage_categories(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            
            # If it's an AJAX request, return JSON response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'budget': float(category.budget)
                    }
                })
            
            messages.success(request, 'Category added successfully!')
            return redirect('manage_categories')
    else:
        form = CategoryForm()
    
    categories = Category.objects.filter(user=request.user)
    return render(request, 'expenses/manage_categories.html', {
        'form': form,
        'categories': categories
    })

@login_required(login_url='login')
def update_category_budget(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id, user=request.user)
        try:
            budget = float(request.POST.get('budget', 0))
            category.budget = budget
            category.save()
            return JsonResponse({'status': 'success'})
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid budget amount'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required(login_url='login')
def set_budget(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Check for monthly budget reset
    check_and_reset_monthly_budget()
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=user_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.last_budget_reset = timezone.now()
            profile.save()
            messages.success(request, 'Budget updated successfully!')
            return redirect('dashboard')
    else:
        form = BudgetForm(instance=user_profile)
    
    return render(request, 'expenses/set_budget.html', {
        'form': form,
        'user_profile': user_profile
    })


@login_required(login_url='login')
def expense_list(request):
    # Get filter parameters from request
    category = request.GET.get('category')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    sort_by = request.GET.get('sort_by', '-date')  # Default sort by date descending
    
    # Start with all user's expenses
    expenses = Expense.objects.filter(user=request.user)
    
    # Apply filters
    if category:
        expenses = expenses.filter(category_id=category)
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)
    
    # Apply sorting
    expenses = expenses.order_by(sort_by)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(user=request.user)
    
    # Calculate totals
    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0

    # Add monthly comparisons
    today = datetime.now().date()
    monthly_comparisons = []
    
    for month_offset in range(3):
        month_date = today - timedelta(days=30 * month_offset)
        month_start = month_date.replace(day=1)
        if month_offset < 2:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        else:
            month_end = month_date

        # Get monthly totals and category breakdown
        month_data = Expense.objects.filter(
            user=request.user,
            date__gte=month_start,
            date__lte=month_end
        )
        
        month_total = month_data.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get top categories for the month
        top_categories = month_data.values(
            'category__name'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')[:3]  # Get top 3 categories

        # Calculate percentages for top categories
        for category in top_categories:
            category['percentage'] = (category['total'] / month_total * 100) if month_total > 0 else 0
            category['total'] = float(category['total'])

        monthly_comparisons.append({
            'month': month_start.strftime('%B %Y'),
            'total': float(month_total),
            'top_categories': list(top_categories),
            'transaction_count': month_data.count()
        })
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'total_amount': total_amount,
        'selected_category': category,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'monthly_comparisons': monthly_comparisons
    }
    
    return render(request, 'expenses/expense_list.html', context)

@login_required(login_url='login')
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('categories')
    else:
        form = CategoryForm()
    
    categories = Category.objects.filter(user=request.user).order_by('name')
    return render(request, 'expenses/categories.html', {
        'categories': categories,
        'form': form
    })

@login_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category added successfully!')
            return redirect('categories')
    else:
        form = CategoryForm()
    return render(request, 'expenses/add_category.html', {'form': form})

@login_required
@require_http_methods(["POST"])
def edit_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id, user=request.user)
        data = json.loads(request.body)
        
        category.name = data.get('name')
        category.budget = data.get('budget')
        category.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Category updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def delete_category(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id, user=request.user)
        category.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Category deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required(login_url='login')
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'expenses/profile.html', {
        'user_profile': user_profile
    })

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('dashboard')
    else:
        form = ExpenseForm(request.user, instance=expense)
    
    return render(request, 'expenses/edit_expense.html', {
        'form': form,
        'expense': expense
    })

@login_required
@require_http_methods(["POST", "DELETE"])
def delete_expense(request, expense_id):
    try:
        expense = get_object_or_404(Expense, id=expense_id, user=request.user)
        expense.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Expense deleted successfully'
            })
        
        messages.success(request, 'Expense deleted successfully!')
        return redirect('dashboard')
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, f'Error deleting expense: {str(e)}')
        return redirect('dashboard')

@login_required(login_url='login')
def get_insights(request):
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # Get current month's data
        current_month = timezone.now().replace(day=1)
        monthly_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=current_month
        )
        
        total_spent = monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        user_profile = UserProfile.objects.get(user=request.user)
        
        # Get category breakdown
        category_expenses = monthly_expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        insights = []
        
        # Add budget warning if necessary
        if user_profile.total_budget and total_spent > (user_profile.total_budget * Decimal('0.8')):
            insights.append({
                'message': f"You've spent {(total_spent/user_profile.total_budget)*100:.1f}% of your monthly budget.",
                'category': 'budget_warning'
            })
        
        # Add AI-generated insight
        if total_spent > 0:
            prompt = f"""
            Analyze this spending data and provide one specific financial insight:
            Total Budget: ${user_profile.total_budget}
            Spent so far: ${total_spent}
            Category breakdown: {', '.join([f"{cat['category__name']}: ${cat['total']}" for cat in category_expenses])}
            
            Provide a short, specific insight about spending patterns or budget management.
            Keep it under 100 characters.
            """
            
            response = model.generate_content(prompt)
            if response.text:
                insights.append({
                    'message': response.text.strip(),
                    'category': 'budget_status'
                })
    
    except Exception as e:
        print(f"Error generating insights: {str(e)}")
        insights = [{
            'message': "Unable to generate insights at this time.",
            'category': 'error'
        }]
    
    return render(request, 'expenses/insights_widget.html', {'insights': insights})

@login_required
def generate_insights(request):
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # Get user's financial data
        today = datetime.now().date()
        start_of_month = today.replace(day=1)
        
        # Get current month's expenses
        current_month_expenses = Expense.objects.filter(
            user=request.user,
            date__gte=start_of_month
        )
        
        total_spent = current_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get category breakdown
        category_expenses = current_month_expenses.values('category__name').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Format category data
        category_breakdown = []
        for cat in category_expenses:
            if cat['category__name']:
                percentage = (cat['total'] / total_spent * 100) if total_spent > 0 else 0
                category_breakdown.append(f"{cat['category__name']}: ${cat['total']:.2f} ({percentage:.1f}%)")

        # Calculate budget metrics
        total_budget = float(request.user.userprofile.total_budget)
        remaining_budget = total_budget - float(total_spent)
        budget_percentage = (remaining_budget / total_budget * 100) if total_budget > 0 else 0

        # Prepare prompt for Gemini
        prompt = f"""
        Analyze this user's financial data and provide 3-4 specific, actionable insights:

        Monthly Budget: ${total_budget:.2f}
        Spent so far: ${total_spent:.2f}
        Remaining: ${remaining_budget:.2f} ({budget_percentage:.1f}% of budget)

        Category Breakdown:
        {chr(10).join(category_breakdown)}

        Please provide:
        1. A spending pattern analysis
        2. Budget adherence feedback
        3. Specific saving recommendations
        4. Areas of concern (if any)

        Keep insights concise and actionable.
        """

        # Generate response using Gemini
        response = model.generate_content(prompt)
        insights = response.text.strip()

        print("Generated insights:", insights)  # Debug log

        return JsonResponse({
            'status': 'success',
            'insights': insights
        })

    except Exception as e:
        print(f"Error generating insights: {str(e)}")  # Debug log
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def export_expenses(request):
    try:
        print("Starting PDF generation...") # Debug log
        
        # Get current month's data
        current_month = timezone.now().replace(day=1)
        expenses = Expense.objects.filter(
            user=request.user,
            date__gte=current_month
        ).order_by('-date')
        
        print(f"Found {expenses.count()} expenses") # Debug log
        
        # Create the PDF buffer
        buffer = BytesIO()
        
        # Create the PDF object
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Add title
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title = Paragraph(f"Expense Report - {current_month.strftime('%B %Y')}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Add summary
        total_spent = expenses.aggregate(total=Sum('amount'))['total'] or 0
        print(f"Total spent: ${total_spent}") # Debug log
        
        summary_style = ParagraphStyle(
            'CustomStyle',
            fontSize=12,
            spaceAfter=20
        )
        
        elements.append(Paragraph(f"Total Spent: ${total_spent:.2f}", summary_style))
        elements.append(Spacer(1, 20))
        
        # Create table data
        data = [['Date', 'Description', 'Category', 'Amount']]
        for expense in expenses:
            data.append([
                expense.date.strftime('%Y-%m-%d'),
                expense.description,
                expense.category.name if expense.category else 'Uncategorized',
                f"${expense.amount:.2f}"
            ])
        
        # Create and style the table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        print("Building PDF...") # Debug log
        # Build PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        print("PDF generated successfully") # Debug log
        
        # Create the HTTP response
        response = HttpResponse(content_type='application/pdf')
        filename = f"expense_report_{current_month.strftime('%B_%Y')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write(pdf)
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}") # Debug log
        return HttpResponse("Error generating PDF report", status=500)

@login_required
def daily_spending(request, period):
    today = datetime.now().date()
    
    if period == 'week':
        start_date = today - timedelta(days=7)
    else:  # month
        start_date = today - timedelta(days=30)
    
    # Get daily spending data
    daily_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=today
    ).annotate(
        day=TruncDate('date')
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')
    
    # Create a complete date range with zeros for days without expenses
    date_range = []
    amounts = []
    current_date = start_date
    
    expense_dict = {expense['day']: expense['total'] for expense in daily_expenses}
    
    while current_date <= today:
        date_range.append(current_date.strftime('%b %d'))
        amounts.append(float(expense_dict.get(current_date, 0)))
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'dates': date_range,
        'amounts': amounts
    })
