import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { RedBirdLogo } from '../components/RedBirdLogo';
export function LoginPage() {
  const navigate = useNavigate();
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/feed');
  };
  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4 font-sans">
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
          <div className="flex flex-col items-center mb-8">
            <RedBirdLogo size={48} className="mb-4" />
            <h1 className="text-2xl font-bold text-white tracking-wider">
              RedBird
            </h1>
            <p className="text-gray-400 mt-2 text-sm">
              Sign in to see photos and videos
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email or username"
                className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
                required />
              
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-brand focus:ring-1 focus:ring-brand transition-colors"
                required />
              
            </div>
            <button
              type="submit"
              className="w-full bg-brand hover:bg-brand-hover text-white font-bold py-3 rounded-xl transition-colors mt-2">
              
              Log In
            </button>
          </form>

          <div className="flex items-center my-6">
            <div className="flex-1 border-t border-dark-600"></div>
            <span className="px-4 text-gray-500 text-sm font-medium">OR</span>
            <div className="flex-1 border-t border-dark-600"></div>
          </div>

          <button className="w-full bg-white text-black font-bold py-3 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-100 transition-colors">
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
            Sign in with Google
          </button>

          <div className="mt-6 text-center">
            <a
              href="#"
              className="text-sm text-brand hover:text-brand-hover transition-colors">
              
              Forgot password?
            </a>
          </div>
        </div>

        <div className="mt-4 bg-dark-800 border border-dark-600 rounded-2xl p-6 text-center shadow-lg">
          <p className="text-gray-400">
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-brand font-bold hover:text-brand-hover transition-colors">
              
              Sign up
            </Link>
          </p>
        </div>
      </motion.div>
    </div>);

}