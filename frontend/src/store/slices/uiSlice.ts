import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
  sidebarOpen: boolean;
  loading: boolean;
  error: string | null;
  notification: {
    show: boolean;
    message: string;
    type: 'success' | 'error' | 'warning' | 'info';
  } | null;
}

const initialState: UiState = {
  sidebarOpen: false,
  loading: false,
  error: null,
  notification: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    showNotification: (
      state,
      action: PayloadAction<{
        message: string;
        type: 'success' | 'error' | 'warning' | 'info';
      }>
    ) => {
      state.notification = {
        show: true,
        message: action.payload.message,
        type: action.payload.type,
      };
    },
    hideNotification: (state) => {
      state.notification = null;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setLoading,
  setError,
  showNotification,
  hideNotification,
} = uiSlice.actions;

export default uiSlice.reducer;
