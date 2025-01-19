document.addEventListener('DOMContentLoaded', function() {
    const refreshButton = document.getElementById('refreshInsights');
    const insightsContent = document.querySelector('.insights-content');
    
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshButton.disabled = true;
            refreshButton.innerHTML = '<i class="mdi mdi-loading mdi-spin"></i> Generating...';
            
            // Generate new insights
            fetch('/insights/generate/')
                .then(response => response.json())
                .then(data => {
                    // Refresh insights display
                    fetch('/insights/')
                        .then(response => response.text())
                        .then(html => {
                            insightsContent.innerHTML = html;
                            refreshButton.disabled = false;
                            refreshButton.innerHTML = '<i class="mdi mdi-refresh"></i> Get New Advice';
                        });
                })
                .catch(error => {
                    console.error('Error:', error);
                    refreshButton.disabled = false;
                    refreshButton.innerHTML = '<i class="mdi mdi-refresh"></i> Get New Advice';
                });
        });
    }
}); 