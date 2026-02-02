import { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
} from '@mui/material';
import { Edit, Trash2, Plus, Filter, Download } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

interface RecordDataViewerProps {
  recordId: number;
  recordName: string;
  onClose: () => void;
}

interface DataRow {
  id: number;
  record_id: number;
  row_index: number;
  data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export default function RecordDataViewer({ recordId, recordName, onClose }: RecordDataViewerProps) {
  const [loading, setLoading] = useState(false);
  const [rows, setRows] = useState<DataRow[]>([]);
  const [totalRows, setTotalRows] = useState(0);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(100);
  const [filterField, setFilterField] = useState('');
  const [filterValue, setFilterValue] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [editingRow, setEditingRow] = useState<DataRow | null>(null);
  const [editData, setEditData] = useState<Record<string, any>>({});
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

  // Reset pagination and filters only when record ID changes
  useEffect(() => {
    setPage(0);
  }, [recordId]);

  // Debug: log pagination state
  useEffect(() => {
    console.log(`📊 Pagination State: page=${page}, rowsPerPage=${rowsPerPage}, totalRows=${totalRows}, totalPages=${Math.ceil(totalRows / rowsPerPage)}`);
  }, [page, rowsPerPage, totalRows]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {
        page: page + 1,
        per_page: rowsPerPage,
      };
      
      if (filterField && filterValue) {
        params.filter_field = filterField;
        params.filter_value = filterValue;
      }
      
      if (sortField) {
        params.sort_field = sortField;
        params.sort_order = sortOrder;
      }

      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/metadata/${recordId}/data`, {
        params,
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setRows(response.data.data || []);
      setTotalRows(response.data.total_rows || 0);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [recordId, page, rowsPerPage, filterField, filterValue, sortField, sortOrder]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleEditRow = (row: DataRow) => {
    setEditingRow(row);
    setEditData({ ...row.data });
  };

  const handleSaveEdit = async () => {
    if (!editingRow) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(`/api/metadata/${recordId}/data/${editingRow.id}`, {
        data: editData
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      toast.success('Row updated successfully');
      setEditingRow(null);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to update row');
    }
  };

  const handleDeleteRow = async (rowId: number) => {
    if (!confirm('Delete this row?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/metadata/${recordId}/data/${rowId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      toast.success('Row deleted successfully');
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to delete row');
    }
  };

  const handleExport = async (format: 'json' | 'csv' | 'excel') => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch all data for export
      const response = await axios.get(`/api/metadata/${recordId}/data`, {
        params: { per_page: totalRows || 100000 },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      const allData = response.data.data || [];
      if (allData.length === 0) {
        toast.warning('No data to export');
        return;
      }

      const fields = Object.keys(allData[0].data);
      let blob: Blob;
      let filename: string;

      if (format === 'json') {
        // Export as JSON
        const jsonData = JSON.stringify(allData.map((r: any) => r.data), null, 2);
        blob = new Blob([jsonData], { type: 'application/json' });
        filename = `${recordName}_data.json`;
      } else {
        // Export as CSV
        const csvRows = [];
        
        // Header row
        csvRows.push(fields.join(','));
        
        // Data rows
        allData.forEach((row: any) => {
          const values = fields.map(field => {
            let value = row.data[field];
            if (value === null || value === undefined) return '';
            if (typeof value === 'object') value = JSON.stringify(value);
            // Escape quotes and wrap in quotes if contains comma, quote, or newline
            value = String(value);
            if (value.includes(',') || value.includes('"') || value.includes('\n')) {
              value = '"' + value.replace(/"/g, '""') + '"';
            }
            return value;
          });
          csvRows.push(values.join(','));
        });
        
        const csvContent = csvRows.join('\n');
        
        if (format === 'excel') {
          // Add BOM for Excel UTF-8 support
          const BOM = '\uFEFF';
          blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
          filename = `${recordName}_data.csv`;
        } else {
          blob = new Blob([csvContent], { type: 'text/csv' });
          filename = `${recordName}_data.csv`;
        }
      }
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export data');
    }
  };

  const fields = rows.length > 0 ? Object.keys(rows[0].data) : [];

  return (
    <Dialog open fullScreen onClose={onClose}>
      <DialogTitle sx={{ bgcolor: 'primary.main', color: 'white', py: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>{recordName}</Typography>
            <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
              {totalRows.toLocaleString()} rows total • Table-based storage (ACID compliant)
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Button 
              variant="outlined" 
              startIcon={<Download />} 
              onClick={(e) => setExportMenuAnchor(e.currentTarget)}
              sx={{ color: 'white', borderColor: 'white', '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.1)' } }}
            >
              Export
            </Button>
            <Menu
              anchorEl={exportMenuAnchor}
              open={Boolean(exportMenuAnchor)}
              onClose={() => setExportMenuAnchor(null)}
            >
              <MenuItem onClick={() => { handleExport('json'); setExportMenuAnchor(null); }}>
                📄 Export as JSON
              </MenuItem>
              <MenuItem onClick={() => { handleExport('csv'); setExportMenuAnchor(null); }}>
                📊 Export as CSV
              </MenuItem>
              <MenuItem onClick={() => { handleExport('excel'); setExportMenuAnchor(null); }}>
                📗 Export as CSV (Excel)
              </MenuItem>
            </Menu>
            <Button 
              onClick={onClose}
              sx={{ color: 'white', borderColor: 'white', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}
            >
              Close
            </Button>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ bgcolor: '#f5f5f5', p: 3 }}>
        {/* Filters */}
        <Card sx={{ mb: 3, boxShadow: 2 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600, color: 'text.secondary' }}>
              FILTERS & SORTING
            </Typography>
            <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
              <TextField
                select
                label="Filter Field"
                value={filterField}
                onChange={(e) => setFilterField(e.target.value)}
                size="small"
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="">-- Select Field --</MenuItem>
                {fields.map(field => (
                  <MenuItem key={field} value={field}>{field}</MenuItem>
                ))}
              </TextField>
              
              <TextField
                label="Filter Value"
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
                size="small"
                disabled={!filterField}
                placeholder="Enter value to filter..."
                sx={{ minWidth: 200 }}
              />

              <Box sx={{ width: 1, height: 30, bgcolor: 'divider', mx: 1 }} />

              <TextField
                select
                label="Sort By"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
                size="small"
                sx={{ minWidth: 180 }}
              >
                <MenuItem value="">-- Select Field --</MenuItem>
                {fields.map(field => (
                  <MenuItem key={field} value={field}>{field}</MenuItem>
                ))}
              </TextField>

              <Button
                variant="outlined"
                size="medium"
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                disabled={!sortField}
                sx={{ minWidth: 80 }}
              >
                {sortOrder === 'asc' ? '↑ ASC' : '↓ DESC'}
              </Button>

              <Box sx={{ flexGrow: 1 }} />

              <Button
                variant="outlined"
                size="medium"
                color="error"
                startIcon={<Filter />}
                onClick={() => {
                  setFilterField('');
                  setFilterValue('');
                  setSortField('');
                }}
                disabled={!filterField && !sortField}
              >
                Clear All
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Data Table */}
        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper} sx={{ boxShadow: 3, borderRadius: 2, maxHeight: 'calc(100vh - 320px)' }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell 
                    sx={{ 
                      bgcolor: 'primary.dark', 
                      color: 'white', 
                      fontWeight: 700,
                      fontSize: '0.875rem',
                      borderBottom: '2px solid',
                      borderColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 2
                    }}
                  >
                    Row #
                  </TableCell>
                  {fields.map(field => (
                    <TableCell 
                      key={field}
                      sx={{ 
                        bgcolor: 'primary.dark', 
                        color: 'white', 
                        fontWeight: 700,
                        fontSize: '0.875rem',
                        borderBottom: '2px solid',
                        borderColor: 'primary.main',
                        position: 'sticky',
                        top: 0,
                        zIndex: 2,
                        textTransform: 'capitalize'
                      }}
                    >
                      {field.replace(/_/g, ' ')}
                    </TableCell>
                  ))}
                  <TableCell 
                    align="right"
                    sx={{ 
                      bgcolor: 'primary.dark', 
                      color: 'white', 
                      fontWeight: 700,
                      fontSize: '0.875rem',
                      borderBottom: '2px solid',
                      borderColor: 'primary.main',
                      position: 'sticky',
                      top: 0,
                      zIndex: 2
                    }}
                  >
                    Actions
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => (
                  <TableRow 
                    key={row.id}
                    sx={{ 
                      '&:nth-of-type(odd)': { bgcolor: '#fafafa' },
                      '&:hover': { bgcolor: 'action.hover', boxShadow: 1 },
                      transition: 'all 0.2s'
                    }}
                  >
                    <TableCell sx={{ fontWeight: 600, color: 'primary.main' }}>
                      {row.row_index}
                    </TableCell>
                    {fields.map(field => (
                      <TableCell 
                        key={field}
                        sx={{ 
                          maxWidth: 250, 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis',
                          fontFamily: 'monospace',
                          fontSize: '0.85rem'
                        }}
                      >
                        {typeof row.data[field] === 'object'
                          ? JSON.stringify(row.data[field])
                          : String(row.data[field] ?? '—')}
                      </TableCell>
                    ))}
                    <TableCell align="right">
                      <Box display="flex" gap={0.5} justifyContent="flex-end">
                        <IconButton 
                          size="small" 
                          onClick={() => handleEditRow(row)}
                          color="primary"
                          sx={{ 
                            '&:hover': { bgcolor: 'primary.light', color: 'white' },
                            transition: 'all 0.2s'
                          }}
                        >
                          <Edit size={18} />
                        </IconButton>
                        <IconButton 
                          size="small" 
                          onClick={() => handleDeleteRow(row.id)}
                          color="error"
                          sx={{ 
                            '&:hover': { bgcolor: 'error.light', color: 'white' },
                            transition: 'all 0.2s'
                          }}
                        >
                          <Trash2 size={18} />
                        </IconButton>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <TablePagination
              component="div"
              count={totalRows}
              page={page}
              onPageChange={(_, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[10, 25, 50, 100, 500, 1000, 5000]}
              showFirstButton
              showLastButton
              sx={{ 
                borderTop: '2px solid',
                borderColor: 'divider',
                bgcolor: '#fafafa'
              }}
            />
          </TableContainer>
        )}
      </DialogContent>

      {/* Edit Dialog */}
      <Dialog open={!!editingRow} onClose={() => setEditingRow(null)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Row #{editingRow?.row_index}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={2}>
            {editingRow && Object.keys(editingRow.data).map(field => (
              <TextField
                key={field}
                label={field}
                value={editData[field] ?? ''}
                onChange={(e) => setEditData({ ...editData, [field]: e.target.value })}
                fullWidth
              />
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingRow(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEdit}>Save</Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
}
