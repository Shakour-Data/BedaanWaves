import { renderHook, act } from '@testing-library/react';
import { usePasswordRecoveryFSM } from '@/hooks/usePasswordRecoveryFSM';
import * as api from '@/lib/password-recovery-api';

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: () => ({
    "en": 'en',
    setLanguage: vi.fn() }) }));

vi.mock('@/lib/password-recovery-api', async (importOriginal) => {
  const actual = await importOriginal<typeof api>();
  return {
    ...actual,
    requestPasswordReset: vi.fn(),
    isValidEmail: actual.isValidEmail };
});

describe('usePasswordRecoveryFSM', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts in the Welcome state', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    expect(result.current.state).toBe('Welcome');
  });

  it('transitions Welcome → Data_Entry on start()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    expect(result.current.state).toBe('Data_Entry');
  });

  it('shows Error_Recovery when email is empty on validateAndProceed', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.validateAndProceed());
    expect(result.current.state).toBe('Error_Recovery');
  });

  it('shows Error_Recovery when email is invalid on validateAndProceed', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('not-an-email'));
    act(() => result.current.validateAndProceed());
    expect(result.current.state).toBe('Error_Recovery');
  });

  it('transitions Data_Entry → Confirmation on valid input', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());
    expect(result.current.state).toBe('Confirmation');
    expect(result.current.data.email).toBe('user@example.com');
  });

  it('transitions Confirmation → Data_Entry on edit()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());
    act(() => result.current.edit());
    expect(result.current.state).toBe('Data_Entry');
  });

  it('transitions Confirmation → Processing → Result on successful confirm', async () => {
    vi.mocked(api.requestPasswordReset).mockResolvedValue({
      success: true,
      message: 'Recovery link sent to your email' });

    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());

    // confirm() starts an async IIFE; the synchronous part sets Processing
    act(() => result.current.confirm());
    expect(result.current.state).toBe('Processing');
    expect(result.current.isProcessing).toBe(true);

    // Flush microtasks (resolve mock) + setTimeout(200)
    await act(async () => {
      await new Promise((r) => setTimeout(r, 300));
    });

    expect(result.current.state).toBe('Result');
    expect(result.current.isProcessing).toBe(false);
  });

  it('transitions Processing → Error_Recovery on failed confirm', async () => {
    vi.mocked(api.requestPasswordReset).mockResolvedValue({
      success: false,
      message: 'Network error' });

    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());

    act(() => result.current.confirm());
    expect(result.current.state).toBe('Processing');

    await act(async () => {
      await new Promise((r) => setTimeout(r, 300));
    });

    expect(result.current.state).toBe('Error_Recovery');
    expect(result.current.errorMessage).not.toBeNull();
    expect(result.current.errorMessage?.solutions.length).toBeGreaterThanOrEqual(2);
  });

  it('transitions Error_Recovery → Data_Entry on retry()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('bad-email'));
    act(() => result.current.validateAndProceed());
    expect(result.current.state).toBe('Error_Recovery');

    act(() => result.current.retry());
    expect(result.current.state).toBe('Data_Entry');
  });

  it('transitions Error_Recovery → Welcome on cancel()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('bad-email'));
    act(() => result.current.validateAndProceed());
    expect(result.current.state).toBe('Error_Recovery');

    act(() => result.current.cancel());
    expect(result.current.state).toBe('Welcome');
  });

  it('transitions Result → Welcome via reset()', async () => {
    vi.mocked(api.requestPasswordReset).mockResolvedValue({
      success: true,
      message: 'Sent' });

    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    act(() => result.current.start());
    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());
    act(() => result.current.confirm());

    await act(async () => {
      await new Promise((r) => setTimeout(r, 300));
    });

    expect(result.current.state).toBe('Result');
    act(() => result.current.reset());
    expect(result.current.state).toBe('Welcome');
    expect(result.current.data.email).toBe('');
  });

  it('rejects forbidden transitions (Welcome → Result) via confirm()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    // confirm() should not change state from Welcome (not in Confirmation)
    act(() => result.current.confirm());
    expect(result.current.state).toBe('Welcome');
  });

  it('rejects forbidden transitions (Welcome → Result) via back()', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    // back() from Welcome should stay at Welcome
    act(() => result.current.back());
    expect(result.current.state).toBe('Welcome');
  });

  it('calculates step percentage based on current state', () => {
    const { result } = renderHook(() => usePasswordRecoveryFSM('en'));
    // Welcome → step 0 → 0%
    expect(result.current.stepPct).toBe(0);

    act(() => result.current.start());
    // Data_Entry → step 1 → 25%
    expect(result.current.stepPct).toBe(25);

    act(() => result.current.setEmail('user@example.com'));
    act(() => result.current.validateAndProceed());
    // Confirmation → step 2 → 50%
    expect(result.current.stepPct).toBe(50);
  });
});
