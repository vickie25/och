"use client"

import { Button } from "@/components/ui/Button"
import { useState, useEffect } from "react"
import { apiGateway } from "@/services/apiGateway"

const EMOJIS = ["🔥", "💯", "👏", "❤️", "😂"] as const

interface ReactionBarProps {
  reactions: Record<string, number>
  postId: string
  userId?: string
}

export function ReactionBar({ reactions, postId, userId }: ReactionBarProps) {
  const [userReactions, setUserReactions] = useState<Set<string>>(new Set())
  const [localReactions, setLocalReactions] = useState<Record<string, number>>(reactions)

  // NOTE: user-specific reaction state is not fetched here.
  // The Django API returns `user_reaction` on feed endpoints; we keep this
  // component optimistic and only sync counts with incoming props.
  useEffect(() => {
    setUserReactions(new Set())
  }, [postId, userId])

  // Sync local reactions with props
  useEffect(() => {
    setLocalReactions(reactions)
  }, [reactions])

  const toggleReaction = async (emoji: string) => {
    if (!userId) {
      // Redirect to login or show error
      return
    }

    const isReacted = userReactions.has(emoji)

    // Optimistic update
    const newUserReactions = new Set(userReactions)
    const newLocalReactions = { ...localReactions }

    if (isReacted) {
      newUserReactions.delete(emoji)
      newLocalReactions[emoji] = Math.max(0, (newLocalReactions[emoji] || 0) - 1)
    } else {
      newUserReactions.add(emoji)
      newLocalReactions[emoji] = (newLocalReactions[emoji] || 0) + 1
    }

    setUserReactions(newUserReactions)
    setLocalReactions(newLocalReactions)

    // Server update
    try {
      // Django toggles reactions; it uses `reaction_type` choices (like/love/fire...)
      // Our UI currently uses emoji strings. Map to a compatible reaction_type.
      const emojiToType: Record<string, string> = {
        "🔥": "fire",
        "💯": "insightful",
        "👏": "clap",
        "❤️": "love",
        "😂": "curious",
      }

      const reaction_type = emojiToType[emoji] || "like"
      await apiGateway.post(`/community/posts/${postId}/react/`, { reaction_type })
    } catch (e) {
      // Rollback on error
      setUserReactions(new Set())
      setLocalReactions(reactions)
    }
  }

  return (
    <div className="flex items-center gap-1">
      {EMOJIS.map((emoji) => (
        <Button
          key={emoji}
          variant="outline"
          size="sm"
          className={`h-9 px-2 text-slate-400 hover:text-slate-200 transition-all ${
            userReactions.has(emoji)
              ? "bg-indigo-500/20 text-indigo-400 scale-110 shadow-md shadow-indigo-500/25"
              : ""
          }`}
          onClick={() => toggleReaction(emoji)}
        >
          <span className="text-lg">{emoji}</span>
          {localReactions[emoji] > 0 && (
            <span className="ml-1 text-xs font-mono tabular-nums">
              {localReactions[emoji]}
            </span>
          )}
        </Button>
      ))}
    </div>
  )
}

