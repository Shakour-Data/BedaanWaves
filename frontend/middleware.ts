import { NextRequest, NextResponse } from 'next/server';

function generateNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Buffer.from(bytes).toString('base64url');
}

function getCspHeader(nonce: string): string {
  return [
    "default-src 'self'",
    "script-src 'self' 'nonce-" + nonce + "'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "connect-src 'self' http://localhost:3000 http://127.0.0.1:3000 http://localhost:8000 https:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');
}

const SUPPORTED_LOCALES = ['en'];
const DEFAULT_LOCALE = 'en';

function getLocaleFromRequest(request: NextRequest): string {
  return DEFAULT_LOCALE;
}

export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const pathname = url.pathname;

  if (
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  const nonce = generateNonce();
  const locale = getLocaleFromRequest(request);

  const response = NextResponse.next();

  response.headers.set('Content-Security-Policy', getCspHeader(nonce));
  response.cookies.set('__csp_nonce', nonce, {
    path: '/',
    maxAge: 60 * 60,
    httpOnly: true,
    sameSite: 'lax',
  });
  response.cookies.set('locale', locale, {
    path: '/',
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
  });

  return response;
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};