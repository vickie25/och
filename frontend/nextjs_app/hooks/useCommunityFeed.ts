"use client"

import { useEffect, useState, useCallback } from "react"
import { apiGateway } from "@/services/apiGateway"
import type {
  CommunityPost,
  Community,
  University,
  CreatePostData,
} from "@/types/community"

export function useCommunityFeed(userId: string) {
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [universities, setUniversities] = useState<University[]>([])
  const [currentUniversity, setCurrentUniversity] = useState<University | null>(null)
  const [communities, setCommunities] = useState<Community[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'my-university' | 'global' | 'competitions' | 'leaderboard'>('my-university')

  const fetchUserPrimaryUniversity = useCallback(async () => {
    try {
      const memberships = await apiGateway.get<any[]>(`/community/memberships/`)
      const primary = memberships?.find((m) => m.is_primary)
      if (primary?.university) {
        setCurrentUniversity(primary.university as University)
      } else {
        setCurrentUniversity(null)
      }
    } catch {
      setCurrentUniversity(null)
    }
  }, [])

  // Fetch initial data
  const fetchInitialData = useCallback(async () => {
    if (!userId) return

    setLoading(true)
    setError(null)

    try {
      await fetchUserPrimaryUniversity()

      const universitiesResp = await apiGateway.get<any[]>(`/community/universities/?country=KE`)
      setUniversities((universitiesResp || []) as University[])

      const feedType = activeTab === 'my-university'
        ? 'my-university'
        : activeTab

      const feedResp = await apiGateway.get<any>(`/community/feed/?feed_type=${encodeURIComponent(feedType)}`)
      const apiPosts: any[] = feedResp?.posts || []

      const mappedPosts: CommunityPost[] = apiPosts.map((p) => {
        const author = p.author || {}
        const reactionType = p.user_reaction
        const reactions: Record<string, number> = {}
        if (reactionType) {
          reactions[reactionType] = 1
        }

        return {
          id: p.id,
          community_id: p.university_code || (p.visibility === 'global' ? 'global' : 'university'),
          user_id: author.id,
          post_type: p.post_type,
          title: p.title || undefined,
          content: p.content,
          media_urls: p.media_urls || undefined,
          event_details: p.event_details || undefined,
          poll_options: p.poll_options || undefined,
          achievement_data: p.achievement_data || undefined,
          tags: p.tags || [],
          status: p.status,
          view_count: p.view_count || 0,
          reaction_count: p.reaction_count || 0,
          comment_count: p.comment_count || 0,
          pinned_by: undefined,
          pinned_at: p.pinned_at || undefined,
          created_at: p.created_at,
          updated_at: p.updated_at || p.created_at,
          user_name: author.display_name || `${author.first_name || ''} ${author.last_name || ''}`.trim() || author.email || 'Anonymous',
          user_avatar: author.avatar_url || undefined,
          user_circle: undefined,
          university_name: p.university_name || undefined,
          university_logo: p.university_logo || undefined,
          reactions,
        }
      })

      setPosts(mappedPosts)
    } catch (err: any) {
      setError(err.message || "Failed to fetch data")
    } finally {
      setLoading(false)
    }
  }, [userId, activeTab, fetchUserPrimaryUniversity])

  // Fetch data when tab changes
  useEffect(() => {
    fetchInitialData()
  }, [fetchInitialData])

  // Create post
  const createPost = useCallback(async (postData: CreatePostData) => {
    try {
      // Determine visibility based on active tab (university vs global)
      const visibility = activeTab === 'global' ? 'global' : 'university'

      // For university posts, attach the user's primary university
      let universityId: string | null = null
      if (visibility === 'university') {
        const memberships = await apiGateway.get<any[]>(`/community/memberships/`)
        const primary = memberships?.find((m) => m.is_primary)
        universityId = primary?.university?.id || null
      }

      await apiGateway.post(`/community/posts/`, {
        post_type: postData.post_type,
        title: postData.title,
        content: postData.content,
        media_urls: postData.media_urls || [],
        visibility,
        tags: postData.tags || [],
        university_id: universityId,
        event_details: postData.event_details,
        poll_options: postData.poll_options,
        achievement_type: (postData as any).achievement_type,
        achievement_data: postData.achievement_data,
      })

      await fetchInitialData()
      return null
    } catch (err: any) {
      throw new Error(err.message || "Failed to create post")
    }
  }, [activeTab, fetchInitialData])

  return {
    posts,
    universities,
    currentUniversity,
    communities,
    loading,
    error,
    createPost,
    activeTab,
    setActiveTab,
    refetch: fetchInitialData,
  }
}

