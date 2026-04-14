/**
 * Habit-Specific Hook
 * Logic for habit tracking and streaks
 */
import { useMemo } from 'react'
import { useCoachingStore } from '@/lib/coaching/store'
import { calculateStreak, getToday } from '@/lib/coaching/utils'
import type { Habit, HabitLog } from '@/lib/coaching/types'

export function useHabits() {
  const { habits, habitLogs, logHabit } = useCoachingStore()
  
  const todayHabits = useMemo(() => {
    const today = getToday()
    return habits.filter(h => h.isActive).map(habit => {
      const logs = habitLogs.filter(log => log.habitId === habit.id)
      const todayLog = logs.find(log => log.date === today)
      const expectedLogs = logs.map(l => ({ date: l.date, completed: l.status === 'completed' }))
      const streakData = calculateStreak(expectedLogs)
      
      return {
        ...habit,
        todayStatus: todayLog?.status || ('pending' as const),
        streakData,
        logs,
      }
    })
  }, [habits, habitLogs])
  
  const handleLogHabit = async (habitId: string, status: HabitLog['status']) => {
    await logHabit(habitId, status)
  }
  
  const getHabitStreak = (habitId: string) => {
    const habit = habits.find(h => h.id === habitId)
    if (!habit) return null
    
    const logs = habitLogs.filter(log => log.habitId === habitId)
    const expectedLogs = logs.map(l => ({ date: l.date, completed: l.status === 'completed' }))
    return calculateStreak(expectedLogs)
  }
  
  return {
    habits,
    todayHabits,
    logHabit: handleLogHabit,
    getHabitStreak,
  }
}
