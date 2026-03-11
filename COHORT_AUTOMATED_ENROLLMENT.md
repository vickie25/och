# Automated Cohort Enrollment Process - Updated Implementation

## 🔄 Changes from Original Design

### What Changed

#### ❌ Removed Features
1. **Manual Mentor Review** - No longer needed
2. **Interview Stage** - Completely removed
3. **Unique Credentials in Email** - Students create their own passwords

#### ✅ New Automated Features
1. **Application Test Questions** - Automated assessment
2. **Director Sets Cut-off Grade** - One-click grading
3. **Automated Status Updates** - Pass/Fail/Waitlist
4. **Payment Deadline Countdown** - Time-limited payment window
5. **Self-Service Password Creation** - Students set their own passwords

---

## 📋 Updated Student Journey

### New Automated Flow

```
1. Student Applies (Public Form)
   ↓
2. Application Test Sent Automatically
   ↓
3. Student Completes Test
   ↓
4. Director Sets Cut-off Grade
   ↓
5. System Auto-Grades All Applications
   ├── PASSED → Onboarding Email
   ├── FAILED → Waitlist
   └── Waitlist → Rejection Email (when director sends)
   ↓
6. Student Receives Onboarding Email
   - Contains account creation link
   - NO credentials included
   ↓
7. Student Creates Password
   ↓
8. Payment Page with Countdown
   - Paystack integration
   - Payment deadline timer
   - Auto-reject if deadline passes
   ↓
9. Payment Verification
   ↓
10. Profiling
    ↓
11. Foundations
    ↓
12. Cohorts Section
```

---

## 🔧 Implementation Updates Needed

### 1. Remove Interview Stage

**Files to Update**:
- `backend/django_app/programs/models.py` - CohortPublicApplication model
- `backend/django_app/programs/views/public_registration_views.py`

**Changes**:
```python
# In CohortPublicApplication model
# REMOVE these fields:
# - interview_mentor
# - interview_score
# - interview_graded_at
# - interview_status

# KEEP only:
# - reviewer_mentor (for test grading)
# - review_score (test score)
# - review_graded_at
# - review_status
```

### 2. Add Payment Deadline

**New Model Fields**:
```python
class CohortPublicApplication(models.Model):
    # ... existing fields ...
    
    # NEW FIELDS
    payment_deadline = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Deadline for payment after approval'
    )
    onboarding_link_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When onboarding email was sent'
    )
    password_created_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When student created their password'
    )
```

### 3. Automated Grading Endpoint

**New API Endpoint**:
```python
# backend/django_app/programs/views/public_registration_views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def auto_grade_applications(request):
    """
    POST /api/v1/programs/director/public-applications/auto-grade/
    
    Automatically grade all applications based on cut-off score.
    
    Request:
    {
        "cohort_id": "uuid",
        "cutoff_score": 70.0,
        "payment_deadline_hours": 48
    }
    
    Response:
    {
        "passed": 25,
        "failed": 15,
        "waitlist": 15,
        "total": 55
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        cutoff_score = Decimal(request.data.get('cutoff_score', 70))
        payment_deadline_hours = int(request.data.get('payment_deadline_hours', 48))
        
        # Get all pending applications
        applications = CohortPublicApplication.objects.filter(
            cohort_id=cohort_id,
            status='pending',
            review_status='reviewed'  # Test completed
        )
        
        passed = 0
        failed = 0
        
        for app in applications:
            if app.review_score >= cutoff_score:
                # PASSED - Send onboarding email
                app.status = 'approved'
                app.review_status = 'passed'
                app.payment_deadline = timezone.now() + timedelta(hours=payment_deadline_hours)
                app.save()
                
                # Send onboarding email
                send_onboarding_email(app)
                passed += 1
            else:
                # FAILED - Add to waitlist
                app.review_status = 'failed'
                app.status = 'pending'  # Keep as pending (waitlist)
                app.save()
                failed += 1
        
        return Response({
            'passed': passed,
            'failed': failed,
            'waitlist': failed,
            'total': passed + failed,
            'message': f'Graded {passed + failed} applications. {passed} passed, {failed} on waitlist.'
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 4. Send Rejection Emails

**New API Endpoint**:
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProgramDirector])
def send_rejection_emails(request):
    """
    POST /api/v1/programs/director/public-applications/send-rejections/
    
    Send rejection emails to waitlisted students.
    
    Request:
    {
        "cohort_id": "uuid",
        "application_ids": ["uuid1", "uuid2", ...]  # Optional, if empty sends to all waitlist
    }
    """
    try:
        cohort_id = request.data.get('cohort_id')
        application_ids = request.data.get('application_ids', [])
        
        # Get waitlisted applications
        query = CohortPublicApplication.objects.filter(
            cohort_id=cohort_id,
            review_status='failed',
            status='pending'
        )
        
        if application_ids:
            query = query.filter(id__in=application_ids)
        
        rejected_count = 0
        for app in query:
            # Update status
            app.status = 'rejected'
            app.save()
            
            # Send rejection email
            send_rejection_email(app)
            rejected_count += 1
        
        return Response({
            'rejected': rejected_count,
            'message': f'Sent {rejected_count} rejection emails'
        })
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 5. Onboarding Email (No Credentials)

**Email Template**:
```python
def send_onboarding_email(application):
    """
    Send onboarding email with account creation link (no credentials).
    """
    cohort = application.cohort
    email = application.form_data.get('email')
    name = application.form_data.get('name', 'Student')
    
    # Generate secure token for account creation
    token = generate_secure_token(application.id)
    
    # Create onboarding link
    onboarding_link = f"{settings.FRONTEND_URL}/onboarding/create-account?token={token}"
    
    # Payment deadline
    deadline = application.payment_deadline.strftime('%B %d, %Y at %I:%M %p')
    
    subject = f"Welcome to {cohort.name} - Create Your Account"
    
    message = f"""
    Dear {name},
    
    Congratulations! You have been accepted into {cohort.name}.
    
    NEXT STEPS:
    
    1. Create Your Account
       Click the link below to set your password:
       {onboarding_link}
    
    2. Complete Payment
       After creating your account, you'll be directed to the payment page.
       
       IMPORTANT: Payment must be completed by {deadline}
       
       Amount: ${cohort.enrollment_fee}
       Payment Methods: Credit/Debit Card, Bank Transfer, Mobile Money
    
    3. Start Learning
       Once payment is verified, you'll complete profiling and access your cohort.
    
    PAYMENT DEADLINE: {deadline}
    
    If you don't complete payment by the deadline, your spot will be released.
    
    Questions? Reply to this email or contact support@och.com
    
    Welcome aboard!
    
    The OCH Team
    """
    
    # Send email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )
    
    # Update application
    application.onboarding_link_sent_at = timezone.now()
    application.save()
```

### 6. Account Creation Page

**New Frontend Page**: `frontend/nextjs_app/app/onboarding/create-account/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiGateway } from '@/services/apiGateway';

export default function CreateAccountPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [applicationData, setApplicationData] = useState(null);

  useEffect(() => {
    // Verify token and get application data
    verifyToken();
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await apiGateway.get(`/programs/onboarding/verify-token?token=${token}`);
      setApplicationData(response.data);
    } catch (error) {
      setError('Invalid or expired link. Please contact support.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      // Create account
      const response = await apiGateway.post('/programs/onboarding/create-account', {
        token,
        password
      });
      
      // Redirect to payment page
      router.push(`/cohorts/payment?enrollment_id=${response.enrollment_id}`);
    } catch (error) {
      setError(error.message || 'Failed to create account');
    } finally {
      setIsLoading(false);
    }
  };

  if (!applicationData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
      <div className="max-w-md w-full bg-och-midnight/60 border border-och-steel/10 rounded-3xl p-8">
        <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-2">
          Create Your Account
        </h1>
        <p className="text-och-steel mb-8">
          Welcome to {applicationData.cohort_name}
        </p>

        {error && (
          <div className="bg-och-defender/10 border border-och-defender/30 rounded-xl p-4 mb-6">
            <p className="text-och-defender text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
              Email
            </label>
            <input
              type="email"
              value={applicationData.email}
              disabled
              className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 px-4 text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password (min 8 characters)"
              className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 px-4 text-white"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 px-4 text-white"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-4 hover:bg-och-gold/90 transition-all disabled:opacity-50"
          >
            {isLoading ? 'Creating Account...' : 'Create Account & Continue to Payment'}
          </button>
        </form>

        <div className="mt-6 p-4 bg-och-mint/5 border border-och-mint/20 rounded-xl">
          <p className="text-xs text-och-steel">
            <strong className="text-och-mint">Next Step:</strong> After creating your account, 
            you'll be directed to the payment page to complete your enrollment.
          </p>
        </div>
      </div>
    </div>
  );
}
```

### 7. Payment Page with Countdown

**Updated Payment Page**: `frontend/nextjs_app/app/cohorts/payment/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiGateway } from '@/services/apiGateway';
import { Clock, CreditCard, AlertTriangle } from 'lucide-react';

export default function PaymentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const enrollmentId = searchParams.get('enrollment_id');
  
  const [enrollment, setEnrollment] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchEnrollmentData();
  }, [enrollmentId]);

  useEffect(() => {
    if (enrollment?.payment_deadline) {
      const timer = setInterval(() => {
        updateCountdown();
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [enrollment]);

  const fetchEnrollmentData = async () => {
    try {
      const response = await apiGateway.get(`/programs/enrollments/${enrollmentId}`);
      setEnrollment(response.data);
    } catch (error) {
      setError('Failed to load enrollment data');
    }
  };

  const updateCountdown = () => {
    if (!enrollment?.payment_deadline) return;
    
    const deadline = new Date(enrollment.payment_deadline);
    const now = new Date();
    const diff = deadline - now;
    
    if (diff <= 0) {
      setTimeRemaining({ expired: true });
      return;
    }
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    setTimeRemaining({ days, hours, minutes, seconds, expired: false });
  };

  const handlePayment = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      // Initialize payment
      const response = await apiGateway.post('/cohorts/payment/initiate/', {
        enrollment_id: enrollmentId,
        callback_url: `${window.location.origin}/cohorts/payment/verify`
      });
      
      // Redirect to Paystack
      window.location.href = response.authorization_url;
    } catch (error) {
      setError(error.message || 'Failed to initialize payment');
    } finally {
      setIsLoading(false);
    }
  };

  if (!enrollment) {
    return <div>Loading...</div>;
  }

  if (timeRemaining?.expired) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center">
          <AlertTriangle className="w-16 h-16 text-och-defender mx-auto mb-4" />
          <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-4">
            Payment Deadline Expired
          </h1>
          <p className="text-och-steel mb-8">
            Your payment deadline has passed. Your enrollment spot has been released.
            Please contact support if you'd like to reapply.
          </p>
          <button
            onClick={() => router.push('/')}
            className="px-8 py-4 bg-och-gold text-black font-black uppercase tracking-widest rounded-2xl"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-och-midnight p-8">
      <div className="max-w-4xl mx-auto">
        
        {/* Countdown Timer */}
        <div className="mb-8 p-6 bg-och-defender/10 border border-och-defender/30 rounded-3xl">
          <div className="flex items-center gap-4 mb-4">
            <Clock className="w-6 h-6 text-och-defender" />
            <h2 className="text-xl font-black text-white uppercase tracking-tighter">
              Payment Deadline
            </h2>
          </div>
          
          {timeRemaining && !timeRemaining.expired && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-4xl font-black text-och-defender">
                  {timeRemaining.days}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest">Days</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-black text-och-defender">
                  {timeRemaining.hours}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest">Hours</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-black text-och-defender">
                  {timeRemaining.minutes}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest">Minutes</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-black text-och-defender">
                  {timeRemaining.seconds}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest">Seconds</div>
              </div>
            </div>
          )}
          
          <p className="text-sm text-och-steel mt-4">
            Complete payment before the deadline to secure your spot in the cohort.
          </p>
        </div>

        {/* Payment Details */}
        <div className="bg-och-midnight/60 border border-och-steel/10 rounded-3xl p-8">
          <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-6">
            Complete Your Enrollment
          </h1>

          <div className="space-y-4 mb-8">
            <div className="flex justify-between">
              <span className="text-och-steel">Cohort:</span>
              <span className="text-white font-bold">{enrollment.cohort_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-och-steel">Enrollment Fee:</span>
              <span className="text-white font-bold text-2xl">
                ${enrollment.amount}
              </span>
            </div>
          </div>

          {error && (
            <div className="bg-och-defender/10 border border-och-defender/30 rounded-xl p-4 mb-6">
              <p className="text-och-defender text-sm">{error}</p>
            </div>
          )}

          <button
            onClick={handlePayment}
            disabled={isLoading}
            className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-4 hover:bg-och-gold/90 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <CreditCard className="w-5 h-5" />
            {isLoading ? 'Processing...' : 'Pay with Paystack'}
          </button>

          <div className="mt-6 p-4 bg-och-mint/5 border border-och-mint/20 rounded-xl">
            <p className="text-xs text-och-steel">
              <strong className="text-och-mint">Secure Payment:</strong> All payments are 
              processed securely through Paystack. We accept credit/debit cards, bank transfers, 
              and mobile money.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 📊 Updated Database Schema

### Add New Fields to CohortPublicApplication

```sql
-- Add payment deadline and tracking fields
ALTER TABLE cohort_public_applications
ADD COLUMN payment_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN onboarding_link_sent_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN password_created_at TIMESTAMP WITH TIME ZONE;

-- Remove interview fields (if they exist)
ALTER TABLE cohort_public_applications
DROP COLUMN IF EXISTS interview_mentor_id,
DROP COLUMN IF EXISTS interview_score,
DROP COLUMN IF EXISTS interview_graded_at,
DROP COLUMN IF EXISTS interview_status;

-- Add index for payment deadline queries
CREATE INDEX idx_payment_deadline ON cohort_public_applications(payment_deadline);
```

### Add Enrollment Fee to Cohort

```sql
-- Add enrollment fee to cohorts table
ALTER TABLE cohorts
ADD COLUMN enrollment_fee DECIMAL(10, 2) DEFAULT 100.00;
```

---

## 🔄 Updated API Endpoints

### New Endpoints

1. **Auto-Grade Applications**
   ```
   POST /api/v1/programs/director/public-applications/auto-grade/
   ```

2. **Send Rejection Emails**
   ```
   POST /api/v1/programs/director/public-applications/send-rejections/
   ```

3. **Verify Onboarding Token**
   ```
   GET /api/v1/programs/onboarding/verify-token?token=xxx
   ```

4. **Create Account**
   ```
   POST /api/v1/programs/onboarding/create-account
   ```

### Updated Endpoints

1. **Remove Interview Grading**
   ```
   DELETE /api/v1/programs/mentor/applications-to-review/<uuid>/grade-interview/
   ```

---

## 📝 Updated User Guide Section

### Automated Enrollment Process

#### For Students:

**Step 1: Apply**
- Fill out application form on homepage
- Submit application

**Step 2: Complete Application Test**
- Receive email with test link
- Complete test within time limit
- Submit answers

**Step 3: Wait for Results**
- Director grades all applications
- Automatic pass/fail based on cut-off score

**Step 4: Receive Onboarding Email (if passed)**
- Email contains account creation link
- **NO credentials** - you create your own password
- Payment deadline clearly stated

**Step 5: Create Account**
- Click link in email
- Set your password
- Automatically redirected to payment page

**Step 6: Complete Payment**
- **Payment deadline countdown** displayed
- Pay via Paystack
- Multiple payment methods available
- Must complete before deadline

**Step 7: Payment Verified**
- Automatic verification
- Redirected to profiling

**Step 8: Continue Journey**
- Complete profiling
- Access Foundations
- Enter Cohorts section

#### For Directors:

**Step 1: Create Cohort**
- Set cohort details
- Configure application test questions
- Set enrollment fee
- Set payment deadline (hours after approval)

**Step 2: Review Applications**
- View all submitted applications
- Check test completion status

**Step 3: Set Cut-off Grade**
- Decide minimum passing score
- Click "Auto-Grade Applications"
- System automatically:
  - Passes students above cut-off
  - Sends onboarding emails
  - Adds failed students to waitlist

**Step 4: Manage Waitlist**
- View waitlisted students
- Option to send rejection emails
- Or keep on waitlist for future cohorts

**Step 5: Monitor Payments**
- Track payment status
- View payment deadlines
- Auto-reject expired payments

---

## ✅ Implementation Checklist

### Backend Updates
- [ ] Remove interview fields from model
- [ ] Add payment deadline fields
- [ ] Add enrollment fee to cohort
- [ ] Create auto-grade endpoint
- [ ] Create rejection email endpoint
- [ ] Create onboarding token verification
- [ ] Create account creation endpoint
- [ ] Update email templates

### Frontend Updates
- [ ] Create account creation page
- [ ] Update payment page with countdown
- [ ] Remove interview references
- [ ] Update director dashboard
- [ ] Add auto-grade button
- [ ] Add rejection email button

### Database Updates
- [ ] Run SQL migration
- [ ] Add new indexes
- [ ] Remove interview columns

### Testing
- [ ] Test auto-grading
- [ ] Test onboarding flow
- [ ] Test payment countdown
- [ ] Test deadline expiration
- [ ] Test rejection emails

---

## 🎯 Summary of Changes

### Removed
- ❌ Manual mentor review
- ❌ Interview stage
- ❌ Unique credentials in email

### Added
- ✅ Automated grading based on cut-off
- ✅ Waitlist management
- ✅ Self-service password creation
- ✅ Payment deadline countdown
- ✅ Automatic deadline enforcement

### Improved
- ✅ Faster enrollment process
- ✅ Less manual work for directors
- ✅ Better student experience
- ✅ Clear payment deadlines
- ✅ Automated status updates

---

This updated implementation provides a fully automated, streamlined enrollment process that requires minimal manual intervention while maintaining quality control through the application test and cut-off grade system.
