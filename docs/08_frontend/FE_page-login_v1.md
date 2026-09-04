# Login Page

## Overview
The Login page enables authenticated users to securely access their accounts, portfolio, and personalized features on the BedaanWaves platform.

## Key Features
- **Authentication**: JWT-based authentication with refresh token rotation
- **Session Management**: Secure session cookies with HttpOnly flags
- **Multi-Factor Option**: Two-factor authentication (2FA) support
- **Password Reset**: Forgot password flow with email verification
- **Role-Based Access**: Different layouts for standard vs premium users

## Flow
1. Enter credentials on `/login`
2. Submit form → `/api/v1/auth/login`
3. Receive JWT token → stored in httpOnly cookie
4. Redirect to dashboard or home

## Security Measures
- Password hashing with bcrypt
- Rate limiting on login attempts (5 per minute)
- Account lockout after 5 failed attempts
- Secure cookie attributes (HttpOnly, Secure, SameSite)
- CSRF protection via double submit token

## Technical Details
- Protected route: Requires valid JWT
- Token expiration: 24 hours (access token), 7 days (refresh token)
- Session cleanup on logout
- Integration with JWT secret from `.env`
- Automatic redirect to dashboard on success
- Error handling for expired/invalid tokens

## Technical Details
- Built with React Hook Form
- API endpoint: `POST /api/v1/auth/login`
- Response: JWT token on success, error message on failure
- Client-side validation of token presence
- Redirect logic based on user role
- Mobile-responsive layout