// Fonctions utilitaires globales
function formatDate(date) {
    return new Date(date).toLocaleDateString('fr-FR');
}

function formatTime(time) {
    return new Date(time).toLocaleTimeString('fr-FR');
}

// Gestionnaire d'erreurs global
function handleError(error) {
    console.error('Erreur:', error);
    alert('Une erreur est survenue. Veuillez réessayer.');
}

// Animation de chargement
function showLoading() {
    // Implémenter l'animation de chargement
}

function hideLoading() {
    // Masquer l'animation de chargement
}