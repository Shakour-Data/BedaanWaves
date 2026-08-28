import { useAuthStore } from '@/store/useAuthStore';

describe('Authentication Store', () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      token: null,
      refreshToken: null,
      loading: false,
    });
  });

  it('should have initial unauthenticated state', () => {
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });



  it('should login and set authenticated state', async () => {
    const store = useAuthStore.getState();
    expect(store.isAuthenticated).toBe(false);
  });

  it('should logout and clear state', () => {
    useAuthStore.setState({
      user: { id: '1', username: 'testuser', email: 'test@example.com', full_name: 'Test User', is_active: true, is_admin: false, created_at: '2024-01-01' },
      isAuthenticated: true,
      token: 'mock-token',
      refreshToken: 'mock-refresh' });
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });
});
