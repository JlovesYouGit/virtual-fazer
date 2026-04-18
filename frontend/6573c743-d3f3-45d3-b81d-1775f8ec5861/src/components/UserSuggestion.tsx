import React, { useState } from 'react';
interface UserSuggestionProps {
  username: string;
  subtitle: string;
  avatarUrl: string;
}
export function UserSuggestion({
  username,
  subtitle,
  avatarUrl
}: UserSuggestionProps) {
  const [isFollowing, setIsFollowing] = useState(false);
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3 cursor-pointer">
        <img
          src={avatarUrl}
          alt={username}
          className="w-10 h-10 rounded-full object-cover" />
        
        <div className="flex flex-col">
          <span className="font-semibold text-sm hover:text-gray-300">
            {username}
          </span>
          <span className="text-xs text-gray-500">{subtitle}</span>
        </div>
      </div>
      <button
        onClick={() => setIsFollowing(!isFollowing)}
        className={`text-xs font-semibold ${isFollowing ? 'text-white' : 'text-brand hover:text-brand-hover'}`}>
        
        {isFollowing ? 'Following' : 'Follow'}
      </button>
    </div>);

}