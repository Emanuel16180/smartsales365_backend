import csv 
import io
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone 
from .services import render_to_pdf


# --- LIBRERÍA DE PDF (ReportLab - Python Puro) ---
from reportlab.pdfgen import canvas         
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Importaciones de otras apps
from apps.sales.models import Sale
from apps.sales.filters import SaleFilter
from .utils import format_sale_details_for_csv 


class AdminReportView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        report_format = request.query_params.get('format', 'csv').lower()
        
        # 1. Obtener y Filtrar el Queryset
        queryset = Sale.objects.all().order_by('-created_at').prefetch_related(
            'user', 'details__product'
        )
        filterset = SaleFilter(request.query_params, queryset=queryset)
        
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        filtered_queryset = filterset.qs
        
        
        if report_format == 'csv':
            # --- Lógica de CSV (OK) ---
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="reporte_ventas_filtrado.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID_Venta', 'Fecha', 'Cliente', 'Email', 'Monto_Total', 'Estado', 'Detalle_Productos'])

            for sale in filtered_queryset:
                # Detalles de productos: soportar ambos esquemas (detalle separado o FK directo)
                if hasattr(sale, 'details'):
                    try:
                        product_details = format_sale_details_for_csv(sale.details.all())
                    except Exception:
                        product_details = "N/A"
                elif hasattr(sale, 'product') and hasattr(sale, 'quantity'):
                    try:
                        product_details = f"{sale.product.name} ({sale.quantity}x)"
                    except Exception:
                        product_details = "N/A"
                else:
                    product_details = "N/A"

                # Usuario (si existe)
                if hasattr(sale, 'user') and sale.user:
                    user_name = f"{sale.user.first_name} {sale.user.last_name}"
                    user_email = sale.user.email
                else:
                    user_name = "N/A"
                    user_email = "N/A"

                # Monto y estado con fallback
                total_amount = getattr(sale, 'total_amount', None)
                if total_amount is None:
                    total_amount = getattr(sale, 'total', 'N/A')
                status = getattr(sale, 'status', 'N/A')

                writer.writerow([sale.id, sale.created_at.strftime('%Y-%m-%d %H:%M:%S'), user_name, user_email, total_amount, status, product_details])
            
            return response
            
        elif report_format == 'pdf':
            # --- Lógica de PDF con ReportLab (CORREGIDA) ---
            
            # Crear un buffer en memoria para el PDF
            buffer = io.BytesIO()
            
            # Crear el canvas con el buffer
            p = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Título
            p.setFont("Helvetica-Bold", 16)
            p.drawString(1 * inch, height - 1 * inch, "REPORTE DE VENTAS")
            
            # Fecha de generación
            p.setFont("Helvetica", 10)
            fecha_actual = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            p.drawString(1 * inch, height - 1.3 * inch, f"Generado: {fecha_actual}")
            
            # Encabezados de columna
            p.setFont("Helvetica-Bold", 9)
            y_position = height - 1.8 * inch
            p.drawString(0.5 * inch, y_position, "ID")
            p.drawString(1 * inch, y_position, "Fecha")
            p.drawString(2.5 * inch, y_position, "Cliente")
            p.drawString(4.5 * inch, y_position, "Monto")
            p.drawString(5.8 * inch, y_position, "Estado")
            
            # Línea separadora
            p.line(0.5 * inch, y_position - 0.1 * inch, 7.5 * inch, y_position - 0.1 * inch)
            
            # Datos
            p.setFont("Helvetica", 8)
            y_position -= 0.3 * inch
            
            count = 0
            for sale in filtered_queryset:
                # Control de página: si llegamos al final, crear nueva página
                if y_position < 1 * inch:
                    p.showPage()
                    p.setFont("Helvetica", 8)
                    y_position = height - 1 * inch
                
                 # Formatear datos con fallback a distintos esquemas de modelo
                 if hasattr(sale, 'user') and sale.user:
                     user_name = f"{sale.user.first_name} {sale.user.last_name}"
                 else:
                     user_name = "N/A"
                 fecha = sale.created_at.strftime('%Y-%m-%d')

                 total_amount_val = getattr(sale, 'total_amount', None)
                 if total_amount_val is None:
                     total_amount_val = getattr(sale, 'total', 0)
                 try:
                     total_text = f"${float(total_amount_val):.2f}"
                 except Exception:
                     total_text = str(total_amount_val)

                 status_text = getattr(sale, 'status', 'N/A')

                 # Dibujar fila
                 p.drawString(0.5 * inch, y_position, str(sale.id))
                 p.drawString(1 * inch, y_position, fecha)
                 p.drawString(2.5 * inch, y_position, user_name[:20])
                 p.drawString(4.5 * inch, y_position, total_text)
                 p.drawString(5.8 * inch, y_position, status_text[:15])
                
                y_position -= 0.25 * inch
                count += 1
            
            # Total de registros
            p.setFont("Helvetica-Bold", 10)
            if y_position < 1.5 * inch:
                p.showPage()
                y_position = height - 1 * inch
            y_position -= 0.3 * inch
            p.drawString(0.5 * inch, y_position, f"Total de ventas: {count}")
            
            # Finalizar el PDF
            p.showPage()
            p.save()
            
            # Obtener el contenido del buffer
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Crear la respuesta HTTP
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="reporte_ventas.pdf"'
            
            return response
            
        else:
            return Response({"error": "Formato no soportado. Usa format=csv o format=pdf."}, status=400)

class SaleReportPDFView(APIView):
    """Endpoint de ejemplo que genera un PDF desde la plantilla `sale_report.html`.

    Nota: Esta vista usa un contexto mínimo (lista vacía) porque los modelos
    de `sales` en este scaffold pueden no coincidir con los campos usados en
    la plantilla. Integra aquí la consulta real a tus ventas y detalles.
    """
    def get(self, request):
        context = {
            'filters': request.GET.dict(),
            'current_date': timezone.now(),
            'sales_data': [],  # reemplazar por queryset/serializers reales
        }
        pdf_bytes = render_to_pdf('reports/sale_report.html', context)
        if not pdf_bytes:
            return Response({'detail': 'Error generando PDF'}, status=500)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
        return response