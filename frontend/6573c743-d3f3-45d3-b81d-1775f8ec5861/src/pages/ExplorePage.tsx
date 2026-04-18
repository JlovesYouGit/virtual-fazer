import React from 'react';
import { Search, PlaySquare, Copy } from 'lucide-react';
export function ExplorePage() {
  const categories = [
  'For You',
  'Trending',
  'Art',
  'Music',
  'Gaming',
  'Sports',
  'Fashion',
  'Tech'];

  // Generate masonry layout items
  const exploreItems = Array.from({
    length: 20
  }).map((_, i) => {
    const isLarge = i % 7 === 0; // Every 7th item is large
    const isReel = i % 5 === 0;
    const isCarousel = i % 8 === 0;
    return {
      id: i,
      imageUrl: `https://picsum.photos/seed/explore${i}/${isLarge ? '800/800' : '400/400'}`,
      isLarge,
      isReel,
      isCarousel,
      likes: Math.floor(Math.random() * 10000),
      comments: Math.floor(Math.random() * 500)
    };
  });
  return (
    <div className="max-w-5xl mx-auto pt-4 md:pt-8 px-4 pb-20">
      {/* Search Bar */}
      <div className="relative max-w-xl mx-auto mb-6">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <Search size={20} className="text-gray-500" />
        </div>
        <input
          type="text"
          placeholder="Search"
          className="w-full bg-dark-800 border border-dark-600 rounded-xl py-3 pl-12 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors" />
        
      </div>

      {/* Categories */}
      <div className="flex gap-3 overflow-x-auto no-scrollbar mb-8 pb-2">
        {categories.map((cat, idx) =>
        <button
          key={idx}
          className={`whitespace-nowrap px-6 py-2 rounded-xl font-semibold text-sm transition-colors ${idx === 0 ? 'bg-brand text-white' : 'bg-dark-800 text-white border border-dark-600 hover:bg-dark-700'}`}>
          
            {cat}
          </button>
        )}
      </div>

      {/* Masonry Grid */}
      <div className="grid grid-cols-3 gap-1 sm:gap-4">
        {exploreItems.map((item) =>
        <div
          key={item.id}
          className={`relative group cursor-pointer bg-dark-800 ${item.isLarge ? 'col-span-2 row-span-2' : 'aspect-square'}`}>
          
            <img
            src={item.imageUrl}
            alt="Explore content"
            className="w-full h-full object-cover" />
          

            {/* Icons for content type */}
            <div className="absolute top-2 right-2 text-white drop-shadow-md">
              {item.isReel && <PlaySquare size={20} fill="currentColor" />}
              {item.isCarousel && <Copy size={20} fill="currentColor" />}
            </div>

            {/* Hover Overlay */}
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-6">
              <div className="flex items-center gap-2 font-bold text-white">
                <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor">
                
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                </svg>
                {item.likes > 1000 ?
              (item.likes / 1000).toFixed(1) + 'k' :
              item.likes}
              </div>
              <div className="flex items-center gap-2 font-bold text-white">
                <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="currentColor">
                
                  <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
                </svg>
                {item.comments}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>);

}