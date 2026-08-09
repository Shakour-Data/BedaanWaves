'use client';

import { useAuthStore } from '../store/useAuthStore';
import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';

export function AuthGuard() {
  const authStore = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const handleAuthCheck = async () => {
      const isProtected = pathname.startsWith('/dashboard') ||
        pathname.startsWith('/stocks') ||
        pathname.startsWith('/login') ||
        pathname.startsWith('/register');

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
  }, [authStore.isAuthenticated, pathname]);

  return null; // This component doesn't render anything
}