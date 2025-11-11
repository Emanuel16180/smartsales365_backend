# apps/reports/urls.py
from django.urls import path
from .views import AdminReportView, SaleReportPDFView # Importa las vistas

urlpatterns = [
    # Endpoint principal para generar el reporte (CSV / PDF via ReportLab)
    path('admin/report/', AdminReportView.as_view(), name='admin-report'),
    # Endpoint ejemplo que genera un PDF a partir de la plantilla HTML
    path('export/pdf/', SaleReportPDFView.as_view(), name='reports-export-pdf'),
]