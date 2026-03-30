/**
 * Portfolio Coordination Module
 * Handles sync between Portfolio, Settings, Missions, and Coaching
 * Rewired from Supabase to Django APIs
 */

import { apiGateway } from '@/services/apiGateway';
import type { PortfolioItem, PortfolioVisibility } from './types';

/**
 * Sync portfolio items visibility when settings change
 */
export async function syncPortfolioVisibility(
  userId: string,
  newVisibility: PortfolioVisibility
): Promise<void> {
  try {
    // TODO: Implement when Django endpoint supports bulk visibility update
    console.log('Syncing portfolio visibility for user:', userId, 'to:', newVisibility);
  } catch (error) {
    console.error('Error syncing portfolio visibility:', error);
    throw error;
  }
}

/**
 * Check if mission should create portfolio item (85% threshold)
 */
export function shouldCreatePortfolioItem(missionScore: number): boolean {
  return missionScore >= 85;
}

/**
 * Create portfolio item from completed mission
 */
export async function createPortfolioFromMission(
  userId: string,
  missionId: string,
  missionData: {
    title: string;
    summary?: string;
    score: number;
    skills?: string[];
    files?: any[];
  }
): Promise<PortfolioItem | null> {
  // Only create if score meets threshold
  if (!shouldCreatePortfolioItem(missionData.score)) {
    return null;
  }

  try {
    const { createPortfolioItem } = await import('./api');
    const item = await createPortfolioItem(userId, {
      title: `Mission: ${missionData.title}`,
      summary: missionData.summary || 'Auto-imported from completed mission',
      type: 'mission',
      missionId,
      visibility: 'private',
      skillTags: missionData.skills || [],
      evidenceFiles: missionData.files || [],
    });

    return item;
  } catch (error) {
    console.error('Error creating portfolio from mission:', error);
    return null;
  }
}

/**
 * Get portfolio items for coaching recommendations
 */
export async function getPortfolioForCoaching(userId: string): Promise<{
  totalItems: number;
  approvedItems: number;
  recentItems: PortfolioItem[];
  topSkills: string[];
}> {
  try {
    const { getPortfolioItems, getPortfolioHealthMetrics } = await import('./api');
    const [items, health] = await Promise.all([
      getPortfolioItems(userId),
      getPortfolioHealthMetrics(userId),
    ]);

    const approvedItems = items.filter(item => item.status === 'approved');
    const topSkills = health.topSkills.map(s => s.skill).slice(0, 5);

    return {
      totalItems: items.length,
      approvedItems: approvedItems.length,
      recentItems: items.slice(0, 5),
      topSkills,
    };
  } catch (error) {
    console.error('Error fetching portfolio for coaching:', error);
    return {
      totalItems: 0,
      approvedItems: 0,
      recentItems: [],
      topSkills: [],
    };
  }
}

/**
 * Update portfolio health when items change
 */
export async function updatePortfolioHealth(userId: string): Promise<void> {
  try {
    // Portfolio health is recalculated on-demand in Django
    console.log('Portfolio health updated for user:', userId);
  } catch (error) {
    console.error('Error updating portfolio health:', error);
  }
}

/**
 * Notify mentors and directors when a portfolio item is created
 * Calls Django API endpoint to handle notifications (mentors and directors)
 */
export async function notifyMentorsAndDirectors(
  userId: string,
  portfolioItemId: string,
  portfolioItemTitle: string
): Promise<void> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL;

    // Call Django API to handle notifications
    const response = await fetch(`${apiUrl}/api/v1/portfolio/notify-item-created`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        portfolio_item_id: portfolioItemId,
        portfolio_item_title: portfolioItemTitle,
      }),
    });

    if (!response.ok) {
      console.warn('Failed to send notifications via API:', response.statusText);
    } else {
      console.log(`Notifications sent for portfolio item ${portfolioItemId}`);
    }
  } catch (error) {
    console.error('Error sending notifications to mentors and directors:', error);
    // Don't throw - notifications are non-critical
  }
}
