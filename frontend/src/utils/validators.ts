import * as yup from 'yup';

// Login form validation
export const loginSchema = yup.object({
  username: yup
    .string()
    .required('Username is required')
    .min(3, 'Username must be at least 3 characters'),
  password: yup
    .string()
    .required('Password is required')
    .min(6, 'Password must be at least 6 characters'),
  user_type: yup
    .string()
    .oneOf(['staff', 'customer'], 'Invalid user type')
    .required('User type is required'),
});

// SRF form validation
export const srfSchema = yup.object({
  contact_person: yup
    .string()
    .required('Contact person is required')
    .min(2, 'Contact person name must be at least 2 characters'),
  special_instructions: yup.string().optional(),
  priority: yup
    .string()
    .oneOf(['normal', 'urgent', 'critical'])
    .default('normal'),
  items: yup
    .array()
    .of(
      yup.object({
        equip_desc: yup
          .string()
          .required('Equipment description is required'),
        make: yup.string().optional(),
        model: yup.string().optional(),
        serial_no: yup
          .string()
          .required('Serial number is required'),
        range_text: yup.string().optional(),
        unit: yup.string().optional(),
        calibration_points: yup.string().optional(),
        calibration_mode: yup.string().optional(),
        quantity: yup
          .number()
          .min(1, 'Quantity must be at least 1')
          .default(1),
        remarks: yup.string().optional(),
      })
    )
    .min(1, 'At least one equipment item is required'),
});

// Email validation
export const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Phone validation (Indian format)
export const phoneRegex = /^[+]?[91]?[0-9]{10}$/;

// Serial number validation (alphanumeric)
export const serialNumberRegex = /^[A-Za-z0-9\-_]+$/;

export const validateEmail = (email: string): boolean => {
  return emailRegex.test(email);
};

export const validatePhone = (phone: string): boolean => {
  return phoneRegex.test(phone);
};

export const validateSerialNumber = (serialNo: string): boolean => {
  return serialNumberRegex.test(serialNo) && serialNo.length >= 3;
};
