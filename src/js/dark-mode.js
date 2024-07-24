// dark_mode.js
(() => {
    // Set color-scheme to dark
    document.documentElement.style.colorScheme = 'dark';

    // Add a meta tag for color-scheme if it doesn't exist
    if (!document.querySelector('meta[name="color-scheme"]')) {
        const meta = document.createElement('meta');
        meta.name = 'color-scheme';
        meta.content = 'dark';
        document.head.appendChild(meta);
    }

    // Set prefers-color-scheme media query (for Tailwind's media strategy)
    const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    Object.defineProperty(darkModeMediaQuery, 'matches', { get: () => true });
    window.dispatchEvent(new Event('dark-mode-change'));

    // Add 'dark' class to <html> element (for Tailwind's class strategy)
    document.documentElement.classList.add('dark');

    // Attempt to trigger any custom dark mode logic
    document.dispatchEvent(new CustomEvent('darkmode', { detail: { darkMode: true } }));

    // Force re-render for frameworks that might not react to class changes
    document.body.style.display = 'none';
    document.body.offsetHeight; // Trigger reflow
    document.body.style.display = '';
})();