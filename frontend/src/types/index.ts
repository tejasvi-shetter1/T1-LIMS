// Auth Types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  user_type: UserType;
  customer_id?: number;
  is_active: boolean;
  last_login?: string;
  created_at: string;
}

export enum UserRole {
  ADMIN = 'ADMIN',
  LAB_MANAGER = 'LAB_MANAGER',
  TECHNICIAN = 'TECHNICIAN',
  QA_MANAGER = 'QA_MANAGER',
  CUSTOMER_ADMIN = 'CUSTOMER_ADMIN',
  CUSTOMER_USER = 'CUSTOMER_USER',
}

export enum UserType {
  INTERNAL = 'internal',
  EXTERNAL = 'external',
  CUSTOMER = 'customer',
}

export interface LoginRequest {
  username: string;
  password: string;
  user_type: 'staff' | 'customer';
}

export interface LoginResponse {
  token: string;
  user: User;
  expires_in: number;
}

// SRF Types
export interface Customer {
  id: number;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
}

export interface SRFItem {
  id?: number;
  sl_no: number;
  equip_desc: string;
  make?: string;
  model?: string;
  serial_no: string;
  range_text?: string;
  unit?: string;
  calibration_points?: string;
  calibration_mode?: string;
  quantity: number;
  remarks?: string;
}

export interface SRF {
  id: number;
  srf_no: string;
  customer_id: number;
  customer?: Customer;
  contact_person?: string;
  date_received: string;
  status: SRFStatus;
  priority: 'normal' | 'urgent' | 'critical';
  special_instructions?: string;
  nextage_contract_reference?: string;
  calibration_frequency: string;
  items: SRFItem[];
  created_at: string;
  updated_at?: string;
}

export enum SRFStatus {
  SUBMITTED = 'submitted',
  UNDER_REVIEW = 'under_review',
  ACCEPTED = 'accepted',
  INWARD_COMPLETED = 'inward_completed',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
}

export interface SRFCreateRequest {
  contact_person: string;
  special_instructions?: string;
  priority?: 'normal' | 'urgent' | 'critical';
  nextage_contract_reference?: string;
  items: Omit<SRFItem, 'id'>[];
}

// Job Types
export interface Job {
  id: number;
  job_number: string;
  nepl_work_id: string;
  inward_id: number;
  calibration_type: string;
  calibration_method: string;
  calibration_procedure?: string;
  measurement_points: string[];
  status: JobStatus;
  priority: 'normal' | 'urgent' | 'critical';
  assigned_technician?: string;
  created_at: string;
  updated_at?: string;
  inward?: Inward;
}

export enum JobStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  MEASUREMENTS_COMPLETE = 'measurements_complete',
  CALCULATIONS_COMPLETE = 'calculations_complete',
  UNDER_REVIEW = 'under_review',
  DEVIATION_PENDING = 'deviation_pending',
  APPROVED = 'approved',
  CERTIFICATE_GENERATED = 'certificate_generated',
  COMPLETED = 'completed',
  ON_HOLD = 'on_hold',
}

// Inward Types
export interface Inward {
  id: number;
  srf_item_id: number;
  nepl_id: string;
  inward_date: string;
  customer_dc_no?: string;
  customer_dc_date?: string;
  condition_on_receipt: string;
  status: InwardStatus;
  created_at: string;
  srf_item?: SRFItem;
}

export enum InwardStatus {
  RECEIVED = 'received',
  INSPECTION_COMPLETE = 'inspection_complete',
  READY_FOR_CALIBRATION = 'ready_for_calibration',
  IN_CALIBRATION = 'in_calibration',
  CALIBRATION_COMPLETE = 'calibration_complete',
  READY_FOR_DISPATCH = 'ready_for_dispatch',
  DISPATCHED = 'dispatched',
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

// Common UI Types
export interface NavigationItem {
  name: string;
  href: string;
  icon: string;
  current?: boolean;
  children?: NavigationItem[];
  roles?: UserRole[];
}

export interface DashboardStat {
  title: string;
  count: number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: string;
  href?: string;
}
