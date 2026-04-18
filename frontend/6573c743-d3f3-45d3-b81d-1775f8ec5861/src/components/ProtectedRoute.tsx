import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Loader2 } from 'lucide-react';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { status, isLoading, user } = useAuth();
  const location = useLocation();
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    // Check if user is a guest
    const guestFlag = localStorage.getItem('isGuest');
    const userData = localStorage.getItem('user');
    if (guestFlag === 'true' && userData) {
      setIsGuest(true);
    }
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark-900">
        <div className="text-center">
          <Loader2 className="animate-spin mx-auto mb-4" size={48} />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Allow access if authenticated OR guest
  if (status !== 'authenticated' && !isGuest) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
