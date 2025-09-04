// Evitar caché en todas las páginas
window.addEventListener('load', function() {
    if (performance.navigation.type === 1 && !window.location.href.includes('login_page')) {
        window.location.replace(window.location.origin + '/login_page.py');
    }
});