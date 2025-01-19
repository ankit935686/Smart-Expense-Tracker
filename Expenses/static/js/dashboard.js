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