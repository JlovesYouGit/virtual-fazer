import React, { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Loader2, AlertCircle } from 'lucide-react';
import { socialApi } from '../services/socialApi';

export function NotificationsPage() {
  const [activeTab, setActiveTab] = useState('All');
  const tabs = ['All', 'Follows', 'Likes', 'Comments'];

  // Fetch real notifications from backend
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['notifications', activeTab],
    queryFn: () => socialApi.getNotifications({ page: 1 }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Mark notifications as read mutation
  const markReadMutation = useMutation({
    mutationFn: (ids: string[]) => socialApi.markNotificationsRead(ids),
    onSuccess: () => refetch(),
  });

  const notifications = data?.results || [];

  // Filter notifications based on active tab
  const filteredNotifications = notifications.filter((notif) => {
    if (activeTab === 'All') return true;
    if (activeTab === 'Follows') return notif.notification_type === 'follow' || notif.notification_type === 'follow_request';
    if (activeTab === 'Likes') return notif.notification_type === 'like';
    if (activeTab === 'Comments') return notif.notification_type === 'comment' || notif.notification_type === 'reel_comment' || notif.notification_type === 'post_comment';
    return true;
  });

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d`;
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'follow':
      case 'follow_request':
        return '👤';
      case 'like':
        return '❤️';
      case 'comment':
      case 'reel_comment':
      case 'post_comment':
        return '💬';
      case 'share':
        return '🔄';
      case 'mention':
        return '@️';
      default:
        return '🔔';
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto pt-4 md:pt-8 px-4 pb-20">
        <h1 className="text-2xl font-bold mb-6">Notifications</h1>
        <div className="flex justify-center py-8">
          <Loader2 className="animate-spin" size={32} />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-2xl mx-auto pt-4 md:pt-8 px-4 pb-20">
        <h1 className="text-2xl font-bold mb-6">Notifications</h1>
        <div className="flex flex-col items-center py-8 text-red-500">
          <AlertCircle size={32} />
          <p className="mt-2">Failed to load notifications</p>
          <p className="text-sm mt-1 text-gray-400">{error?.message || 'Unknown error'}</p>
          <button onClick={() => refetch()} className="mt-2 text-sm underline">
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto pt-4 md:pt-8 px-4 pb-20">
      <h1 className="text-2xl font-bold mb-6">Notifications</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-2 rounded-full font-semibold text-sm transition-colors ${
              activeTab === tab 
                ? 'bg-white text-black' 
                : 'bg-dark-800 text-white hover:bg-dark-700'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        {filteredNotifications.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">🔔</div>
            <p className="text-lg font-medium">No notifications</p>
            <p className="text-sm mt-1">You're all caught up!</p>
          </div>
        ) : (
          <>
            <div className="font-semibold text-base mb-4">
              {filteredNotifications.some(n => !n.is_read) ? 'New' : 'Recent'}
            </div>
            {filteredNotifications.map((notif) => (
              <div
                key={notif.id}
                className={`flex items-center justify-between py-3 px-4 rounded-xl transition-colors ${
                  !notif.is_read ? 'bg-dark-800/50' : ''
                }`}
                onClick={() => {
                  if (!notif.is_read) {
                    markReadMutation.mutate([notif.id]);
                  }
                }}
              >
                <div className="flex items-center gap-3 flex-1">
                  <div className="relative">
                    <div className="w-11 h-11 rounded-full bg-brand/20 flex items-center justify-center text-lg">
                      {getNotificationIcon(notif.notification_type)}
                    </div>
                    {!notif.is_read && (
                      <div className="absolute -top-1 -right-1 w-3 h-3 bg-brand rounded-full border-2 border-dark-900"></div>
                    )}
                  </div>

                  <div className="text-sm pr-4">
                    <span className="font-semibold text-white">
                      {notif.sender?.username || 'Unknown'}
                    </span>{' '}
                    <span className="text-gray-300">{notif.message}</span>{' '}
                    <span className="text-gray-500">{formatTimeAgo(notif.created_at)}</span>
                  </div>
                </div>

                {/* Action Button */}
                {notif.notification_type === 'follow' || notif.notification_type === 'follow_request' ? (
                  <button className="px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors bg-brand text-white hover:bg-brand-hover">
                    Follow Back
                  </button>
                ) : null}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
