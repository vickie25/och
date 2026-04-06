import { existsSync } from 'fs'
import { promises as fs } from 'fs'
import path from 'path'

// Prefer the newer OCF file name; fall back to the existing CCF asset.
const MARKETING_HTML_CANDIDATES = [
  'OCH-OCF_Interactive_Platform_Revised.html',
  'OCH-CCF_Interactive_Platform_Revised.html',
]

/** Next may use `frontend/nextjs_app` or monorepo root as cwd; walk up until the file is found. */
function resolveMarketingHtmlPath(): string {
  for (const filename of MARKETING_HTML_CANDIDATES) {
    const publicCandidate = path.join(process.cwd(), 'public', filename)
    if (existsSync(publicCandidate)) {
      return publicCandidate
    }
  }

  let dir = process.cwd()
  for (let i = 0; i < 10; i++) {
    for (const filename of MARKETING_HTML_CANDIDATES) {
      const candidate = path.join(dir, filename)
      if (existsSync(candidate)) {
        return candidate
      }

      const candidateInPublic = path.join(dir, 'public', filename)
      if (existsSync(candidateInPublic)) {
        return candidateInPublic
      }
    }
    const parent = path.dirname(dir)
    if (parent === dir) {
      break
    }
    dir = parent
  }
  throw new Error(
    `Could not find marketing HTML (${MARKETING_HTML_CANDIDATES.join(' or ')}) (started search from ${process.cwd()})`
  )
}

/** CSP for the static marketing document (not the Next shell). Include prod host + localhost. */
function legacyHomeContentSecurityPolicy(): string {
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
 * Safari/WebKit can paint a dark page when gradient + background-clip:text + transparent fill fails
 * (many h1 rules in the marketing HTML use this pattern).
 */
const SAFARI_HEADLINE_FIX = `
<script>
(function () {
  var ua = navigator.userAgent || '';
  var isSafari = /Safari\\//.test(ua) && !/Chrom(e|ium)\\//.test(ua);
  if (isSafari) document.documentElement.classList.add('och-safari-text-fallback');
})();
</script>
<style id="och-safari-headline-fallback">
.och-safari-text-fallback h1 {
  -webkit-text-fill-color: #f1f5f9 !important;
  color: #f1f5f9 !important;
  background: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
}
.och-safari-text-fallback .landing-h1 {
  color: #e2e8f0 !important;
  -webkit-text-fill-color: #e2e8f0 !important;
  background: none !important;
}
.och-safari-text-fallback .landing-h1 span,
.och-safari-text-fallback .gradient-text,
.och-safari-text-fallback .pr-h2 span,
.och-safari-text-fallback .ch-title span,
.och-safari-text-fallback .wl-hero h2 span,
.och-safari-text-fallback .wl-chip .wl-num,
.och-safari-text-fallback .wl-price-big,
.och-safari-text-fallback .wl-reg-header h2,
.och-safari-text-fallback .wl-pay-amount-val {
  -webkit-text-fill-color: #f59e0b !important;
  color: #ea580c !important;
  background: none !important;
  -webkit-background-clip: border-box !important;
  background-clip: border-box !important;
}
</style>
`

export async function GET() {
  const htmlPath = resolveMarketingHtmlPath()
  let html = await fs.readFile(htmlPath, 'utf8')

  html = html.replace('<head>', `<head>${SAFARI_HEADLINE_FIX}`)

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

    // When embedded in an iframe on "/", navigate the top window for real app routes (URL bar updates).
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
      // Allow embedding this marketing doc in the homepage iframe (same-origin).
      // Next may add `X-Frame-Options: DENY` by default; setting SAMEORIGIN here overrides it.
      'X-Frame-Options': 'SAMEORIGIN',
      'Content-Security-Policy': legacyHomeContentSecurityPolicy(),
    },
  })
}
