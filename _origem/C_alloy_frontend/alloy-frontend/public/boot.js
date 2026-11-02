// Aplica tema e idioma salvos antes da primeira pintura (evita "piscar" do tema).
// Arquivo externo para respeitar a CSP (script-src 'self', sem inline).
(function () {
  try {
    var raw = localStorage.getItem('alloy.prefs');
    var prefs = raw ? JSON.parse(raw).state || JSON.parse(raw) : null;
    var legacyTheme = localStorage.getItem('crystalab-theme');
    var theme = (prefs && prefs.theme) || legacyTheme || 'system';
    if (theme === 'system') theme = window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = theme;
    if (prefs && prefs.locale) document.documentElement.lang = prefs.locale;
  } catch (e) { /* armazenamento indisponível: usa padrões */ }
})();
