import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Home,
  Compass,
  PlusSquare,
  PlaySquare,
  User,
  MessageCircle,
  Bell,
  BarChart2 } from
'lucide-react';
import { RedBirdLogo } from './RedBirdLogo';
export function SideNav() {
  const navigate = useNavigate();
  const navItems = [
  {
    icon: Home,
    label: 'Home',
    path: '/feed'
  },
  {
    icon: Compass,
    label: 'Explore',
    path: '/explore'
  },
  {
    icon: PlaySquare,
    label: 'Reels',
    path: '/reels'
  },
  {
    icon: MessageCircle,
    label: 'Messages',
    path: '/chat'
  },
  {
    icon: Bell,
    label: 'Notifications',
    path: '/notifications'
  },
  {
    icon: BarChart2,
    label: 'Analytics',
    path: '/analytics'
  },
  {
    icon: User,
    label: 'Profile',
    path: '/profile'
  }];

  return (
    <div className="hidden md:flex flex-col w-64 lg:w-72 fixed h-screen border-r border-dark-600 bg-dark-900 p-4 z-50">
      <div className="flex items-center gap-3 px-4 py-6 mb-6">
        <RedBirdLogo size={32} />
        <span className="text-xl font-bold tracking-wider text-white">
          RedBird
        </span>
      </div>

      <nav className="flex-1 space-y-2 overflow-y-auto">
        {navItems.map((item) =>
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
          `flex items-center gap-4 px-4 py-3 rounded-xl transition-colors ${isActive ? 'bg-dark-800 text-brand font-semibold' : 'text-white hover:bg-dark-800 hover:text-brand'}`
          }>
          
            <item.icon size={24} />
            <span className="text-lg">{item.label}</span>
          </NavLink>
        )}
      </nav>

      <button 
        onClick={() => navigate('/create')}
        className="mt-4 flex items-center justify-center gap-2 w-full bg-brand hover:bg-brand-hover text-white py-3 rounded-xl font-semibold transition-colors">
        <PlusSquare size={20} />
        <span>Create Post</span>
      </button>
    </div>);

}