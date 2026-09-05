import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import ForgotPasswordPage from '@/app/(auth)/forgot-password/page';

vi.mock('@/lib/password-recovery-api', () => ({
  requestPasswordReset: vi.fn(() => Promise.resolve({ success: true, message: 'Recovery link sent to your email' })),
  isValidEmail: vi.fn(() => true),
}));

vi.mock('@/store/useUXStore', () => ({
  useUXStore: (selector: (state: { addToast: ReturnType<typeof vi.fn> }) => unknown) =>
    selector({ addToast: vi.fn() }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  }),
}));

describe('ForgotPasswordPage', () => {
  it('renders initially with email field and Send button', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByLabelText(/email/i)).not.toBeNull();
    expect(screen.getByRole('button', { name: /send reset link/i })).not.toBeNull();
  });

  it('renders email input field', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByLabelText(/email/i)).not.toBeNull();
  });

  it('renders Back to Sign in link', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByRole('link', { name: /back to sign in/i })).not.toBeNull();
  });

  it('shows loading state while submitting', async () => {
    render(<ForgotPasswordPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    expect(screen.getByRole('button', { name: /processing/i })).not.toBeNull();

    await waitFor(() => {
      expect(screen.getByText(/reset link sent/i)).not.toBeNull();
    });
  });

  it('shows success message after submission', async () => {
    render(<ForgotPasswordPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByText(/reset link sent/i)).not.toBeNull();
    });
  });

  it('shows Back to Sign in link after submission', async () => {
    render(<ForgotPasswordPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /back to sign in/i })).not.toBeNull();
    });
  });

  it('disables submit button when loading', async () => {
    render(<ForgotPasswordPage />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }));

    const button = screen.getByRole('button', { name: /processing/i });
    expect(button).toBeDisabled();
  });
});
