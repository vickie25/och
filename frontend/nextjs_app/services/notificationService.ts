import { apiGateway } from '@/services/apiGateway'

export const notificationService = {
  async getAll() {
    return apiGateway.get('/notifications/')
  },

  async getUnreadCount() {
    return apiGateway.get('/notifications/unread_count')
  },

  async markAsRead(id: string) {
    return apiGateway.post(`/notifications/${id}/mark_read/`)
  },

  async markAllAsRead() {
    return apiGateway.post('/notifications/mark_all_read/')
  },

  async getPreferences() {
    return apiGateway.get('/notifications/preferences')
  },

  async updatePreferences(preferences: any) {
    return apiGateway.put('/notifications/update_preferences/', preferences)
  }
}
