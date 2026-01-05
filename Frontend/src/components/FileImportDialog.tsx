import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  TextField,
  Chip,
} from '@mui/material';
import { Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { useSchemaStore } from '../stores/schemaStore';
import { useAssetTypesStore } from '../stores/assetTypesStore';

interface FileImportDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function FileImportDialog({ open, onClose, onSuccess }: FileImportDialogProps) {
  const { schemas } = useSchemaStore();
  const { assetTypes } = useAssetTypesStore();

  const [file, setFile] = useState<File | null>(null);
  const [schemaId, setSchemaId] = useState<number | ''>('');
  const [assetTypeId, setAssetTypeId] = useState<number | ''>('');
  const [autoAdapt, setAutoAdapt] = useState(true);
  const [tag, setTag] = useState('');

  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [allParsedRecords, setAllParsedRecords] = useState<any[]>([]);
  const [step, setStep] = useState<'upload' | 'schema-select' | 'preview' | 'confirm'>('upload');
  const [suggestedFields, setSuggestedFields] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [similarSchemas, setSimilarSchemas] = useState<any[]>([]);
  const [schemaChoice, setSchemaChoice] = useState<{action: 'reuse' | 'new_version' | 'add_fields' | 'create_new', schema_id?: number} | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const allowedExtensions = ['json', 'csv', 'tsv', 'xlsx', 'xls', 'txt'];
    const fileExtension = selectedFile.name.split('.').pop()?.toLowerCase();
    if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
      const errMsg = `Invalid file format: .${fileExtension}. Supported formats: JSON, CSV, TSV, Excel (.xlsx, .xls), TXT`;
      setError(errMsg);
      toast.error(errMsg);
      return;
    }

    setFile(selectedFile);
    setError('');

    // Preview file
    setLoading(true);
    try {
      console.log(`📁 FILE SELECTED: ${selectedFile.name}, Size: ${selectedFile.size} bytes, Type: ${selectedFile.type}`);
      
      const formData = new FormData();
      formData.append('file', selectedFile);
      if (schemaId) formData.append('schema_id', String(schemaId));
      if (assetTypeId) formData.append('asset_type_id', String(assetTypeId));
      formData.append('auto_adapt_schema', String(autoAdapt));
      
      console.log(`📤 SENDING FormData with file size: ${selectedFile.size} bytes`);

      const response = await fetch('/api/uploads/import-file', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = `Failed to parse ${fileExtension?.toUpperCase()} file`;
        try {
          const err = await response.json();
          errorMessage = err.error || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const responseText = await response.text();
      if (!responseText) {
        throw new Error('Empty response from server');
      }

      const data = JSON.parse(responseText);
      console.log('📥 FILE UPLOAD RESPONSE KEYS:', Object.keys(data));
      console.log('📥 FILE UPLOAD RESPONSE:', {
        record_count: data.record_count,
        preview_length: data.preview?.length,
        all_records_exists: !!data.all_records,
        all_records_length: data.all_records?.length,
        fields: data.data_fields
      });
      
      if (!data.all_records) {
        console.warn('⚠️ WARNING: all_records not in response! Response keys:', Object.keys(data));
        console.warn('Response text length:', responseText.length);
      }
      
      setPreview(data);
      // Store ALL parsed records for import, not just preview
      const allRecords = data.all_records || data.preview || [];
      console.log(`📦 STORING ${allRecords.length} RECORDS FOR IMPORT (server said: ${data.record_count})`);
      
      if (allRecords.length < data.record_count) {
        console.error(`❌ ERROR: Only got ${allRecords.length} records but server parsed ${data.record_count}`);
      }
      
      setAllParsedRecords(allRecords);
      setSuggestedFields(data.suggested_fields || []);
      setSimilarSchemas(data.similar_schemas || []);
      
      // If similar schemas found, go to selection step. Otherwise go to preview
      if (data.similar_schemas && data.similar_schemas.length > 0) {
        console.log(`🔍 Found ${data.similar_schemas.length} similar schemas`);
        setStep('schema-select');
      } else {
        console.log('ℹ️ No similar schemas found, going to preview step');
        setStep('preview');
      }
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to import file';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!allParsedRecords || allParsedRecords.length === 0) {
      toast.error('No records to import');
      return;
    }

    console.log(`📤 IMPORTING ${allParsedRecords.length} RECORDS TO BACKEND`);
    
    // Generate better record name from file name
    let recordName = 'Imported Dataset';
    if (file) {
      // Remove extension and use as base name
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
      recordName = nameWithoutExt || 'Imported Dataset';
    }
    
    const importPayload = {
      records: allParsedRecords,  // Send ALL records, not just preview
      schema_id: !schemaChoice ? (preview.schema_info?.schema_id || schemaId || undefined) : undefined,
      asset_type_id: assetTypeId || undefined,
      tag: tag || undefined,
      record_name: recordName,
      suggested_fields: suggestedFields || [],
      schema_choice: schemaChoice || undefined,  // Add schema choice here
    };
    
    console.log(`📦 Payload size: ${JSON.stringify(importPayload).length / 1024}KB`);
    console.log(`📦 Records in payload: ${importPayload.records.length}`);
    try {
      const response = await fetch('/api/uploads/import-file-confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(importPayload),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to import records';
        try {
          const err = await response.json();
          errorMessage = err.error || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const responseText = await response.text();
      if (!responseText) {
        throw new Error('Empty response from server');
      }

      const result = JSON.parse(responseText);
      console.log(`✅ IMPORT SUCCESS:`, {
        record_id: result.record_id,
        total_rows_stored: result.total_rows,
        message: result.message
      });
      toast.success(`✅ Imported ${result.total_rows} records successfully!`);
      handleClose();
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to import records');
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setPreview(null);
    setStep('upload');
    setSuggestedFields([]);
    setError('');
    setSchemaId('');
    setAssetTypeId('');
    setTag('');
    onClose();
  };

  const getAssetTypeName = (id: number | undefined) => {
    if (!id) return '-';
    return assetTypes.find((at) => at.id === id)?.name || `Asset Type ${id}`;
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Upload size={24} />
          Import Data from File
        </Box>
      </DialogTitle>

      <DialogContent>
        {step === 'upload' && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" sx={{ mb: 2 }}>
              Supported formats: JSON, CSV, TSV, Excel (.xlsx), Tab-separated values
            </Typography>

            <Box
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': { borderColor: '#999' },
              }}
              component="label"
            >
              <input
                type="file"
                hidden
                accept=".json,.csv,.tsv,.xlsx,.xls,.txt"
                onChange={handleFileSelect}
                disabled={loading}
              />
              <Typography>Drag & drop your file or click to select</Typography>
              {file && <Typography variant="body2" sx={{ mt: 1, color: 'success.main' }}>{file.name}</Typography>}
            </Box>

            <Box sx={{ mt: 3, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
              <Select
                value={schemaId}
                onChange={(e) => setSchemaId(e.target.value as any)}
                displayEmpty
              >
                <MenuItem value="">Auto-detect schema</MenuItem>
                {schemas.map((s) => (
                  <MenuItem key={s.id} value={s.id}>
                    {s.name}
                  </MenuItem>
                ))}
              </Select>

              <Select
                value={assetTypeId}
                onChange={(e) => setAssetTypeId(e.target.value as any)}
                displayEmpty
              >
                <MenuItem value="">Select Asset Type</MenuItem>
                {assetTypes.map((at) => (
                  <MenuItem key={at.id} value={at.id}>
                    {at.name}
                  </MenuItem>
                ))}
              </Select>

              <TextField
                fullWidth
                label="Tag (optional)"
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                placeholder="e.g., Batch 1"
              />

              <FormControlLabel
                control={<Checkbox checked={autoAdapt} onChange={(e) => setAutoAdapt(e.target.checked)} />}
                label="Auto-adapt schema for new fields"
              />
            </Box>

            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </Box>
        )}

        {step === 'schema-select' && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>
              ✅ {allParsedRecords.length} records found in file
            </Typography>
            
            <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 'bold' }}>
              Similar schemas detected. How would you like to proceed?
            </Typography>

            {similarSchemas.map((schema, idx) => (
              <Box
                key={schema.schema_id}
                sx={{
                  p: 3,
                  mb: 2,
                  border: '1px solid #ddd',
                  borderRadius: 2,
                  backgroundColor: '#f9f9f9',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      {schema.schema_name}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                      {schema.similarity.toFixed(0)}% field match
                    </Typography>
                  </Box>
                  <Chip
                    label={`${schema.similarity.toFixed(0)}% match`}
                    color={schema.similarity >= 80 ? 'success' : 'primary'}
                    size="small"
                  />
                </Box>

                {schema.new_fields && schema.new_fields.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                      New Fields in Your File:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {schema.new_fields.map((field) => (
                        <Chip
                          key={field}
                          label={field}
                          color="success"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {schema.missing_fields && schema.missing_fields.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                      Fields in Schema but Not in File:
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {schema.missing_fields.map((field) => (
                        <Chip
                          key={field}
                          label={field}
                          color="warning"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => {
                      setSchemaChoice({
                        action: 'reuse',
                        schema_id: schema.schema_id,
                      });
                      setStep('preview');
                    }}
                  >
                    Reuse This Schema
                  </Button>

                  {schema.new_fields && schema.new_fields.length > 0 && (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => {
                        setSchemaChoice({
                          action: 'add_fields',
                          schema_id: schema.schema_id,
                        });
                        setStep('preview');
                      }}
                    >
                      Add New Fields to Schema
                    </Button>
                  )}

                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => {
                      setSchemaChoice({
                        action: 'new_version',
                        schema_id: schema.schema_id,
                      });
                      setStep('preview');
                    }}
                  >
                    Create New Version
                  </Button>
                </Box>
              </Box>
            ))}

            <Box sx={{ mt: 3, p: 3, backgroundColor: '#f0f7ff', borderRadius: 2, border: '1px solid #b3e5fc' }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
                Or Create Completely New Schema
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                This will create a new schema with all fields from your file.
              </Typography>
              <Button
                variant="contained"
                onClick={() => {
                  setSchemaChoice({
                    action: 'create_new',
                  });
                  setStep('preview');
                }}
              >
                Create New Schema
              </Button>
            </Box>

            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </Box>
        )}

        {step === 'preview' && preview && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle2">
                Found {preview.record_count} records • Format: {preview.format_detected}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {preview.schema_created && (
                  <Chip label="✨ New schema created" color="success" size="small" />
                )}
                {preview.fields_added && !preview.schema_created && (
                  <Chip label="✨ Schema updated with new fields" color="success" size="small" />
                )}
                {preview.schema_info && (
                  <Chip label={`Schema: ${preview.schema_info.schema_name}`} color="primary" size="small" variant="outlined" />
                )}
              </Box>
            </Box>

            {suggestedFields.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Detected Fields</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {suggestedFields.map((field) => (
                    <Chip
                      key={field.field_name}
                      label={`${field.field_name} (${field.field_type})`}
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Box>
              </Box>
            )}

            <Typography variant="subtitle2" sx={{ mb: 1 }}>Preview (first 10 records)</Typography>
            <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    {Object.keys(preview.preview[0] || {}).map((key) => (
                      <TableCell key={key} sx={{ fontWeight: 'bold' }}>
                        {key}
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {preview.preview.map((row: any, idx: number) => (
                    <TableRow key={idx}>
                      {Object.values(row).map((val: any, vidx: number) => (
                        <TableCell key={vidx}>
                          {val === null || val === undefined
                            ? '-'
                            : typeof val === 'object'
                              ? JSON.stringify(val).substring(0, 80) + (JSON.stringify(val).length > 80 ? '...' : '')
                              : String(val).substring(0, 50)}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button
          onClick={() => {
            if (step === 'schema-select') {
              setStep('upload');
              setFile(null);
              setAllParsedRecords([]);
              setSimilarSchemas([]);
              setSchemaChoice(null);
              setError('');
            } else if (step === 'preview') {
              setStep('upload');
              setFile(null);
              setAllParsedRecords([]);
              setSimilarSchemas([]);
              setSchemaChoice(null);
              setError('');
            } else {
              handleClose();
            }
          }}
          disabled={loading}
        >
          {step === 'schema-select' || step === 'preview' ? 'Start Over' : 'Cancel'}
        </Button>
        {step === 'preview' && (
          <Button
            variant="contained"
            onClick={handleConfirmImport}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : undefined}
          >
            {loading ? 'Importing...' : 'Confirm & Import'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
