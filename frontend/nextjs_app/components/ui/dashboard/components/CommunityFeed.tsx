/**
 * Community Feed Component
 * Displays trending intelligence and achievements from local or global feeds.
 */

'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, Heart, Share2, MoreHorizontal, User, Zap, Star, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { useCommunityFeed } from '@/hooks/useCommunityFeed';
import { useAuth } from '@/hooks/useAuth';
import clsx from 'clsx';

export function CommunityFeed({ type }: { type: 'university' | 'global' }) {
  const { user } = useAuth();
  const { posts, loading, error, activeTab, setActiveTab, refetch } = useCommunityFeed(String(user?.id || ''));

  // Sync activeTab with prop type
  useEffect(() => {
    const targetTab = type === 'university' ? 'my-university' : 'global';
    if (activeTab !== targetTab) {
      setActiveTab(targetTab as 'my-university' | 'global' | 'competitions' | 'leaderboard');
    }
  }, [type, activeTab, setActiveTab]);

  // Refetch when tab changes
  useEffect(() => {
    refetch();
  }, [type, refetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 text-och-gold animate-spin" />
        <span className="ml-2 text-sm text-och-steel">Loading feed...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-sm">
        <p>Failed to load feed: {error}</p>
        <button 
          onClick={refetch}
          className="mt-2 text-xs underline hover:text-white"
        >
          Try again
        </button>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="p-6 rounded-[2rem] bg-och-steel/5 border border-white/5 text-center">
        <p className="text-sm text-och-steel">
          No posts yet in {type === 'university' ? 'your university' : 'global'} feed.
        </p>
        <p className="text-xs text-och-steel/60 mt-1">
          Be the first to share something!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <AnimatePresence mode="popLayout">
        {posts.map((post) => (
          <motion.div
            key={`${type}-${post.id}`}
            layout
            initial={{ opacity: 0, x: type === 'university' ? -20 : 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={clsx(
              "p-6 rounded-[2rem] bg-och-steel/5 border border-white/5 hover:border-white/10 transition-all group",
              post.post_type === 'announcement' && "bg-gradient-to-r from-och-mint/5 to-transparent border-och-mint/10"
            )}
          >
            <div className="flex justify-between items-start mb-4">
               <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-och-midnight border border-white/10 flex items-center justify-center overflow-hidden">
                     {post.user_avatar ? (
                       <img src={post.user_avatar} alt={post.user_name} className="w-full h-full object-cover" />
                     ) : (
                       <User className="w-5 h-5 text-och-steel" />
                     )}
                  </div>
                  <div>
                     <div className="flex items-center gap-2">
                        <h5 className="text-xs font-black text-white uppercase tracking-tight leading-none">{post.user_name}</h5>
                        {post.is_verified && <Zap className="w-3 h-3 text-och-gold" />}
                     </div>
                     <p className="text-[9px] text-och-steel font-black uppercase tracking-widest mt-1">
                        {post.user_circle ? `${post.user_circle} • ` : ''}{post.university_name || (type === 'global' ? 'Global' : 'University')}
                     </p>
                  </div>
               </div>
               <button className="text-och-steel hover:text-white transition-colors">
                  <MoreHorizontal className="w-4 h-4" />
               </button>
            </div>

            {post.title && (
              <h4 className="text-sm font-bold text-white mb-2">{post.title}</h4>
            )}

            <p className="text-xs text-slate-300 leading-relaxed mb-4">
               {post.content}
            </p>

            {post.media_urls && post.media_urls.length > 0 && (
              <div className="mb-4 rounded-xl overflow-hidden">
                <img 
                  src={post.media_urls[0]} 
                  alt="Post media" 
                  className="w-full h-48 object-cover"
                />
              </div>
            )}

            <div className="flex flex-wrap gap-2 mb-6">
               {post.tags?.map(tag => (
                 <Badge key={tag} variant="outline" className="text-[8px] font-black uppercase tracking-tighter border-och-steel/20 text-och-steel">
                    #{tag}
                 </Badge>
               ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/5">
               <div className="flex items-center gap-6">
                  <button className="flex items-center gap-1.5 text-[10px] text-och-steel hover:text-och-gold transition-colors font-black">
                     <Heart className={clsx("w-4 h-4", Object.keys(post.reactions || {}).length > 0 && "fill-och-gold text-och-gold")} />
                     {post.reaction_count || 0}
                  </button>
                  <button className="flex items-center gap-1.5 text-[10px] text-och-steel hover:text-och-gold transition-colors font-black">
                     <MessageSquare className="w-4 h-4" />
                     {post.comment_count || 0}
                  </button>
               </div>
               <button className="text-och-steel hover:text-white transition-colors">
                  <Share2 className="w-4 h-4" />
               </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

