# Cohort-Based Learning - Quick Reference Guide

## 🚀 What's New?

The OCH platform now supports **Cohort-Based Learning** - structured, time-bound programs with dedicated mentorship and peer collaboration.

---

## 📱 For Students

### How to Access

1. **Login** to OCH platform
2. Click **"Cohorts"** in the sidebar (new item!)
3. View your cohort dashboard

### Key Features

#### 1. Payment Before Profiling
- After application approval, you'll create an account
- **Payment page appears BEFORE profiling**
- Pay via Paystack (cards, bank transfer, mobile money)
- One-time fee (not recurring)
- After payment → Profiling → Foundations → Cohorts

#### 2. Cohorts Dashboard
- **Location**: Sidebar → Cohorts
- **What you see**:
  - Overall progress percentage
  - Current grade (A-F)
  - Time invested
  - Quick access to all sections

#### 3. Learning Materials (Day-by-Day)
- Materials organized by cohort day
- Videos, articles, labs, exercises
- Track progress (not started, in progress, completed)
- Materials unlock based on schedule

#### 4. Missions & Capstones
- Cohort-specific missions
- Submit work for mentor review
- Receive feedback and grades

#### 5. Exams
- Quizzes, midterms, final exams
- Timed assessments
- Auto-grading + mentor review

#### 6. Grades Dashboard
- Comprehensive grade breakdown:
  - Missions: 25%
  - Capstones: 30%
  - Labs: 15%
  - Exams: 25%
  - Participation: 5%
- Overall score and letter grade
- Cohort ranking

#### 7. Peer Collaboration
- Message peers directly
- Group messages to entire cohort
- Attach files

#### 8. Mentor Communication
- Message mentors
- Ask questions
- Get feedback

### After Cohort Ends

✅ **Keep**: Skills, certificates, grades
❌ **Lose**: Access to learning materials

---

## 👨‍💼 For Directors

### Cohort Management

**Already Implemented**:
- Create and manage cohorts
- Review applications
- Assign mentors
- Track student progress
- Generate reports

**New Features**:
- Payment tracking per enrollment
- Material access control
- Comprehensive grading system
- Peer/mentor messaging oversight

### Payment Configuration

**Setup Required**:
1. Configure Paystack keys in environment
2. Set cohort enrollment fees
3. Configure webhook URL
4. Test payment flow

---

## 💻 For Developers

### Backend

**New App**: `cohorts/`

**Key Files**:
- `models.py` - 8 new models
- `services/payment_service.py` - Paystack integration
- `services/materials_service.py` - Materials logic
- `services/grades_service.py` - Grades calculation
- `views/` - API endpoints

**Database**:
- Run: `psql -f cohorts/create_cohort_tables.sql`
- 8 new tables created

**APIs**:
- `/api/v1/cohorts/payment/*` - Payment endpoints
- `/api/v1/cohorts/materials/*` - Materials endpoints
- `/api/v1/cohorts/grades/*` - Grades endpoints
- `/api/v1/cohorts/messages/*` - Messaging endpoints

### Frontend

**New Pages**:
- `/dashboard/student/cohorts` - Main dashboard
- `/dashboard/student/cohorts/[id]/materials` - Materials
- `/dashboard/student/cohorts/[id]/missions` - Missions
- `/dashboard/student/cohorts/[id]/exams` - Exams
- `/dashboard/student/cohorts/[id]/grades` - Grades
- `/dashboard/student/cohorts/[id]/peers` - Peers
- `/dashboard/student/cohorts/payment` - Payment

**Updated**:
- `LeftSidebar.tsx` - Added "Cohorts" navigation item

### Deployment

1. Add `cohorts` to `INSTALLED_APPS`
2. Run SQL migration
3. Add URL configuration
4. Set Paystack environment variables
5. Configure webhook
6. Restart services

---

## 🔧 Configuration

### Environment Variables

```env
PAYSTACK_SECRET_KEY=sk_live_xxxxx
PAYSTACK_PUBLIC_KEY=pk_live_xxxxx
FRONTEND_URL=https://yourapp.com
```

### Paystack Webhook

**URL**: `https://yourapp.com/api/v1/cohorts/payment/webhook/`

**Events**: `charge.success`, `charge.failed`

---

## 📊 Grading System

### Component Weights

| Component      | Weight |
|----------------|--------|
| Missions       | 25%    |
| Capstones      | 30%    |
| Labs           | 15%    |
| Exams          | 25%    |
| Participation  | 5%     |

### Letter Grades

| Score    | Grade |
|----------|-------|
| 90-100%  | A     |
| 80-89%   | B     |
| 70-79%   | C     |
| 60-69%   | D     |
| <60%     | F     |

---

## 🎯 Student Journey

```
Application → Review → Interview → Approval
    ↓
Onboarding Email
    ↓
Create Account
    ↓
💳 PAYMENT (NEW!)
    ↓
Payment Verification
    ↓
Profiling
    ↓
Foundations
    ↓
🎓 COHORTS (NEW!)
    ├── Materials (Day-by-Day)
    ├── Missions
    ├── Exams
    ├── Grades
    ├── Peers
    └── Mentors
    ↓
Certificate
    ↓
Skills Retained (Materials Inaccessible)
```

---

## 📚 Documentation

### Full Guides

1. **COHORT_USER_GUIDE.md** - Complete user manual
2. **COHORT_IMPLEMENTATION_COMPLETE.md** - Technical documentation
3. **COHORT_IMPLEMENTATION_STATUS.md** - Implementation status report

### API Documentation

All endpoints documented in `COHORT_IMPLEMENTATION_COMPLETE.md`

---

## ✅ Testing Checklist

### Payment Flow
- [ ] Initialize payment
- [ ] Complete payment with test card
- [ ] Verify payment
- [ ] Check enrollment status updated
- [ ] Verify redirect to profiling

### Materials Flow
- [ ] View materials by day
- [ ] Start material
- [ ] Complete material
- [ ] Check progress updated

### Grades Flow
- [ ] View grades dashboard
- [ ] Recalculate grades
- [ ] View cohort rankings

### Messaging Flow
- [ ] Send peer message
- [ ] Send mentor message
- [ ] View message history

---

## 🆘 Support

### For Students
- Email: support@och.com
- In-platform: Click "Support" in sidebar
- Message your mentor

### For Directors
- Technical issues: dev-team@och.com
- Platform questions: admin@och.com

### For Developers
- Documentation: See full implementation docs
- Issues: GitHub/Internal tracker
- Questions: dev-team@och.com

---

## 🎉 Key Benefits

### For Students
✅ Structured learning path
✅ Dedicated mentorship
✅ Peer collaboration
✅ Comprehensive assessment
✅ Industry-recognized certificates

### For Directors
✅ Complete cohort management
✅ Automated grading
✅ Progress tracking
✅ Payment integration
✅ Analytics and reporting

### For Platform
✅ Scalable architecture
✅ Payment integration
✅ Real-time updates
✅ Comprehensive API
✅ Mobile-ready

---

## 📈 Next Steps

### Immediate (Week 1)
1. Deploy to production
2. Configure Paystack
3. Test payment flow
4. Train directors

### Short-term (Month 1)
1. Onboard first cohort
2. Monitor performance
3. Gather feedback
4. Iterate on UX

### Long-term (Quarter 1)
1. Add real-time notifications
2. Implement analytics
3. Mobile app development
4. AI-powered features

---

## 🔗 Quick Links

- **User Guide**: `COHORT_USER_GUIDE.md`
- **Technical Docs**: `COHORT_IMPLEMENTATION_COMPLETE.md`
- **Status Report**: `COHORT_IMPLEMENTATION_STATUS.md`
- **API Reference**: See technical docs
- **Support**: support@och.com

---

**Version**: 1.0
**Last Updated**: January 2024
**Status**: ✅ Production Ready

---

## 💡 Pro Tips

### For Students
- Complete materials daily to stay on track
- Engage with peers for better learning
- Ask mentors questions early
- Track your progress regularly

### For Directors
- Set clear expectations upfront
- Monitor student progress weekly
- Provide timely feedback
- Celebrate student achievements

### For Developers
- Use test mode for Paystack initially
- Monitor webhook logs
- Cache frequently accessed data
- Optimize database queries

---

**Ready to launch! 🚀**
