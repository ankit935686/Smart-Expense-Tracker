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

    // Add event listeners to period selector buttons
    document.querySelectorAll('.chart-period-selector .btn').forEach(btn => {
        btn.addEventListener('click', () => {
            updateDailySpendingData(btn.dataset.period);
        });
    });

    // Initial load of daily spending data
    updateDailySpendingData('week');
});

function updateDailySpendingTable(amounts, dates) {
    const tableBody = document.getElementById('dailySpendingBody');
    tableBody.innerHTML = '';
    
    // Find maximum amount for calculating distribution width
    const maxAmount = Math.max(...amounts);
    
    // Create table rows
    dates.forEach((date, index) => {
        const amount = amounts[index];
        const percentage = maxAmount > 0 ? (amount / maxAmount) * 100 : 0;
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${new Date(date).toLocaleDateString()}</td>
            <td>$${amount.toFixed(2)}</td>
            <td>
                <div class="progress">
                    <div class="progress-bar" 
                         style="width: ${percentage}%"
                         role="progressbar"
                         aria-valuenow="${percentage}"
                         aria-valuemin="0"
                         aria-valuemax="100">
                    </div>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Add this function to handle period changes
function updateDailySpendingData(period = 'week') {
    // Get all period buttons and update active state
    document.querySelectorAll('.chart-period-selector .btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.period === period);
    });

    // Fetch data from the API
    fetch(`/api/daily-spending/${period}/`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDailySpendingTable(data.amounts, data.dates);
            } else {
                console.error('Error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}