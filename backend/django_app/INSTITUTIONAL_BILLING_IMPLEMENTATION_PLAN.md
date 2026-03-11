# INSTITUTIONAL BILLING SYSTEM - IMPLEMENTATION PLAN

## 🚨 CURRENT STATUS: NOT IMPLEMENTED

The current system only has basic organization enrollment with simple invoicing. 
The full Stream B institutional billing requirements are MISSING.

## 📋 REQUIRED IMPLEMENTATION

### 1. INSTITUTIONAL CONTRACT SYSTEM

**New Models Needed:**
```python
class InstitutionalContract(models.Model):
    organization = models.ForeignKey(Organization)
    contract_number = models.CharField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()  # 12-month minimum
    student_seat_count = models.IntegerField()
    per_student_rate = models.DecimalField()  # Based on tier
    billing_cycle = models.CharField(choices=[('monthly', 'quarterly', 'annual')])
    status = models.CharField(choices=[('active', 'expired', 'terminated')])
    auto_renew = models.BooleanField(default=True)
    early_termination_notice_date = models.DateField(null=True)
    
class InstitutionalBilling(models.Model):
    contract = models.ForeignKey(InstitutionalContract)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    active_seat_count = models.IntegerField()
    seat_adjustments = models.JSONField(default=list)
    subtotal = models.DecimalField()
    total_amount = models.DecimalField()
    invoice_generated_at = models.DateTimeField()
    due_date = models.DateField()  # Net 30 days
    status = models.CharField(choices=[('pending', 'paid', 'overdue')])
```

### 2. PRICING TIER SYSTEM

**Volume-Based Pricing:**
- 1-50 students: $15/student/month
- 51-200 students: $12/student/month  
- 201-500 students: $9/student/month
- 500+ students: $7/student/month

**Implementation:**
```python
def calculate_institutional_rate(seat_count):
    if seat_count <= 50:
        return Decimal('15.00')
    elif seat_count <= 200:
        return Decimal('12.00')
    elif seat_count <= 500:
        return Decimal('9.00')
    else:
        return Decimal('7.00')
```

### 3. AUTOMATED BILLING SYSTEM

**Features Needed:**
- Monthly/Quarterly/Annual invoice generation
- Seat count adjustments with proration
- Net 30 payment terms
- Email delivery to institution contacts
- Payment tracking and reminders

### 4. DIRECTOR DASHBOARD INTEGRATION

**Missing Features:**
- Institutional contract management
- Seat count monitoring
- Billing history for institutions
- Contract renewal alerts
- Revenue tracking by institution

### 5. FINANCE DASHBOARD ENHANCEMENTS

**Required Views:**
- Institutional revenue analytics
- Contract expiration tracking
- Seat utilization reports
- Payment status monitoring
- Volume discount impact analysis

## 🚀 IMPLEMENTATION PRIORITY

### Phase 1: Core Models (Week 1)
- InstitutionalContract model
- InstitutionalBilling model
- Pricing tier calculations
- Database migrations

### Phase 2: Billing Engine (Week 2)
- Automated invoice generation
- Seat count adjustments
- Proration calculations
- Email notifications

### Phase 3: Dashboard Integration (Week 3)
- Director contract management
- Finance institutional analytics
- Contract renewal system
- Reporting and exports

### Phase 4: Testing & Deployment (Week 4)
- End-to-end testing
- Payment integration
- Production deployment
- Documentation

## 💰 BUSINESS IMPACT

**Without Institutional Billing:**
- ❌ Cannot serve enterprise customers
- ❌ Missing high-value contracts ($21,600+ annually)
- ❌ No volume discount incentives
- ❌ Manual billing processes
- ❌ Poor institutional customer experience

**With Institutional Billing:**
- ✅ Enterprise-ready billing system
- ✅ Automated contract management
- ✅ Volume-based pricing incentives
- ✅ Professional invoicing
- ✅ Scalable institutional revenue

## 🎯 NEXT STEPS

1. **Approve Implementation Plan**
2. **Create Institutional Billing Models**
3. **Build Automated Billing Engine**
4. **Integrate with Director Dashboard**
5. **Add Finance Analytics**
6. **Test with Pilot Institution**
7. **Deploy to Production**

The institutional billing system is a critical missing piece for enterprise customers and represents significant revenue opportunity.