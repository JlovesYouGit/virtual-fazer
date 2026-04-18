import React from 'react';
import { StoryCircle } from '../components/StoryCircle';
import { PostCard } from '../components/PostCard';
import { UserSuggestion } from '../components/UserSuggestion';
export function FeedPage() {
  const stories = Array.from({
    length: 10
  }).map((_, i) => ({
    id: i,
    username: `user_${i + 1}`,
    imageUrl: `https://picsum.photos/seed/story${i}/150/150`,
    hasUnseen: i < 5
  }));
  const posts = Array.from({
    length: 5
  }).map((_, i) => ({
    id: i,
    user: {
      username: `creator_${i + 1}`,
      avatarUrl: `https://picsum.photos/seed/avatar${i}/150/150`
    },
    imageUrl: `https://picsum.photos/seed/post${i}/800/1000`,
    likes: Math.floor(Math.random() * 10000) + 100,
    caption: 'Living my best life! 🔴⚫️ #redbird #vibes',
    timeAgo: `${i + 1}h`
  }));
  const suggestions = Array.from({
    length: 5
  }).map((_, i) => ({
    id: i,
    username: `suggested_${i + 1}`,
    subtitle: 'Followed by user_1 + 2 more',
    avatarUrl: `https://picsum.photos/seed/sug${i}/150/150`
  }));
  return (
    <div className="max-w-4xl mx-auto pt-4 md:pt-8 px-0 md:px-4 flex justify-center gap-8">
      {/* Main Feed Column */}
      <div className="w-full max-w-lg">
        {/* Stories */}
        <div className="mb-6 bg-dark-900 sm:bg-dark-800 sm:border border-dark-600 sm:rounded-xl p-4 overflow-x-auto no-scrollbar flex gap-4">
          <StoryCircle
            imageUrl="https://picsum.photos/seed/myavatar/150/150"
            username="Your Story"
            hasUnseenStory={false} />
          
          {stories.map((story) =>
          <StoryCircle
            key={story.id}
            imageUrl={story.imageUrl}
            username={story.username}
            hasUnseenStory={story.hasUnseen} />

          )}
        </div>

        {/* Posts */}
        <div className="space-y-4 sm:space-y-6">
          {posts.map((post) =>
          <PostCard key={post.id} {...post} />
          )}
        </div>
      </div>

      {/* Right Sidebar (Desktop only) */}
      <div className="hidden lg:block w-80 pt-4">
        {/* Current User Mini Profile */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4 cursor-pointer">
            <img
              src="https://picsum.photos/seed/myavatar/150/150"
              alt="Me"
              className="w-14 h-14 rounded-full object-cover" />
            
            <div className="flex flex-col">
              <span className="font-semibold text-sm">current_user</span>
              <span className="text-sm text-gray-500">John Doe</span>
            </div>
          </div>
          <button className="text-xs font-semibold text-brand hover:text-brand-hover">
            Switch
          </button>
        </div>

        {/* Suggestions */}
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-gray-500">
            Suggested for you
          </span>
          <button className="text-xs font-semibold hover:text-gray-300">
            See All
          </button>
        </div>

        <div className="space-y-3">
          {suggestions.map((sug) =>
          <UserSuggestion key={sug.id} {...sug} />
          )}
        </div>

        {/* Footer Links */}
        <div className="mt-8 text-xs text-gray-600 space-y-4">
          <div className="flex flex-wrap gap-x-2 gap-y-1">
            <a href="#" className="hover:underline">
              About
            </a>
            <a href="#" className="hover:underline">
              Help
            </a>
            <a href="#" className="hover:underline">
              Press
            </a>
            <a href="#" className="hover:underline">
              API
            </a>
            <a href="#" className="hover:underline">
              Jobs
            </a>
            <a href="#" className="hover:underline">
              Privacy
            </a>
            <a href="#" className="hover:underline">
              Terms
            </a>
          </div>
          <p>© 2026 REDBIRD FROM META</p>
        </div>
      </div>
    </div>);

}