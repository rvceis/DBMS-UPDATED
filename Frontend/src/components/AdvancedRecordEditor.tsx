import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import { FileText, Code, Table as TableIcon } from 'lucide-react';
import toast from 'react-hot-toast';
import axios from 'axios';

interface AdvancedRecordEditorProps {
  open: boolean;
  recordId: number;
  recordName: string;
  schemaId: number;
  currentData: Record<string, any>;
  onClose: () => void;
  onSuccess: () => void;
}

interface SchemaField {
  id: number;
  field_name: string;
  field_type: string;
  is_required: boolean;
  description?: string;
}

type EditMode = 'form' | 'json' | 'csv';
type SchemaAction = 'validate' | 'adapt' | 'create_new' | 'keep_current';

export default function AdvancedRecordEditor({
  open,
  recordId,
  recordName,
  schemaId,
  currentData,
  onClose,
  onSuccess,
}: AdvancedRecordEditorProps) {
  const [mode, setMode] = useState<EditMode>('form');
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [jsonData, setJsonData] = useState('');
  const [csvData, setCsvData] = useState('');
  const [schemaFields, setSchemaFields] = useState<SchemaField[]>([]);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState<any>(null);
  const [newFields, setNewFields] = useState<string[]>([]);
  const [schemaAction, setSchemaAction] = useState<SchemaAction>('validate');
  const [newSchemaName, setNewSchemaName] = useState('');

  useEffect(() => {
    if (open) {
      fetchSchemaFields();
      setFormData({ ...currentData });
      setJsonData(JSON.stringify(currentData, null, 2));
      setCsvData(objectToCsv(currentData));
    }
  }, [open, schemaId, currentData]);

  const fetchSchemaFields = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/schemas/detail/${schemaId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setSchemaFields(response.data.fields || []);
    } catch (error) {
      toast.error('Failed to fetch schema');
    }
  };

  const objectToCsv = (obj: Record<string, any>) => {
    const keys = Object.keys(obj);
    const values = keys.map(k => obj[k]);
    return `${keys.join(',')}\n${values.join(',')}`;
  };

  const csvToObject = (csv: string) => {
    const lines = csv.trim().split('\n');
    if (lines.length < 2) return {};
    
    const keys = lines[0].split(',');
    const values = lines[1].split(',');
    const obj: Record<string, any> = {};
    keys.forEach((key, i) => {
      obj[key.trim()] = values[i]?.trim() || '';
    });
    return obj;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setValidationError(null);

    try {
      let dataToSend: any;
      let format: string = mode;

      if (mode === 'form') {
        dataToSend = formData;
        format = 'form';
      } else if (mode === 'json') {
        try {
          dataToSend = JSON.parse(jsonData);
        } catch (e) {
          toast.error('Invalid JSON');
          setLoading(false);
          return;
        }
      } else if (mode === 'csv') {
        dataToSend = csvToObject(csvData);
      }

      const token = localStorage.getItem('token');
      const response = await axios.put(`/api/metadata/${recordId}/update-advanced`, {
        format,
        data: dataToSend,
        schema_action: schemaAction,
        new_schema_name: schemaAction === 'create_new' ? newSchemaName : undefined,
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      toast.success('Record updated successfully!');
      onSuccess();
      onClose();
    } catch (error: any) {
      if (error.response?.data?.validation_error) {
        // Schema validation failed - new fields detected
        setValidationError(error.response.data);
        setNewFields(error.response.data.new_fields || []);
        toast.error('New fields detected - choose an action to proceed');
      } else {
        toast.error(error.response?.data?.error || 'Failed to update record');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetryWithAction = async () => {
    setValidationError(null);
    handleSubmit();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box>
          <Typography variant="h6">Edit Record: {recordName}</Typography>
          <Typography variant="caption" color="text.secondary">
            Record ID: {recordId} • Schema ID: {schemaId}
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Mode Toggle */}
        <Box mb={3}>
          <Typography variant="subtitle2" gutterBottom>
            Edit Mode
          </Typography>
          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={(_, newMode) => newMode && setMode(newMode)}
            size="small"
            fullWidth
          >
            <ToggleButton value="form">
              <FileText size={16} style={{ marginRight: 8 }} />
              Form
            </ToggleButton>
            <ToggleButton value="json">
              <Code size={16} style={{ marginRight: 8 }} />
              JSON
            </ToggleButton>
            <ToggleButton value="csv">
              <TableIcon size={16} style={{ marginRight: 8 }} />
              CSV
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Validation Error */}
        {validationError && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {validationError.message}
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
              {newFields.map(field => (
                <Chip key={field} label={field} size="small" color="warning" />
              ))}
            </Box>
            
            <Typography variant="body2" gutterBottom>
              Choose how to handle new fields:
            </Typography>
            
            <ToggleButtonGroup
              value={schemaAction}
              exclusive
              onChange={(_, action) => action && setSchemaAction(action)}
              size="small"
              fullWidth
              sx={{ mt: 1 }}
            >
              <ToggleButton value="adapt">Add to Schema</ToggleButton>
              <ToggleButton value="create_new">New Schema</ToggleButton>
              <ToggleButton value="keep_current">Keep Current</ToggleButton>
            </ToggleButtonGroup>

            {schemaAction === 'create_new' && (
              <TextField
                label="New Schema Name"
                value={newSchemaName}
                onChange={(e) => setNewSchemaName(e.target.value)}
                fullWidth
                size="small"
                sx={{ mt: 2 }}
                placeholder="Enter name for new schema version"
              />
            )}

            <Button
              variant="contained"
              size="small"
              onClick={handleRetryWithAction}
              sx={{ mt: 2 }}
              fullWidth
            >
              Apply Changes
            </Button>
          </Alert>
        )}

        {/* Form Mode */}
        {mode === 'form' && (
          <Box display="flex" flexDirection="column" gap={2}>
            {schemaFields.length > 0 ? (
              schemaFields.map((field) => (
                <TextField
                  key={field.id}
                  label={field.field_name}
                  value={formData[field.field_name] ?? ''}
                  onChange={(e) =>
                    setFormData({ ...formData, [field.field_name]: e.target.value })
                  }
                  required={field.is_required}
                  helperText={field.description}
                  fullWidth
                  type={
                    field.field_type === 'integer' || field.field_type === 'float'
                      ? 'number'
                      : 'text'
                  }
                />
              ))
            ) : (
              <Alert severity="info">Loading schema fields...</Alert>
            )}

            {/* Additional fields not in schema */}
            {Object.keys(formData).filter(
              key => !schemaFields.find(f => f.field_name === key)
            ).map(key => (
              <TextField
                key={key}
                label={`${key} (not in schema)`}
                value={formData[key] ?? ''}
                onChange={(e) =>
                  setFormData({ ...formData, [key]: e.target.value })
                }
                fullWidth
              />
            ))}
          </Box>
        )}

        {/* JSON Mode */}
        {mode === 'json' && (
          <TextField
            multiline
            rows={15}
            value={jsonData}
            onChange={(e) => setJsonData(e.target.value)}
            fullWidth
            placeholder='{"field1": "value1", "field2": "value2"}'
            sx={{ fontFamily: 'monospace' }}
          />
        )}

        {/* CSV Mode */}
        {mode === 'csv' && (
          <TextField
            multiline
            rows={10}
            value={csvData}
            onChange={(e) => setCsvData(e.target.value)}
            fullWidth
            placeholder="field1,field2,field3&#10;value1,value2,value3"
            sx={{ fontFamily: 'monospace' }}
          />
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading && <CircularProgress size={16} />}
        >
          {loading ? 'Updating...' : 'Update Record'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
