import { NextRequest, NextResponse } from 'next/server';
 
const SUPPORTED_LOCALES = ['en', 'fa'];
const DEFAULT_LOCALE = 'fa';
 
function getLocaleFromRequest(request: NextRequest): string {
  // 1. Check cookie
  const cookieLocale = request.cookies.get('locale')?.value;
  if (cookieLocale && SUPPORTED_LOCALES.includes(cookieLocale)) {
    return cookieLocale;
  }
 
  // 2. Check Accept-Language header
  const acceptLanguage = request.headers.get('accept-language');
  if (acceptLanguage) {
    const headerLocale = acceptLanguage.split(',')[0]?.split('-')[0];
    if (headerLocale && SUPPORTED_LOCALES.includes(headerLocale)) {
      return headerLocale;
    }
  }
 
  // 3. Return default
  return DEFAULT_LOCALE;
}
 
export function middleware(request: NextRequest) {
  const url = request.nextUrl.clone();
  const pathname = url.pathname;
 
  // Skip internal paths and static files
  if (
    pathname.startsWith('/api/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon.ico') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }
 
  // Check if path already has locale prefix
  const hasLocalePrefix = SUPPORTED_LOCALES.some(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`)
  );
 
  if (!hasLocalePrefix) {
    const locale = getLocaleFromRequest(request);
    url.pathname = `/${locale}${pathname}`;
    
    // Set cookie for future requests
    const response = NextResponse.redirect(url);
    response.cookies.set('locale', locale, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365, // 1 year
      sameSite: 'lax',
    });
    return response;
  }
 
  // For paths with locale, ensure we set the cookie
  const currentLocale = pathname.split('/')[1];
  if (SUPPORTED_LOCALES.includes(currentLocale)) {
    const response = NextResponse.next();
    response.cookies.set('locale', currentLocale, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365,
      sameSite: 'lax',
    });
    return response;
  }
 
  return NextResponse.next();
}
 
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};