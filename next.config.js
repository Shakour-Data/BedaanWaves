module.exports = {
  i18n: {
    locales: ['en', 'fa'],
    defaultLocale: 'fa',
    pageExtensions: ['default.js', 'default.ts', 'jsx', 'tsx'],
    // Add locale detection for non-prefixed routes
    locateInterestedRoutes: () => {
      return {
        '/register': { locales: ['en', 'fa'] },
        '/login': { locales: ['en', 'fa'] },
        '/dashboard': { locales: ['en', 'fa'] },
        '/charts': { locales: ['en', 'fa'] },
      };
    },
  },
};