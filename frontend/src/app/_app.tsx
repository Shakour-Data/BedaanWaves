'use client';

import { useAuthStore } from '../store/useAuthStore';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function AuthGuard() {
  const authStore = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const handleAuthCheck = async () => {
      const isProtected = window.location.pathname.startsWith('/dashboard') ||
        window.location.pathname.startsWith('/stocks') ||
        window.location.pathname.startsWith('/login') ||
        window.location.pathname.startsWith('/register');

      if (authStore.isAuthenticated && isProtected) {
        // User is authenticated and trying to access protected route - allowed
      } else if (!authStore.isAuthenticated && !isProtected) {
        // User is not authenticated trying to access login/register - allowed
      } else if (!authStore.isAuthenticated) {
        // User is not authenticated and trying to access protected route
        router.replace('/login');
      }
    };

    handleAuthCheck();
  }, [authStore.isAuthenticated, router.pathname]);

  return null; // This component doesn't render anything
}