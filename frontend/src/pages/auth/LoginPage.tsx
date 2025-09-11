import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { useDispatch, useSelector } from 'react-redux';
import { useLoginMutation } from '../../services/authApi';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';
import { showNotification } from '../../store/slices/uiSlice';
import { loginSchema } from '../../utils/validators';
import { LoginRequest } from '../../types';
import { RootState } from '../../store';
import Button from '../../components/common/Button';
import { APP_CONFIG, ROUTES } from '../../utils/constants';

const LoginPage: React.FC = () => {
  const [userType, setUserType] = useState<'staff' | 'customer'>('staff');
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const { isAuthenticated, isLoading } = useSelector((state: RootState) => state.auth);
  const [login, { isLoading: isLoginLoading }] = useLoginMutation();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<LoginRequest>({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
      user_type: 'staff',
    },
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || ROUTES.STAFF_DASHBOARD;
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  // Update form when user type changes
  useEffect(() => {
    setValue('user_type', userType);
  }, [userType, setValue]);

  const onSubmit = async (data: LoginRequest) => {
    try {
      dispatch(loginStart());
      const result = await login(data).unwrap();
      
      dispatch(loginSuccess({
        user: result.user,
        token: result.token,
      }));

      dispatch(showNotification({
        message: 'Login successful!',
        type: 'success',
      }));

      // Redirect based on user type and role
      const redirectPath = getRedirectPath(result.user.user_type, result.user.role);
      navigate(redirectPath, { replace: true });
      
    } catch (error: any) {
      dispatch(loginFailure());
      dispatch(showNotification({
        message: error?.data?.detail || 'Login failed. Please try again.',
        type: 'error',
      }));
    }
  };

  const getRedirectPath = (userType: string, role: string): string => {
    if (userType === 'customer') {
      return ROUTES.CUSTOMER_DASHBOARD;
    }
    
    // Staff redirects based on role
    switch (role) {
      case 'TECHNICIAN':
        return ROUTES.STAFF_MEASUREMENTS;
      case 'QA_MANAGER':
        return ROUTES.STAFF_CERTIFICATES;
      default:
        return ROUTES.STAFF_DASHBOARD;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-primary-600 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl text-white">🔬</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">{APP_CONFIG.name}</h1>
          <p className="mt-2 text-gray-600">{APP_CONFIG.company}</p>
          <h2 className="mt-4 text-xl font-semibold text-gray-800">
            Sign in to your account
          </h2>
        </div>

        {/* Login Form */}
        <div className="bg-white p-8 rounded-lg shadow-md">
          {/* User Type Selection */}
          <div className="flex mb-6 p-1 bg-gray-100 rounded-lg">
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                userType === 'staff'
                  ? 'bg-primary-600 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              onClick={() => setUserType('staff')}
            >
              🏢 Staff Portal
            </button>
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                userType === 'customer'
                  ? 'bg-secondary-600 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
              onClick={() => setUserType('customer')}
            >
              👤 Customer Portal
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                className={`input-field ${errors.username ? 'border-red-300' : ''}`}
                placeholder="Enter your username"
                {...register('username')}
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className={`input-field ${errors.password ? 'border-red-300' : ''}`}
                placeholder="Enter your password"
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-700">
                  Remember me
                </label>
              </div>
              <button
                type="button"
                className="text-sm text-primary-600 hover:text-primary-500"
                onClick={() => {
                  // TODO: Implement forgot password
                  dispatch(showNotification({
                    message: 'Please contact your administrator for password reset.',
                    type: 'info',
                  }));
                }}
              >
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              variant={userType === 'customer' ? 'success' : 'primary'}
              fullWidth
              loading={isLoginLoading || isLoading}
              disabled={isLoginLoading || isLoading}
            >
              Sign in
            </Button>
          </form>

          {/* Additional Info */}
          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500">
              By signing in, you agree to our terms and conditions.
            </p>
          </div>
        </div>

        {/* Version Info */}
        <div className="text-center text-xs text-gray-500">
          Version {APP_CONFIG.version} | © 2025 {APP_CONFIG.company}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
