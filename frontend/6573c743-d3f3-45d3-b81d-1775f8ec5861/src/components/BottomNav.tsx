import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, Compass, PlusSquare, PlaySquare, User } from 'lucide-react';
export function BottomNav() {
  const navItems = [
  {
    icon: Home,
    path: '/feed'
  },
  {
    icon: Compass,
    path: '/explore'
  },
  {
    icon: PlusSquare,
    path: '/create'
  },
  {
    icon: PlaySquare,
    path: '/reels'
  },
  {
    icon: User,
    path: '/profile'
  }];

  return (
    <div className="md:hidden fixed bottom-0 w-full bg-dark-900 border-t border-dark-600 z-50 pb-safe">
      <nav className="flex justify-around items-center h-16">
        {navItems.map((item) =>
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
          `p-3 transition-colors ${isActive ? 'text-brand' : 'text-white hover:text-brand'}`
          }>
          
            <item.icon size={24} />
          </NavLink>
        )}
      </nav>
    </div>);

}