# Registration Page

## Overview
The Registration page allows new users to create an account on the BedaanWaves platform, providing access to market analysis tools, portfolio management, and personalized features.

## Key Features
- **Account Creation**: Secure registration with email verification
- **Profile Setup**: Basic user information and preferences
- **Password Security**: Strong password requirements with confirmation
- **Email Verification**: Required activation link sent to registered email
- **Terms & Conditions**: Acceptance of platform usage policies

## Form Fields
1. **Email**: Valid email address (used for login and communication)
2. **Password**: Minimum 8 characters with uppercase, lowercase, number, and special character
3. **Confirm Password**: Must match password field
4. **Full Name**: User's legal name for profile display
5. **Accept Terms**: Checkbox required to proceed

## Navigation
- Access via: `/register` (public route)
- Redirects to: `/login` upon successful registration
- Links to: `/login` for existing users

## Validation
- Real-time email format validation
- Password strength meter
- Duplicate email check via API (`POST /api/v1/auth/register`)
- Terms acceptance required before submission

## Technical Details
- Built with React Hook Form for form state management
- API integration: `POST /api/v1/auth/register`
- Success redirects with toast notification
- Error handling for duplicate emails, weak passwords, and server errors
- Responsive design for mobile and desktop