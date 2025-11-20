// ===== FUNCIONALIDADES JAVASCRIPT =====

document.addEventListener('DOMContentLoaded', function() {
    // Auto-ocultar mensajes flash después de 5 segundos
    autoHideFlashMessages();
    
    // Confirmación para acciones destructivas
    setupConfirmations();
    
    // Mejoras en formularios
    enhanceForms();
});

// Auto-ocultar mensajes flash
function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => {
                if (message.parentElement) {
                    message.parentElement.removeChild(message);
                }
            }, 500);
        }, 5000); // 5 segundos
    });
}

// Configurar confirmaciones
function setupConfirmations() {
    const deleteButtons = document.querySelectorAll('.btn-delete');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('¿Estás seguro de que quieres eliminar este elemento? Esta acción no se puede deshacer.')) {
                e.preventDefault();
            }
        });
    });
}

// Mejorar formularios
function enhanceForms() {
    // Validación de precios
    const precioCompraInputs = document.querySelectorAll('input[name="precio_compra"]');
    const precioVentaInputs = document.querySelectorAll('input[name="precio_venta"]');
    
    precioCompraInputs.forEach(input => {
        input.addEventListener('blur', validatePrecios);
    });
    
    precioVentaInputs.forEach(input => {
        input.addEventListener('blur', validatePrecios);
    });
    
    // Validación de stock
    const stockInputs = document.querySelectorAll('input[name="stock_actual"], input[name="stock_minimo"]');
    stockInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value < 0) {
                this.value = 0;
                showFieldError(this, 'El stock no puede ser negativo');
            }
        });
    });
}

// Validar que precio de venta sea mayor que precio de compra
function validatePrecios() {
    const form = this.closest('form');
    if (!form) return;
    
    const precioCompra = form.querySelector('input[name="precio_compra"]');
    const precioVenta = form.querySelector('input[name="precio_venta"]');
    
    if (precioCompra && precioVenta && precioCompra.value && precioVenta.value) {
        if (parseFloat(precioVenta.value) <= parseFloat(precioCompra.value)) {
            showFieldError(precioVenta, 'El precio de venta debe ser mayor al precio de compra');
        } else {
            clearFieldError(precioVenta);
        }
    }
}

// Mostrar error en campo
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.style.borderColor = '#dc3545';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#dc3545';
    errorDiv.style.fontSize = '0.875rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
}

// Limpiar error de campo
function clearFieldError(field) {
    field.style.borderColor = '';
    
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Función para búsqueda en tiempo real (si se implementa)
function setupRealTimeSearch() {
    const searchInput = document.getElementById('q');
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.closest('form').submit();
            }, 500);
        });
    }
}

// Exportar funciones globalmente (para uso en consola si es necesario)
window.SistemaInventario = {
    autoHideFlashMessages,
    validatePrecios,
    showFieldError,
    clearFieldError
};