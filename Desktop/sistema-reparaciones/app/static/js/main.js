// app/static/js/main.js
// JavaScript principal del Sistema de Gestión de Reparaciones

/**
 * Configuración global de la aplicación
 */
const RepairSystem = {
    config: {
        loadingTimeout: 30000, // 30 segundos
        alertAutoDismissTime: 5000, // 5 segundos
        toastDuration: 4000, // 4 segundos
        animationDuration: 300 // 300ms
    },
    
    state: {
        isLoading: false,
        activeToasts: 0,
        formSubmitting: false
    }
};

/**
 * Inicialización cuando el DOM está listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Sistema de Reparaciones cargado');
    
    // Inicializar componentes
    RepairSystem.initializeBootstrapComponents();
    RepairSystem.setupFormValidation();
    RepairSystem.setupButtonLoading();
    RepairSystem.setupAlertAutoDismiss();
    RepairSystem.setupGlobalEventListeners();
    
    // Cargar estadísticas si estamos en la página de reparaciones
    if (window.location.pathname.includes('/repairs')) {
        RepairSystem.loadStats();
    }
    
    console.log('✅ Inicialización completada');
});

/**
 * 1. Inicialización de componentes de Bootstrap
 */
RepairSystem.initializeBootstrapComponents = function() {
    // Inicializar tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 500, hide: 100 }
        });
    });
    
    // Inicializar popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => {
        return new bootstrap.Popover(popoverTriggerEl, {
            trigger: 'focus'
        });
    });
    
    // Configurar modals para auto-focus
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('shown.bs.modal', function() {
            const autofocusElement = modal.querySelector('[autofocus]');
            if (autofocusElement) {
                autofocusElement.focus();
            }
        });
    });
    
    console.log('📋 Componentes Bootstrap inicializados');
};

/**
 * 2. Validación de formularios en tiempo real
 */
RepairSystem.setupFormValidation = function() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        // Validación en tiempo real
        form.addEventListener('input', function(e) {
            if (e.target.matches('input, select, textarea')) {
                RepairSystem.validateField(e.target);
            }
        });
        
        // Validación al enviar
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                RepairSystem.showToast('Por favor, corrige los errores en el formulario', 'error');
            }
            form.classList.add('was-validated');
        });
    });
    
    console.log('📝 Validación de formularios configurada');
};

/**
 * 3. Validar campo individual
 */
RepairSystem.validateField = function(field) {
    const isValid = field.checkValidity();
    
    // Remover clases previas
    field.classList.remove('is-valid', 'is-invalid');
    
    // Agregar clase apropiada
    if (field.value.trim() !== '') {
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    }
    
    // Mostrar/ocultar mensaje de error personalizado
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback && !isValid && field.value.trim() !== '') {
        feedback.style.display = 'block';
    } else if (feedback) {
        feedback.style.display = 'none';
    }
};

/**
 * 4. Estados de loading para botones
 */
RepairSystem.setupButtonLoading = function() {
    const submitButtons = document.querySelectorAll('button[type="submit"], .btn-loading-trigger');
    
    submitButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const form = button.closest('form');
            
            // Solo aplicar loading si el formulario es válido
            if (form && form.checkValidity()) {
                RepairSystem.setButtonLoading(button, true);
                RepairSystem.state.formSubmitting = true;
                
                // Timeout de seguridad
                const timeout = setTimeout(() => {
                    RepairSystem.setButtonLoading(button, false);
                    RepairSystem.showToast('La operación está tardando más de lo esperado. Por favor, intenta de nuevo.', 'warning');
                }, RepairSystem.config.loadingTimeout);
                
                // Limpiar timeout cuando la página cambie
                window.addEventListener('beforeunload', () => clearTimeout(timeout));
                window.addEventListener('pageshow', () => {
                    RepairSystem.setButtonLoading(button, false);
                    RepairSystem.state.formSubmitting = false;
                });
            }
        });
    });
};

/**
 * 5. Establecer estado de loading en botón
 */
RepairSystem.setButtonLoading = function(button, isLoading) {
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.dataset.originalDisabled = button.disabled;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
        button.disabled = true;
        button.classList.add('btn-loading');
    } else {
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
        button.disabled = button.dataset.originalDisabled === 'true';
        button.classList.remove('btn-loading');
        RepairSystem.state.formSubmitting = false;
    }
};

/**
 * 6. Auto-dismiss de alertas
 */
RepairSystem.setupAlertAutoDismiss = function() {
    const alerts = document.querySelectorAll('.alert:not(.alert-important):not(.alert-persistent)');
    
    alerts.forEach(alert => {
        // Solo auto-dismiss alertas de éxito e info
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                if (alert && alert.parentNode && !alert.classList.contains('fade')) {
                    const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, RepairSystem.config.alertAutoDismissTime);
        }
    });
};

/**
 * 7. Mostrar notificación toast
 */
RepairSystem.showToast = function(message, type = 'info', duration = null) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        console.warn('Toast container no encontrado');
        return;
    }
    
    duration = duration || RepairSystem.config.toastDuration;
    
    // Crear toast
    const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0" 
             role="alert" id="${toastId}" data-bs-autohide="true" data-bs-delay="${duration}">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${RepairSystem.getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Agregar al container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Inicializar y mostrar
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    
    RepairSystem.state.activeToasts++;
    
    // Limpiar cuando se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
        RepairSystem.state.activeToasts--;
    });
    
    toast.show();
    
    return toastId;
};

/**
 * 8. Obtener icono para toast según tipo
 */
RepairSystem.getToastIcon = function(type) {
    const icons = {
        'success': 'bi-check-circle-fill',
        'error': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };
    return icons[type] || icons['info'];
};

/**
 * 9. Cargar estadísticas del dashboard
 */
RepairSystem.loadStats = function() {
    fetch('/repairs/stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                RepairSystem.updateStatsDisplay(data.stats, data.priorities);
            }
        })
        .catch(error => {
            console.error('Error cargando estadísticas:', error);
        });
};

/**
 * 10. Actualizar display de estadísticas
 */
RepairSystem.updateStatsDisplay = function(stats, priorities) {
    // Actualizar contadores por estado
    const pendingElement = document.getElementById('pending-diagnosis-count');
    const waitingElement = document.getElementById('waiting-parts-count');
    const readyElement = document.getElementById('ready-delivery-count');
    const urgentElement = document.getElementById('urgent-count');
    
    if (pendingElement && stats.pending_diagnosis) {
        RepairSystem.animateNumber(pendingElement, stats.pending_diagnosis.count);
    }
    
    if (waitingElement && stats.waiting_parts) {
        RepairSystem.animateNumber(waitingElement, stats.waiting_parts.count);
    }
    
    if (readyElement && stats.ready_for_delivery) {
        RepairSystem.animateNumber(readyElement, stats.ready_for_delivery.count);
    }
    
    if (urgentElement && priorities) {
        RepairSystem.animateNumber(urgentElement, priorities.urgent);
    }
};

/**
 * 11. Animar números en contadores
 */
RepairSystem.animateNumber = function(element, targetValue) {
    const startValue = parseInt(element.textContent) || 0;
    const duration = 1000; // 1 segundo
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = Math.round(startValue + (targetValue - startValue) * easeOutQuart);
        
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
};

/**
 * 12. Configurar event listeners globales
 */
RepairSystem.setupGlobalEventListeners = function() {
    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target) && !dropdown.previousElementSibling.contains(e.target)) {
                const bsDropdown = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
                if (bsDropdown) {
                    bsDropdown.hide();
                }
            }
        });
    });
    
    // Atajos de teclado
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / para enfocar búsqueda
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[placeholder*="Buscar"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape para cerrar modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
    
    // Prevenir doble envío de formularios
    document.addEventListener('submit', function(e) {
        if (RepairSystem.state.formSubmitting) {
            e.preventDefault();
            RepairSystem.showToast('Procesando... Por favor espera', 'warning');
            return false;
        }
    });
    
    console.log('🎯 Event listeners globales configurados');
};

/**
 * 13. Utilidades de formateo
 */
RepairSystem.formatCurrency = function(amount) {
    return new Intl.NumberFormat('es-AR', {
        style: 'currency',
        currency: 'ARS'
    }).format(amount);
};

RepairSystem.formatDate = function(dateString, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('es-AR', { ...defaultOptions, ...options })
        .format(new Date(dateString));
};

RepairSystem.formatRelativeTime = function(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'hace 1 día';
    } else if (diffDays < 7) {
        return `hace ${diffDays} días`;
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return `hace ${weeks} semana${weeks > 1 ? 's' : ''}`;
    } else {
        const months = Math.floor(diffDays / 30);
        return `hace ${months} mes${months > 1 ? 'es' : ''}`;
    }
};

/**
 * 14. Manejo de errores globales
 */
RepairSystem.setupErrorHandling = function() {
    // Errores JavaScript no capturados
    window.addEventListener('error', function(e) {
        console.error('Error JavaScript:', e.error);
        if (window.location.hostname !== 'localhost') {
            RepairSystem.showToast('Se ha producido un error inesperado. Por favor, recarga la página.', 'error');
        }
    });
    
    // Promesas rechazadas no manejadas
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promesa rechazada no manejada:', e.reason);
        if (window.location.hostname !== 'localhost') {
            RepairSystem.showToast('Error de conexión. Verifica tu conexión a internet.', 'warning');
        }
    });
};

/**
 * 15. Utilidades de UI
 */
RepairSystem.showLoading = function() {
    if (RepairSystem.state.isLoading) return;
    
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'globalLoadingOverlay';
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="text-center text-white">
            <div class="loading-spinner mb-3"></div>
            <p>Cargando...</p>
        </div>
    `;
    
    document.body.appendChild(loadingOverlay);
    RepairSystem.state.isLoading = true;
    
    // Auto-hide después de 30 segundos
    setTimeout(() => {
        RepairSystem.hideLoading();
    }, RepairSystem.config.loadingTimeout);
};

RepairSystem.hideLoading = function() {
    const overlay = document.getElementById('globalLoadingOverlay');
    if (overlay) {
        overlay.remove();
    }
    RepairSystem.state.isLoading = false;
};

/**
 * 16. Confirmaciones personalizadas
 */
RepairSystem.confirm = function(message, title = 'Confirmar acción') {
    return new Promise((resolve) => {
        // Crear modal de confirmación
        const modalId = 'confirmModal-' + Date.now();
        const modalHtml = `
            <div class="modal fade" id="${modalId}" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-question-circle text-warning me-2"></i>
                                ${title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Cancelar
                            </button>
                            <button type="button" class="btn btn-primary confirm-btn">
                                Confirmar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        const modal = document.getElementById(modalId);
        const bsModal = new bootstrap.Modal(modal);
        
        // Event listeners
        modal.querySelector('.confirm-btn').addEventListener('click', () => {
            bsModal.hide();
            resolve(true);
        });
        
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
            resolve(false);
        });
        
        bsModal.show();
    });
};

/**
 * 17. Debounce utility
 */
RepairSystem.debounce = function(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
};

/**
 * 18. API helper
 */
RepairSystem.api = {
    get: function(url) {
        return fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(response => response.json());
    },
    
    post: function(url, data = {}) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        }).then(response => response.json());
    },
    
    put: function(url, data = {}) {
        return fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        }).then(response => response.json());
    },
    
    delete: function(url) {
        return fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(response => response.json());
    }
};

// Configurar manejo de errores
RepairSystem.setupErrorHandling();

// Exponer globalmente para uso en otros scripts
window.RepairSystem = RepairSystem;

// Log de carga exitosa
console.log('🚀 main.js cargado exitosamente');