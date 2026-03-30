/**
 * Portfolio Engine - Django API Operations
 * Complete CRUD operations for portfolio items, reviews, and marketplace
 * Rewired from Supabase to Django APIs
 */

import { apiGateway } from '@/services/apiGateway';
import type {
  PortfolioItem,
  PortfolioReview,
  MarketplaceProfile,
  CreatePortfolioItemInput,
  UpdatePortfolioItemInput,
  CreateReviewInput,
  EvidenceFile,
  PortfolioHealthMetrics,
} from './types';

// ============================================================================
// PORTFOLIO ITEMS
// ============================================================================

export async function getPortfolioItems(userId: string): Promise<PortfolioItem[]> {
  const response = await apiGateway.get<{ items: PortfolioItem[] }>(
    `/student/dashboard/portfolio/${userId}`
  );
  return response.items.map(mapPortfolioItem);
}

export async function getPortfolioItem(itemId: string): Promise<PortfolioItem | null> {
  try {
    const response = await apiGateway.get<PortfolioItem>(
      `/student/dashboard/portfolio/item/${itemId}`
    );
    return mapPortfolioItem(response);
  } catch (error) {
    if ((error as any)?.status === 404) return null;
    throw error;
  }
}

export async function createPortfolioItem(
  userId: string,
  input: CreatePortfolioItemInput
): Promise<PortfolioItem> {
  const response = await apiGateway.post<PortfolioItem>(
    `/student/dashboard/portfolio/${userId}/items`,
    {
      title: input.title,
      summary: input.summary,
      type: input.type,
      missionId: input.missionId || null,
      visibility: input.visibility || 'private',
      skillTags: input.skillTags || [],
      evidenceFiles: input.evidenceFiles || [],
      status: 'draft',
    }
  );

  const portfolioItem = mapPortfolioItem(response);

  // Notify mentors and directors (non-blocking)
  import('./coordination').then(({ notifyMentorsAndDirectors }) => {
    notifyMentorsAndDirectors(userId, portfolioItem.id, portfolioItem.title).catch((err) => {
      console.error('Failed to send notifications:', err);
    });
  });

  return portfolioItem;
}

export async function updatePortfolioItem(
  itemId: string,
  input: UpdatePortfolioItemInput
): Promise<PortfolioItem> {
  const response = await apiGateway.patch<PortfolioItem>(
    `/student/dashboard/portfolio/item/${itemId}`,
    {
      ...(input.title && { title: input.title }),
      ...(input.summary && { summary: input.summary }),
      ...(input.visibility && { visibility: input.visibility }),
      ...(input.skillTags && { skillTags: input.skillTags }),
      ...(input.evidenceFiles && { evidenceFiles: input.evidenceFiles }),
      ...(input.status && { status: input.status }),
    }
  );
  return mapPortfolioItem(response);
}

export async function deletePortfolioItem(itemId: string): Promise<void> {
  await apiGateway.delete(`/student/dashboard/portfolio/item/${itemId}`);
}

export async function incrementMarketplaceViews(itemId: string): Promise<void> {
  // TODO: Implement when Django endpoint is available
  console.log('Marketplace view increment for item:', itemId);
}

// ============================================================================
// PORTFOLIO REVIEWS
// ============================================================================

export async function getPortfolioReviews(itemId: string): Promise<PortfolioReview[]> {
  // TODO: Implement when Django endpoint is available
  console.log('Fetching reviews for item:', itemId);
  return [];
}

export async function createPortfolioReview(
  input: CreateReviewInput
): Promise<PortfolioReview> {
  // TODO: Implement when Django endpoint is available
  console.log('Creating review:', input);
  throw new Error('Portfolio reviews not yet implemented in Django');
}

export async function approveReview(reviewId: string): Promise<void> {
  // TODO: Implement when Django endpoint is available
  console.log('Approving review:', reviewId);
}

// ============================================================================
// MARKETPLACE PROFILES
// ============================================================================

export async function getMarketplaceProfile(
  username: string
): Promise<MarketplaceProfile | null> {
  // TODO: Implement when Django endpoint is available
  console.log('Fetching marketplace profile for:', username);
  return null;
}

export async function getMarketplaceProfileByUserId(
  userId: string
): Promise<MarketplaceProfile | null> {
  // TODO: Implement when Django endpoint is available
  console.log('Fetching marketplace profile for user:', userId);
  return null;
}

export async function updateMarketplaceProfile(
  userId: string,
  updates: Partial<MarketplaceProfile>
): Promise<MarketplaceProfile> {
  // TODO: Implement when Django endpoint is available
  console.log('Updating marketplace profile:', userId, updates);
  throw new Error('Marketplace profiles not yet implemented in Django');
}

export async function incrementMarketplaceProfileViews(username: string): Promise<void> {
  // TODO: Implement when Django endpoint is available
  console.log('Incrementing profile views for:', username);
}

// ============================================================================
// PORTFOLIO HEALTH & METRICS
// ============================================================================

export async function getPortfolioHealthMetrics(
  userId: string
): Promise<PortfolioHealthMetrics> {
  const response = await apiGateway.get<{
    totalItems: number;
    approvedItems: number;
    pendingItems: number;
    inReviewItems: number;
    healthScore: number;
    averageScore: number;
    topSkills: Array<{ skill: string; count: number; score: number }>;
    readinessScore: number;
    readinessTrend: number;
  }>(`/student/dashboard/portfolio/${userId}/health`);

  return {
    totalItems: response.totalItems,
    approvedItems: response.approvedItems,
    pendingReviews: response.pendingItems + response.inReviewItems,
    averageScore: response.averageScore,
    healthScore: response.healthScore / 10, // Convert 0-100 to 0-10
    topSkills: response.topSkills.map(s => ({
      skill: s.skill,
      score: s.score,
      count: s.count,
    })),
  };
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function mapPortfolioItem(data: any): PortfolioItem {
  return {
    id: data.id || data.uuid,
    userId: data.userId || data.user_id,
    title: data.title,
    summary: data.summary || '',
    type: data.type || data.item_type || 'mission',
    missionId: data.missionId || data.mission_id,
    status: data.status || 'draft',
    visibility: data.visibility || 'private',
    skillTags: data.skillTags || data.skill_tags || [],
    competencyScores: data.competencyScores || data.competency_scores || {},
    evidenceFiles: data.evidenceFiles || data.evidence_files || [],
    externalProviders: data.externalProviders || data.external_providers || {},
    mentorFeedback: data.mentorFeedback || data.mentor_feedback,
    marketplaceViews: data.marketplaceViews || data.marketplace_views || 0,
    employerContacts: data.employerContacts || data.employer_contacts || 0,
    createdAt: data.createdAt || data.created_at,
    updatedAt: data.updatedAt || data.updated_at,
    approvedAt: data.approvedAt || data.approved_at,
    publishedAt: data.publishedAt || data.published_at,
  };
}

function mapPortfolioReview(data: any): PortfolioReview {
  return {
    id: data.id,
    portfolioItemId: data.portfolioItemId || data.portfolio_item_id,
    reviewerId: data.reviewerId || data.reviewer_id,
    reviewerName: data.reviewerName || data.reviewer_name,
    rubricScores: data.rubricScores || data.rubric_scores || {},
    totalScore: data.totalScore || data.total_score || 0,
    comments: data.comments || '',
    status: data.status,
    createdAt: data.createdAt || data.created_at,
    updatedAt: data.updatedAt || data.updated_at,
  };
}

function mapMarketplaceProfile(data: any): MarketplaceProfile {
  return {
    id: data.id,
    userId: data.userId || data.user_id,
    username: data.username,
    headline: data.headline || '',
    bio: data.bio || '',
    avatar: data.avatar || data.avatar_url,
    readinessScore: data.readinessScore || data.readiness_score || 0,
    portfolioHealth: data.portfolioHealth || data.portfolio_health || 0,
    isContactEnabled: data.isContactEnabled || data.is_contact_enabled || false,
    profileStatus: data.profileStatus || data.profile_status || 'foundation',
    featuredItems: [],
    skills: {},
    totalViews: data.totalViews || data.total_views || 0,
    weeklyRankChange: data.weeklyRankChange || data.weekly_rank_change || 0,
    createdAt: data.createdAt || data.created_at,
    updatedAt: data.updatedAt || data.updated_at,
  };
}

// Get marketplace rank for a user
export async function getMarketplaceRank(userId: string): Promise<number> {
  // TODO: Implement when Django endpoint is available
  console.log('Getting marketplace rank for:', userId);
  return 999;
}

// Auto-create portfolio item from mission
export async function createPortfolioItemFromMission(
  userId: string,
  missionId: string,
  files: EvidenceFile[]
): Promise<PortfolioItem> {
  return createPortfolioItem(userId, {
    title: `Mission Completion`,
    summary: `Portfolio item created from completed mission`,
    type: 'mission',
    missionId,
    visibility: 'marketplace_preview',
    evidenceFiles: files,
  });
}
