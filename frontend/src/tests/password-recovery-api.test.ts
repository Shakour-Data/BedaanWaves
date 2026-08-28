vi.mock('@/lib/api', () => ({
  apiClient: {
    post: vi.fn() } }));

vi.mock('@/store/useAuthStore', () => ({
  useAuthStore: () => ({
    "en": 'en',
    token: null,
    refreshToken: null }) }));

import {
  isValidEmail,
  isValidPassword,
  passwordsMatch,
  saveDraftEmail,
  getDraftEmail,
  clearDraftEmail,
  requestPasswordReset,
  verifyResetToken,
  confirmResetPassword } from '@/lib/password-recovery-api';
import { apiClient } from '@/lib/api';

describe('password-recovery-api utilities', () => {
  describe('isValidEmail', () => {
    it('accepts valid emails', () => {
      expect(isValidEmail('user@example.com')).toBe(true);
      expect(isValidEmail('test.name+tag@sub.domain.co')).toBe(true);
    });

    it('rejects invalid emails', () => {
      expect(isValidEmail('')).toBe(false);
      expect(isValidEmail('not-an-email')).toBe(false);
      expect(isValidEmail('missing@domain')).toBe(false);
      expect(isValidEmail('spaces in@email.com')).toBe(false);
      expect(isValidEmail('special<chars>@email.com')).toBe(false);
    });
  });

  describe('isValidPassword', () => {
    it('accepts passwords >= 8 characters', () => {
      expect(isValidPassword('password123')).toBe(true);
      expect(isValidPassword('12345678')).toBe(true);
    });

    it('rejects passwords < 8 characters', () => {
      expect(isValidPassword('')).toBe(false);
      expect(isValidPassword('short')).toBe(false);
      expect(isValidPassword('1234567')).toBe(false);
    });
  });

  describe('passwordsMatch', () => {
    it('returns true when passwords match', () => {
      expect(passwordsMatch('secret123', 'secret123')).toBe(true);
    });

    it('returns false when passwords differ', () => {
      expect(passwordsMatch('secret123', 'secret456')).toBe(false);
    });

    it('returns false when either is empty', () => {
      expect(passwordsMatch('', '')).toBe(false);
      expect(passwordsMatch('secret', '')).toBe(false);
    });
  });

  describe('localStorage draft email', () => {
    beforeEach(() => {
      localStorage.clear();
    });

    it('saves and retrieves draft email', () => {
      saveDraftEmail('draft@example.com');
      expect(getDraftEmail()).toBe('draft@example.com');
    });

    it('clears draft email', () => {
      saveDraftEmail('draft@example.com');
      clearDraftEmail();
      expect(getDraftEmail()).toBe('');
    });

    it('returns empty string when no draft', () => {
      expect(getDraftEmail()).toBe('');
    });
  });

  describe('requestPasswordReset', () => {
    beforeEach(() => {
      vi.mocked(apiClient.post).mockReset();
      localStorage.clear();
    });

    it('returns success on 200 response', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: { status: 'success', message: 'Recovery link sent to your email' } });

      const result = await requestPasswordReset({ email: 'user@example.com' });
      expect(result.success).toBe(true);
      expect(result.message).toBe('Recovery link sent to your email');
      expect(apiClient.post).toHaveBeenCalledWith(
        'auth/password-reset/request',
        { email: 'user@example.com' },
      );
    });

    it('returns failure on network error', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'));

      const result = await requestPasswordReset({ email: 'user@example.com' });
      expect(result.success).toBe(false);
    });
  });

  describe('verifyResetToken', () => {
    beforeEach(() => {
      vi.mocked(apiClient.post).mockReset();
    });

    it('returns valid=true on 200 response', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: { valid: true, email_hint: null } });

      const result = await verifyResetToken('token-abc');
      expect(result).toBe(true);
    });

    it('returns valid=false on 400 response', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        response: { data: { detail: 'Invalid token' } } });

      const result = await verifyResetToken('bad-token', 'en');
      expect(result.valid).toBe(false);
    });
  });

  describe('confirmResetPassword', () => {
    beforeEach(() => {
      vi.mocked(apiClient.post).mockReset();
    });

    it('returns success on valid reset', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({
        data: { status: 'success', message: 'Password updated' } });

      const result = await confirmResetPassword({ token: 'token-abc', newPassword: 'newpassword123' });
      expect(result.success).toBe(true);
      expect(result.message).toBe('Password updated');
    });

    it('returns failure with detail message', async () => {
      vi.mocked(apiClient.post).mockRejectedValue({
        response: { data: { detail: 'Token expired' } } });

      const result = await confirmResetPassword({ token: 'expired', newPassword: 'newpassword123' });
      expect(result.success).toBe(false);
      expect(result.message).toBe('Token expired');
    });
  });
});
