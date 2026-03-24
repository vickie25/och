import { promises as fs } from 'fs'
import path from 'path'

export async function GET() {
  const htmlPath = path.resolve(process.cwd(), '../../OCH-CCF_Interactive_Platform_Revised.html')
  const html = await fs.readFile(htmlPath, 'utf8')

  const authBridgeScript = `
<script>
  (function () {
    // Force all homepage auth actions to use app-native auth routes.
    window.showAuth = function (mode) {
      if (mode === 'login') {
        window.location.href = '/login';
        return;
      }
      window.location.href = '/register';
    };

    window.closeAuth = function () {
      var overlay = document.getElementById('auth-overlay');
      if (overlay) overlay.classList.remove('show');
    };

    document.addEventListener('DOMContentLoaded', function () {
      var authBtn = document.getElementById('auth-btn');
      if (authBtn) {
        authBtn.onclick = function () {
          var text = (authBtn.textContent || '').toLowerCase();
          if (text.indexOf('sign in') !== -1) {
            window.location.href = '/login';
            return false;
          }
          window.location.href = '/register';
          return false;
        };
      }
    });
  })();
</script>`

  const patchedHtml = html.includes('</body>')
    ? html.replace('</body>', `${authBridgeScript}\n</body>`)
    : `${html}\n${authBridgeScript}`

  return new Response(patchedHtml, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
    },
  })
}
