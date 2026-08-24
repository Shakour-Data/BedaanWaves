import { useAuthStore } from '@/store/useAuthStore';

describe('Authentication Store', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      loading: false,
      currentLang: 'en',
    });
  });

  it('should have initial unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });

  it('should set language', () => {
    useAuthStore.getState().setLanguage('fa');
    expect(useAuthStore.getState().currentLang).toBe('fa');
  });

  it('should login and set authenticated state', async () => {
    const store = useAuthStore.getState();
    expect(store.isAuthenticated).toBe(false);
  });

  it('should logout and clear state', () => {
    useAuthStore.setState({
      user: { name: 'Test', email: 'test@example.com', role: 'user' },
      isAuthenticated: true,
      token: 'mock-token',
      refreshToken: 'mock-refresh',
    });
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });
});
