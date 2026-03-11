/**
 * Payment Page with Countdown Timer
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiGateway } from '@/services/apiGateway';
import { Clock, CreditCard, AlertTriangle, CheckCircle, Shield } from 'lucide-react';

export default function PaymentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const enrollmentId = searchParams.get('enrollment_id');
  
  const [enrollment, setEnrollment] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFetching, setIsFetching] = useState(true);

  useEffect(() => {
    if (enrollmentId) {
      fetchEnrollmentData();
    }
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
      setIsFetching(true);
      const response = await apiGateway.get(`/programs/enrollments/${enrollmentId}`);
      setEnrollment(response);
    } catch (error) {
      setError('Failed to load enrollment data');
    } finally {
      setIsFetching(false);
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
      const response = await apiGateway.post('/cohorts/payment/initiate/', {
        enrollment_id: enrollmentId,
        callback_url: `${window.location.origin}/cohorts/payment/verify`
      });
      
      window.location.href = response.authorization_url;
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to initialize payment');
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetching) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">
            Loading payment details...
          </p>
        </div>
      </div>
    );
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
          </p>
          <button
            onClick={() => router.push('/')}
            className="w-full px-8 py-4 bg-och-gold text-black font-black uppercase tracking-widest rounded-2xl"
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
        
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-och-gold/10 border border-och-gold/30 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-10 h-10 text-och-gold" />
          </div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-2">
            Complete Your Enrollment
          </h1>
          <p className="text-och-steel text-lg">
            {enrollment?.cohort_name}
          </p>
        </div>

        <div className="mb-8 p-6 bg-och-defender/10 border border-och-defender/30 rounded-3xl">
          <div className="flex items-center gap-4 mb-6">
            <Clock className="w-6 h-6 text-och-defender" />
            <div>
              <h2 className="text-xl font-black text-white uppercase tracking-tighter">
                Payment Deadline
              </h2>
              <p className="text-sm text-och-steel">
                Complete payment before time runs out
              </p>
            </div>
          </div>
          
          {timeRemaining && !timeRemaining.expired && (
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-och-midnight/60 rounded-2xl border border-och-defender/20">
                <div className="text-5xl font-black text-och-defender mb-2">
                  {timeRemaining.days}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Days</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-2xl border border-och-defender/20">
                <div className="text-5xl font-black text-och-defender mb-2">
                  {String(timeRemaining.hours).padStart(2, '0')}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Hours</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-2xl border border-och-defender/20">
                <div className="text-5xl font-black text-och-defender mb-2">
                  {String(timeRemaining.minutes).padStart(2, '0')}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Minutes</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-2xl border border-och-defender/20">
                <div className="text-5xl font-black text-och-defender mb-2">
                  {String(timeRemaining.seconds).padStart(2, '0')}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Seconds</div>
              </div>
            </div>
          )}
        </div>

        <div className="bg-och-midnight/60 border border-och-steel/10 rounded-3xl p-8">
          <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-6">
            Payment Details
          </h2>

          <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center p-4 bg-och-gold/10 border border-och-gold/30 rounded-xl">
              <span className="text-och-gold font-black text-lg">Enrollment Fee:</span>
              <span className="text-white font-black text-3xl">
                ${enrollment?.amount || 100}
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
            className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-5 hover:bg-och-gold/90 transition-all disabled:opacity-50 flex items-center justify-center gap-3 text-lg"
          >
            {isLoading ? (
              <>
                <div className="w-6 h-6 border-3 border-black/30 border-t-black rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <CreditCard className="w-6 h-6" />
                Pay with Paystack
              </>
            )}
          </button>

          <div className="mt-8 p-6 bg-och-mint/5 border border-och-mint/20 rounded-xl">
            <p className="text-xs font-black text-och-mint uppercase tracking-widest mb-4">
              Accepted Payment Methods
            </p>
            <div className="grid grid-cols-2 gap-3 text-xs text-och-steel">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-och-mint" />
                Credit/Debit Cards
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-och-mint" />
                Bank Transfer
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-och-mint" />
                Mobile Money
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
