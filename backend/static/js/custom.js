// BedaanWaves Swagger UI Enhancements

// Auto-expand description sections and add time formatting
document.addEventListener("DOMContentLoaded", function() {
    // Find all parameter description sections
    const descriptions = document.querySelectorAll('.opblock-description');
    descriptions.forEach(desc => {
        // Expand collapsed descriptions
        const toggle = desc.closest('.scheme-container, .opblock')?.querySelector('.collapsed');
        if (toggle) {
            const expandButton = desc.querySelector('.expandBtn');
            if (expandButton && expandButton.parentElement === desc) {
                expandButton.click();
            }
        }
    });

    // Format time parameters' values
    const params = new URLSearchParams(window.location.search);
    const timeParams = params.toString().match(/time=[^&]*/g) || [];
    timeParams.forEach(param => {
        const name = param.split('=')[0];
        const value = param.split('=')[1];
        if (/^\d+$/.test(value)) {
            const formattedValue = new Date(parseInt(value)).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            history.replaceState(null, null, `${window.location.pathname}?${params.toString().replace(param, `time=${formattedValue}`)}`);
        }
    });
});

// Apply custom button styles and improve click responses
document.addEventListener('focusin', function(e) {
    if (e.target.matches('.btn.execute')) {
        e.target.style.transform = 'scale(1.05)';
        e.target.style.boxShadow = '0 4px 12px rgba(54, 200, 32, 0.3)';
    }
    if (e.target.matches('.btn.try-out')) {
        e.target.style.transform = 'scale(1.05)';
    }
});

document.addEventListener('mouseleave', function(e) {
    if (e.target.matches('.btn.execute') || e.target.matches('.btn.try-out')) {
        e.target.style.transform = 'scale(1)';
    }
});