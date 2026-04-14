import io

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class InvoicePDFGenerator:
    @staticmethod
    def generate_invoice_pdf(invoice):
        """Generate PDF invoice"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

        # Container for the 'Flowable' objects
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2563eb')
        )

        # Company header
        elements.append(Paragraph("OCH - Online Coding Hub", title_style))
        elements.append(Spacer(1, 12))

        # Invoice details
        invoice_data = [
            ['Invoice Number:', invoice.invoice_number],
            ['Date:', invoice.created_at.strftime('%B %d, %Y')],
            ['Customer:', invoice.subscription.user.get_full_name() or invoice.subscription.user.email],
            ['Email:', invoice.subscription.user.email],
            ['Billing Period:', f"{invoice.subscription.current_period_start.strftime('%b %d, %Y')} - {invoice.subscription.current_period_end.strftime('%b %d, %Y')}"]
        ]

        invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
        invoice_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(invoice_table)
        elements.append(Spacer(1, 30))

        # Line items
        line_items = [['Description', 'Amount']]
        line_items.append([f"{invoice.subscription.plan_type.title()} Subscription", f"${invoice.subtotal:.2f}"])

        if invoice.discount_amount > 0:
            line_items.append([f"Discount ({invoice.promo_code})", f"-${invoice.discount_amount:.2f}"])

        line_items.append(['Tax', f"${invoice.tax_amount:.2f}"])
        line_items.append(['Total', f"${invoice.total_amount:.2f}"])

        items_table = Table(line_items, colWidths=[4*inch, 2*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))

        elements.append(items_table)
        elements.append(Spacer(1, 30))

        # Footer
        footer_text = "Thank you for your business! If you have any questions about this invoice, please contact support@och.com"
        elements.append(Paragraph(footer_text, styles['Normal']))

        # Build PDF
        doc.build(elements)

        # Get the value of the BytesIO buffer and return it
        pdf = buffer.getvalue()
        buffer.close()

        return pdf

    @staticmethod
    def serve_invoice_pdf(invoice):
        """Serve PDF as HTTP response"""
        pdf_content = InvoicePDFGenerator.generate_invoice_pdf(invoice)

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

        return response
