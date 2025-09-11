import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { Job } from '../types';
import { RootState } from '../store';

export const jobApi = createApi({
  reducerPath: 'jobApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.REACT_APP_API_BASE_URL}/api/${process.env.REACT_APP_API_VERSION}`,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Job'],
  endpoints: (builder) => ({
    getJobs: builder.query<Job[], { skip?: number; limit?: number; status?: string }>({
      query: ({ skip = 0, limit = 10, status } = {}) => {
        let url = `/jobs?skip=${skip}&limit=${limit}`;
        if (status) url += `&status=${status}`;
        return url;
      },
      providesTags: ['Job'],
    }),
    getJobById: builder.query<Job, number>({
      query: (id) => `/jobs/${id}`,
      providesTags: (result, error, id) => [{ type: 'Job', id }],
    }),
  }),
});

export const {
  useGetJobsQuery,
  useGetJobByIdQuery,
} = jobApi;
