/**
 * Community Service Client
 * Handles posts, comments, reactions, groups, and Discord-style spaces/threads/messages
 */

import { apiGateway } from './apiGateway'
import type {
  CommunityPost,
  PostComment,
  CommunityGroup,
  CommunitySpace,
  CommunityThread,
  CommunityMessage,
} from './types/community'

export const communityClient = {
  /**
   * Get community feed
   */
  async getFeed(params?: {
    group_id?: string
    page?: number
    page_size?: number
  }): Promise<{ results: CommunityPost[]; count: number }> {
    return apiGateway.get('/community/posts/feed', { params })
  },

  /**
   * Create post
   */
  async createPost(data: {
    title: string
    content: string
    group_id?: string
    tags?: string[]
  }): Promise<CommunityPost> {
    return apiGateway.post('/community/posts', data)
  },

  /**
   * Get post comments
   */
  async getComments(postId: string): Promise<PostComment[]> {
    return apiGateway.get(`/community/posts/${postId}/comments`)
  },

  /**
   * Add comment
   */
  async addComment(postId: string, data: {
    content: string
    reply_to_id?: string
  }): Promise<PostComment> {
    return apiGateway.post(`/community/posts/${postId}/comments`, data)
  },

  /**
   * React to post
   */
  async reactToPost(postId: string, emoji: string): Promise<{ detail: string }> {
    return apiGateway.post(`/community/posts/${postId}/reactions`, { emoji })
  },

  /**
   * Get user groups
   */
  async getGroups(menteeId: string): Promise<CommunityGroup[]> {
    return apiGateway.get(`/community/groups/memberships`, { params: { mentee_id: menteeId } })
  },

  /**
   * Follow user
   */
  async followUser(menteeId: string, targetUserId: string): Promise<{ detail: string }> {
    return apiGateway.post(`/community/follow`, { mentee_id: menteeId, target_user_id: targetUserId })
  },

  /**
   * Get recent posts filtered by track
   */
  async getRecentPosts(params?: {
    filter?: string
    track?: string
    page_size?: number
  }): Promise<{ results: CommunityPost[]; count: number }> {
    return apiGateway.get('/community/posts/recent', { params })
  },

  // ============================================================================
  // Discord-style Community Spaces
  // ============================================================================

  /**
   * Get community spaces for current user
   */
  async getSpaces(params?: {
    track?: string
    level?: string
    global?: boolean
  }): Promise<{ spaces: CommunitySpace[] }> {
    return apiGateway.get('/community/spaces/', { params })
  },

  /**
   * Get single space details by slug
   */
  async getSpace(spaceSlug: string): Promise<{ space: CommunitySpace }> {
    return apiGateway.get(`/community/spaces/${spaceSlug}/`)
  },

  /**
   * Join a community space
   */
  async joinSpace(spaceSlug: string): Promise<{ joined: boolean }> {
    return apiGateway.post(`/community/spaces/${spaceSlug}/join/`)
  },

  /**
   * Get space members
   */
  async getSpaceMembers(spaceSlug: string): Promise<Array<{
    id: string
    user: {
      id: string
      first_name: string
      last_name: string
      email: string
      avatar_url: string | null
      timezone?: string
      display_name?: string
    }
    role: string
    joined_at: string
  }>> {
    return apiGateway.get(`/community/spaces/${spaceSlug}/members/`)
  },

  // ============================================================================
  // Discord-style Threads
  // ============================================================================

  /**
   * Get threads for a channel
   */
  async getThreads(params: {
    channel_id: string
    type?: string
  }): Promise<CommunityThread[]> {
    return apiGateway.get('/community/threads/', { params })
  },

  /**
   * Create a new thread
   */
  async createThread(data: {
    channel: string
    title: string
    thread_type?: string
    mission_id?: string
    recipe_slug?: string
    module_id?: string
  }): Promise<CommunityThread> {
    return apiGateway.post('/community/threads/', data)
  },

  // ============================================================================
  // Discord-style Messages
  // ============================================================================

  /**
   * Get messages for a thread
   */
  async getMessages(params: {
    thread_id: string
    limit?: number
    cursor?: string
  }): Promise<{
    messages: CommunityMessage[]
    has_more: boolean
    next_cursor: string | null
    total_count: number
  }> {
    return apiGateway.get('/community/messages/', { params })
  },

  /**
   * Create a message in a thread
   */
  async createMessage(data: {
    thread: string
    body: string
    reply_to_message?: string | null
  }): Promise<CommunityMessage> {
    return apiGateway.post('/community/messages/', data)
  },

  /**
   * React to a message (toggle)
   */
  async reactToMessage(messageId: string, emoji: string): Promise<{
    reaction: 'added' | 'removed'
    emoji: string
  }> {
    return apiGateway.post(`/community/messages/${messageId}/react/`, { emoji })
  },

  /**
   * Flag a message for moderation
   */
  async flagMessage(messageId: string, reason?: string): Promise<{ flagged: boolean }> {
    return apiGateway.post(`/community/messages/${messageId}/flag/`, { reason })
  },
}

export type {
  CommunitySpace,
  CommunityThread,
  CommunityMessage,
}
