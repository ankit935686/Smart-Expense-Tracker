document.addEventListener('DOMContentLoaded', function() {
    // Expense Chart
    const ctx = document.getElementById('expenseChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Food', 'Transport', 'Entertainment', 'Utilities', 'Others'],
            datasets: [{
                data: [300, 150, 100, 200, 50],
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Recent Expenses Table
    const expenseTableBody = document.getElementById('expenseTableBody');
    const expenses = [
        { date: '2023-04-15', category: 'Food', amount: 25.50, description: 'Lunch with colleagues' },
        { date: '2023-04-14', category: 'Transport', amount: 10.00, description: 'Uber ride' },
        { date: '2023-04-13', category: 'Entertainment', amount: 50.00, description: 'Movie tickets' },
        { date: '2023-04-12', category: 'Utilities', amount: 100.00, description: 'Electricity bill' },
        { date: '2023-04-11', category: 'Others', amount: 30.00, description: 'Office supplies' }
    ];

    expenses.forEach(expense => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${expense.date}</td>
            <td>${expense.category}</td>
            <td>$${expense.amount.toFixed(2)}</td>
            <td>${expense.description}</td>
        `;
        expenseTableBody.appendChild(row);
    });

    // AI Insights
    const aiInsights = document.getElementById('aiInsights');
    const insights = [
        "Consider reducing your food expenses by meal prepping at home.",
        "You've been consistent with your entertainment budget. Great job!",
        "Your utility bills are higher than average. Try energy-saving measures."
    ];

    function displayInsights() {
        aiInsights.innerHTML = '';
        insights.forEach(insight => {
            const p = document.createElement('p');
            p.textContent = insight;
            aiInsights.appendChild(p);
        });
    }

    displayInsights();

    document.getElementById('refreshInsights').addEventListener('click', displayInsights);

    // Add hover effect to expense rows
    const expenseRows = document.querySelectorAll('#expenseTableBody tr');
    expenseRows.forEach(row => {
        row.addEventListener('mouseenter', () => {
            row.style.backgroundColor = 'var(--sage-green)';
            row.style.color = 'white';
        });
        row.addEventListener('mouseleave', () => {
            row.style.backgroundColor = '';
            row.style.color = '';
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // Add mobile menu toggle button to header
    const header = document.querySelector('.dashboard-header');
    const menuButton = document.createElement('button');
    menuButton.classList.add('mobile-menu-toggle');
    menuButton.innerHTML = '<i class="mdi mdi-menu"></i>';
    
    // Only show menu button on mobile
    if (window.innerWidth <= 768) {
        header.insertBefore(menuButton, header.firstChild);
    }

    // Toggle sidebar on mobile
    menuButton.addEventListener('click', () => {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('active');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.sidebar');
            const menuButton = document.querySelector('.mobile-menu-toggle');
            
            if (!sidebar.contains(e.target) && !menuButton.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
});