import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { SRF, SRFCreateRequest, PaginatedResponse } from '../types';
import { RootState } from '../store';

export const srfApi = createApi({
  reducerPath: 'srfApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${process.env.REACT_APP_API_BASE_URL}/api/${process.env.REACT_APP_API_VERSION}/srf`,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['SRF'],
  endpoints: (builder) => ({
    createSRF: builder.mutation<SRF, SRFCreateRequest>({
      query: (srfData) => ({
        url: '',
        method: 'POST',
        body: srfData,
      }),
      invalidatesTags: ['SRF'],
    }),
    getSRFs: builder.query<SRF[], { skip?: number; limit?: number }>({
      query: ({ skip = 0, limit = 10 } = {}) => `?skip=${skip}&limit=${limit}`,
      providesTags: ['SRF'],
      transformResponse: (response: SRF[]) => response,
    }),
    getSRFById: builder.query<SRF, number>({
      query: (id) => `/${id}`,
      providesTags: (result, error, id) => [{ type: 'SRF', id }],
    }),
    updateSRFStatus: builder.mutation<
      { message: string },
      { id: number; status: string }
    >({
      query: ({ id, status }) => ({
        url: `/${id}/status`,
        method: 'PUT',
        body: { new_status: status },
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'SRF', id }],
    }),
    checkInwardEligible: builder.query<
      {
        eligible: boolean;
        reason: string;
        srf_id: number;
        item_id: number;
      },
      { srfId: number; itemId: number }
    >({
      query: ({ srfId, itemId }) => `/${srfId}/items/${itemId}/inward-eligible`,
    }),
  }),
});

export const {
  useCreateSRFMutation,
  useGetSRFsQuery,
  useGetSRFByIdQuery,
  useUpdateSRFStatusMutation,
  useCheckInwardEligibleQuery,
} = srfApi;
