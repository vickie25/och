# Dynamic Pricing System Implementation

## Overview

The OCH platform now supports **fully dynamic pricing** for institution and employer contracts, allowing administrators to update pricing without code changes while maintaining backward compatibility with existing hardcoded rates.

## Features

### ✅ Dynamic Pricing Tiers
- **Database-driven**: All pricing stored in `PricingTier` model
- **Multi-currency**: Support for USD, KES, EUR
- **Flexible billing**: Monthly, quarterly, annual cycles
- **Volume discounts**: Automatic annual discount calculations
- **Effective periods**: Schedule pricing changes for future dates

### ✅ Pricing History Tracking
- **Audit trail**: Complete history of all pricing changes
- **Change tracking**: Old vs new values with reasons
- **User attribution**: Track who made changes and when
- **Read-only API**: Secure access to pricing history

### ✅ Admin Interface
- **Django Admin**: Full CRUD operations for pricing tiers
- **Bulk updates**: Edit multiple tiers simultaneously
- **Validation**: Built-in data integrity checks
- **History view**: Integrated pricing history display

### ✅ API Endpoints
- **REST API**: Complete CRUD for pricing management
- **Price calculator**: Real-time pricing calculations
- **History API**: Access to pricing change history
- **Fallback support**: Graceful degradation to hardcoded rates

## Implementation Details

### Models Added

#### `PricingTier`
```python
class PricingTier(models.Model):
    name = models.CharField(max_length=50)  # tier_1_50, starter
    display_name = models.CharField(max_length=100)
    tier_type = models.CharField(choices=[('institution', 'Institution'), ('employer', 'Employer')])
    min_quantity = models.PositiveIntegerField()
    max_quantity = models.PositiveIntegerField(null=True, blank=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    billing_frequency = models.CharField(max_length=20, default='monthly')
    annual_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
```

#### `PricingHistory`
```python
class PricingHistory(models.Model):
    pricing_tier = models.ForeignKey(PricingTier, related_name='history')
    old_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    new_price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    change_reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, null=True, related_name='pricing_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
```

### Services Added

#### `DynamicPricingService`
- **Rate lookup**: Find appropriate pricing tier for quantity
- **Price calculation**: Handle billing cycles and discounts
- **Fallback logic**: Use hardcoded rates if no dynamic pricing found
- **History tracking**: Record all pricing changes

### API Endpoints

#### Pricing Tiers
```
GET    /api/v1/finance/pricing-tiers/              # List all tiers
GET    /api/v1/finance/pricing-tiers/active/        # Active tiers only
GET    /api/v1/finance/pricing-tiers/calculate_price/  # Calculate price
POST   /api/v1/finance/pricing-tiers/{id}/update_price/  # Update with history
```

#### Pricing History
```
GET    /api/v1/finance/pricing-history/            # List all changes
GET    /api/v1/finance/pricing-history/recent/      # Recent changes
```

## Migration Strategy

### Step 1: Database Migration
```bash
python manage.py migrate finance
```

### Step 2: Initialize Pricing Tiers
```bash
python manage.py setup_pricing_tiers
```

This command creates pricing tiers with current hardcoded values:
- **Institution**: 4 tiers (1-50, 51-200, 201-500, 500+ students)
- **Employer**: 3 plans (starter, growth, enterprise)

### Step 3: Verify Integration
- Check Django Admin for pricing tiers
- Test API endpoints
- Verify invoice calculations use dynamic pricing

## Backward Compatibility

### Fallback Logic
The system maintains **100% backward compatibility**:
1. **Dynamic pricing first**: Check database for active tiers
2. **Fallback to hardcoded**: Use existing dictionaries if no dynamic pricing found
3. **Graceful degradation**: No disruption to existing functionality

### Existing Contracts
- **Active contracts**: Continue with existing pricing
- **New contracts**: Use dynamic pricing automatically
- **Manual override**: Still possible via `total_value` field

## Usage Examples

### Admin Updates
1. Go to Django Admin → Finance → Pricing Tiers
2. Edit tier pricing directly
3. System automatically tracks changes in history

### API Updates
```bash
# Update institution tier pricing
curl -X POST "http://localhost:8000/api/v1/finance/pricing-tiers/{tier_id}/update_price/" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "price_per_unit": 18.00,
    "annual_discount_percent": 3.0,
    "reason": "Market adjustment for 2026"
  }'
```

### Price Calculations
```bash
# Calculate institution pricing for 75 students
curl "http://localhost:8000/api/v1/finance/pricing-tiers/calculate_price/?tier_type=institution&quantity=75&billing_frequency=monthly"

# Response:
{
  "tier_type": "institution",
  "quantity": 75,
  "unit_price": 12.00,
  "total_amount": 900.00,
  "currency": "USD"
}
```

## Benefits

### ✅ Business Agility
- **Rapid pricing updates**: No code deployments required
- **Market responsiveness**: Quick adaptation to competition
- **A/B testing**: Test different pricing strategies
- **Regional pricing**: Support for different currencies/markets

### ✅ Operational Excellence
- **Audit compliance**: Complete change tracking
- **Error reduction**: Validated data entry
- **Team collaboration**: Multiple administrators can manage pricing
- **Historical analysis**: Track pricing impact on revenue

### ✅ Technical Advantages
- **Zero downtime**: Hot-swappable pricing
- **Data integrity**: Database constraints and validation
- **API-first**: Programmatic pricing management
- **Scalable**: Support for unlimited pricing tiers

## Future Enhancements

### Planned Features
- **Scheduled pricing**: Automatic price changes on specific dates
- **Promotional pricing**: Temporary discounts and campaigns
- **Customer-specific pricing**: Custom rates for key accounts
- **Analytics dashboard**: Pricing performance metrics
- **Approval workflows**: Multi-level pricing change approvals

### Integration Opportunities
- **CRM integration**: Sync pricing with sales systems
- **Billing automation**: Automated invoice generation
- **Revenue forecasting**: Predictive pricing analytics
- **Competitor monitoring**: Market price tracking

## Support

For questions or issues with the dynamic pricing system:
1. Check Django Admin → Finance → Pricing History for change logs
2. Review API documentation for endpoint details
3. Contact the finance team for pricing strategy questions
4. Submit technical issues to the development team

---

**Status**: ✅ **PRODUCTION READY**  
**Compatibility**: ✅ **BACKWARD COMPATIBLE**  
**Migration**: ✅ **ZERO DOWNTIME**
