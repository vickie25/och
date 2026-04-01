import { headers } from 'next/headers'

async function getMarketingHtml() {
  const headersList = await headers()
  const host = headersList.get('host') || 'localhost:3000'
  const protocol = process.env.NODE_ENV === 'development' ? 'http' : 'https'
  
  try {
    const res = await fetch(`${protocol}://${host}/legacy-home`, {
      cache: 'no-store'
    })
    if (!res.ok) throw new Error('Failed to fetch')
    return res.text()
  } catch {
    return '<div style="padding:40px;text-align:center;">Loading...</div>'
  }
}

export default async function HomePage() {
  const html = await getMarketingHtml()
  
  // Extract styles from head (get CSS content only, not the tags)
  const stylesMatch = html.match(/<style[^>]*>([\s\S]*?)<\/style>/gi) || []
  const allStyles = stylesMatch.map(s => s.replace(/<\/?style[^>]*>/gi, '')).join('\n')
  
  // Extract body content
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i)
  const bodyContent = bodyMatch ? bodyMatch[1] : html
  
  // Keep all inline scripts (they handle view switching), only remove external scripts
  const cleanedContent = bodyContent
    .replace(/<script[^>]+src=[^>]*>.*?<\/script>/gi, '') // External scripts only
    .replace(/<!DOCTYPE[^>]*>/i, '')
    .replace(/<html[^>]*>|<\/html>/gi, '')
  
  // Add script to handle navigation clicks for Next.js
  const navScript = `<script>
    (function() {
      document.addEventListener('click', function(e) {
        var a = e.target.closest && e.target.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) !== '/') return;
        if (/^\\/(login|register|dashboard|cohorts|onboarding)/.test(href)) {
          e.preventDefault();
          window.location.href = href;
        }
      }, true);
    })();
  </script>`
  
  const fullContent = `<style>${allStyles}</style>${cleanedContent}${navScript}`
  
  return (
    <main 
      className="min-h-screen w-full"
      dangerouslySetInnerHTML={{ __html: fullContent }}
    />
  )
}
