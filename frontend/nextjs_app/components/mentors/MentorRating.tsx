"use client";

import React, { useState } from 'react';
import { Star, MessageSquare, Award, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface MentorRatingProps {
  mentorId: string;
  mentorName: string;
  onSubmit: (rating: number, review: string) => Promise<void>;
}

export function MentorRating({ mentorId, mentorName, onSubmit }: MentorRatingProps) {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [review, setReview] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit(rating, review);
      setSubmitted(true);
    } catch (error) {
      console.error('Failed to submit rating:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCreditValue = (stars: number) => {
    const credits = { 5: 10, 4: 8, 3: 6, 2: 4, 1: 2 };
    return credits[stars as keyof typeof credits] || 0;
  };

  if (submitted) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="pt-6 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Thank You!</h3>
          <p className="text-muted-foreground">
            Your rating has been submitted. {mentorName} received {getCreditValue(rating)} credits!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="w-5 h-5" />
          Rate Your Mentor
        </CardTitle>
        <CardDescription>
          Rate {mentorName} to award them credits they can use for courses, certificates, and more.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Star Rating */}
        <div className="flex flex-col items-center gap-2">
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className="p-1 transition-transform hover:scale-110 focus:outline-none"
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(star)}
              >
                <Star
                  className={cn(
                    "w-8 h-8 transition-colors",
                    (hoverRating || rating) >= star
                      ? "fill-yellow-400 text-yellow-400"
                      : "text-gray-300"
                  )}
                />
              </button>
            ))}
          </div>
          
          {rating > 0 && (
            <p className="text-sm text-muted-foreground">
              {rating} stars = {getCreditValue(rating)} credits for {mentorName}
            </p>
          )}
        </div>

        {/* Review Text */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Written Review (Optional)
          </label>
          <Textarea
            placeholder="Share your experience with this mentor..."
            value={review}
            onChange={(e) => setReview(e.target.value)}
            rows={3}
          />
        </div>

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={rating === 0 || isSubmitting}
          className="w-full"
        >
          {isSubmitting ? 'Submitting...' : `Submit Rating & Award ${getCreditValue(rating)} Credits`}
        </Button>

        {/* Credit Values Legend */}
        <div className="pt-4 border-t">
          <p className="text-xs text-muted-foreground text-center">
            Credit values: 5★ = 10 credits | 4★ = 8 credits | 3★ = 6 credits | 2★ = 4 credits | 1★ = 2 credits
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

interface MentorCreditsDisplayProps {
  credits: {
    current_balance: number;
    total_earned: number;
    total_redeemed: number;
  };
  recentTransactions: Array<{
    id: string;
    type: 'earned' | 'redeemed';
    amount: number;
    description: string;
    created_at: string;
  }>;
}

export function MentorCreditsDisplay({ credits, recentTransactions }: MentorCreditsDisplayProps) {
  return (
    <Card className="w-full max-w-lg mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Award className="w-5 h-5 text-yellow-500" />
          Your Credits
        </CardTitle>
        <CardDescription>
          Earn credits from student ratings and redeem them for rewards
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Credit Balance */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-primary/10 rounded-lg">
            <p className="text-2xl font-bold text-primary">{credits.current_balance}</p>
            <p className="text-xs text-muted-foreground">Available</p>
          </div>
          <div className="p-3 bg-green-100 rounded-lg">
            <p className="text-2xl font-bold text-green-600">{credits.total_earned}</p>
            <p className="text-xs text-muted-foreground">Total Earned</p>
          </div>
          <div className="p-3 bg-blue-100 rounded-lg">
            <p className="text-2xl font-bold text-blue-600">{credits.total_redeemed}</p>
            <p className="text-xs text-muted-foreground">Redeemed</p>
          </div>
        </div>

        {/* Recent Transactions */}
        {recentTransactions.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Recent Activity</h4>
            <div className="space-y-2">
              {recentTransactions.slice(0, 5).map((tx) => (
                <div
                  key={tx.id}
                  className={cn(
                    "flex items-center justify-between p-2 rounded text-sm",
                    tx.type === 'earned' ? "bg-green-50" : "bg-blue-50"
                  )}
                >
                  <div className="flex items-center gap-2">
                    {tx.type === 'earned' ? (
                      <Award className="w-4 h-4 text-green-500" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-blue-500" />
                    )}
                    <span className="text-muted-foreground">{tx.description}</span>
                  </div>
                  <span className={cn(
                    "font-medium",
                    tx.type === 'earned' ? "text-green-600" : "text-blue-600"
                  )}>
                    {tx.type === 'earned' ? '+' : ''}{tx.amount}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Redemption Options */}
        <div className="pt-4 border-t">
          <h4 className="text-sm font-medium mb-3">Redeem Credits For:</h4>
          <div className="grid grid-cols-2 gap-2">
            {[
              { type: 'course', name: 'Course', cost: 50 },
              { type: 'certificate', name: 'Certificate', cost: 30 },
              { type: 'badge', name: 'Badge', cost: 20 },
              { type: 'priority', name: 'Priority Matching', cost: 40 },
            ].map((option) => (
              <Button
                key={option.type}
                variant="outline"
                size="sm"
                disabled={credits.current_balance < option.cost}
                className="justify-between"
              >
                <span>{option.name}</span>
                <span className="text-xs text-muted-foreground">{option.cost} cr</span>
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
