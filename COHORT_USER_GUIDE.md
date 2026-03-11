# Cohort-Based Learning System - User Guide

## 📚 Table of Contents
1. [Overview](#overview)
2. [What is a Cohort?](#what-is-a-cohort)
3. [Student Journey](#student-journey)
4. [Features](#features)
5. [How to Use](#how-to-use)
6. [FAQ](#faq)

---

## Overview

The OCH Cohort-Based Learning System provides structured, time-bound learning experiences with dedicated mentorship, peer collaboration, and comprehensive assessment. This guide explains how students interact with the cohort system.

---

## What is a Cohort?

A **cohort** is a defined group of 10-50 students enrolled in the same learning program track with:

### Key Characteristics:
- ✅ **Fixed enrollment period**: Students enroll within a specific date window
- ✅ **Fixed program duration**: Defined start and end dates (typically 8-24 weeks)
- ✅ **Limited seat capacity**: Maximum 50 students per cohort
- ✅ **Dedicated mentors**: Assigned mentor team for live sessions and support
- ✅ **Structured curriculum**: Predefined mission sequences and learning materials
- ✅ **One-time fee**: Flat enrollment fee (not recurring subscription)
- ✅ **Fixed schedule**: Live sessions, milestones, and deliverables follow cohort calendar

### Cohort Types:
1. **Public Cohorts**: Open enrollment for individual students
2. **Private Cohorts**: Institution-sponsored programs
3. **Enterprise Cohorts**: Employer-sponsored training

---

## Student Journey

### Phase 1: Application & Enrollment

#### Step 1: Apply to Cohort
- Browse available cohorts on the homepage
- Submit application form (no account required)
- Provide required information (name, email, background, motivation)

#### Step 2: Application Review
- Director assigns application to mentor for review
- Mentor grades application based on criteria
- Passing score: Moves to interview stage
- Failing score: Application rejected

#### Step 3: Interview (if applicable)
- Mentor conducts interview
- Interview graded based on cohort criteria
- Passing score: Eligible for enrollment
- Failing score: Application rejected

#### Step 4: Enrollment Notification
- Approved applicants receive onboarding email
- Email contains account creation link
- Unique credentials for platform access

### Phase 2: Payment & Onboarding

#### Step 5: Create Account
- Click link in onboarding email
- Set password for account
- **IMPORTANT**: Before accessing profiling, payment is required

#### Step 6: Payment
- **Payment Page** appears before profiling
- Pay cohort enrollment fee via **Paystack**
- Supported payment methods:
  - Credit/Debit Cards (Visa, Mastercard)
  - Bank Transfer
  - Mobile Money (M-Pesa, Airtel Money, etc.)
- One-time payment (not recurring)

#### Step 7: Payment Verification
- System verifies payment with Paystack
- Upon successful payment:
  - Enrollment status: `pending_payment` → `active`
  - Payment status: `pending` → `paid`
  - Redirected to profiling

#### Step 8: Profiling
- Complete profiling questionnaire
- AI analyzes responses
- Determines learning path and recommendations

#### Step 9: Foundations
- Access Foundations module
- Learn platform basics
- Understand cybersecurity fundamentals

### Phase 3: Cohort Learning Experience

#### Step 10: Access Cohorts Section
- Navigate to **"Cohorts"** in sidebar
- View cohort dashboard with:
  - Overall progress
  - Current grade
  - Time invested
  - Quick access to materials

#### Step 11: Day-by-Day Learning
- Materials organized by cohort day (Day 1, Day 2, etc.)
- Each day contains:
  - **Videos**: Instructional content
  - **Articles**: Reading materials
  - **Slides**: Presentation decks
  - **Labs**: Hands-on practice
  - **Exercises**: Skill-building activities

#### Step 12: Missions & Capstones
- Complete cohort-specific missions
- Work on capstone projects
- Submit artifacts for mentor review
- Receive feedback and grades

#### Step 13: Practice Labs
- Access hands-on lab environments
- Practice real-world scenarios
- Build practical skills

#### Step 14: Exams
- Take scheduled exams:
  - **Quizzes**: Short assessments
  - **Midterm**: Mid-cohort evaluation
  - **Final Exam**: Comprehensive assessment
- Timed exams with auto-grading
- Mentor review for subjective questions

#### Step 15: Peer Collaboration
- Message peers in cohort
- Group discussions
- Collaborative projects
- Peer code review

#### Step 16: Mentor Communication
- Message mentors directly
- Ask questions about materials
- Request feedback on work
- Schedule office hours

#### Step 17: Track Progress
- View comprehensive grades dashboard:
  - **Missions Score** (25% weight)
  - **Capstones Score** (30% weight)
  - **Labs Score** (15% weight)
  - **Exams Score** (25% weight)
  - **Participation Score** (5% weight)
- Overall grade (A, B, C, D, F)
- Cohort ranking (optional)

### Phase 4: Post-Cohort

#### Step 18: Cohort Completion
- Cohort ends on scheduled end date
- Final grades calculated
- Certificate generated (if passing)

#### Step 19: Skills Retention
- Skills remain attached to profile
- Visible on TalentScope
- Accessible to employers on Marketplace

#### Step 20: Material Access Revocation
- **Learning materials become inaccessible** after cohort ends
- Rationale: Cohort-specific content for active learners
- Skills and certificates remain permanent

---

## Features

### 1. Cohorts Dashboard
**Location**: `/dashboard/student/cohorts`

**What you see**:
- Cohort name and status
- Start and end dates
- Overall progress percentage
- Current grade and letter grade
- Cohort rank
- Time invested
- Quick access buttons to all sections

**Actions**:
- Navigate to learning materials
- Access missions and exams
- View grades
- Message peers and mentors

### 2. Learning Materials
**Location**: `/dashboard/student/cohorts/[cohortId]/materials`

**What you see**:
- Materials organized by day
- Material type (video, article, lab, etc.)
- Estimated time for each material
- Lock/unlock status (based on cohort schedule)
- Your progress (not started, in progress, completed)

**Actions**:
- Start material (marks as "in progress")
- Complete material (marks as "completed")
- Add notes to materials
- Track time spent

**Material Types**:
- 📹 **Video**: Instructional videos
- 📄 **Article**: Reading materials
- 📊 **Slides**: Presentation decks
- 🧪 **Lab**: Hands-on practice
- 📖 **Reading**: Additional resources
- ✏️ **Exercise**: Skill-building activities

### 3. Missions
**Location**: `/dashboard/student/cohorts/[cohortId]/missions`

**What you see**:
- Cohort-specific missions
- Mission difficulty and competencies
- Submission status
- Mentor feedback and scores

**Actions**:
- Start mission
- Submit artifacts (code, documents, links)
- View mentor feedback
- Resubmit if needed

### 4. Exams
**Location**: `/dashboard/student/cohorts/[cohortId]/exams`

**What you see**:
- Scheduled exams (quizzes, midterm, final)
- Exam type and duration
- Total points and passing score
- Your submission status

**Actions**:
- Start exam (timer begins)
- Answer questions
- Submit exam
- View results after grading

**Exam Types**:
- **Quiz**: Short assessment (10-20 minutes)
- **Midterm**: Mid-cohort evaluation (60-90 minutes)
- **Final Exam**: Comprehensive assessment (120+ minutes)
- **Practical**: Hands-on skills test

### 5. Grades Dashboard
**Location**: `/dashboard/student/cohorts/[cohortId]/grades`

**What you see**:
- Overall score and letter grade
- Cohort rank
- Component breakdown:
  - Missions: 25% weight
  - Capstones: 30% weight
  - Labs: 15% weight
  - Exams: 25% weight
  - Participation: 5% weight
- Individual scores for each component
- Count of completed items per component

**Actions**:
- Recalculate grades (updates scores)
- View cohort rankings
- Export grade report

**Grading Scale**:
- **A**: 90-100%
- **B**: 80-89%
- **C**: 70-79%
- **D**: 60-69%
- **F**: Below 60%

### 6. Peer Collaboration
**Location**: `/dashboard/student/cohorts/[cohortId]/peers`

**What you see**:
- List of peers in cohort
- Peer profiles (name, track)
- Message history

**Actions**:
- Send direct message to peer
- Send group message to entire cohort
- View message history
- Attach files to messages

### 7. Mentor Communication
**Location**: `/dashboard/student/cohorts/[cohortId]/mentors`

**What you see**:
- Assigned mentors
- Message history with mentors
- Mentor responses

**Actions**:
- Send message to mentor
- Attach files
- View mentor replies
- Mark messages as read

---

## How to Use

### Accessing Your Cohort

1. **Login** to OCH platform
2. Click **"Cohorts"** in left sidebar
3. View your cohort dashboard

### Completing Daily Materials

1. Go to **Cohorts** → **Learning Materials**
2. Select current day
3. Click on material to open
4. Click **"Start Material"** (marks as in progress)
5. Complete material (watch video, read article, etc.)
6. Click **"Complete Material"** (marks as completed)
7. Optionally add notes
8. Progress automatically tracked

### Submitting Missions

1. Go to **Cohorts** → **Missions**
2. Select mission
3. Read requirements
4. Complete mission work
5. Click **"Submit"**
6. Upload artifacts (code, documents, links)
7. Wait for mentor review
8. View feedback and score

### Taking Exams

1. Go to **Cohorts** → **Exams**
2. Select exam
3. Click **"Start Exam"** (timer begins)
4. Answer all questions
5. Click **"Submit Exam"**
6. Wait for grading
7. View results

### Messaging Peers

1. Go to **Cohorts** → **Peers**
2. Select peer or choose "Group Message"
3. Type message
4. Attach files (optional)
5. Click **"Send"**

### Messaging Mentors

1. Go to **Cohorts** → **Mentors**
2. Select mentor
3. Enter subject and message
4. Attach files (optional)
5. Click **"Send"**
6. Wait for mentor reply

### Viewing Grades

1. Go to **Cohorts** → **Grades**
2. View overall score and letter grade
3. See component breakdown
4. Check cohort rank
5. Click **"Recalculate"** to update scores

---

## FAQ

### General Questions

**Q: What happens if I miss the payment deadline?**
A: Your enrollment will remain in `pending_payment` status. You won't be able to access profiling or cohort materials until payment is completed.

**Q: Can I get a refund?**
A: Refund policies vary by cohort. Contact support for refund requests. Refunds are typically available within the first week of cohort start.

**Q: What if I can't attend live sessions?**
A: Live sessions are recorded and available for replay. However, participation scores may be affected.

**Q: Can I switch cohorts?**
A: Cohort switching is not typically allowed. Contact your director for exceptional circumstances.

### Payment Questions

**Q: What payment methods are accepted?**
A: We accept credit/debit cards (Visa, Mastercard), bank transfers, and mobile money (M-Pesa, Airtel Money, Orange Money) via Paystack.

**Q: Is payment recurring?**
A: No. Cohort enrollment is a one-time payment.

**Q: What currency is used?**
A: Default is USD, but local currencies may be supported depending on your region.

**Q: Is payment secure?**
A: Yes. All payments are processed through Paystack, a PCI-DSS compliant payment gateway.

### Learning Questions

**Q: Can I access materials before they unlock?**
A: No. Materials unlock based on the cohort schedule to ensure all students progress together.

**Q: What if I fall behind?**
A: You can catch up at your own pace, but be mindful of exam deadlines and cohort end date.

**Q: Can I retake exams?**
A: Exam retake policies vary by cohort. Check with your mentor or director.

**Q: How are grades calculated?**
A: Grades are weighted:
- Missions: 25%
- Capstones: 30%
- Labs: 15%
- Exams: 25%
- Participation: 5%

### Post-Cohort Questions

**Q: What happens to my materials after cohort ends?**
A: Learning materials become inaccessible. However, your skills, certificates, and grades remain on your profile.

**Q: Can I access materials from a previous cohort?**
A: No. Cohort materials are only accessible during the active cohort period.

**Q: Will my certificate expire?**
A: No. Certificates are permanent and remain on your profile.

**Q: Can employers see my cohort performance?**
A: Yes, if you enable TalentScope visibility. Employers can see your skills, certificates, and readiness score.

### Technical Questions

**Q: What if I have technical issues during an exam?**
A: Contact support immediately. Exam timers can be paused in exceptional circumstances.

**Q: Can I use mobile devices?**
A: Yes. The platform is mobile-responsive. However, exams and labs are best completed on desktop.

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, and Edge (latest versions).

**Q: What if payment verification fails?**
A: Contact support with your payment reference. We'll manually verify with Paystack.

---

## Support

### Need Help?

- **Email**: support@och.com
- **In-Platform**: Click "Support" in sidebar
- **Mentor**: Message your assigned mentor
- **Director**: Contact cohort director for program-specific questions

### Reporting Issues

1. Go to **Support** in sidebar
2. Click **"Report Issue"**
3. Describe problem
4. Attach screenshots (if applicable)
5. Submit ticket

---

## Conclusion

The OCH Cohort-Based Learning System provides a comprehensive, structured learning experience with dedicated mentorship and peer collaboration. Follow this guide to make the most of your cohort journey!

**Good luck with your learning! 🚀**
