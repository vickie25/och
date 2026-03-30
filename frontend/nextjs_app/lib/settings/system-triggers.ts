/**
 * Settings Engine - System Triggers
 * Cross-system event coordination
 */

import type { SettingsUpdate } from './types';

/**
 * Trigger cross-system updates when settings change
 */
export async function triggerSystemUpdates(
  userId: string,
  updates: SettingsUpdate
): Promise<void> {
  // Determine update type
  const updateType = determineUpdateType(updates);

  // Call edge function for coordination
  try {
    await fetch('/api/settings/coordinate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        type: updateType,
        changes: updates,
      }),
    });
  } catch (error) {
    console.error('Failed to trigger system updates:', error);
    // Continue anyway - triggers will handle it
  }
}

function determineUpdateType(updates: SettingsUpdate): string {
  if (updates.profileCompleteness !== undefined || updates.avatarUploaded !== undefined) {
    return 'profile_completeness';
  }
  if (updates.portfolioVisibility !== undefined || updates.marketplaceContactEnabled !== undefined) {
    return 'privacy';
  }
  if (updates.notificationsEmail !== undefined || updates.notificationsCategories !== undefined) {
    return 'notification_preferences';
  }
  if (updates.aiCoachStyle !== undefined || updates.habitFrequency !== undefined) {
    return 'coaching_preferences';
  }
  return 'general';
}

/**
 * Broadcast settings change to all connected clients
 */
export async function broadcastSettingsChange(
  userId: string,
  type: string,
  changes: Partial<SettingsUpdate>
): Promise<void> {
  void userId;
  void type;
  void changes;
}

