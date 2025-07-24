// app/static/js/repairs.js
// JavaScript específico para el módulo de reparaciones

/**
 * Inicialización específica para reparaciones
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Módulo de reparaciones cargado');
    
    RepairsModule.init();
});

/**
 * Módulo principal de reparaciones
 */
const RepairsModule = {
    init: function() {
        this.setupStatusSelectors();
        this.setupDeleteButtons();
        this.setupSearchFilters();
        this.loadInitialStats();
        this.setupKeyboardShortcuts();
        this.setupAutoRefresh();
        console.log('✅ Módulo de reparaciones inicializado');
    },

    /**
     * Configurar selectores de estado con cambio automático
     */
    setupStatusSelectors: function() {
        const statusSelects = document.querySelectorAll('.status-select');
        
        statusSelects.forEach(select => {
            select.addEventListener('change', function() {
                const repairId = this.dataset.repairId;
                const newStatus = this.value;
                const originalStatus = this.dataset.originalStatus || this.querySelector('option[selected]')?.value;
                
                // Guardar estado original si no existe
                if (!this.dataset.originalStatus) {
                    this.dataset.originalStatus = originalStatus;
                }
                
                RepairsModule.updateRepairStatus(repairId, newStatus, this, originalStatus);
            });
            
            // Aplicar color según estado actual
            RepairsModule.updateSelectColor(select, select.value);
        });
        
        console.log(`📝 ${statusSelects.length} selectores de estado configurados`);
    },

    /**
     * Actualizar estado de reparación via AJAX
     */
    updateRepairStatus: function(repairId, newStatus, selectElement, originalStatus) {
        // Mostrar loading
        selectElement.classList.add('status-loading');
        selectElement.disabled = true;
        
        // Preparar datos del formulario
        const formData = new FormData();
        formData.append('status', newStatus);
        
        fetch(`/repairs/quick-status/${repairId}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar UI
                RepairsModule.updateSelectColor(selectElement, newStatus);
                selectElement.dataset.originalStatus = newStatus;
                
                // Actualizar fila si existe
                const row = selectElement.closest('tr, .repair-card-mobile');
                if (row && data.priority_class) {
                    row.className = row.className.replace(/priority-\w+/g, '');
                    row.classList.add(data.priority_class);
                    
                    // Animación de éxito
                    row.classList.add('status-change-animation');
                    setTimeout(() => {
                        row.classList.remove('status-change-animation');
                    }, 500);
                }
                
                // Mostrar notificación
                RepairSystem.showToast(data.message, 'success');
                
                // Actualizar estadísticas
                RepairsModule.loadStats();
                
            } else {
                // Revertir cambio
                selectElement.value = originalStatus;
                RepairsModule.updateSelectColor(selectElement, originalStatus);
                RepairSystem.showToast(data.message || 'Error al actualizar el estado', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revertir cambio
            selectElement.value = originalStatus;
            RepairsModule.updateSelectColor(selectElement, originalStatus);
            RepairSystem.showToast('Error de conexión. Inténtalo de nuevo.', 'error');
        })
        .finally(() => {
            // Quitar loading
            selectElement.classList.remove('status-loading');
            selectElement.disabled = false;
        });
    },

    /**
     * Actualizar color del selector según estado
     */
    updateSelectColor: function(selectElement, status) {
        // Remover clases de estado previas
        selectElement.className = selectElement.className.replace(/status-\w+/g, '');
        
        // Aplicar nueva clase
        selectElement.classList.add(`status-${status.replace('_', '-')}`);
        selectElement.dataset.status = status;
    },

    /**
     * Configurar botones de eliminación
     */
    setupDeleteButtons: function() {
        const deleteButtons = document.querySelectorAll('.delete-btn');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const repairId = this.dataset.repairId;
                const clientName = this.dataset.client;
                const deviceType = this.dataset.device;
                
                RepairsModule.showDeleteModal(repairId, clientName, deviceType);
            });
        });
        
        console.log(`🗑️ ${deleteButtons.length} botones de eliminación configurados`);
    },

    /**
     * Mostrar modal de confirmación de eliminación
     */
    showDeleteModal: function(repairId, clientName, deviceType) {
        const modal = document.getElementById('deleteModal');
        if (!modal) {
            console.error('Modal de eliminación no encontrado');
            return;
        }
        
        // Actualizar contenido del modal
        document.getElementById('delete-client').textContent = clientName;
        document.getElementById('delete-device').textContent = deviceType;
        
        // Configurar formulario
        const form = document.getElementById('delete-form');
        form.action = `/repairs/delete/${repairId}`;
        
        // Mostrar modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    },

    /**
     * Configurar filtros de búsqueda
     */
    setupSearchFilters: function() {
        const searchForm = document.querySelector('.search-filters form');
        if (!searchForm) return;
        
        const searchInput = searchForm.querySelector('input[name="search"]');
        const statusFilter = searchForm.querySelector('select[name="status_filter"]');
        const priorityFilter = searchForm.querySelector('select[name="priority_filter"]');
        
        // Búsqueda con debounce
        if (searchInput) {
            const debouncedSearch = RepairSystem.debounce(() => {
                RepairsModule.performSearch();
            }, 500);
            
            searchInput.addEventListener('input', debouncedSearch);
        }
        
        // Filtros instantáneos
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                RepairsModule.performSearch();
            });
        }
        
        if (priorityFilter) {
            priorityFilter.addEventListener('change', () => {
                RepairsModule.performSearch();
            });
        }
        
        console.log('🔍 Filtros de búsqueda configurados');
    },

    /**
     * Realizar búsqueda/filtrado
     */
    performSearch: function() {
        const form = document.querySelector('.search-filters form');
        if (!form) return;
        
        // Obtener parámetros actuales
        const formData = new FormData(form);
        const params = new URLSearchParams();
        
        for (let [key, value] of formData.entries()) {
            if (value.trim() !== '') {
                params.append(key, value);
            }
        }
        
        // Mantener página actual si no hay cambios en filtros
        const currentUrl = new URL(window.location);
        const currentPage = currentUrl.searchParams.get('page');
        if (currentPage && !params.has('page')) {
            params.append('page', '1'); // Reset a primera página en nueva búsqueda
        }
        
        // Navegar con nuevos parámetros
        const newUrl = `${window.location.pathname}?${params.toString()}`;
        window.location.href = newUrl;
    },

    /**
     * Cargar estadísticas actualizadas
     */
    loadStats: function() {
        RepairSystem.api.get('/repairs/stats')
            .then(data => {
                if (data.success) {
                    RepairsModule.updateStatsCounters(data.stats, data.priorities);
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
    updateStatsCounters: function(stats, priorities) {
        const counters = {
            'pending-diagnosis-count': stats.pending_diagnosis?.count || 0,
            'waiting-parts-count': stats.waiting_parts?.count || 0,
            'ready-delivery-count': stats.ready_for_delivery?.count || 0,
            'urgent-count': priorities?.urgent || 0
        };
        
        Object.entries(counters).forEach(([elementId, value]) => {
            const element = document.getElementById(elementId);
            if (element) {
                RepairSystem.animateNumber(element, value);
            }
        });
    },

    /**
     * Configurar atajos de teclado específicos
     */
    setupKeyboardShortcuts: function() {
        document.addEventListener('keydown', function(e) {
            // Ctrl + N para nueva reparación
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const addButton = document.querySelector('a[href*="/repairs/add"]');
                if (addButton) {
                    window.location.href = addButton.href;
                }
            }
            
            // R para refrescar estadísticas
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey && !e.altKey) {
                const activeElement = document.activeElement;
                if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
                    return; // No interferir si el usuario está escribiendo
                }
                e.preventDefault();
                RepairsModule.loadStats();
                RepairSystem.showToast('Estadísticas actualizadas', 'info', 2000);
            }
        });
    },

    /**
     * Auto-refresh de estadísticas
     */
    setupAutoRefresh: function() {
        // Refresh cada 2 minutos
        setInterval(() => {
            RepairsModule.loadStats();
        }, 120000);
        
        // Refresh cuando la ventana recupera el foco
        window.addEventListener('focus', () => {
            RepairsModule.loadStats();
        });
    },

    /**
     * Utilidades de formateo específicas
     */
    formatPriority: function(days) {
        if (days >= 15) {
            return { class: 'priority-high', label: 'Urgente', color: 'danger' };
        } else if (days >= 7) {
            return { class: 'priority-medium', label: 'Media', color: 'warning' };
        } else {
            return { class: 'priority-low', label: 'Baja', color: 'success' };
        }
    },

    formatStatus: function(status) {
        const statusMap = {
            'pending_diagnosis': { label: 'Falta diagnóstico', color: 'warning', icon: 'exclamation-triangle' },
            'diagnosed': { label: 'Diagnóstico hecho', color: 'info', icon: 'check-circle' },
            'waiting_parts': { label: 'Esperando repuestos', color: 'primary', icon: 'clock-history' },
            'ready_for_delivery': { label: 'Pendiente de entrega', color: 'success', icon: 'truck' },
            'delivered': { label: 'Entregado', color: 'secondary', icon: 'check-all' },
            'no_repair': { label: 'Sin reparación', color: 'danger', icon: 'x-circle' }
        };
        
        return statusMap[status] || { label: 'Desconocido', color: 'secondary', icon: 'question' };
    }
};

// Exponer módulo globalmente
window.RepairsModule = RepairsModule;

console.log('🔧 repairs.js cargado exitosamente');