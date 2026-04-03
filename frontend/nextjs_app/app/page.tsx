export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-white mb-4">OCH Platform</h1>
        <p className="text-xl text-gray-300 mb-8">Africa's Premier Cybersecurity Platform</p>
        <div className="space-x-4">
          <a 
            href="/login/student" 
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Sign In
          </a>
          <a 
            href="/signup/student" 
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold"
          >
            Get Started
          </a>
        </div>
      </div>
    </div>
  )
}
