import { create } from 'zustand';

export interface DataRecord {
  id: number;
  name: string;
  schema_id: number;
  asset_type_id?: number;
  values: Record<string, any>;
  tag?: string;
  created_by: number;
  created_at: string;
  updated_at?: string;
}

export interface DataFilters {
  asset_type_id?: number;
  schema_id?: number;
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

interface DataStore {
  records: DataRecord[];
  selectedRecord: DataRecord | null;
  filters: DataFilters;
  loading: boolean;
  error: string | null;
  total: number;

  fetchRecords: (filters?: DataFilters) => Promise<void>;
  fetchRecordById: (id: number) => Promise<DataRecord | null>;
  createRecord: (data: any) => Promise<DataRecord>;
  createBulkRecords: (data: any) => Promise<any>;
  updateRecord: (id: number, data: Partial<DataRecord>) => Promise<void>;
  deleteRecord: (id: number) => Promise<void>;
  selectRecord: (record: DataRecord | null) => void;
  setFilters: (filters: Partial<DataFilters>) => void;
  suggestSchema: (values: Record<string, any>, assetTypeId?: number) => Promise<any>;
}

const API_BASE = '/api';

const buildHeaders = (withJson = false) => {
  const headers: Record<string, string> = {};
  const token = localStorage.getItem('token');
  if (token) headers.Authorization = `Bearer ${token}`;
  if (withJson) headers['Content-Type'] = 'application/json';
  return headers;
};

export const useDataStore = create<DataStore>((set, get) => ({
  records: [],
  selectedRecord: null,
  filters: { limit: 100, offset: 0 },
  loading: false,
  error: null,
  total: 0,

  fetchRecords: async (filters = {}) => {
    set({ loading: true, error: null });
    try {
      const params = new URLSearchParams();
      const mergedFilters = { ...get().filters, ...filters };
      
      if (mergedFilters.schema_id) params.append('schema_id', mergedFilters.schema_id.toString());
      if (mergedFilters.asset_type_id) params.append('asset_type_id', mergedFilters.asset_type_id.toString());
      if (mergedFilters.tag) params.append('tag', mergedFilters.tag);
      if (mergedFilters.search) params.append('search', mergedFilters.search);
      if (mergedFilters.limit) params.append('limit', mergedFilters.limit.toString());
      if (mergedFilters.offset) params.append('offset', mergedFilters.offset.toString());

      const response = await fetch(`${API_BASE}/data?${params}`, {
        headers: buildHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to fetch records');
      
      const data = await response.json();
      set({ 
        records: data.records || [],
        total: data.total || 0,
        loading: false, 
        filters: mergedFilters 
      });
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
    }
  },

  fetchRecordById: async (id: number) => {
    try {
      const response = await fetch(`${API_BASE}/data/${id}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  },

  createRecord: async (data) => {
    set({ loading: true, error: null });
    try {
      const payload = {
        name: data.name || 'Unnamed Record',
        schema_id: data.schema_id,
        asset_type_id: data.asset_type_id,
        tag: data.tag,
        values: data.values || data.data || {},
        create_new_schema: data.create_new_schema || false,
        allow_additional_fields: data.allow_additional_fields !== undefined ? data.allow_additional_fields : true,
        schema_name: data.schema_name,
      };

      const response = await fetch(`${API_BASE}/data`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let message = 'Failed to create record';
        try {
          const err = await response.json();
          if (err?.error) message = err.error;
          if (err?.validation_errors) {
            message = `Validation failed: ${JSON.stringify(err.validation_errors)}`;
          }
        } catch {
          const errText = await response.text();
          if (errText) message = errText;
        }
        throw new Error(message);
      }

      const result = await response.json();
      const record = result.record || result;
      
      set((state) => ({
        records: [record, ...state.records],
        loading: false,
      }));
      
      return record;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  createBulkRecords: async (data) => {
    set({ loading: true, error: null });
    try {
      const payload = {
        records: data.records || data.data || [],
        schema_name: data.schema_name || 'BulkImport',
        asset_type_id: data.asset_type_id,
        tag: data.tag,
        create_new_schema: data.create_new_schema !== undefined ? data.create_new_schema : true,
      };

      const response = await fetch(`${API_BASE}/data/bulk`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let message = 'Failed to create records';
        try {
          const err = await response.json();
          if (err?.error) message = err.error;
        } catch {
          const errText = await response.text();
          if (errText) message = errText;
        }
        throw new Error(message);
      }

      const result = await response.json();
      
      // Refresh records list
      await get().fetchRecords(get().filters);
      
      set({ loading: false });
      return result;
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  updateRecord: async (id, data) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/data/${id}`, {
        method: 'PUT',
        headers: buildHeaders(true),
        body: JSON.stringify(data),
      });
      
      if (!response.ok) throw new Error('Failed to update record');
      
      await get().fetchRecords(get().filters);
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  deleteRecord: async (id) => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${API_BASE}/data/${id}`, {
        method: 'DELETE',
        headers: buildHeaders(),
      });
      
      if (!response.ok) throw new Error('Failed to delete record');
      
      set((state) => ({
        records: state.records.filter((r) => r.id !== id),
        selectedRecord: state.selectedRecord?.id === id ? null : state.selectedRecord,
        loading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, loading: false });
      throw error;
    }
  },

  selectRecord: (record) => set({ selectedRecord: record }),
  
  setFilters: (filters) => set((state) => ({ 
    filters: { ...state.filters, ...filters } 
  })),

  suggestSchema: async (values, assetTypeId) => {
    try {
      const response = await fetch(`${API_BASE}/data/suggest-schema`, {
        method: 'POST',
        headers: buildHeaders(true),
        body: JSON.stringify({ 
          values, 
          asset_type_id: assetTypeId 
        }),
      });
      
      if (!response.ok) return null;
      
      const data = await response.json();
      return data;
    } catch {
      return null;
    }
  },
}));
