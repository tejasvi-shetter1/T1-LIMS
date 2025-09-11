export const APP_CONFIG = {
  name: process.env.REACT_APP_APP_NAME || 'NEPL LIMS',
  company: process.env.REACT_APP_COMPANY_NAME || 'Nextage Engineering Pvt. Ltd.',
  version: '1.0.0',
};

export const API_CONFIG = {
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  version: process.env.REACT_APP_API_VERSION || 'v1',
  timeout: 30000,
};

export const ROUTES = {
  // Public routes
  LOGIN: '/login',
  
  // Customer routes
  CUSTOMER_DASHBOARD: '/customer/dashboard',
  CUSTOMER_SRF_CREATE: '/customer/srf/create',
  CUSTOMER_SRF_LIST: '/customer/srf/list',
  CUSTOMER_SRF_DETAIL: '/customer/srf/:id',
  CUSTOMER_CERTIFICATES: '/customer/certificates',
  
  // Staff routes
  STAFF_DASHBOARD: '/staff/dashboard',
  STAFF_SRF_LIST: '/staff/srf/list',
  STAFF_SRF_DETAIL: '/staff/srf/:id',
  STAFF_JOBS: '/staff/jobs',
  STAFF_JOB_DETAIL: '/staff/jobs/:id',
  STAFF_MEASUREMENTS: '/staff/measurements',
  STAFF_DEVIATIONS: '/staff/deviations',
  STAFF_CERTIFICATES: '/staff/certificates',
} as const;

export const USER_ROLES = {
  ADMIN: 'ADMIN',
  LAB_MANAGER: 'LAB_MANAGER',
  TECHNICIAN: 'TECHNICIAN',
  QA_MANAGER: 'QA_MANAGER',
  CUSTOMER_ADMIN: 'CUSTOMER_ADMIN',
  CUSTOMER_USER: 'CUSTOMER_USER',
} as const;

export const SRF_STATUS_COLORS = {
  submitted: 'bg-blue-100 text-blue-800',
  under_review: 'bg-yellow-100 text-yellow-800',
  accepted: 'bg-green-100 text-green-800',
  inward_completed: 'bg-purple-100 text-purple-800',
  in_progress: 'bg-orange-100 text-orange-800',
  completed: 'bg-gray-100 text-gray-800',
};

export const JOB_STATUS_COLORS = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  measurements_complete: 'bg-yellow-100 text-yellow-800',
  calculations_complete: 'bg-purple-100 text-purple-800',
  under_review: 'bg-orange-100 text-orange-800',
  deviation_pending: 'bg-red-100 text-red-800',
  approved: 'bg-green-100 text-green-800',
  certificate_generated: 'bg-indigo-100 text-indigo-800',
  completed: 'bg-green-200 text-green-900',
  on_hold: 'bg-red-200 text-red-900',
};
