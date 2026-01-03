import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Drawer,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Chip,
  Alert,
} from '@mui/material';
import { Plus, Trash2, Filter, X, Upload, Edit, Eye, Database } from 'lucide-react';
import { useDataStore } from '../stores/dataStore';
import { useSchemaStore } from '../stores/schemaStore';
import { useAssetTypesStore, AssetType } from '../stores/assetTypesStore';
import toast from 'react-hot-toast';
import FileImportDialog from '../components/FileImportDialog';
import RecordDataViewer from '../components/RecordDataViewer';
import AdvancedRecordEditor from '../components/AdvancedRecordEditor';

export default function DataPage() {
  const {
    records,
    selectedRecord,
    filters,
    loading,
    total,
    fetchRecords,
    createRecord,
    createBulkRecords,
    deleteRecord,
    selectRecord,
    setFilters,
    suggestSchema,
  } = useDataStore();

  const { schemas, fetchSchemas } = useSchemaStore();
  const { assetTypes, fetchAssetTypes } = useAssetTypesStore();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [fileImportOpen, setFileImportOpen] = useState(false);
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false);
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [schemaSelectDialogOpen, setSchemaSelectDialogOpen] = useState(false);
  const [matchingSchemas, setMatchingSchemas] = useState<any[]>([]);

  const [formData, setFormData] = useState<any>({
    name: '',
    schema_id: '',
    asset_type_id: '',
    tag: '',
    values: {},
    create_new_schema: false,
    schema_name: '',
  });

  const [bulkData, setBulkData] = useState('');
  const [bulkStep, setBulkStep] = useState<'input' | 'schema-select' | 'confirm'>('input');
  const [bulkSimilarSchemas, setBulkSimilarSchemas] = useState<any[]>([]);
  const [bulkSchemaChoice, setBulkSchemaChoice] = useState<{action: 'reuse' | 'new_version' | 'add_fields' | 'create_new', schema_id?: number} | null>(null);
  const [bulkRecordsPreview, setBulkRecordsPreview] = useState<any[]>([]);
  const [dataFormat, setDataFormat] = useState<'json' | 'csv' | 'tsv' | 'pipe' | 'semicolon' | 'keyvalue'>('json');
  const [dataInput, setDataInput] = useState('');
  const [jsonError, setJsonError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  const [updating, setUpdating] = useState(false);
  
  // Edit record states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [recordToEdit, setRecordToEdit] = useState<any>(null);
  const [editRecordData, setEditRecordData] = useState('');
  const [newFieldsDetected, setNewFieldsDetected] = useState<string[]>([]);
  const [schemaChangeDialogOpen, setSchemaChangeDialogOpen] = useState(false);
  
  // New: Data viewer and advanced editor
  const [dataViewerOpen, setDataViewerOpen] = useState(false);
  const [viewingRecord, setViewingRecord] = useState<any>(null);
  const [advancedEditorOpen, setAdvancedEditorOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any>(null);

  // Parse data based on format
  const parseDataInput = (input: string, format: string): Record<string, any> => {
    try {
      switch (format) {
        case 'json':
          return JSON.parse(input);
        case 'csv':
        case 'tsv':
        case 'pipe':
        case 'semicolon': {
          const delimiter = format === 'csv' ? ',' : format === 'tsv' ? '\t' : format === 'pipe' ? '|' : ';';
          const lines = input.trim().split('\n');
          if (lines.length < 2) return {};
          const headers = lines[0].split(delimiter).map(h => h.trim());
          const values = lines[1].split(delimiter).map(v => v.trim());
          return Object.fromEntries(headers.map((h, i) => [h, values[i]]));
        }
        case 'keyvalue': {
          const result: Record<string, any> = {};
          input.split('\n').forEach(line => {
            const [key, value] = line.split(':').map(s => s.trim());
            if (key) result[key] = value;
          });
          return result;
        }
        default:
          return {};
      }
    } catch (e) {
      throw new Error(`Failed to parse ${format.toUpperCase()} format`);
    }
  };

  useEffect(() => {
    fetchRecords();
    fetchSchemas();
    fetchAssetTypes();
  }, []);

  const handleCreateOpen = () => {
    setFormData({
      name: '',
      schema_id: '',
      asset_type_id: '',
      tag: '',
      values: {},
      create_new_schema: false,
      schema_name: '',
    });
    setDataInput('');
    setDataFormat('json');
    setCreateDialogOpen(true);
  };

  const handleCreateSubmit = async (schemaIdOverride?: string | number) => {
    try {
      setJsonError('');
      const parsed = parseDataInput(dataInput, dataFormat);
      
      if (!parsed || Object.keys(parsed).length === 0) {
        setJsonError('Please enter valid data');
        return;
      }
      
      let finalSchemaId: string | number | undefined = schemaIdOverride ? (schemaIdOverride === 'new' ? undefined : schemaIdOverride) : formData.schema_id;
      let createNewSchema = schemaIdOverride === 'new' || formData.create_new_schema;
      let schemaName = formData.schema_name;
      
      // If no schema selected and no override, find matching schemas with similarity calculation
      if (!finalSchemaId && !createNewSchema) {
        const dataKeys = new Set(Object.keys(parsed));
        
        // Calculate similarity for each schema (50%+ match)
        const matches = schemas
          .map(s => {
            if (!s.fields) return null;
            const schemaFields = new Set(s.fields.map((f: any) => f.field_name));
            const matchingFields = Array.from(dataKeys).filter(k => schemaFields.has(k)).length;
            const totalFields = new Set([...dataKeys, ...schemaFields]).size;
            const similarity = totalFields > 0 ? (matchingFields / totalFields) * 100 : 0;
            
            return similarity >= 50 ? { ...s, similarity } : null;
          })
          .filter((s): s is any => s !== null)
          .sort((a, b) => b.similarity - a.similarity);
        
        if (matches.length > 0) {
          setMatchingSchemas(matches);
          setSchemaSelectDialogOpen(true);
          setJsonError('');
          return;
        }
        
        // No matching schemas - will auto-create
        createNewSchema = true;
        schemaName = `Schema_${new Date().toISOString().slice(0, 10)}`;
      }
      
      await createRecord({ 
        name: formData.name || 'Unnamed Record',
        schema_id: finalSchemaId || undefined,
        asset_type_id: formData.asset_type_id || undefined,
        tag: formData.tag || undefined,
        values: parsed,
        create_new_schema: createNewSchema,
        schema_name: schemaName,
      });
      toast.success('Record created successfully!');
      setCreateDialogOpen(false);
      await fetchRecords();
    } catch (error: any) {
      setJsonError(error.message || 'Invalid data format');
      toast.error(error.message || 'Failed to create record');
    }
  };

  const handleBulkSubmit = async () => {
    try {
      setJsonError('');
      const parsed = JSON.parse(bulkData);
      
      if (!Array.isArray(parsed)) {
        setJsonError('Data must be an array of objects');
        return;
      }

      // First, preview and get similar schemas
      console.log(`📤 PREVIEWING ${parsed.length} RECORDS FOR SCHEMA DETECTION`);
      const token = localStorage.getItem('token');
      const response = await fetch('/api/data/bulk-preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          records: parsed,
          asset_type_id: formData.asset_type_id || null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to preview bulk import');
      }

      const previewData = await response.json();
      console.log(`🔍 FOUND ${previewData.similar_schemas?.length || 0} SIMILAR SCHEMAS`);
      
      setBulkRecordsPreview(parsed);
      setBulkSimilarSchemas(previewData.similar_schemas || []);
      
      // If similar schemas found, show selection dialog. Otherwise proceed to confirm
      if (previewData.similar_schemas && previewData.similar_schemas.length > 0) {
        setBulkStep('schema-select');
      } else {
        setBulkStep('confirm');
      }
    } catch (error: any) {
      if (error instanceof SyntaxError) {
        setJsonError('Invalid JSON format');
      } else {
        toast.error(error.message || 'Failed to preview data');
        setJsonError(error.message || 'Failed to preview data');
      }
    }
  };

  const handleBulkConfirmImport = async () => {
    try {
      await createBulkRecords({
        records: bulkRecordsPreview,
        schema_name: formData.schema_name || 'BulkImport',
        asset_type_id: formData.asset_type_id || null,
        create_new_schema: !bulkSchemaChoice || bulkSchemaChoice.action === 'create_new',
        schema_choice: bulkSchemaChoice || undefined,
      });

      toast.success(`Created ${bulkRecordsPreview.length} records!`);
      setBulkDialogOpen(false);
      setBulkData('');
      setBulkStep('input');
      setBulkSchemaChoice(null);
      setBulkSimilarSchemas([]);
    } catch (error: any) {
      toast.error(error.message || 'Failed to import data');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Delete this record?')) {
      try {
        await deleteRecord(id);
        toast.success('Record deleted');
      } catch (error: any) {
        toast.error('Failed to delete record');
      }
    }
  };

  const handleEditToggle = () => {
    if (!editMode && selectedRecord) {
      setEditData({ ...selectedRecord });
    }
    setEditMode(!editMode);
  };

  const handleSaveUpdate = async () => {
    if (!selectedRecord || !editData) return;

    setUpdating(true);
    try {
      const response = await fetch(`/api/metadata/${selectedRecord.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          name: editData.name,
          tag: editData.tag,
          asset_type_id: editData.asset_type_id,
          values: editData.values,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to update record');
      }

      toast.success('✅ Record updated');
      setEditMode(false);
      setEditData(null);
      
      // Refresh records
      fetchRecords(filters);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleEditClick = (record: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setRecordToEdit(record);
    setEditRecordData(JSON.stringify(record.values || {}, null, 2));
    setNewFieldsDetected([]);
    setEditDialogOpen(true);
  };

  const handleEditRecordSubmit = async () => {
    try {
      const parsed = JSON.parse(editRecordData);
      const schema = schemas.find(s => s.id === recordToEdit.schema_id);
      
      if (!schema) {
        toast.error('Schema not found');
        return;
      }

      // Detect new fields
      const existingFields = schema.fields?.map((f: any) => f.field_name) || [];
      const newKeys = Object.keys(parsed).filter(key => !existingFields.includes(key));
      
      if (newKeys.length > 0 && schema.allow_additional_fields) {
        // New fields detected - show dialog to user
        setNewFieldsDetected(newKeys);
        setSchemaChangeDialogOpen(true);
      } else if (newKeys.length > 0 && !schema.allow_additional_fields) {
        toast.error(`Schema "${schema.name}" doesn't allow additional fields. Remove: ${newKeys.join(', ')}`);
        return;
      } else {
        // No new fields, proceed with update
        await performUpdate(parsed, false);
      }
    } catch (error: any) {
      toast.error(error.message || 'Invalid JSON format');
    }
  };

  const performUpdate = async (values: any, addFieldsToSchema: boolean) => {
    try {
      setUpdating(true);

      const url = addFieldsToSchema 
        ? `/api/metadata/${recordToEdit.id}/add-fields`
        : `/api/metadata/${recordToEdit.id}`;

      const response = await fetch(url, {
        method: addFieldsToSchema ? 'POST' : 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ values }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to update record');
      }

      toast.success('✅ Record updated successfully');
      setEditDialogOpen(false);
      setSchemaChangeDialogOpen(false);
      fetchRecords(filters);
    } catch (error: any) {
      toast.error(error.message);
    } finally {
      setUpdating(false);
    }
  };

  const handleRowClick = (record: any) => {
    selectRecord(record);
    setDetailDrawerOpen(true);
  };

  const selectedSchema = schemas.find((s) => s.id === formData.schema_id);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={600}>
            Data Records
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {total} total records
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Filter size={18} />}
            onClick={() => setFilterDrawerOpen(true)}
          >
            Filters
          </Button>
          <Button 
            variant="outlined"
            startIcon={<Upload size={18} />}
            onClick={() => setFileImportOpen(true)}
          >
            Import File
          </Button>
          <Button variant="outlined" onClick={() => setBulkDialogOpen(true)}>
            Bulk Import
          </Button>
          <Button variant="contained" startIcon={<Plus size={18} />} onClick={handleCreateOpen}>
            Create Record
          </Button>
        </Box>
      </Box>

      {/* Data Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Schema</TableCell>
              <TableCell>Asset Type</TableCell>
              <TableCell>Tag</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            )}
            {!loading && records.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No records found. Create your first one!
                </TableCell>
              </TableRow>
            )}
            {records.map((record) => (
              <TableRow
                key={record.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => handleRowClick(record)}
              >
                <TableCell>{record.id}</TableCell>
                <TableCell>{record.name}</TableCell>
                <TableCell>
                  {schemas.find((s) => s.id === record.schema_id)?.name || `Schema ${record.schema_id}`}
                </TableCell>
                <TableCell>
                  {record.asset_type_id
                    ? assetTypes.find((at) => at.id === record.asset_type_id)?.name || `Asset Type ${record.asset_type_id}`
                    : '-'}
                </TableCell>
                <TableCell>
                  {record.tag ? <Chip label={record.tag} size="small" /> : '-'}
                </TableCell>
                <TableCell>{new Date(record.created_at).toLocaleDateString()}</TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    color="info"
                    onClick={(e) => {
                      e.stopPropagation();
                      setViewingRecord(record);
                      setDataViewerOpen(true);
                    }}
                    title="View Data Rows"
                  >
                    <Eye size={18} />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingRecord(record);
                      setAdvancedEditorOpen(true);
                    }}
                    title="Edit Record (Advanced)"
                  >
                    <Edit size={18} />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(record.id);
                    }}
                    title="Delete Record"
                  >
                    <Trash2 size={18} />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create Data Record</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>

            <Grid item xs={6}>
              <Select
                fullWidth
                value={formData.schema_id}
                onChange={(e) => setFormData({ ...formData, schema_id: e.target.value })}
                displayEmpty
              >
                <MenuItem value="">Auto-detect or create</MenuItem>
                {schemas.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.name}
                  </MenuItem>
                ))}
              </Select>
            </Grid>

            <Grid item xs={6}>
              <Select
                fullWidth
                value={formData.asset_type_id}
                onChange={(e) => setFormData({ ...formData, asset_type_id: e.target.value })}
                displayEmpty
              >
                <MenuItem value="">No Asset Type</MenuItem>
                {assetTypes.map((a: AssetType) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.name}
                  </MenuItem>
                ))}
              </Select>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Tag (optional)"
                value={formData.tag}
                onChange={(e) => setFormData({ ...formData, tag: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle2">Data Input</Typography>
                <Select
                  value={dataFormat}
                  onChange={(e) => setDataFormat(e.target.value as any)}
                  sx={{ minWidth: 120 }}
                  size="small"
                >
                  <MenuItem value="json">JSON</MenuItem>
                  <MenuItem value="csv">CSV (comma-separated)</MenuItem>
                  <MenuItem value="tsv">TSV (tab-separated)</MenuItem>
                  <MenuItem value="pipe">Pipe (|)-separated</MenuItem>
                  <MenuItem value="semicolon">Semicolon (;)-separated</MenuItem>
                  <MenuItem value="keyvalue">Key-Value (key: value)</MenuItem>
                </Select>
              </Box>
              <TextField
                fullWidth
                multiline
                rows={8}
                placeholder={
                  dataFormat === 'json'
                    ? '{\n  "key1": "value1",\n  "key2": 123,\n  "key3": true\n}'
                    : dataFormat === 'csv'
                    ? 'name,age,email\nJohn,30,john@example.com'
                    : dataFormat === 'tsv'
                    ? 'name\tage\temail\nJohn\t30\tjohn@example.com'
                    : dataFormat === 'pipe'
                    ? 'name|age|email\nJohn|30|john@example.com'
                    : dataFormat === 'semicolon'
                    ? 'name;age;email\nJohn;30;john@example.com'
                    : 'name: John\nage: 30\nemail: john@example.com'
                }
                value={dataInput}
                onChange={(e) => {
                  setDataInput(e.target.value);
                  setJsonError('');
                }}
                error={!!jsonError}
                helperText={jsonError}
              />
            </Grid>

            {!formData.schema_id && (
              <Grid item xs={12}>
                <Alert severity="info">
                  💡 <strong>Schema Options:</strong>
                  <br />
                  • Select an existing schema above
                  <br />
                  • Or click "Create" to auto-detect matching schemas from your data
                  <br />
                  • Or create a new schema automatically
                </Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => handleCreateSubmit()} variant="contained" color="primary">
            Create Record
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schema Selection Dialog */}
      <Dialog open={schemaSelectDialogOpen} onClose={() => setSchemaSelectDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Select Schema or Create New</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              Found {matchingSchemas.length} matching schema{matchingSchemas.length !== 1 ? 's' : ''}. Choose one or create new:
            </Typography>

            {matchingSchemas.map((schema: any) => (
              <Button
                key={schema.id}
                fullWidth
                variant="outlined"
                onClick={() => {
                  setSchemaSelectDialogOpen(false);
                  handleCreateSubmit(schema.id);
                }}
                sx={{ mb: 1, justifyContent: 'flex-start', textAlign: 'left' }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    {schema.name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                    {schema.fields?.length || 0} fields • {schema.asset_type?.name || 'No asset type'}
                  </Typography>
                </Box>
              </Button>
            ))}

            <Button
              fullWidth
              variant="contained"
              color="primary"
              onClick={() => {
                setSchemaSelectDialogOpen(false);
                handleCreateSubmit('new');
              }}
              sx={{ mt: 2 }}
            >
              ➕ Create New Schema
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSchemaSelectDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Import Dialog */}
      <Dialog open={bulkDialogOpen} onClose={() => setBulkDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Bulk Import Data</DialogTitle>
        <DialogContent>
          {bulkStep === 'input' && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Schema Name (optional)"
                  placeholder="Will auto-generate if empty"
                  value={formData.schema_name || ''}
                  onChange={(e) => setFormData({ ...formData, schema_name: e.target.value })}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  JSON Array of Records
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={12}
                  placeholder={'[\n  {"name": "Item 1", "value": 100},\n  {"name": "Item 2", "value": 200}\n]'}
                  value={bulkData}
                  onChange={(e) => setBulkData(e.target.value)}
                  error={!!jsonError}
                  helperText={jsonError}
                />
              </Grid>

              <Grid item xs={12}>
                <Alert severity="info">
                  Paste a JSON array of objects. Schema will be automatically created from the first record.
                </Alert>
              </Grid>
            </Grid>
          )}

          {bulkStep === 'schema-select' && bulkSimilarSchemas.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ mb: 3 }}>
                ✅ {bulkRecordsPreview.length} records found
              </Typography>
              
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                Similar schemas detected. How would you like to proceed?
              </Typography>

              {bulkSimilarSchemas.map((schema) => (
                <Box
                  key={schema.schema_id}
                  sx={{
                    p: 2,
                    mb: 2,
                    border: '1px solid #ddd',
                    borderRadius: 2,
                    backgroundColor: '#f9f9f9',
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        {schema.schema_name}
                      </Typography>
                      <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                        {schema.similarity.toFixed(0)}% field match
                      </Typography>
                    </Box>
                    <Chip label={`${schema.similarity.toFixed(0)}% match`} color="primary" size="small" />
                  </Box>

                  {schema.new_fields && schema.new_fields.length > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 'bold' }}>New Fields:</Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {schema.new_fields.map((f: string) => (
                          <Chip key={f} label={f} color="success" variant="outlined" size="small" />
                        ))}
                      </Box>
                    </Box>
                  )}

                  <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                    <Button
                      size="small"
                      variant="contained"
                      onClick={() => {
                        setBulkSchemaChoice({ action: 'reuse', schema_id: schema.schema_id });
                        setBulkStep('confirm');
                      }}
                    >
                      Reuse
                    </Button>
                    {schema.new_fields && schema.new_fields.length > 0 && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setBulkSchemaChoice({ action: 'add_fields', schema_id: schema.schema_id });
                          setBulkStep('confirm');
                        }}
                      >
                        Add Fields
                      </Button>
                    )}
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => {
                        setBulkSchemaChoice({ action: 'new_version', schema_id: schema.schema_id });
                        setBulkStep('confirm');
                      }}
                    >
                      New Version
                    </Button>
                  </Box>
                </Box>
              ))}

              <Box sx={{ mt: 3, p: 2, backgroundColor: '#f0f7ff', borderRadius: 2, border: '1px solid #b3e5fc' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Or Create New Schema
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => {
                    setBulkSchemaChoice({ action: 'create_new' });
                    setBulkStep('confirm');
                  }}
                >
                  Create New Schema
                </Button>
              </Box>
            </Box>
          )}

          {bulkStep === 'confirm' && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
                Ready to Import: {bulkRecordsPreview.length} records
              </Typography>
              {bulkSchemaChoice && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {bulkSchemaChoice.action === 'reuse' && 'Will reuse selected schema'}
                  {bulkSchemaChoice.action === 'add_fields' && 'Will add new fields to selected schema'}
                  {bulkSchemaChoice.action === 'new_version' && 'Will create new version of selected schema'}
                  {bulkSchemaChoice.action === 'create_new' && 'Will create completely new schema'}
                </Alert>
              )}
              <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                Click "Confirm Import" to proceed with the bulk import.
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              if (bulkStep !== 'input') {
                setBulkStep('input');
                setBulkSchemaChoice(null);
                setBulkSimilarSchemas([]);
              } else {
                setBulkDialogOpen(false);
                setBulkData('');
                setBulkStep('input');
              }
            }}
          >
            {bulkStep === 'input' ? 'Cancel' : 'Back'}
          </Button>
          {bulkStep === 'input' && (
            <Button onClick={handleBulkSubmit} variant="contained">
              Next
            </Button>
          )}
          {bulkStep === 'confirm' && (
            <Button onClick={handleBulkConfirmImport} variant="contained">
              Confirm Import
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Filter Drawer */}
      <Drawer anchor="right" open={filterDrawerOpen} onClose={() => setFilterDrawerOpen(false)}>
        <Box sx={{ width: 350, p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">Filters</Typography>
            <IconButton onClick={() => setFilterDrawerOpen(false)}>
              <X size={20} />
            </IconButton>
          </Box>

          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Search"
                value={filters.search || ''}
                onChange={(e) => setFilters({ search: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <Select
                fullWidth
                value={filters.schema_id || ''}
                onChange={(e) => setFilters({ schema_id: Number(e.target.value) || undefined })}
                displayEmpty
              >
                <MenuItem value="">All Schemas</MenuItem>
                {schemas.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.name}
                  </MenuItem>
                ))}
              </Select>
            </Grid>

            <Grid item xs={12}>
              <Select
                fullWidth
                value={filters.asset_type_id || ''}
                onChange={(e) => setFilters({ asset_type_id: Number(e.target.value) || undefined })}
                displayEmpty
              >
                <MenuItem value="">All Asset Types</MenuItem>
                {assetTypes.map((a: AssetType) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.name}
                  </MenuItem>
                ))}
              </Select>
            </Grid>

            <Grid item xs={12}>
              <Button fullWidth variant="contained" onClick={() => fetchRecords(filters)}>
                Apply Filters
              </Button>
            </Grid>

            <Grid item xs={12}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  setFilters({ search: '', schema_id: undefined, asset_type_id: undefined });
                  fetchRecords({});
                }}
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Drawer>

      {/* Detail Drawer */}
      <Drawer
        anchor="right"
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
      >
        <Box sx={{ width: 450, p: 3 }}>
          {selectedRecord && (
            <>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  {editMode ? '✏️ Edit Record' : selectedRecord.name}
                </Typography>
                <Box>
                  <Button
                    size="small"
                    variant={editMode ? 'contained' : 'outlined'}
                    onClick={handleEditToggle}
                    disabled={updating}
                    sx={{ mr: 1 }}
                  >
                    {editMode ? 'Cancel' : 'Edit'}
                  </Button>
                  <IconButton onClick={() => setDetailDrawerOpen(false)}>
                    <X size={20} />
                  </IconButton>
                </Box>
              </Box>

              {editMode && editData && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#f0f9ff', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Name
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    sx={{ mb: 1 }}
                  />

                  <Typography variant="caption" color="text.secondary">
                    Tag
                  </Typography>
                  <TextField
                    fullWidth
                    size="small"
                    value={editData.tag || ''}
                    onChange={(e) => setEditData({ ...editData, tag: e.target.value })}
                    sx={{ mb: 2 }}
                  />

                  <Button
                    fullWidth
                    variant="contained"
                    color="success"
                    size="small"
                    onClick={handleSaveUpdate}
                    disabled={updating}
                  >
                    {updating ? 'Saving...' : '✅ Save Changes'}
                  </Button>
                </Box>
              )}

              <Card sx={{ p: 2, mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  ID
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {selectedRecord.id}
                </Typography>
              </Card>

              <Card sx={{ p: 2, mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Schema
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {schemas.find((s) => s.id === selectedRecord.schema_id)?.name || `Schema ${selectedRecord.schema_id}`}
                </Typography>
              </Card>

              <Card sx={{ p: 2, mb: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Asset Type
                </Typography>
                <Typography variant="body1" fontWeight={500}>
                  {selectedRecord.asset_type_id
                    ? assetTypes.find((at) => at.id === selectedRecord.asset_type_id)?.name || `Asset Type ${selectedRecord.asset_type_id}`
                    : '-'}
                </Typography>
              </Card>

              <Card sx={{ p: 2, mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  Data Values
                </Typography>
                <pre
                  style={{
                    background: '#f5f5f5',
                    padding: '12px',
                    borderRadius: '4px',
                    overflow: 'auto',
                    fontSize: '12px',
                  }}
                >
                  {JSON.stringify(selectedRecord.values, null, 2)}
                </pre>
              </Card>

              <Card sx={{ p: 2 }}>
                <Typography variant="caption" color="text.secondary">
                  Created
                </Typography>
                <Typography variant="body2">
                  {new Date(selectedRecord.created_at).toLocaleString()}
                </Typography>
              </Card>
            </>
          )}
        </Box>
      </Drawer>

      {/* Edit Record Dialog */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Edit Record: {recordToEdit?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Edit the JSON data below. New fields will be detected and you can choose whether to add them to the schema.
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={15}
            value={editRecordData}
            onChange={(e) => setEditRecordData(e.target.value)}
            placeholder="Enter JSON data..."
            variant="outlined"
            sx={{
              fontFamily: 'monospace',
              '& textarea': {
                fontFamily: 'monospace',
                fontSize: '13px',
              }
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleEditRecordSubmit}
            variant="contained"
            color="primary"
          >
            Update Record
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schema Change Confirmation Dialog */}
      <Dialog
        open={schemaChangeDialogOpen}
        onClose={() => setSchemaChangeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          🔔 New Fields Detected
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            The following new fields were detected in your updated data:
          </Typography>
          <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 1, mb: 2 }}>
            {newFieldsDetected.map((field, idx) => (
              <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace' }}>
                • {field}
              </Typography>
            ))}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Would you like to add these fields to the <strong>{recordToEdit?.schema_name}</strong> schema?
          </Typography>
          <Box sx={{ 
            p: 1.5, 
            bgcolor: '#fff3cd', 
            border: '1px solid #ffc107',
            borderRadius: 1,
            mb: 2
          }}>
            <Typography variant="caption" color="warning.dark">
              ⚠️ Adding fields to the schema will affect all records using this schema.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => {
              setSchemaChangeDialogOpen(false);
              try {
                const values = JSON.parse(editRecordData);
                performUpdate(values, false);
              } catch (err) {
                console.error('JSON parse error:', err);
              }
            }}
            variant="outlined"
          >
            Keep Current Schema
          </Button>
          <Button 
            onClick={() => {
              setSchemaChangeDialogOpen(false);
              try {
                const values = JSON.parse(editRecordData);
                performUpdate(values, true);
              } catch (err) {
                console.error('JSON parse error:', err);
              }
            }}
            variant="contained"
            color="primary"
          >
            Add to Schema
          </Button>
        </DialogActions>
      </Dialog>

      {/* File Import Dialog */}
      <FileImportDialog 
        open={fileImportOpen} 
        onClose={() => setFileImportOpen(false)}
        onSuccess={() => {
          fetchRecords();
          setFileImportOpen(false);
        }}
      />

      {/* Record Data Viewer - View bulk import data rows */}
      {dataViewerOpen && viewingRecord && (
        <RecordDataViewer
          recordId={viewingRecord.id}
          recordName={viewingRecord.name}
          onClose={() => {
            setDataViewerOpen(false);
            setViewingRecord(null);
            fetchRecords(filters);
          }}
        />
      )}

      {/* Advanced Record Editor - Multi-mode editing with schema validation */}
      {advancedEditorOpen && editingRecord && (
        <AdvancedRecordEditor
          open={advancedEditorOpen}
          recordId={editingRecord.id}
          recordName={editingRecord.name}
          schemaId={editingRecord.schema_id}
          currentData={editingRecord.values || {}}
          onClose={() => {
            setAdvancedEditorOpen(false);
            setEditingRecord(null);
          }}
          onSuccess={() => {
            setAdvancedEditorOpen(false);
            setEditingRecord(null);
            fetchRecords(filters);
            toast.success('Record updated successfully!');
          }}
        />
      )}
    </Box>
  );
}
