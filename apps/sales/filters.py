import django_filters
from .models import Sale
from django_filters import DateFilter
from django.db.models import Q

class SaleFilter(django_filters.FilterSet):
    """
    Filtro personalizado para el endpoint de administrador de Ventas.
    """
    
    # 1. Filtro por Cliente (user__id)
    client_search = django_filters.CharFilter(
        method='filter_by_client_name_or_email',
        label="Buscar por Cliente (Nombre, Apellido o Email)"
    )

    # 2. Filtro por Mes y Año
    month = django_filters.NumberFilter(field_name='created_at__month')
    year = django_filters.NumberFilter(field_name='created_at__year')

    # 3. Filtro por Producto (busca en los SaleDetail)
    product_name = django_filters.CharFilter(
        field_name='details__product__name',  # Busca en el nombre del producto
        lookup_expr='icontains',              # 'icontains' = no sensible a mayúsculas
        distinct=True,
        label="Buscar por Nombre de Producto"
    )
    # 4. Filtro por Monto (Rango)
    monto_min = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    monto_max = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    #5. Filtro por Fecha (Rango)
    fecha_inicio = DateFilter(field_name='created_at', lookup_expr='gte')
    fecha_fin = DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Sale
        # Define los campos que se pueden filtrar exactamente (además de los personalizados)
        fields = ['status', 'client_search', 'month', 'year', 'product_name', 'monto_min', 'monto_max', 'fecha_inicio', 'fecha_fin']


    def filter_by_client_name_or_email(self, queryset, name, value):
            """
            Filtra el queryset por nombre, apellido o email del usuario.
            """
            if not value:
                return queryset
            
            # Busca el texto 'value' en cualquiera de estos tres campos
            return queryset.filter(
                Q(user__first_name__icontains=value) |
                Q(user__last_name__icontains=value) |
                Q(user__email__icontains=value)
            ).distinct()