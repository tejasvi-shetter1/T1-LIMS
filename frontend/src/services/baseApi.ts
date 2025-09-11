import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../store';

const baseQuery = fetchBaseQuery({
  baseUrl: `${process.env.REACT_APP_API_BASE_URL}/api/${process.env.REACT_APP_API_VERSION}`,
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.token;
    
    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }
    
    headers.set('Content-Type', 'application/json');
    return headers;
  },
});

export const baseApi = createApi({
  reducerPath: 'baseApi',
  baseQuery,
  tagTypes: ['User', 'SRF', 'Job', 'Inward', 'Measurement', 'Deviation', 'Certificate'],
  endpoints: () => ({}),
});
