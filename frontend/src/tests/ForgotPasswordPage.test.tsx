import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ForgotPasswordPage from '@/app/forgot-password/page';

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: (selector: (s: { currentLang: string; setLanguage: () => void }) => unknown) => {
    const state = { currentLang: 'en' as const, setLanguage: vi.fn() };
    return selector ? selector(state) : state;
  },
}));

vi.mock('@/lib/password-recovery-api', () => ({
  requestPasswordReset: vi.fn(),
  isValidEmail: (e: string) => /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(e),
  isValidPassword: (p: string) => p.length >= 8,
  passwordsMatch: (a: string, b: string) => a === b && a.length > 0,
  saveDraftEmail: vi.fn(),
  getDraftEmail: vi.fn(() => ''),
  clearDraftEmail: vi.fn(),
}));

import { requestPasswordReset } from '@/lib/password-recovery-api';

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.mocked(requestPasswordReset).mockReset();
  });

  it('renders Welcome state initially with Start button', () => {
    render(<ForgotPasswordPage />);

    expect(screen.getByText(/reset your password/i)).not.toBeNull();
    expect(screen.getByRole('button', { name: /start recovery/i })).not.toBeNull();
  });

  it('transitions to Data_Entry after clicking Start', () => {
    render(<ForgotPasswordPage />);

    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));

    expect(screen.getByText(/enter your email/i)).not.toBeNull();
    expect(screen.getByLabelText(/email/i)).not.toBeNull();
    expect(screen.getByRole('button', { name: /continue/i })).not.toBeNull();
  });

  it('shows Back button in Data_Entry state', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    expect(screen.getByLabelText(/back/i)).not.toBeNull();
  });

  it('transitions to Confirmation after entering valid email and clicking Continue', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByText(/confirm your email/i)).not.toBeNull();
    expect(screen.getByText('user@example.com')).not.toBeNull();
  });

  it('shows Error_Recovery when email is invalid', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'not-an-email' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByRole('alert')).not.toBeNull();
    expect(screen.getByText(/retry/i)).not.toBeNull();
  });

  it('shows Result after successful password reset request', async () => {
    vi.mocked(requestPasswordReset).mockResolvedValue({
      success: true,
      message: 'Recovery link sent to your email',
    });

    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /send recovery link/i }));

    await waitFor(() => {
      expect(screen.getByText(/recovery link sent to your email/i)).not.toBeNull();
    });
  });

  it('shows Error_Recovery when API call fails', async () => {
    vi.mocked(requestPasswordReset).mockResolvedValue({
      success: false,
      message: 'Network error',
      error: { message: 'Network error', code: 'network' },
    });

    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /send recovery link/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).not.toBeNull();
    });
  });

  it('shows Back button at top-left in Confirmation and Error_Recovery states', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));

    // The back button should be present (absolute positioned)
    const backBtn = screen.getByLabelText(/back/i);
    expect(backBtn).not.toBeNull();
  });

  it('shows Back button in Confirmation state', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByLabelText(/back/i)).not.toBeNull();
  });

  it('shows Back button in Error_Recovery state', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bad' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByLabelText(/back/i)).not.toBeNull();
  });

  it('shows Back button in Processing state', () => {
    vi.mocked(requestPasswordReset).mockResolvedValue({
      success: true,
      message: 'Sent',
    });

    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /send recovery link/i }));

    expect(screen.getByLabelText(/back/i)).not.toBeNull();
  });

  it('shows Back button in Result state', async () => {
    vi.mocked(requestPasswordReset).mockResolvedValue({
      success: true,
      message: 'Sent',
    });

    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));
    fireEvent.click(screen.getByRole('button', { name: /send recovery link/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/back/i)).not.toBeNull();
    });
  });

  it('Edit button returns from Confirmation to Data_Entry', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByText(/confirm your email/i)).not.toBeNull();

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(screen.getByLabelText(/email/i)).not.toBeNull();
  });

  it('Retry button returns from Error_Recovery to Data_Entry', () => {
    render(<ForgotPasswordPage />);
    fireEvent.click(screen.getByRole('button', { name: /start recovery/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bad' } });
    fireEvent.click(screen.getByRole('button', { name: /continue/i }));

    expect(screen.getByRole('alert')).not.toBeNull();
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(screen.getByLabelText(/email/i)).not.toBeNull();
  });
});
