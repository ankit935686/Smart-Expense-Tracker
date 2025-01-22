from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    
    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ['name', 'user']
    
    def __str__(self):
        return self.name

    def get_monthly_expenses(self):
        start_date = timezone.now().replace(day=1)
        return self.expense_set.filter(
            date__gte=start_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0

class Expense(models.Model):
    RECURRING_CHOICES = [
        ('none', 'None'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    description = models.CharField(max_length=200)
    date = models.DateField()
    recurring = models.CharField(
        max_length=10,
        choices=RECURRING_CHOICES,
        default='none'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - {self.amount}"

    @classmethod
    def get_monthly_total(cls, user):
        start_date = timezone.now().replace(day=1)
        return cls.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0

    @classmethod
    def get_category_breakdown(cls, user):
        start_date = timezone.now().replace(day=1)
        total_expenses = cls.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or 0

        if total_expenses == 0:
            return []

        breakdown = cls.objects.filter(
            user=user,
            date__gte=start_date
        ).values('category__name').annotate(
            total=Sum('amount'),
            percentage=ExpressionWrapper(
                F('total') * 100.0 / total_expenses,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).order_by('-total')
        
        return [{
            'category': item['category__name'] or 'Uncategorized',
            'total': float(item['total']),
            'percentage': float(item['percentage'])
        } for item in breakdown]

    @classmethod
    def get_daily_breakdown(cls, user):
        start_date = timezone.now().replace(day=1)
        return cls.objects.filter(
            user=user,
            date__gte=start_date
        ).values('date').annotate(
            total=Sum('amount')
        ).order_by('date')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    last_budget_reset = models.DateTimeField(default=timezone.now)
    
    def get_remaining_budget(self):
        monthly_expenses = Expense.get_monthly_total(self.user)
        return self.total_budget - monthly_expenses

    def get_budget_percentage(self):
        if self.total_budget > 0:
            return (self.get_remaining_budget() / self.total_budget) * 100
        return 0

class AIInsight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    category = models.CharField(max_length=50)  # e.g., 'budget', 'spending', 'saving'
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
