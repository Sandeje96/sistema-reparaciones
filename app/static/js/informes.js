// app/static/js/informes.js
// JavaScript específico para el módulo de informes técnicos

/**
 * Inicialización específica para informes
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 Módulo de informes cargado');
    
    InformesModule.init();
});

/**
 * Módulo principal de informes técnicos
 */
const InformesModule = {
    init: function() {
        this.setupDeleteButtons();
        this.setupSearchFilters();
        this.loadInitialStats();
        this.setupKeyboardShortcuts();
        this.setupAutoRefresh();
        this.setupFormValidation();
        this.setupImageHandling();
        console.log('✅ Módulo de informes inicializado');
    },

    /**
     * Configurar botones de eliminación
     */
    setupDeleteButtons: function() {
        const deleteButtons = document.querySelectorAll('.delete-btn');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const reportId = this.dataset.reportId;
                const claimNumber = this.dataset.claim;
                const deviceType = this.dataset.device;
                
                InformesModule.showDeleteModal(reportId, claimNumber, deviceType);
            });
        });
        
        console.log(`🗑️ ${deleteButtons.length} botones de eliminación configurados`);
    },

    /**
     * Mostrar modal de confirmación de eliminación
     */
    showDeleteModal: function(reportId, claimNumber, deviceType) {
        const modal = document.getElementById('deleteModal');
        if (!modal) {
            console.error('Modal de eliminación no encontrado');
            return;
        }
        
        // Actualizar contenido del modal
        const claimElement = document.getElementById('delete-claim');
        const deviceElement = document.getElementById('delete-device');
        
        if (claimElement) claimElement.textContent = claimNumber;
        if (deviceElement) deviceElement.textContent = deviceType;
        
        // Configurar formulario
        const form = document.getElementById('delete-form');
        if (form) {
            form.action = `/informes/delete/${reportId}`;
        }
        
        // Mostrar modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    },

    /**
     * Configurar filtros de búsqueda
     */
    setupSearchFilters: function() {
        const searchForm = document.querySelector('form[method="GET"]');
        if (!searchForm) return;
        
        const searchInput = searchForm.querySelector('input[name="search"]');
        
        // Búsqueda con debounce
        if (searchInput) {
            const debouncedSearch = RepairSystem.debounce(() => {
                // No hacer búsqueda automática, solo cuando se presione el botón
            }, 500);
            
            // Buscar al presionar Enter
            searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    InformesModule.performSearch();
                }
            });
        }
        
        console.log('🔍 Filtros de búsqueda configurados');
    },

    /**
     * Realizar búsqueda/filtrado
     */
    performSearch: function() {
        const form = document.querySelector('form[method="GET"]');
        if (!form) return;
        
        // Enviar formulario
        form.submit();
    },

    /**
     * Cargar estadísticas actualizadas
     */
    loadStats: function() {
        fetch('/informes/stats')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    InformesModule.updateStatsCounters(data);
                }
            })
            .catch(error => {
                console.error('Error cargando estadísticas:', error);
            });
    },

    /**
     * Cargar estadísticas iniciales
     */
    loadInitialStats: function() {
        // Pequeño delay para permitir que la página se cargue completamente
        setTimeout(() => {
            this.loadStats();
        }, 500);
    },

    /**
     * Actualizar contadores de estadísticas
     */
    updateStatsCounters: function(data) {
        // Actualizar total de informes
        const totalElement = document.getElementById('total-reports-count');
        if (totalElement && data.total_reports !== undefined) {
            RepairSystem.animateNumber(totalElement, data.total_reports);
        }
        
        // Actualizar informes del mes actual
        const monthlyElement = document.getElementById('monthly-reports-count');
        if (monthlyElement && data.monthly_stats) {
            const currentMonth = new Date().getMonth() + 1;
            const currentYear = new Date().getFullYear();
            const currentMonthData = data.monthly_stats.find(s => 
                s.month === currentMonth && s.year === currentYear
            );
            const monthlyCount = currentMonthData ? currentMonthData.count : 0;
            RepairSystem.animateNumber(monthlyElement, monthlyCount);
        }
        
        // Actualizar marca más frecuente
        const topBrandElement = document.getElementById('top-brand');
        if (topBrandElement && data.top_brands && data.top_brands.length > 0) {
            topBrandElement.textContent = data.top_brands[0].brand;
        }
    },

    /**
     * Configurar atajos de teclado específicos
     */
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', function(e) {
            // Ctrl + I para nuevo informe
            if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
                e.preventDefault();
                const createButton = document.querySelector('a[href*="/informes/create"]');
                if (createButton) {
                    window.location.href = createButton.href;
                }
            }
            
            // R para refrescar estadísticas
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                const activeElement = document.activeElement;
                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                    return; // No interferir si el usuario está escribiendo
                }
                e.preventDefault();
                InformesModule.loadStats();
                RepairSystem.showToast('Estadísticas actualizadas', 'info', 2000);
            }
        });
    },

    /**
     * Auto-refresh de estadísticas
     */
    setupAutoRefresh: function() {
        // Refresh cada 5 minutos
        setInterval(() => {
            InformesModule.loadStats();
        }, 300000);
        
        // Refresh cuando la ventana recupera el foco
        window.addEventListener('focus', () => {
            InformesModule.loadStats();
        });
    },

    /**
     * Configurar validación de formularios
     */
    setupFormValidation: function() {
        // Validación para precios
        const priceInputs = document.querySelectorAll('input[name*="price"]');
        priceInputs.forEach(input => {
            input.addEventListener('input', function() {
                let value = this.value;
                // Permitir solo números y punto decimal
                value = value.replace(/[^0-9.]/g, '');
                // Solo un punto decimal
                const parts = value.split('.');
                if (parts.length > 2) {
                    value = parts[0] + '.' + parts.slice(1).join('');
                }
                this.value = value;
                
                // Validar rango
                const numValue = parseFloat(value);
                if (numValue < 0) {
                    this.setCustomValidity('El precio debe ser positivo');
                } else {
                    this.setCustomValidity('');
                }
            });
        });
        
        // Validación para fechas
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.addEventListener('change', function() {
                const selectedDate = new Date(this.value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                if (selectedDate > today) {
                    this.setCustomValidity('La fecha no puede ser futura');
                } else {
                    this.setCustomValidity('');
                }
            });
        });
        
        // Contador de caracteres para diagnóstico técnico
        const diagnosisTextarea = document.querySelector('textarea[name="technical_diagnosis"]');
        if (diagnosisTextarea) {
            this.setupCharacterCounter(diagnosisTextarea, 50, 2000);
        }
        
        console.log('✅ Validación de formularios configurada');
    },

    /**
     * Configurar contador de caracteres
     */
    setupCharacterCounter: function(textarea, minLength, maxLength) {
        const helpText = textarea.parentNode.querySelector('.form-text');
        if (!helpText) return;
        
        const originalText = helpText.textContent;
        
        function updateCounter() {
            const length = textarea.value.length;
            
            let status = '';
            let className = 'form-text';
            
            if (length < minLength) {
                status = `(${length}/${minLength} mínimo)`;
                className += ' text-warning';
            } else if (length > maxLength) {
                status = `(${length}/${maxLength} máximo excedido)`;
                className += ' text-danger';
            } else {
                status = `(${length} caracteres)`;
                className += ' text-success';
            }
            
            helpText.textContent = `${originalText} ${status}`;
            helpText.className = className;
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Inicial
    },

    /**
     * Configurar manejo de imágenes
     */
    setupImageHandling: function() {
        // Preview de imágenes seleccionadas
        const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
        imageInputs.forEach((input, index) => {
            input.addEventListener('change', function() {
                InformesModule.handleImagePreview(this);
            });
        });
        
        // Eliminar imágenes existentes
        const deleteImageBtns = document.querySelectorAll('.delete-image-btn');
        deleteImageBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                InformesModule.handleImageDeletion(this);
            });
        });
        
        console.log('📷 Manejo de imágenes configurado');
    },

    /**
     * Manejar preview de imágenes
     */
    handleImagePreview: function(input) {
        const file = input.files[0];
        if (!file) return;
        
        const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB
        const helpText = input.parentNode.querySelector('.form-text');
        
        // Validar tamaño
        if (file.size > 10 * 1024 * 1024) { // 10MB
            helpText.textContent = `Archivo muy grande (${fileSize}MB). Máximo: 10MB`;
            helpText.className = 'form-text text-danger';
            input.value = ''; // Limpiar selección
            return;
        }
        
        // Validar tipo
        if (!file.type.startsWith('image/')) {
            helpText.textContent = 'Solo se permiten archivos de imagen';
            helpText.className = 'form-text text-danger';
            input.value = ''; // Limpiar selección
            return;
        }
        
        // Mostrar información del archivo
        helpText.textContent = `Seleccionado: ${file.name} (${fileSize}MB)`;
        helpText.className = 'form-text text-success';
        
        // Crear preview si es posible
        const previewContainer = input.parentNode.querySelector('.image-preview');
        if (previewContainer) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewContainer.innerHTML = `
                    <img src="${e.target.result}" 
                         class="img-thumbnail mt-2" 
                         style="max-width: 150px; max-height: 150px;"
                         alt="Preview">
                `;
            };
            reader.readAsDataURL(file);
        }
    },

    /**
     * Manejar eliminación de imágenes
     */
    handleImageDeletion: function(button) {
        const imageNum = button.dataset.imageNum;
        const reportId = button.dataset.reportId;
        
        if (!confirm(`¿Estás seguro de que deseas eliminar la imagen ${imageNum}?`)) {
            return;
        }
        
        // Mostrar loading
        button.classList.add('loading');
        button.disabled = true;
        
        fetch(`/informes/delete-image/${reportId}/${imageNum}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                RepairSystem.showToast(data.message, 'success');
                // Recargar página para mostrar cambios
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                RepairSystem.showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            RepairSystem.showToast('Error de conexión. Inténtalo de nuevo.', 'error');
        })
        .finally(() => {
            button.classList.remove('loading');
            button.disabled = false;
        });
    },

    /**
     * Generar PDF con indicador de progreso
     */
    generatePDF: function(reportId, preview = false) {
        const button = event.target;
        const originalText = button.innerHTML;
        
        // Mostrar loading
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generando...';
        button.disabled = true;
        
        const url = preview ? 
            `/informes/preview-pdf/${reportId}` : 
            `/informes/generate-pdf/${reportId}`;
        
        if (preview) {
            // Abrir en nueva ventana para preview
            window.open(url, '_blank');
            // Restaurar botón inmediatamente
            button.innerHTML = originalText;
            button.disabled = false;
        } else {
            // Descargar archivo
            window.location.href = url;
            // Restaurar botón después de un delay
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
            }, 2000);
        }
    },

    /**
     * Utilidades de formateo específicas
     */
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-AR', {
            style: 'currency',
            currency: 'ARS',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    },

    formatDate: function(dateString) {
        return new Intl.DateTimeFormat('es-AR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }).format(new Date(dateString));
    },

    /**
     * Validar formulario antes de envío
     */
    validateForm: function(form) {
        let isValid = true;
        const errors = [];
        
        // Validar campos requeridos
        const requiredFields = form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                errors.push(`${field.labels[0]?.textContent || field.name} es obligatorio`);
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Validar precios
        const priceFields = form.querySelectorAll('input[name*="price"]');
        priceFields.forEach(field => {
            const value = parseFloat(field.value);
            if (field.value && (isNaN(value) || value < 0)) {
                errors.push(`${field.labels[0]?.textContent || field.name} debe ser un número positivo`);
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        // Mostrar errores si los hay
        if (!isValid) {
            RepairSystem.showToast(
                `Por favor corrige los siguientes errores: ${errors.join(', ')}`, 
                'error', 
                5000
            );
        }
        
        return isValid;
    }
};

// Exponer módulo globalmente
window.InformesModule = InformesModule;

// Funciones globales para llamar desde templates
window.generatePDF = function(reportId, preview = false) {
    InformesModule.generatePDF(reportId, preview);
};

window.deleteReport = function(reportId, claimNumber, deviceType) {
    InformesModule.showDeleteModal(reportId, claimNumber, deviceType);
};

console.log('📋 informes.js cargado exitosamente');