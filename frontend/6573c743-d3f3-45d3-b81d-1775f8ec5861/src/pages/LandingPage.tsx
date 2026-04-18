import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  PlaySquare,
  MessageCircle,
  Brain,
  BarChart2,
  ArrowRight } from
'lucide-react';
import { RedBirdLogo } from '../components/RedBirdLogo';
import { FloatingBubbles } from '../components/FloatingBubbles';
export function LandingPage() {
  const features = [
  {
    icon: PlaySquare,
    title: 'Immersive Reels',
    desc: 'Full-screen vertical video experience with snap-scroll.'
  },
  {
    icon: MessageCircle,
    title: 'Real-time Chat',
    desc: 'Connect instantly with friends and followers.'
  },
  {
    icon: Brain,
    title: 'Neural Feed',
    desc: 'AI-powered content categorization and recommendations.'
  },
  {
    icon: BarChart2,
    title: 'Deep Analytics',
    desc: 'Track your growth, reach, and engagement metrics.'
  }];

  return (
    <div className="min-h-screen bg-dark-900 text-white font-sans selection:bg-brand selection:text-white">
      {/* Navbar */}
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <RedBirdLogo size={36} />
          <span className="text-2xl font-bold tracking-wider">RedBird</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="text-white hover:text-brand transition-colors font-medium">
            
            Log in
          </Link>
          <Link
            to="/signup"
            className="bg-brand hover:bg-brand-hover text-white px-6 py-2 rounded-full font-medium transition-colors">
            
            Sign Up
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{
              opacity: 0,
              y: 20
            }}
            animate={{
              opacity: 1,
              y: 0
            }}
            transition={{
              duration: 0.6
            }}
            className="space-y-8">
            
            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight">
              Connect in <span className="text-brand">color.</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-lg">
              The next generation social platform. Share moments, discover
              creators, and build your community with our intelligent neural
              feed.
            </p>
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/signup"
                className="bg-brand hover:bg-brand-hover text-white px-8 py-4 rounded-full font-bold text-lg transition-colors flex items-center gap-2">
                
                Get Started <ArrowRight size={20} />
              </Link>
              <Link
                to="/feed"
                className="bg-dark-800 hover:bg-dark-700 text-white px-8 py-4 rounded-full font-bold text-lg transition-colors border border-dark-600">
                
                View Demo
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{
              opacity: 0,
              scale: 0.9
            }}
            animate={{
              opacity: 1,
              scale: 1
            }}
            transition={{
              duration: 0.8,
              delay: 0.2
            }}
            className="relative">
            
            <FloatingBubbles />
          </motion.div>
        </div>

        {/* Features Grid */}
        <div className="mt-40">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need to grow
            </h2>
            <p className="text-gray-400 text-lg">
              Powerful tools built for creators and communities.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, idx) =>
            <motion.div
              key={idx}
              initial={{
                opacity: 0,
                y: 20
              }}
              whileInView={{
                opacity: 1,
                y: 0
              }}
              viewport={{
                once: true
              }}
              transition={{
                delay: idx * 0.1
              }}
              className="bg-dark-800 p-8 rounded-3xl border border-dark-600 hover:border-brand/50 transition-colors">
              
                <div className="bg-dark-700 w-14 h-14 rounded-2xl flex items-center justify-center mb-6 text-brand">
                  <feature.icon size={28} />
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-gray-400 leading-relaxed">{feature.desc}</p>
              </motion.div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-600 py-12 text-center text-gray-500">
        <div className="flex items-center justify-center gap-2 mb-4">
          <RedBirdLogo size={24} className="text-gray-500" />
          <span className="font-bold tracking-wider">RedBird</span>
        </div>
        <p>© 2026 RedBird Social. All rights reserved.</p>
      </footer>
    </div>);

}