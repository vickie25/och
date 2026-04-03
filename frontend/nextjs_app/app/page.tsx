import { headers } from 'next/headers'

async function getMarketingHtml() {
  const headersList = await headers()
  const host = headersList.get('host') || 'localhost:3000'
  const protocol = process.env.NODE_ENV === 'development' ? 'http' : 'https'
  
  try {
    // Try to fetch from legacy-home route first
    const res = await fetch(`${protocol}://${host}/legacy-home`, {
      cache: 'no-store'
    })
    if (!res.ok) throw new Error('Failed to fetch')
    return res.text()
  } catch (error) {
    console.error('Failed to fetch legacy-home:', error)
    // Fallback to static HTML file
    try {
      const fs = await import('fs')
      const path = await import('path')
      const fsPromises = fs.promises
      const htmlPath = path.join(process.cwd(), 'public', 'OCH-CCF_Interactive_Platform_Revised.html')
      const html = await fsPromises.readFile(htmlPath, 'utf8')
      return html
    } catch (fileError) {
      console.error('Failed to read HTML file:', fileError)
      return '<div style="padding:40px;text-align:center;">Loading...</div>'
    }
  }
}

export default async function HomePage() {
  const html = await getMarketingHtml()
  
  // Extract styles from head (get CSS content only, not <style> tags)
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
  
  // Add script to handle navigation clicks for Next.js - Safari compatible
  const navScript = `<script>
    (function() {
      function handleNavClick(e) {
        var a = e.target.closest && e.target.closest('a[href]');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) !== '/') return;
        if (/^\\/(login|register|dashboard|cohorts|onboarding)/.test(href)) {
          e.preventDefault();
          e.stopPropagation();
          // Safari-friendly navigation
          window.location.href = href;
          return false;
        }
      }
      // Use capture phase for better Safari compatibility
      document.addEventListener('click', handleNavClick, true);
      // Also handle touch events for iOS Safari
      document.addEventListener('touchend', function(e) {
        handleNavClick(e);
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
