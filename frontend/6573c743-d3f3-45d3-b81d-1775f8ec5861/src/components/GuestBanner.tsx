import React from 'react';
import { Link } from 'react-router-dom';
import { UserPlus, X } from 'lucide-react';

export function GuestBanner() {
  const isGuest = localStorage.getItem('isGuest') === 'true';
  
  if (!isGuest) return null;

  return (
    <div className="bg-brand/10 border-b border-brand/30 px-4 py-2">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-brand font-medium">👋 Guest Mode</span>
          <span className="text-gray-400">
            You're browsing as a guest. Some features are limited.
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="flex items-center gap-1 text-sm text-brand hover:text-brand-hover font-medium transition-colors"
          >
            <UserPlus size={16} />
            Sign Up for Full Access
          </Link>
          <button
            onClick={() => {
              localStorage.removeItem('isGuest');
              window.location.reload();
            }}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
