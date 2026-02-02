from datetime import datetime, date
from .base import db

class Invoice(db.Model):
    """
    Billing invoices for overflights and landings
    Supports multiple line items and PDF generation
    """
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    reference_number = db.Column(db.String(50))
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), index=True)
    invoice_type = db.Column(db.String(50), index=True)
    period_start = db.Column(db.Date)
    period_end = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    discount_reason = db.Column(db.String(200))
    tax_rate = db.Column(db.Float, default=0.16)
    tax_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='USD')
    exchange_rate = db.Column(db.Float, default=1.0)
    status = db.Column(db.String(50), default='draft', index=True)
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    paid_date = db.Column(db.Date)
    paid_amount = db.Column(db.Float)
    payment_reference = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    pdf_path = db.Column(db.String(255))
    pdf_generated_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    sent_to = db.Column(db.String(200))
    reminder_count = db.Column(db.Integer, default=0)
    last_reminder_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancelled_at = db.Column(db.DateTime)
    cancelled_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    airline = db.relationship('Airline', backref=db.backref('invoices', lazy='dynamic'))
    overflights = db.relationship('Overflight', backref='invoice', lazy='dynamic')
    landings = db.relationship('Landing', backref='invoice', lazy='dynamic')
    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'reference_number': self.reference_number,
            'airline_id': self.airline_id,
            'airline_name': self.airline.name if self.airline else None,
            'invoice_type': self.invoice_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'currency': self.currency,
            'status': self.status,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def calculate_totals(self):
        """Recalculate invoice totals from line items"""
        self.subtotal = sum(item.total for item in self.line_items)
        taxable = self.subtotal - self.discount_amount
        self.tax_amount = taxable * self.tax_rate
        self.total_amount = taxable + self.tax_amount


class InvoiceLineItem(db.Model):
    """
    Individual line items on an invoice
    Supports overflights, landings, parking, and other charges
    """
    __tablename__ = 'invoice_line_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    line_number = db.Column(db.Integer, default=1)
    item_type = db.Column(db.String(50))
    description = db.Column(db.String(500), nullable=False)
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(50))
    flight_date = db.Column(db.Date)
    callsign = db.Column(db.String(20))
    registration = db.Column(db.String(20))
    route = db.Column(db.String(100))
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(50))
    unit_price = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'line_number': self.line_number,
            'item_type': self.item_type,
            'description': self.description,
            'flight_date': self.flight_date.isoformat() if self.flight_date else None,
            'callsign': self.callsign,
            'registration': self.registration,
            'route': self.route,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'discount': self.discount,
            'total': self.total
        }

    def calculate_total(self):
        """Calculate line item total"""
        self.total = (self.quantity * self.unit_price) - self.discount


class TariffConfig(db.Model):
    """
    Configurable tariff rates for billing
    Supports effective dates for rate changes
    """
    __tablename__ = 'tariff_configs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))
    value = db.Column(db.Float, nullable=False)
    min_value = db.Column(db.Float)
    max_value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    currency = db.Column(db.String(3), default='USD')
    description = db.Column(db.Text)
    description_fr = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_percentage = db.Column(db.Boolean, default=False)
    effective_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'category': self.category,
            'value': self.value,
            'unit': self.unit,
            'currency': self.currency,
            'description': self.description,
            'is_active': self.is_active,
            'is_percentage': self.is_percentage,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None
        }
