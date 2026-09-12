import { render, screen, fireEvent } from '@testing-library/react';
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

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    pushMock.mockClear();
  });

  it('renders disabled state message', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByText(/Password Recovery Disabled/i)).not.toBeNull();
    expect(screen.getByText(/temporarily disabled during development/i)).not.toBeNull();
  });

  it('renders Go to Home button', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByRole('button', { name: /go to home/i })).not.toBeNull();
  });

  it('navigates to home when Go to Home button is clicked', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /go to home/i }));
    expect(pushMock).toHaveBeenCalledWith('/');
  });
});