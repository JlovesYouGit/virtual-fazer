import React from 'react';
interface StoryCircleProps {
  imageUrl: string;
  username: string;
  hasUnseenStory?: boolean;
  size?: 'sm' | 'md' | 'lg';
}
export function StoryCircle({
  imageUrl,
  username,
  hasUnseenStory = true,
  size = 'md'
}: StoryCircleProps) {
  const sizeClasses = {
    sm: 'w-10 h-10',
    md: 'w-16 h-16',
    lg: 'w-20 h-20'
  };
  return (
    <div className="flex flex-col items-center gap-1 cursor-pointer group">
      <div
        className={`relative rounded-full p-[3px] ${hasUnseenStory ? 'bg-gradient-to-tr from-brand via-brand-hover to-orange-500' : 'bg-dark-600'}`}>
        
        <div className="bg-dark-900 rounded-full p-[2px]">
          <img
            src={imageUrl}
            alt={`${username}'s story`}
            className={`${sizeClasses[size]} rounded-full object-cover group-hover:scale-95 transition-transform`} />
          
        </div>
      </div>
      <span className="text-xs text-gray-300 truncate w-16 text-center">
        {username}
      </span>
    </div>);

}