document.addEventListener('DOMContentLoaded', function() {
    // Setup CSRF token for AJAX requests
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Handle Delete Expense
    document.querySelectorAll('.delete-expense').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const expenseId = this.dataset.expenseId;
            
            if (confirm('Are you sure you want to delete this expense?')) {
                fetch(`/expense/${expenseId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Remove the row from table
                        this.closest('tr').remove();
                        showNotification('Expense deleted successfully', 'success');
                        // Refresh dashboard data
                        updateDashboardData();
                    } else {
                        throw new Error(data.message || 'Error deleting expense');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showNotification(error.message, 'error');
                });
            }
        });
    });

    // Handle Edit Expense Links
    document.querySelectorAll('.edit-expense').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const expenseId = this.dataset.expenseId;
            window.location.href = `/expense/${expenseId}/edit/`;
        });
    });

    // Helper function to show notifications
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Function to update dashboard data
    function updateDashboardData() {
        fetch(window.location.href + '?partial=recent_transactions', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#recentTransactionsTable tbody');
            tbody.innerHTML = data.transactions.map(expense => `
                <tr>
                    <td>${new Date(expense.date).toLocaleDateString()}</td>
                    <td>${expense.description}</td>
                    <td><span class="category-badge">${expense.category_name || 'Uncategorized'}</span></td>
                    <td class="amount">$${parseFloat(expense.amount).toFixed(2)}</td>
                    <td>
                        <a href="/expense/${expense.id}/edit/" class="btn btn-icon edit-expense" data-expense-id="${expense.id}">
                            <i class="mdi mdi-pencil"></i>
                        </a>
                        <button class="btn btn-icon delete-expense" data-expense-id="${expense.id}">
                            <i class="mdi mdi-delete"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
            
            // Reattach event listeners to new buttons
            attachEventListeners();
        })
        .catch(error => console.error('Error updating transactions:', error));
    }

    // Function to attach event listeners to new elements
    function attachEventListeners() {
        // Reattach delete handlers
        document.querySelectorAll('.delete-expense').forEach(button => {
            button.addEventListener('click', handleDelete);
        });
        
        // Reattach edit handlers
        document.querySelectorAll('.edit-expense').forEach(link => {
            link.addEventListener('click', handleEdit);
        });
    }
}); 