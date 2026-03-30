/**
 * Settings Engine - API Operations
 * Master control API for user settings
 * Rewired from Supabase to Django APIs
 */

import { apiGateway } from '@/services/apiGateway';
import { calculateProfileCompleteness } from './profile-completeness';
import type { UserSettings, UserEntitlements, SettingsUpdate } from './types';

/**
 * Get user settings
 */
export async function getUserSettings(userId: string): Promise<UserSettings | null> {
  try {
    const response = await apiGateway.get<{
      communityDisplayName?: string;
      country?: string;
      timezone?: string;
      profile_completeness?: number;
      avatar_uploaded?: boolean;
      linkedin_linked?: boolean;
      bio_completed?: boolean;
      name?: string;
      headline?: string;
      location?: string;
      track?: string;
      timezone_set?: string;
      language_preference?: string;
      portfolio_visibility?: string;
      marketplace_contact_enabled?: boolean;
      data_sharing_consent?: Record<string, any>;
      notifications_email?: boolean;
      notifications_push?: boolean;
      notifications_categories?: Record<string, boolean>;
      ai_coach_style?: string;
      habit_frequency?: string;
      reflection_prompt_style?: string;
      integrations?: Record<string, any>;
      two_factor_enabled?: boolean;
      active_sessions?: any[];
      created_at?: string;
      updated_at?: string;
    }>('/settings/');

    return mapUserSettings(response);
  } catch (error) {
    if ((error as any)?.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Update user settings
 */
export async function updateUserSettings(
  userId: string,
  updates: SettingsUpdate,
  hasPortfolioItems?: boolean
): Promise<UserSettings> {
  // Get current settings to calculate new completeness
  const currentSettings = await getUserSettings(userId);
  if (!currentSettings) throw new Error('Settings not found');

  // Merge updates with current settings
  const mergedSettings = { ...currentSettings, ...updates };

  // Check portfolio items if not provided
  let hasItems = hasPortfolioItems;
  if (hasItems === undefined) {
    try {
      const { getPortfolioHealthMetrics } = await import('../portfolio/api');
      const health = await getPortfolioHealthMetrics(userId);
      hasItems = health.approvedItems > 0;
    } catch {
      hasItems = false;
    }
  }

  // Recalculate profile completeness
  const newCompleteness = calculateProfileCompleteness(mergedSettings, hasItems);

  // Build update payload
  const payload = mapToApiFormat(updates);
  payload.profile_completeness = newCompleteness;

  const response = await apiGateway.patch('/settings/', payload);
  return mapUserSettings(response);
}

/**
 * Get user entitlements
 */
export async function getUserEntitlements(userId: string): Promise<UserEntitlements | null> {
  // TODO: Implement when Django endpoint is available
  console.log('Fetching entitlements for user:', userId);
  return null;
}

/**
 * Map API response to UserSettings interface
 */
function mapUserSettings(data: any): UserSettings {
  return {
    userId: data.user_id || '',
    profileCompleteness: data.profile_completeness || 0,
    avatarUploaded: data.avatar_uploaded || false,
    linkedinLinked: data.linkedin_linked || false,
    bioCompleted: data.bio_completed || false,
    name: data.name,
    headline: data.headline,
    location: data.location,
    track: data.track || 'defender',
    timezoneSet: data.timezone_set || data.timezone || 'Africa/Nairobi',
    languagePreference: data.language_preference || 'en',
    portfolioVisibility: data.portfolio_visibility || 'private',
    marketplaceContactEnabled: data.marketplace_contact_enabled || false,
    dataSharingConsent: data.data_sharing_consent || {},
    notificationsEmail: data.notifications_email !== false,
    notificationsPush: data.notifications_push !== false,
    notificationsCategories: data.notifications_categories || {
      missions: true,
      coaching: true,
      mentor: true,
      marketplace: true,
    },
    aiCoachStyle: data.ai_coach_style || 'motivational',
    habitFrequency: data.habit_frequency || 'daily',
    reflectionPromptStyle: data.reflection_prompt_style || 'guided',
    integrations: data.integrations || {},
    twoFactorEnabled: data.two_factor_enabled || false,
    activeSessions: data.active_sessions || [],
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

function mapUserEntitlements(data: any): UserEntitlements {
  return {
    userId: data.user_id,
    profileCompleteness: data.profile_completeness || 0,
    tier: data.tier || 'free',
    subscriptionStatus: data.subscription_status || 'inactive',
    enhancedAccessUntil: data.enhanced_access_until,
    marketplaceFullAccess: data.marketplace_full_access || false,
    aiCoachFullAccess: data.ai_coach_full_access || false,
    mentorAccess: data.mentor_access || false,
    portfolioExportEnabled: data.portfolio_export_enabled || false,
  };
}

function mapToApiFormat(updates: SettingsUpdate): any {
  const apiFormat: any = {};

  if (updates.profileCompleteness !== undefined) apiFormat.profile_completeness = updates.profileCompleteness;
  if (updates.avatarUploaded !== undefined) apiFormat.avatar_uploaded = updates.avatarUploaded;
  if (updates.linkedinLinked !== undefined) apiFormat.linkedin_linked = updates.linkedinLinked;
  if (updates.bioCompleted !== undefined) apiFormat.bio_completed = updates.bioCompleted;
  if (updates.name !== undefined) apiFormat.name = updates.name;
  if (updates.headline !== undefined) apiFormat.headline = updates.headline;
  if (updates.location !== undefined) apiFormat.location = updates.location;
  if (updates.track !== undefined) apiFormat.track = updates.track;
  if (updates.timezoneSet !== undefined) apiFormat.timezone_set = updates.timezoneSet;
  if (updates.languagePreference !== undefined) apiFormat.language_preference = updates.languagePreference;
  if (updates.portfolioVisibility !== undefined) apiFormat.portfolio_visibility = updates.portfolioVisibility;
  if (updates.marketplaceContactEnabled !== undefined) apiFormat.marketplace_contact_enabled = updates.marketplaceContactEnabled;
  if (updates.dataSharingConsent !== undefined) apiFormat.data_sharing_consent = updates.dataSharingConsent;
  if (updates.notificationsEmail !== undefined) apiFormat.notifications_email = updates.notificationsEmail;
  if (updates.notificationsPush !== undefined) apiFormat.notifications_push = updates.notificationsPush;
  if (updates.notificationsCategories !== undefined) apiFormat.notifications_categories = updates.notificationsCategories;
  if (updates.aiCoachStyle !== undefined) apiFormat.ai_coach_style = updates.aiCoachStyle;
  if (updates.habitFrequency !== undefined) apiFormat.habit_frequency = updates.habitFrequency;
  if (updates.reflectionPromptStyle !== undefined) apiFormat.reflection_prompt_style = updates.reflectionPromptStyle;
  if (updates.integrations !== undefined) apiFormat.integrations = updates.integrations;
  if (updates.twoFactorEnabled !== undefined) apiFormat.two_factor_enabled = updates.twoFactorEnabled;

  return apiFormat;
}
