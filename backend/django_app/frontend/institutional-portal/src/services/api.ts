/**
 * API Service for Institutional Portal
 * Handles all API calls to the Django backend
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// Types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  error?: string;
}

export interface Contract {
  id: string;
  contract_number: string;
  organization: {
    id: number;
    name: string;
  };
  status: string;
  start_date: string;
  end_date: string;
  student_seat_count: number;
  per_student_rate: number;
  billing_cycle: string;
  monthly_amount: number;
  annual_amount: number;
  active_students: number;
  seat_utilization: number;
  total_invoiced: number;
  days_until_expiry: number;
  is_renewable: boolean;
}

export interface SeatPool {
  id: string;
  name: string;
  pool_type: string;
  contract: {
    id: string;
    contract_number: string;
    organization: string;
  };
  allocated_seats: number;
  active_seats: number;
  reserved_seats: number;
  available_seats: number;
  utilization_rate: number;
  department: string;
  auto_recycle: boolean;
  recycle_delay_days: number;
  created_at: string;
}

export interface StudentAllocation {
  allocation_id: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  status: string;
  department: string;
  allocated_at: string;
  activated_at?: string;
  assigned_tracks: string[];
  completion_deadline?: string;
  enrollment?: {
    id: string;
    cohort?: string;
    status: string;
  };
}

export interface BulkImport {
  id: string;
  filename: string;
  contract: {
    id: string;
    contract_number: string;
    organization: string;
  };
  seat_pool: {
    id: string;
    name: string;
  };
  status: string;
  total_records: number;
  successful_records: number;
  failed_records: number;
  created_at: string;
  completed_at?: string;
}

export interface DashboardAnalytics {
  contract_info: {
    contract_number: string;
    organization: string;
    status: string;
    start_date: string;
    end_date: string;
    licensed_seats: number;
    monthly_cost: number;
    annual_cost: number;
  };
  seat_utilization: {
    total_allocated: number;
    total_active: number;
    total_available: number;
    utilization_rate: number;
    pools: Array<{
      name: string;
      type: string;
      allocated: number;
      active: number;
      available: number;
      utilization: number;
    }>;
  };
  student_metrics: {
    total_students: number;
    active_students: number;
    completed_students: number;
    withdrawn_students: number;
    completion_rate: number;
    avg_progress: number;
  };
  track_assignments: {
    mandatory_assignments: number;
    completed_assignments: number;
    overdue_assignments: number;
    completion_rate: number;
  };
  roi_metrics: {
    cost_per_student: number;
    avg_completion_time_days: number;
    certification_rate: number;
    roi_percentage: number;
  };
  engagement: {
    avg_login_frequency: number;
    avg_session_duration: number;
    active_last_30_days: number;
    engagement_score: number;
  };
}

export interface StudentProgress {
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  seat_pool: string;
  department: string;
  status: string;
  allocated_at: string;
  track_assignments: Array<{
    track_name: string;
    assignment_type: string;
    status: string;
    progress_percentage: number;
    due_date?: string;
    is_overdue: boolean;
  }>;
  overall_progress: number;
  last_activity: string;
  completion_rate: number;
  cohort?: {
    id: string;
    name: string;
  };
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for auth
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        } else if (error.response?.status >= 500) {
          toast.error('Server error. Please try again later.');
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(email: string, password: string): Promise<{ token: string; user: any }> {
    const response = await this.api.post('/auth/login/', { email, password });
    return response.data;
  }

  async getPortalAccess(): Promise<{ portal_access: any[]; has_access: boolean }> {
    const response = await this.api.get('/institutional/portal-access/');
    return response.data;
  }

  // Contracts
  async getContracts(): Promise<{ contracts: Contract[] }> {
    const response = await this.api.get('/institutional/contracts/');
    return response.data;
  }

  async getContract(contractId: string): Promise<Contract> {
    const response = await this.api.get(`/institutional/contracts/${contractId}/`);
    return response.data;
  }

  // Seat Pools
  async getSeatPools(contractId?: string): Promise<{ seat_pools: SeatPool[] }> {
    const params = contractId ? { contract_id: contractId } : {};
    const response = await this.api.get('/institutional/seat-pools/', { params });
    return response.data;
  }

  async createSeatPool(data: {
    contract_id: string;
    name: string;
    allocated_seats: number;
    pool_type?: string;
    department?: string;
    allowed_tracks?: string[];
  }): Promise<{ id: string; message: string }> {
    const response = await this.api.post('/institutional/seat-pools/', data);
    return response.data;
  }

  async getSeatPoolStudents(poolId: string, filters?: {
    status?: string;
    department?: string;
  }): Promise<{ students: StudentAllocation[]; total_count: number }> {
    const response = await this.api.get(`/institutional/seat-pools/${poolId}/students/`, {
      params: filters,
    });
    return response.data;
  }

  async allocateStudent(poolId: string, data: {
    user_id?: number;
    email?: string;
    assigned_cohort_id?: string;
    assigned_tracks?: string[];
    department?: string;
  }): Promise<{ allocation_id: string; message: string; status: string }> {
    const response = await this.api.post(`/institutional/seat-pools/${poolId}/allocate_student/`, data);
    return response.data;
  }

  // Bulk Imports
  async getBulkImports(contractId?: string): Promise<{ imports: BulkImport[] }> {
    const params = contractId ? { contract_id: contractId } : {};
    const response = await this.api.get('/institutional/bulk-imports/', { params });
    return response.data;
  }

  async createBulkImport(data: {
    contract_id: string;
    seat_pool_id: string;
    csv_file: File;
    auto_enroll?: boolean;
    send_welcome_emails?: boolean;
    update_existing?: boolean;
    default_cohort?: string;
    default_tracks?: string[];
  }): Promise<{
    import_id: string;
    status: string;
    total_records: number;
    successful_records: number;
    failed_records: number;
    message: string;
  }> {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (key === 'csv_file') {
        formData.append(key, value as File);
      } else if (Array.isArray(value)) {
        value.forEach((item) => formData.append(`${key}[]`, item));
      } else {
        formData.append(key, String(value));
      }
    });

    const response = await this.api.post('/institutional/bulk-imports/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  async getBulkImportDetails(importId: string): Promise<BulkImport & {
    import_results: any;
    error_log: string[];
    import_settings: any;
  }> {
    const response = await this.api.get(`/institutional/bulk-imports/${importId}/`);
    return response.data;
  }

  // Dashboard & Analytics
  async getDashboardAnalytics(contractId: string): Promise<DashboardAnalytics> {
    const response = await this.api.get('/institutional/dashboard/', {
      params: { contract_id: contractId },
    });
    return response.data;
  }

  async getStudentProgressReport(contractId: string): Promise<{
    students: StudentProgress[];
    summary: {
      total_students: number;
      avg_progress: number;
      on_track_students: number;
      behind_students: number;
    };
  }> {
    const response = await this.api.get('/institutional/student-progress/', {
      params: { contract_id: contractId },
    });
    return response.data;
  }

  // Seat Management
  async recycleSeats(contractId: string, daysInactive: number = 30): Promise<{
    message: string;
    recycled_students: any[];
    seats_recycled: number;
    errors: string[];
  }> {
    const response = await this.api.post('/institutional/recycle-seats/', {
      contract_id: contractId,
      days_inactive: daysInactive,
    });
    return response.data;
  }

  // Export
  async exportStudentData(contractId: string): Promise<Blob> {
    const response = await this.api.get('/institutional/export-students/', {
      params: { contract_id: contractId },
      responseType: 'blob',
    });
    return response.data;
  }

  // Utility method for handling API errors
  handleApiError(error: any): string {
    if (error.response?.data?.error) {
      return error.response.data.error;
    } else if (error.response?.data?.message) {
      return error.response.data.message;
    } else if (error.message) {
      return error.message;
    } else {
      return 'An unexpected error occurred';
    }
  }
}

export const apiService = new ApiService();
export default apiService;