/**
 * Account Creation Page - Students create their own password
 * No credentials sent via email
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiGateway } from '@/services/apiGateway';
import { Shield, Lock, Mail, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export default function CreateAccountPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(true);
  const [error, setError] = useState('');
  const [applicationData, setApplicationData] = useState(null);
  const [passwordStrength, setPasswordStrength] = useState(0);

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setError('No token provided. Please use the link from your email.');
      setIsVerifying(false);
    }
  }, [token]);

  useEffect(() => {
    calculatePasswordStrength();
  }, [password]);

  const verifyToken = async () => {
    try {
      setIsVerifying(true);
      const response = await apiGateway.get(`/programs/onboarding/verify-token?token=${token}`);
      
      if (response.valid) {
        setApplicationData(response);
      } else {
        setError('Invalid or expired link. Please contact support.');
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Invalid or expired link. Please contact support.');
    } finally {
      setIsVerifying(false);
    }
  };

  const calculatePasswordStrength = () => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (password.length >= 12) strength += 25;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 25;
    if (/\d/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 10;
    setPasswordStrength(Math.min(strength, 100));
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength < 40) return 'bg-och-defender';
    if (passwordStrength < 70) return 'bg-och-orange';
    return 'bg-och-mint';
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength < 40) return 'Weak';
    if (passwordStrength < 70) return 'Medium';
    return 'Strong';
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
      const response = await apiGateway.post('/programs/onboarding/create-account', {
        token,
        password
      });
      
      // Redirect to payment page
      router.push(`/cohorts/payment?enrollment_id=${response.enrollment_id}`);
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to create account. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isVerifying) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">
            Verifying your link...
          </p>
        </div>
      </div>
    );
  }

  if (error && !applicationData) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center">
          <AlertCircle className="w-16 h-16 text-och-defender mx-auto mb-4" />
          <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-4">
            Invalid Link
          </h1>
          <p className="text-och-steel mb-8">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="px-8 py-4 bg-och-gold text-black font-black uppercase tracking-widest rounded-2xl hover:bg-och-gold/90 transition-all"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-20 h-20 rounded-2xl bg-och-gold/10 border border-och-gold/30 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-10 h-10 text-och-gold" />
          </div>
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-2">
            Create Your Account
          </h1>
          <p className="text-och-steel text-lg">
            Welcome to {applicationData?.cohort_name}
          </p>
        </div>

        {/* Payment Deadline Warning */}
        {applicationData?.payment_deadline && (
          <div className="mb-6 p-4 bg-och-defender/10 border border-och-defender/30 rounded-2xl flex items-start gap-3">
            <Clock className="w-5 h-5 text-och-defender shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-bold text-och-defender mb-1">
                Payment Deadline
              </p>
              <p className="text-xs text-och-steel">
                Complete payment by {new Date(applicationData.payment_deadline).toLocaleString()} 
                to secure your spot in the cohort.
              </p>
            </div>
          </div>
        )}

        {/* Main Form */}
        <div className="bg-och-midnight/60 border border-och-steel/10 rounded-3xl p-8">
          
          {error && (
            <div className="bg-och-defender/10 border border-och-defender/30 rounded-xl p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-och-defender shrink-0 mt-0.5" />
              <p className="text-och-defender text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            
            {/* Email (Read-only) */}
            <div>
              <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-och-steel/50" />
                <input
                  type="email"
                  value={applicationData?.email || ''}
                  disabled
                  className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 pl-12 pr-4 text-white"
                />
              </div>
              <p className="text-xs text-och-steel mt-2">
                This is your login email. You cannot change it.
              </p>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
                Create Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-och-steel/50" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (min 8 characters)"
                  className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 pl-12 pr-4 text-white focus:border-och-gold/50 outline-none transition-all"
                  required
                />
              </div>
              
              {/* Password Strength */}
              {password && (
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-och-steel">Password Strength:</span>
                    <span className={`text-xs font-bold ${
                      passwordStrength < 40 ? 'text-och-defender' :
                      passwordStrength < 70 ? 'text-och-orange' :
                      'text-och-mint'
                    }`}>
                      {getPasswordStrengthText()}
                    </span>
                  </div>
                  <div className="h-2 bg-och-midnight/80 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-300 ${getPasswordStrengthColor()}`}
                      style={{ width: `${passwordStrength}%` }}
                    />
                  </div>
                </div>
              )}
              
              <div className="mt-3 space-y-1">
                <p className="text-xs text-och-steel flex items-center gap-2">
                  <CheckCircle className={`w-3 h-3 ${password.length >= 8 ? 'text-och-mint' : 'text-och-steel/30'}`} />
                  At least 8 characters
                </p>
                <p className="text-xs text-och-steel flex items-center gap-2">
                  <CheckCircle className={`w-3 h-3 ${/[A-Z]/.test(password) && /[a-z]/.test(password) ? 'text-och-mint' : 'text-och-steel/30'}`} />
                  Upper and lowercase letters
                </p>
                <p className="text-xs text-och-steel flex items-center gap-2">
                  <CheckCircle className={`w-3 h-3 ${/\d/.test(password) ? 'text-och-mint' : 'text-och-steel/30'}`} />
                  At least one number
                </p>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-xs font-black text-och-steel uppercase tracking-widest mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-och-steel/50" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full bg-och-midnight/80 border border-och-steel/20 rounded-xl py-3 pl-12 pr-4 text-white focus:border-och-gold/50 outline-none transition-all"
                  required
                />
              </div>
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-och-defender mt-2 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  Passwords do not match
                </p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || password !== confirmPassword || password.length < 8}
              className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-4 hover:bg-och-gold/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  Creating Account...
                </>
              ) : (
                'Create Account & Continue to Payment'
              )}
            </button>
          </form>

          {/* Next Steps Info */}
          <div className="mt-8 p-4 bg-och-mint/5 border border-och-mint/20 rounded-xl">
            <p className="text-xs text-och-steel mb-3">
              <strong className="text-och-mint">What happens next:</strong>
            </p>
            <ol className="text-xs text-och-steel space-y-2 list-decimal list-inside">
              <li>Your account will be created</li>
              <li>You'll be redirected to the payment page</li>
              <li>Complete payment (${applicationData?.enrollment_fee || 100})</li>
              <li>Access profiling and start learning!</li>
            </ol>
          </div>
        </div>

        {/* Support */}
        <div className="mt-6 text-center">
          <p className="text-xs text-och-steel">
            Need help? Contact{' '}
            <a href="mailto:support@och.com" className="text-och-gold hover:underline">
              support@och.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
