from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa


def render_to_pdf(template_src, context_dict=None):
    """Renderiza una plantilla Django a PDF y devuelve los bytes del PDF.

    Retorna: bytes del PDF si se genera correctamente, o None si hubo un error.
    """
    context_dict = context_dict or {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.CreatePDF(src=html, dest=result)
    if pdf.err:
        return None
    return result.getvalue()
