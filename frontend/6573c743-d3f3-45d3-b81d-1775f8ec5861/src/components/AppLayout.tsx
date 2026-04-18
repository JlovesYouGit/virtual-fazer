import React from 'react';
import { SideNav } from './SideNav';
import { BottomNav } from './BottomNav';
export function AppLayout({ children }: {children: React.ReactNode;}) {
  return (
    <div className="flex min-h-screen bg-dark-900 text-white font-sans selection:bg-brand selection:text-white">
      <SideNav />
      <main className="flex-1 pb-16 md:pb-0 md:ml-64 lg:ml-72 min-h-screen max-w-[100vw] overflow-x-hidden">
        {children}
      </main>
      <BottomNav />
    </div>);

}