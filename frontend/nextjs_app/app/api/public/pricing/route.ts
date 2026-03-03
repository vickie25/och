import { NextResponse } from 'next/server'
import { apiGateway } from '@/services/apiGateway'

export async function GET() {
  try {
    const response = await apiGateway.get<any>('/admin/plans/', { skipAuth: true })
    
    let plans: any[] = []
    if (response?.results && Array.isArray(response.results)) {
      plans = response.results
    } else if (Array.isArray(response)) {
      plans = response
    }
    
    return NextResponse.json({ plans })
  } catch (error) {
    console.error('Failed to fetch pricing:', error)
    return NextResponse.json({ plans: [] }, { status: 200 })
  }
}
