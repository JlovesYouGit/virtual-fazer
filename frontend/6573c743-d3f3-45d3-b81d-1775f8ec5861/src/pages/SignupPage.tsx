import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { RedBirdLogo } from '../components/RedBirdLogo';
export function SignupPage() {
  const navigate = useNavigate();
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/feed');
  };
  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4 font-sans py-12">
      <motion.div
        initial={{
          opacity: 0,
          y: 20
        }}
        animate={{
          opacity: 1,
          y: 0
        }}
        className="w-full max-w-md">
        
        <div className="bg-dark-800 border border-dark-600 rounded-3xl p-8 shadow-2xl">
          <div className="flex flex-col items-center mb-6">
            <RedBirdLogo size={48} className="mb-4" />
            <h1 className="text-2xl font-bold text-white tracking-wider">
              RedBird
            </h1>
            <p className="text-gray-400 mt-2 text-sm text-center font-medium">
              Sign up to see photos and videos from your friends.
            </p>
          </div>

          <button 
            onClick={() => {
              const googleOAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=473715635548-phpqpcvcji0uilu7sg1tcdppv5aoc63u.apps.googleusercontent.com&redirect_uri=${encodeURIComponent('http://localhost:5174/auth/callback/google/')}&response_type=code&scope=profile email&access_type=online`;
              window.location.href = googleOAuthUrl;
            }}
            className="w-full bg-white text-black font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-100 transition-colors mb-6">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg">
              
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4" />
              
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853" />
              
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05" />
              
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335" />
              
            </svg>
            Sign up with Google
          </button>

          <div className="flex items-center mb-6">
            <div className="flex-1 border-t border-dark-600"></div>
            <span className="px-4 text-gray-500 text-sm font-medium">OR</span>
            <div className="flex-1 border-t border-dark-600"></div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            <input
              type="email"
              placeholder="Email"
              className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
              required />
            
            <input
              type="text"
              placeholder="Full Name"
              className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
              required />
            
            <input
              type="text"
              placeholder="Username"
              className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
              required />
            
            <input
              type="password"
              placeholder="Password"
              className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
              required />
            

            <p className="text-xs text-gray-500 text-center mt-4 leading-relaxed">
              By signing up, you agree to our{' '}
              <a href="#" className="text-gray-300 hover:text-white">
                Terms
              </a>
              ,{' '}
              <a href="#" className="text-gray-300 hover:text-white">
                Privacy Policy
              </a>{' '}
              and{' '}
              <a href="#" className="text-gray-300 hover:text-white">
                Cookies Policy
              </a>
              .
            </p>

            <button
              type="submit"
              className="w-full bg-brand hover:bg-brand-hover text-white font-bold py-3 rounded-xl transition-colors mt-4">
              
              Sign Up
            </button>
          </form>
        </div>

        <div className="mt-4 bg-dark-800 border border-dark-600 rounded-2xl p-6 text-center shadow-lg">
          <p className="text-gray-400">
            Have an account?{' '}
            <Link
              to="/login"
              className="text-brand font-bold hover:text-brand-hover transition-colors">
              
              Log in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>);

}