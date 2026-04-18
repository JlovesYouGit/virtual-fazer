import React, { useState } from 'react';
import {
  Edit,
  Phone,
  Video,
  Info,
  Image as ImageIcon,
  Heart,
  Smile } from
'lucide-react';
export function ChatPage() {
  const [activeChat, setActiveChat] = useState<number | null>(1);
  const conversations = Array.from({
    length: 10
  }).map((_, i) => ({
    id: i + 1,
    user: {
      username: `friend_${i + 1}`,
      name: `Friend Name ${i + 1}`,
      avatarUrl: `https://picsum.photos/seed/chat${i}/150/150`,
      isOnline: i % 3 === 0
    },
    lastMessage:
    i % 2 === 0 ? 'Sent a reel by @creator' : 'Haha that is so funny! 😂',
    timeAgo: `${i + 1}h`,
    unread: i === 0 || i === 2
  }));
  const messages = [
  {
    id: 1,
    senderId: 1,
    text: 'Hey! Did you see that new post?',
    time: '10:00 AM'
  },
  {
    id: 2,
    senderId: 'me',
    text: 'Yeah it was crazy! 🔴',
    time: '10:05 AM'
  },
  {
    id: 3,
    senderId: 1,
    text: 'Haha that is so funny! 😂',
    time: '10:06 AM'
  }];

  return (
    <div className="flex h-screen md:h-[calc(100vh)] bg-dark-900 overflow-hidden pt-0 md:pt-0">
      {/* Sidebar - Conversation List */}
      <div
        className={`${activeChat ? 'hidden md:flex' : 'flex'} flex-col w-full md:w-96 border-r border-dark-600 bg-dark-900`}>
        
        <div className="p-4 border-b border-dark-600 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer">
            <h1 className="text-xl font-bold">current_user</h1>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2">
              
              <path d="M6 9l6 6 6-6" />
            </svg>
          </div>
          <button className="p-2 hover:bg-dark-800 rounded-full transition-colors">
            <Edit size={24} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-base font-semibold mb-4">Messages</h2>
            <div className="space-y-2">
              {conversations.map((conv) =>
              <div
                key={conv.id}
                onClick={() => setActiveChat(conv.id)}
                className={`flex items-center gap-3 p-2 rounded-xl cursor-pointer transition-colors ${activeChat === conv.id ? 'bg-dark-800' : 'hover:bg-dark-800'}`}>
                
                  <div className="relative">
                    <img
                    src={conv.user.avatarUrl}
                    alt={conv.user.username}
                    className="w-14 h-14 rounded-full object-cover" />
                  
                    {conv.user.isOnline &&
                  <div className="absolute bottom-0 right-0 w-4 h-4 bg-green-500 border-2 border-dark-900 rounded-full"></div>
                  }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p
                    className={`text-sm truncate ${conv.unread ? 'font-bold text-white' : 'text-gray-300'}`}>
                    
                      {conv.user.name}
                    </p>
                    <p
                    className={`text-sm truncate ${conv.unread ? 'font-semibold text-white' : 'text-gray-500'}`}>
                    
                      {conv.lastMessage} • {conv.timeAgo}
                    </p>
                  </div>
                  {conv.unread &&
                <div className="w-2.5 h-2.5 bg-brand rounded-full"></div>
                }
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      {activeChat ?
      <div className="flex-1 flex flex-col bg-dark-900">
          {/* Chat Header */}
          <div className="h-16 border-b border-dark-600 flex items-center justify-between px-4">
            <div className="flex items-center gap-3">
              <button
              className="md:hidden p-2 -ml-2 hover:bg-dark-800 rounded-full"
              onClick={() => setActiveChat(null)}>
              
                <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2">
                
                  <path d="M15 18l-6-6 6-6" />
                </svg>
              </button>
              <img
              src={conversations[0].user.avatarUrl}
              alt="User"
              className="w-8 h-8 rounded-full object-cover" />
            
              <span className="font-semibold">
                {conversations[0].user.name}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <button className="text-white hover:text-gray-300">
                <Phone size={24} />
              </button>
              <button className="text-white hover:text-gray-300">
                <Video size={24} />
              </button>
              <button className="text-white hover:text-gray-300">
                <Info size={24} />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="flex flex-col items-center justify-center py-8">
              <img
              src={conversations[0].user.avatarUrl}
              alt="User"
              className="w-24 h-24 rounded-full object-cover mb-4" />
            
              <h2 className="text-xl font-bold">
                {conversations[0].user.name}
              </h2>
              <p className="text-gray-500 text-sm">
                {conversations[0].user.username} • RedBird
              </p>
              <button className="mt-4 bg-dark-800 hover:bg-dark-700 px-4 py-1.5 rounded-lg font-semibold text-sm transition-colors">
                View Profile
              </button>
            </div>

            {messages.map((msg) =>
          <div
            key={msg.id}
            className={`flex ${msg.senderId === 'me' ? 'justify-end' : 'justify-start'}`}>
            
                {msg.senderId !== 'me' &&
            <img
              src={conversations[0].user.avatarUrl}
              alt="User"
              className="w-8 h-8 rounded-full object-cover mr-2 self-end" />

            }
                <div
              className={`max-w-[70%] px-4 py-2 rounded-2xl ${msg.senderId === 'me' ? 'bg-brand text-white rounded-br-sm' : 'bg-dark-800 text-white border border-dark-600 rounded-bl-sm'}`}>
              
                  <p>{msg.text}</p>
                </div>
              </div>
          )}
          </div>

          {/* Input Area */}
          <div className="p-4">
            <div className="border border-dark-600 bg-dark-900 rounded-full flex items-center px-4 py-2 focus-within:border-brand transition-colors">
              <button className="p-2 text-white hover:text-gray-300">
                <Smile size={24} />
              </button>
              <input
              type="text"
              placeholder="Message..."
              className="flex-1 bg-transparent border-none focus:outline-none px-2 text-white" />
            
              <div className="flex items-center gap-2">
                <button className="p-2 text-white hover:text-gray-300">
                  <ImageIcon size={24} />
                </button>
                <button className="p-2 text-white hover:text-gray-300">
                  <Heart size={24} />
                </button>
              </div>
            </div>
          </div>
        </div> :

      <div className="hidden md:flex flex-1 flex-col items-center justify-center bg-dark-900">
          <div className="w-24 h-24 border-2 border-white rounded-full flex items-center justify-center mb-4">
            <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1">
            
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold mb-2">Your Messages</h2>
          <p className="text-gray-500 mb-6">
            Send private photos and messages to a friend or group.
          </p>
          <button className="bg-brand hover:bg-brand-hover text-white px-6 py-2 rounded-xl font-semibold transition-colors">
            Send Message
          </button>
        </div>
      }
    </div>);

}