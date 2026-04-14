"""
Certificate PDF Generation Service
Generates professional PDF certificates for course completions.
"""
import io

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from django.core.files.base import ContentFile


class CertificatePDFGenerator:
    """Generate professional PDF certificates."""

    # Certificate template configurations
    TEMPLATES = {
        'technical': {
            'primary_color': colors.HexColor('#1e40af'),  # Blue
            'accent_color': colors.HexColor('#3b82f6'),
            'bg_color': colors.HexColor('#f8fafc'),
        },
        'leadership': {
            'primary_color': colors.HexColor('#7c3aed'),  # Purple
            'accent_color': colors.HexColor('#a78bfa'),
            'bg_color': colors.HexColor('#faf5ff'),
        },
        'mentorship': {
            'primary_color': colors.HexColor('#059669'),  # Green
            'accent_color': colors.HexColor('#34d399'),
            'bg_color': colors.HexColor('#f0fdf4'),
        },
        'custom': {
            'primary_color': colors.HexColor('#dc2626'),  # Red
            'accent_color': colors.HexColor('#f87171'),
            'bg_color': colors.HexColor('#fef2f2'),
        },
    }

    @classmethod
    def generate_certificate_pdf(cls, certificate, template_name='technical'):
        """
        Generate a professional PDF certificate.

        Args:
            certificate: Certificate model instance
            template_name: One of 'technical', 'leadership', 'mentorship', 'custom'

        Returns:
            BytesIO containing the PDF data
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")

        template = cls.TEMPLATES.get(template_name, cls.TEMPLATES['technical'])

        # Create PDF buffer
        buffer = io.BytesIO()

        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Build certificate content
        story = cls._build_certificate_content(certificate, template)

        # Build PDF
        doc.build(story)

        # Get PDF value and close buffer
        pdf_value = buffer.getvalue()
        buffer.close()

        return pdf_value

    @classmethod
    def _build_certificate_content(cls, certificate, template):
        """Build the certificate content elements."""
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CertificateTitle',
            parent=styles['Heading1'],
            fontSize=36,
            textColor=template['primary_color'],
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CertificateSubtitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=20,
            alignment=TA_CENTER
        )

        recipient_style = ParagraphStyle(
            'RecipientName',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'CertificateBody',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15,
            alignment=TA_CENTER,
            leading=20
        )

        # Logo/Header
        story.append(Spacer(1, 0.5*inch))

        # Certificate Title
        story.append(Paragraph("CERTIFICATE", title_style))
        story.append(Paragraph("OF COMPLETION", subtitle_style))
        story.append(Spacer(1, 0.3*inch))

        # Decorative line
        line_data = [['']]
        line_table = Table(line_data, colWidths=[6*inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, template['accent_color']),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.3*inch))

        # This certifies that
        story.append(Paragraph("This certifies that", body_style))
        story.append(Spacer(1, 0.2*inch))

        # Recipient Name
        recipient_name = f"{certificate.enrollment.user.first_name} {certificate.enrollment.user.last_name}"
        story.append(Paragraph(recipient_name, recipient_style))
        story.append(Spacer(1, 0.2*inch))

        # Has completed
        story.append(Paragraph("has successfully completed the", body_style))
        story.append(Spacer(1, 0.1*inch))

        # Program/Course Name
        program_name = certificate.enrollment.cohort.track.program.name
        course_style = ParagraphStyle(
            'CourseName',
            parent=styles['Heading2'],
            fontSize=20,
            textColor=template['primary_color'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(program_name, course_style))
        story.append(Spacer(1, 0.2*inch))

        # Track info
        track_name = certificate.enrollment.cohort.track.name
        story.append(Paragraph(f"Track: {track_name}", body_style))
        story.append(Spacer(1, 0.1*inch))

        # Cohort info
        cohort_name = certificate.enrollment.cohort.name
        story.append(Paragraph(f"Cohort: {cohort_name}", body_style))
        story.append(Spacer(1, 0.3*inch))

        # Date
        date_str = certificate.issued_at.strftime('%B %d, %Y')
        story.append(Paragraph(f"Completed on {date_str}", body_style))
        story.append(Spacer(1, 0.4*inch))

        # Certificate ID
        cert_id_style = ParagraphStyle(
            'CertID',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER
        )
        story.append(Paragraph(f"Certificate ID: {certificate.id}", cert_id_style))
        story.append(Spacer(1, 0.3*inch))

        # Signature line (if available)
        signature_data = [
            ['_________________', '_________________'],
            ['Director', 'Date']
        ]
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#64748b')),
            ('TOPPADDING', (0, 0), (-1, 0), 20),
        ]))
        story.append(signature_table)

        return story

    @classmethod
    def save_certificate_pdf(cls, certificate, template_name='technical'):
        """
        Generate and save PDF certificate to the certificate model.

        Args:
            certificate: Certificate model instance
            template_name: Certificate template name

        Returns:
            Path to saved certificate file
        """
        pdf_content = cls.generate_certificate_pdf(certificate, template_name)

        # Generate filename
        filename = f"certificate_{certificate.id}.pdf"

        # Save to model
        certificate.certificate_file.save(
            filename,
            ContentFile(pdf_content),
            save=True
        )

        return certificate.certificate_file.path


# Convenience function for certificate generation
def generate_certificate_pdf(certificate, template_name='technical'):
    """Generate a PDF certificate for the given certificate instance."""
    return CertificatePDFGenerator.generate_certificate_pdf(certificate, template_name)
