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
    "style-src 'self' 'nonce-" + nonce + "'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "connect-src 'self' http://localhost:3000 https:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');
}

const SUPPORTED_LOCALES = ['en', 'fa'];
const DEFAULT_LOCALE = 'fa';

function getLocaleFromRequest(request: NextRequest): string {
  const cookieLocale = request.cookies.get('locale')?.value;
  if (cookieLocale && SUPPORTED_LOCALES.includes(cookieLocale)) {
    return cookieLocale;
  }
  const acceptLanguage = request.headers.get('accept-language');
  if (acceptLanguage) {
    const headerLocale = acceptLanguage.split(',')[0]?.split('-')[0];
    if (headerLocale && SUPPORTED_LOCALES.includes(headerLocale)) {
      return headerLocale;
    }
  }
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

  const hasLocalePrefix = SUPPORTED_LOCALES.some(
    (loc) => pathname === `/${loc}` || pathname.startsWith(`/${loc}/`)
  );

  let response: NextResponse;
  if (!hasLocalePrefix) {
    url.pathname = `/${locale}${pathname}`;
    response = NextResponse.redirect(url);
  } else {
    response = NextResponse.next();
  }

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