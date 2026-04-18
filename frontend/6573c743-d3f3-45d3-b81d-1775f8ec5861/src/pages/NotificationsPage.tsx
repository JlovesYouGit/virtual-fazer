import React, { useState } from 'react';
export function NotificationsPage() {
  const [activeTab, setActiveTab] = useState('All');
  const tabs = ['All', 'Follows', 'Likes', 'Comments'];
  const notifications = Array.from({
    length: 15
  }).map((_, i) => {
    const type = i % 3 === 0 ? 'follow' : i % 2 === 0 ? 'like' : 'comment';
    return {
      id: i,
      type,
      user: {
        username: `user_${i + 1}`,
        avatarUrl: `https://picsum.photos/seed/notif${i}/150/150`
      },
      contentUrl:
      type !== 'follow' ?
      `https://picsum.photos/seed/post${i}/150/150` :
      null,
      timeAgo: `${i + 1}h`,
      isFollowing: i % 2 === 0
    };
  });
  return (
    <div className="max-w-2xl mx-auto pt-4 md:pt-8 px-4 pb-20">
      <h1 className="text-2xl font-bold mb-6">Notifications</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto no-scrollbar">
        {tabs.map((tab) =>
        <button
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={`px-6 py-2 rounded-full font-semibold text-sm transition-colors ${activeTab === tab ? 'bg-white text-black' : 'bg-dark-800 text-white hover:bg-dark-700'}`}>
          
            {tab}
          </button>
        )}
      </div>

      {/* Notifications List */}
      <div className="space-y-4">
        <div className="font-semibold text-base mb-4">Today</div>
        {notifications.map((notif) =>
        <div
          key={notif.id}
          className="flex items-center justify-between py-2">
          
            <div className="flex items-center gap-3 flex-1">
              <img
              src={notif.user.avatarUrl}
              alt={notif.user.username}
              className="w-11 h-11 rounded-full object-cover cursor-pointer" />
            
              <div className="text-sm pr-4">
                <span className="font-semibold cursor-pointer hover:text-gray-300">
                  {notif.user.username}
                </span>{' '}
                {notif.type === 'follow' && 'started following you.'}
                {notif.type === 'like' && 'liked your post.'}
                {notif.type === 'comment' &&
              'commented: "This is amazing! 🔥"'}{' '}
                <span className="text-gray-500">{notif.timeAgo}</span>
              </div>
            </div>

            {/* Action Area */}
            {notif.type === 'follow' ?
          <button
            className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors ${notif.isFollowing ? 'bg-dark-700 text-white hover:bg-dark-600' : 'bg-brand text-white hover:bg-brand-hover'}`}>
            
                {notif.isFollowing ? 'Following' : 'Follow'}
              </button> :

          <img
            src={notif.contentUrl!}
            alt="Post"
            className="w-11 h-11 object-cover cursor-pointer" />

          }
          </div>
        )}
      </div>
    </div>);

}