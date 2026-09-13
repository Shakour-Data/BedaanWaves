import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ForgotPasswordPage from '@/app/(auth)/forgot-password/page';

const pushMock = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

vi.mock('@/lib/api', () => ({
  apiClient: {
    post: vi.fn().mockResolvedValue({ status: 200, data: { status: 'success' } }),
  },
  getApiErrorMessage: (err: unknown) => (err instanceof Error ? err.message : String(err)),
}));

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    pushMock.mockClear();
  });

  it('renders a password recovery form', () => {
    render(<ForgotPasswordPage />);
    expect(screen.getByRole('heading', { name: /Reset Password/i })).not.toBeNull();
    expect(screen.getByPlaceholderText(/you@example.com/i)).not.toBeNull();
  });

  it('renders a submit button', () => {
    render(<ForgotPasswordPage />);
    expect(screen.getByRole('button', { name: /Send Recovery Link/i })).not.toBeNull();
  });

  it('navigates to login when Back to Sign In is clicked', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /Back to Sign In/i }));
    expect(pushMock).toHaveBeenCalledWith('/login');
  });
});