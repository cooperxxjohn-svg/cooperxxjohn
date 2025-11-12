import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for BOQ processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

export interface ContractDetails {
  project_name: string;
  location: string;
  contract_no?: string;
  department?: string;
  client?: string;
  completion_days?: number;
  estimated_cost?: number;
}

export interface BOQItem {
  item_no: string;
  description: string;
  category?: string;
  unit?: string;
  quantity?: number;
  unit_rate?: number;
  total_amount?: number;
  location?: string;
  specification?: string;
  materials?: Array<{
    name: string;
    grade?: string;
    quantity?: number;
    rate?: number;
    amount?: number;
  }>;
  labour?: Array<{
    category: string;
    quantity?: number;
    rate?: number;
    amount?: number;
  }>;
}

export interface BOQSection {
  section_no: string;
  title: string;
  description?: string;
  items: BOQItem[];
}

export interface BOQDocument {
  boq_id: string;
  contract: {
    contract_name: string;
    location: string;
    department: string;
    client?: string;
  };
  sections: BOQSection[];
  total_amount: number;
  gst_percentage?: number;
  created_date: string;
}

export interface ValidationIssue {
  category: string;
  message: string;
  severity: 'error' | 'warning' | 'info';
}

export interface ValidationResult {
  is_valid: boolean;
  total_issues: number;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  info: ValidationIssue[];
}

export interface EstimationResponse {
  job_id: string;
  boq: BOQDocument;
  validation: ValidationResult;
  category_summary: Record<string, { amount: number }>;
}

// API methods
export const apiClient = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Upload drawings and create BOQ estimation
  async createEstimation(files: File[], contractDetails: ContractDetails) {
    const formData = new FormData();

    files.forEach((file) => {
      formData.append('drawings', file);
    });

    Object.entries(contractDetails).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        formData.append(key, value.toString());
      }
    });

    const response = await api.post<EstimationResponse>('/estimate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Download BOQ in various formats
  async downloadBOQ(format: 'excel' | 'pdf' | 'csv' | 'json') {
    const response = await api.get(`/download/${format}`, {
      responseType: 'blob',
    });

    return response.data;
  },

  // Download with proper filename
  downloadFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};

export default api;
