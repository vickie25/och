'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { X, CreditCard, AlertTriangle, CheckCircle2, Shield } from 'lucide-react'

interface EnhancedSubscription {
  id: string
  plan_version: {
    name: string
    price_monthly: number
    price_annual: number
  }
  status: string
  billing_cycle: 'monthly' | 'annual'
  trial_end?: string
}

interface PaymentMethodModalProps {
  subscription?: EnhancedSubscription
  onClose: () => void
  onSuccess: () => void
  onTrialConvert?: (paymentMethod: string) => Promise<void>
}

const PAYMENT_METHODS = [
  {
    id: 'card',
    name: 'Credit/Debit Card',
    description: 'Visa, Mastercard, American Express',
    icon: CreditCard,
    popular: true
  },
  {
    id: 'paystack',
    name: 'Paystack',
    description: 'Bank transfer, mobile money, cards',
    icon: CreditCard,
    popular: false
  },
  {
    id: 'bank_transfer',
    name: 'Bank Transfer',
    description: 'Direct bank transfer',
    icon: CreditCard,
    popular: false
  }
]

export default function PaymentMethodModal({ 
  subscription, 
  onClose, 
  onSuccess,
  onTrialConvert
}: PaymentMethodModalProps) {
  const [selectedMethod, setSelectedMethod] = useState('card')
  const [cardDetails, setCardDetails] = useState({
    number: '',
    expiry: '',
    cvv: '',
    name: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isTrialConversion = subscription?.status === 'TRIAL' && onTrialConvert
  const title = isTrialConversion ? 'Convert Trial to Paid Plan' : 'Update Payment Method'

  const handleSubmit = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      if (isTrialConversion && onTrialConvert) {
        await onTrialConvert(selectedMethod)
      } else {
        await apiGateway.post('/enhanced-billing/subscription/update-payment-method/', {
          payment_method: selectedMethod,
          card_details: selectedMethod === 'card' ? cardDetails : undefined
        })
      }
      onSuccess()
    } catch (err: any) {
      setError(err?.message || 'Failed to update payment method')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCardInputChange = (field: string, value: string) => {
    let formattedValue = value

    if (field === 'number') {
      // Format card number with spaces
      formattedValue = value.replace(/\s/g, '').replace(/(.{4})/g, '$1 ').trim()
      if (formattedValue.length > 19) formattedValue = formattedValue.slice(0, 19)
    } else if (field === 'expiry') {
      // Format expiry as MM/YY
      formattedValue = value.replace(/\D/g, '').replace(/(\d{2})(\d)/, '$1/$2')
      if (formattedValue.length > 5) formattedValue = formattedValue.slice(0, 5)
    } else if (field === 'cvv') {
      // Only allow numbers, max 4 digits
      formattedValue = value.replace(/\D/g, '').slice(0, 4)
    }

    setCardDetails(prev => ({ ...prev, [field]: formattedValue }))
  }

  const isCardDetailsValid = () => {
    if (selectedMethod !== 'card') return true
    return (
      cardDetails.number.replace(/\s/g, '').length >= 13 &&
      cardDetails.expiry.length === 5 &&
      cardDetails.cvv.length >= 3 &&
      cardDetails.name.trim().length > 0
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-2xl w-full">
        <div className="p-6 border-b border-och-steel/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">{title}</h2>
              <p className="text-och-steel text-sm mt-1">
                {isTrialConversion 
                  ? `Activate your ${subscription?.plan_version.name} subscription`
                  : 'Update your payment method for future billing'
                }
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <Card className="p-4 bg-red-500/10 border-red-500/30">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <p className="text-sm">{error}</p>
              </div>
            </Card>
          )}

          {/* Trial Conversion Info */}
          {isTrialConversion && subscription && (
            <Card className="p-4 bg-blue-500/10 border-blue-500/30">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-blue-400 mb-1">Trial Conversion</h3>
                  <p className="text-sm text-och-steel mb-2">
                    Your trial ends on {subscription.trial_end ? new Date(subscription.trial_end).toLocaleDateString() : 'soon'}. 
                    Add a payment method to continue with full access.
                  </p>
                  <p className="text-sm text-och-steel">
                    You'll be charged immediately and then billed {subscription.billing_cycle}ly.
                  </p>
                </div>
              </div>
            </Card>
          )}

          {/* Payment Method Selection */}
          <div>
            <h3 className="font-semibold text-white mb-3">Select Payment Method</h3>
            <div className="space-y-3">
              {PAYMENT_METHODS.map(method => {
                const Icon = method.icon
                const isSelected = selectedMethod === method.id
                
                return (
                  <Card
                    key={method.id}
                    className={`p-4 cursor-pointer transition-all ${
                      isSelected
                        ? 'border-och-mint bg-och-mint/10'
                        : 'border-och-steel/20 hover:border-och-steel/40'
                    }`}
                    onClick={() => setSelectedMethod(method.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded-full border-2 ${
                        isSelected
                          ? 'border-och-mint bg-och-mint'
                          : 'border-och-steel'
                      }`}>
                        {isSelected && (
                          <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                        )}
                      </div>
                      <Icon className="w-5 h-5 text-och-steel" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{method.name}</span>
                          {method.popular && (
                            <Badge variant="mint" className="text-xs">Popular</Badge>
                          )}
                        </div>
                        <p className="text-xs text-och-steel">{method.description}</p>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>

          {/* Card Details Form */}
          {selectedMethod === 'card' && (
            <div>
              <h3 className="font-semibold text-white mb-3">Card Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    Card Number
                  </label>
                  <input
                    type="text"
                    value={cardDetails.number}
                    onChange={(e) => handleCardInputChange('number', e.target.value)}
                    placeholder="1234 5678 9012 3456"
                    className="w-full p-3 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/60 focus:border-och-mint focus:outline-none"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">
                      Expiry Date
                    </label>
                    <input
                      type="text"
                      value={cardDetails.expiry}
                      onChange={(e) => handleCardInputChange('expiry', e.target.value)}
                      placeholder="MM/YY"
                      className="w-full p-3 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/60 focus:border-och-mint focus:outline-none"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">
                      CVV
                    </label>
                    <input
                      type="text"
                      value={cardDetails.cvv}
                      onChange={(e) => handleCardInputChange('cvv', e.target.value)}
                      placeholder="123"
                      className="w-full p-3 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/60 focus:border-och-mint focus:outline-none"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-white mb-2">
                    Cardholder Name
                  </label>
                  <input
                    type="text"
                    value={cardDetails.name}
                    onChange={(e) => handleCardInputChange('name', e.target.value)}
                    placeholder="John Doe"
                    className="w-full p-3 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/60 focus:border-och-mint focus:outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Security Notice */}
          <Card className="p-4 bg-green-500/10 border-green-500/30">
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-green-400 mt-0.5" />
              <div>
                <h4 className="font-semibold text-green-400 mb-1">Secure Payment</h4>
                <p className="text-sm text-och-steel">
                  Your payment information is encrypted and secure. We use industry-standard 
                  security measures to protect your data and never store sensitive card details.
                </p>
              </div>
            </div>
          </Card>

          {/* Billing Information */}
          {isTrialConversion && subscription && (
            <Card className="p-4 bg-och-steel/5">
              <h4 className="font-semibold text-white mb-3">Billing Summary</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-och-steel">Plan:</span>
                  <span className="text-white">{subscription.plan_version.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-och-steel">Billing:</span>
                  <span className="text-white">{subscription.billing_cycle}ly</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-och-steel">Next charge:</span>
                  <span className="text-white">Today</span>
                </div>
                <div className="border-t border-och-steel/20 pt-2 flex justify-between font-semibold">
                  <span className="text-white">Total:</span>
                  <span className="text-och-mint">
                    ${subscription.billing_cycle === 'annual' 
                      ? subscription.plan_version.price_annual 
                      : subscription.plan_version.price_monthly
                    }
                  </span>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-och-steel/20">
          <div className="flex items-center justify-end gap-3">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              variant="mint"
              onClick={handleSubmit}
              disabled={isLoading || !isCardDetailsValid()}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <CreditCard className="w-4 h-4" />
                  {isTrialConversion ? 'Activate Subscription' : 'Update Payment Method'}
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}