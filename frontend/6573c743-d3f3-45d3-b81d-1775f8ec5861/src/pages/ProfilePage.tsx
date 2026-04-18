import React, { useState } from 'react';
import { Grid, PlaySquare, UserSquare, Settings } from 'lucide-react';
export function ProfilePage() {
  const [activeTab, setActiveTab] = useState<'posts' | 'reels' | 'tagged'>(
    'posts'
  );
  const posts = Array.from({
    length: 12
  }).map((_, i) => ({
    id: i,
    imageUrl: `https://picsum.photos/seed/profile${i}/400/400`,
    likes: Math.floor(Math.random() * 1000),
    comments: Math.floor(Math.random() * 100)
  }));
  return (
    <div className="max-w-4xl mx-auto pt-8 px-4 sm:px-8">
      {/* Profile Header */}
      <div className="flex flex-col md:flex-row gap-8 md:gap-16 mb-12">
        {/* Avatar */}
        <div className="flex-shrink-0 flex justify-center md:justify-start md:ml-8">
          <div className="w-32 h-32 md:w-40 md:h-40 rounded-full bg-gradient-to-tr from-brand to-orange-500 p-1">
            <img
              src="https://picsum.photos/seed/myavatar/300/300"
              alt="Profile"
              className="w-full h-full rounded-full border-4 border-dark-900 object-cover" />
            
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <h1 className="text-xl font-normal">current_user</h1>
            <div className="flex gap-2">
              <button className="bg-dark-700 hover:bg-dark-600 px-4 py-1.5 rounded-lg font-semibold text-sm transition-colors">
                Edit profile
              </button>
              <button className="bg-dark-700 hover:bg-dark-600 px-4 py-1.5 rounded-lg font-semibold text-sm transition-colors">
                View archive
              </button>
              <button className="p-1.5 hover:text-gray-300">
                <Settings size={24} />
              </button>
            </div>
          </div>

          <div className="flex gap-8 text-sm md:text-base">
            <span>
              <span className="font-semibold">42</span> posts
            </span>
            <span className="cursor-pointer">
              <span className="font-semibold">1,234</span> followers
            </span>
            <span className="cursor-pointer">
              <span className="font-semibold">567</span> following
            </span>
          </div>

          <div className="text-sm">
            <p className="font-semibold">John Doe</p>
            <p className="text-gray-300 whitespace-pre-line">
              Digital Creator 🎨{'\n'}
              Building the future of social 🔴{'\n'}
              linktr.ee/johndoe
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-t border-dark-600 flex justify-center gap-12 text-sm font-semibold tracking-widest uppercase">
        <button
          onClick={() => setActiveTab('posts')}
          className={`flex items-center gap-2 py-4 border-t-2 transition-colors ${activeTab === 'posts' ? 'border-white text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>
          
          <Grid size={16} /> Posts
        </button>
        <button
          onClick={() => setActiveTab('reels')}
          className={`flex items-center gap-2 py-4 border-t-2 transition-colors ${activeTab === 'reels' ? 'border-white text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>
          
          <PlaySquare size={16} /> Reels
        </button>
        <button
          onClick={() => setActiveTab('tagged')}
          className={`flex items-center gap-2 py-4 border-t-2 transition-colors ${activeTab === 'tagged' ? 'border-white text-white' : 'border-transparent text-gray-500 hover:text-gray-300'}`}>
          
          <UserSquare size={16} /> Tagged
        </button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-3 gap-1 sm:gap-4 pb-20">
        {posts.map((post) =>
        <div
          key={post.id}
          className="relative aspect-square group cursor-pointer bg-dark-800">
          
            <img
            src={post.imageUrl}
            alt="Post"
            className="w-full h-full object-cover" />
          
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-6">
              <div className="flex items-center gap-2 font-bold text-white">
                <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor">
                
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
                {post.likes}
              </div>
              <div className="flex items-center gap-2 font-bold text-white">
                <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor">
                
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                </svg>
                {post.comments}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>);

}