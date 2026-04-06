import { existsSync } from 'fs'
import { promises as fs } from 'fs'
import path from 'path'

// Prefer the newer OCF file name; fall back to the existing CCF asset.
const MARKETING_HTML_CANDIDATES = [
  'OCH-OCF_Interactive_Platform_Revised.html',
  'OCH-CCF_Interactive_Platform_Revised.html',
]

/**
 * Resolve marketing HTML under `public/` only (fixed paths — no parent-dir walk).
 * Keeps Turbopack/NFT from tracing the whole monorepo. Use turbopackIgnore on cwd joins.
 */
function resolveMarketingHtmlPath(): string {
  const bases = [
    path.join(/* turbopackIgnore: true */ process.cwd(), 'public'),
    path.join(/* turbopackIgnore: true */ process.cwd(), 'frontend', 'nextjs_app', 'public'),
    path.join(/* turbopackIgnore: true */ process.cwd(), 'nextjs_app', 'public'),
  ]
  for (const base of bases) {
    for (const filename of MARKETING_HTML_CANDIDATES) {
      const p = path.join(base, filename)
      if (existsSync(p)) {
        return p
      }
    }
  }
  throw new Error(
    `Could not find marketing HTML (${MARKETING_HTML_CANDIDATES.join(' or ')}) under public/ (cwd=${process.cwd()})`
  )
}

/** CSP for the static marketing document (not the Next shell). Include prod host + localhost. */
function marketingHomeContentSecurityPolicy(): string {
  const connect = [
    "'self'",
    'http://localhost:8000',
    'https://localhost:8000',
    'https://cybochengine.africa',
    'https://www.cybochengine.africa',
  ]
  const fe = process.env.NEXT_PUBLIC_FRONTEND_URL
  if (fe) {
    try {
      const u = new URL(fe)
      const o = `${u.protocol}//${u.host}`
      if (!connect.includes(o)) connect.push(o)
    } catch {
      /* ignore */
    }
  }
  const frame = [
    "'self'",
    'https://cybochengine.africa',
    'https://www.cybochengine.africa',
    'http://localhost:*',
    'https://localhost:*',
  ]
  return [
    "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' data: https://fonts.gstatic.com",
    "img-src 'self' data: https: blob:",
    `connect-src ${connect.join(' ')}`,
    `frame-ancestors ${frame.join(' ')}`,
  ].join('; ')
}

/**
 * WebKit (Safari + all iOS browsers) fixes for the static marketing HTML:
 * - Gradient + background-clip:text + transparent fill can render invisible text.
 * - body::before { z-index: -1 } can compositor-blank the page in Safari.
 * - backdrop-filter without -webkit-backdrop-filter can black out glass layers.
 */
const MARKETING_WEBKIT_FIX = `
<script>
(function () {
  var ua = navigator.userAgent || '';
  var isIOS =
    /iPad|iPhone|iPod/.test(ua) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isDesktopSafari = /Safari/i.test(ua) && !/Chrom(e|ium)|CriOS|FxiOS|Edg/i.test(ua);
  if (isIOS || isDesktopSafari) {
    document.documentElement.classList.add('och-webkit-landing-fix');
  }
})();
</script>
<style id="och-webkit-landing-fix">
.och-webkit-landing-fix body {
  isolation: isolate;
}
.och-webkit-landing-fix body::before {
  z-index: 0 !important;
}
.och-webkit-landing-fix .container,
.och-webkit-landing-fix .content {
  position: relative;
  z-index: 1;
}
.och-webkit-landing-fix header {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .nav-dropdown-menu {
  -webkit-backdrop-filter: blur(24px);
}
.och-webkit-landing-fix .card {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .option-card {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .result-card {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .pathway-header {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .pnode {
  -webkit-backdrop-filter: blur(16px);
}
.och-webkit-landing-fix .pathway-hover-card {
  -webkit-backdrop-filter: blur(30px);
}
.och-webkit-landing-fix .ac-header {
  -webkit-backdrop-filter: blur(12px);
}
.och-webkit-landing-fix .framework-map-card {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .auth-overlay {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .sticky-cta {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .ch-card {
  -webkit-backdrop-filter: blur(20px);
}
.och-webkit-landing-fix .wl-map-stats {
  -webkit-backdrop-filter: blur(12px);
}
.och-webkit-landing-fix .wl-reg-overlay {
  -webkit-backdrop-filter: blur(16px);
}
.och-webkit-landing-fix h1 {
  -webkit-text-fill-color: #f1f5f9 !important;
  color: #f1f5f9 !important;
  background: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
}
.och-webkit-landing-fix .landing-h1 {
  color: #e2e8f0 !important;
  -webkit-text-fill-color: #e2e8f0 !important;
  background: none !important;
}
.och-webkit-landing-fix .landing-h1 span,
.och-webkit-landing-fix .gradient-text,
.och-webkit-landing-fix .pr-h2 span,
.och-webkit-landing-fix .ch-title span,
.och-webkit-landing-fix .wl-hero h2 span,
.och-webkit-landing-fix .wl-chip .wl-num,
.och-webkit-landing-fix .wl-price-big,
.och-webkit-landing-fix .wl-reg-header h2,
.och-webkit-landing-fix .wl-pay-amount-val,
.och-webkit-landing-fix .journey-modal-title {
  -webkit-text-fill-color: #f59e0b !important;
  color: #ea580c !important;
  background: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
}
</style>
`

/** Full HTML document for the interactive marketing landing (served at `/` and `/legacy-home`). */
export async function getMarketingHomeDocumentResponse(): Promise<Response> {
  const htmlPath = resolveMarketingHtmlPath()
  let html = await fs.readFile(htmlPath, 'utf8')

  html = html.replace('<head>', `<head>${MARKETING_WEBKIT_FIX}`)

  // Remove JS that overrides "Join Pioneer Cohort" to open auth; keep inline waitlist handler.
  html = html.replace(
    /\r?\n\s*\/\/ Wire CTA buttons[^\r\n]*\r?\n\s*const mainCta = document\.getElementById\('join-cta'\);\r?\n\s*if \(mainCta\) \{\r?\n\s*mainCta\.addEventListener\('click', \(\) => \{ showAuth\('register'\); \}\);\r?\n\s*\}\r?\n/,
    '\n'
  )

  const authBridgeScript = `
<script>
  (function () {
    function goApp(path) {
      var w = window.top || window;
      w.location.assign(path);
    }
    function goGetStarted(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      goApp('/register');
    }

    window.showAuth = function (mode) {
      if (mode === 'login') goApp('/login');
      else goApp('/register');
    };

    window.closeAuth = function () {
      var overlay = document.getElementById('auth-overlay');
      if (overlay) overlay.classList.remove('show');
    };

    document.addEventListener('DOMContentLoaded', function () {
      var style = document.createElement('style');
      style.textContent =
        '.och-nav-signin{display:inline-flex;align-items:center;margin-right:14px;font-size:12px;font-weight:600;color:#94a3b8;text-decoration:none;white-space:nowrap}' +
        '.och-nav-signin:hover{color:#f1f5f9}';
      document.head.appendChild(style);

      var authBtn = document.getElementById('auth-btn');
      if (authBtn) {
        authBtn.onclick = function () {
          goApp('/register');
          return false;
        };
      }

      // Single navbar primary CTA + text Sign in (no duplicate orange buttons from React shell)
      var joinCta = document.getElementById('join-cta');
      if (joinCta && joinCta.parentNode) {
        var signIn = document.createElement('a');
        signIn.className = 'och-nav-signin';
        signIn.href = '/login';
        signIn.textContent = 'Sign in';
        joinCta.parentNode.insertBefore(signIn, joinCta);
        joinCta.removeAttribute('onclick');
        joinCta.onclick = goGetStarted;
        joinCta.textContent = 'Get started';
      }

      document.querySelectorAll('.ov-pioneer-btn').forEach(function (btn) {
        btn.removeAttribute('onclick');
        btn.onclick = goGetStarted;
        btn.textContent = 'Join cohort →';
      });

      var acDeploy = document.getElementById('ac-deploy-cta');
      if (acDeploy) {
        acDeploy.removeAttribute('onclick');
        acDeploy.onclick = goGetStarted;
      }

      var resultJoin = document.getElementById('result-join-cta');
      if (resultJoin) {
        resultJoin.onclick = function (e) {
          goGetStarted(e);
        };
      }
    });

    // Same-origin links to app routes: full navigation so the URL bar updates (marketing doc is not the Next shell).
    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a) return;
      var href = a.getAttribute('href');
      if (!href || href.charAt(0) !== '/' || href.indexOf('//') === 0) return;
      if (!/^\\/(login|register|dashboard|cohorts|onboarding|api|auth|support|finance|student|director|admin|terms|privacy|about|pricing)(\\/|$)/.test(href)) return;
      e.preventDefault();
      goApp(href);
    }, true);
  })();
</script>`

  const patchedHtml = html.includes('</body>')
    ? html.replace('</body>', `${authBridgeScript}\n</body>`)
    : `${html}\n${authBridgeScript}`

  return new Response(patchedHtml, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Frame-Options': 'SAMEORIGIN',
      'Content-Security-Policy': marketingHomeContentSecurityPolicy(),
    },
  })
}
