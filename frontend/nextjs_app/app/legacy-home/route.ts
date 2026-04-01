import { existsSync } from 'fs'
import { promises as fs } from 'fs'
import path from 'path'

const MARKETING_HTML = 'OCH-CCF_Interactive_Platform_Revised.html'

/** Next may use `frontend/nextjs_app` or monorepo root as cwd; walk up until the file is found. */
function resolveMarketingHtmlPath(): string {
  const publicCandidate = path.join(process.cwd(), 'public', MARKETING_HTML)
  if (existsSync(publicCandidate)) {
    return publicCandidate
  }

  let dir = process.cwd()
  for (let i = 0; i < 10; i++) {
    const candidate = path.join(dir, MARKETING_HTML)
    if (existsSync(candidate)) {
      return candidate
    }

    const candidateInPublic = path.join(dir, 'public', MARKETING_HTML)
    if (existsSync(candidateInPublic)) {
      return candidateInPublic
    }
    const parent = path.dirname(dir)
    if (parent === dir) {
      break
    }
    dir = parent
  }
  throw new Error(
    `Could not find ${MARKETING_HTML} (started search from ${process.cwd()})`
  )
}

export async function GET() {
  const htmlPath = resolveMarketingHtmlPath()
  let html = await fs.readFile(htmlPath, 'utf8')

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
      // Safari-friendly CSP - allow localhost and relax frame restrictions for dev
      'Content-Security-Policy': "default-src 'self' 'unsafe-inline' 'unsafe-eval'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' http://localhost:8000 https://localhost:8000; frame-ancestors 'self' http://localhost:* https://localhost:*;",
      // Remove X-Frame-Options to avoid conflict with CSP frame-ancestors
    },
  })
}
