import { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Paper,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Eye, Download } from 'lucide-react';
import toast from 'react-hot-toast';

interface SchemaContentViewerProps {
  schemaId: number;
  schemaName: string;
}

interface SchemaSummary {
  schema: any;
  summary: {
    record_count: number;
    field_count: number;
    fields: Array<{
      name: string;
      type: string;
      required: boolean;
      description?: string;
    }>;
    tags: string[];
    asset_types: Array<{ id: number; name: string }>;
  };
}

interface SchemaRecords {
  schema: any;
  records: any[];
  total: number;
  limit: number;
  offset: number;
}

export default function SchemaContentViewer({ schemaId, schemaName }: SchemaContentViewerProps) {
  const [open, setOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [summary, setSummary] = useState<SchemaSummary | null>(null);
  const [records, setRecords] = useState<SchemaRecords | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await fetch(`/api/data/schema/${schemaId}/content`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch schema content');
      }

      const data = await response.json();
      setSummary(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch schema content');
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await fetch(`/api/data/schema/${schemaId}/records?limit=50`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch records');
      }

      const data = await response.json();
      setRecords(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch records');
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    fetchSummary();
  };

  const handleClose = () => {
    setOpen(false);
    setTabValue(0);
    setSummary(null);
    setRecords(null);
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    if (newValue === 1 && !records) {
      fetchRecords();
    }
  };

  const downloadAsJSON = () => {
    if (!summary) return;
    const dataStr = JSON.stringify(summary, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${schemaName}_content.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('Downloaded schema content');
  };

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        startIcon={<Eye size={16} />}
        onClick={handleOpen}
      >
        View Content
      </Button>

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>
          Schema Content: {schemaName}
        </DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Overview" />
            <Tab label={`Records (${summary?.summary?.record_count || 0})`} />
          </Tabs>

          {/* Overview Tab */}
          {tabValue === 0 && (
            <Box sx={{ pt: 2 }}>
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress />
                </Box>
              )}

              {summary && !loading && (
                <>
                  {/* Schema Stats */}
                  <Card sx={{ mb: 2 }}>
                    <CardHeader title="Statistics" />
                    <CardContent>
                      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Total Records
                          </Typography>
                          <Typography variant="h6">
                            {summary.summary.record_count}
                          </Typography>
                        </Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Total Fields
                          </Typography>
                          <Typography variant="h6">
                            {summary.summary.field_count}
                          </Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>

                  {/* Fields */}
                  <Card sx={{ mb: 2 }}>
                    <CardHeader title="Fields" />
                    <CardContent>
                      <TableContainer component={Paper}>
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                              <TableCell><strong>Field Name</strong></TableCell>
                              <TableCell><strong>Type</strong></TableCell>
                              <TableCell align="center"><strong>Required</strong></TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {summary.summary.fields.map((field, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{field.name}</TableCell>
                                <TableCell>
                                  <Chip
                                    label={field.type}
                                    size="small"
                                    variant="outlined"
                                  />
                                </TableCell>
                                <TableCell align="center">
                                  {field.required ? '✅' : '—'}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>

                  {/* Tags */}
                  {summary.summary.tags.length > 0 && (
                    <Card sx={{ mb: 2 }}>
                      <CardHeader title="Tags" />
                      <CardContent>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {summary.summary.tags.map((tag, idx) => (
                            <Chip key={idx} label={tag} />
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Asset Types */}
                  {summary.summary.asset_types.length > 0 && (
                    <Card sx={{ mb: 2 }}>
                      <CardHeader title="Asset Types Used" />
                      <CardContent>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          {summary.summary.asset_types.map((at, idx) => (
                            <Chip key={idx} label={at.name} color="primary" variant="outlined" />
                          ))}
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Download Button */}
                  <Button
                    variant="contained"
                    startIcon={<Download size={16} />}
                    onClick={downloadAsJSON}
                    fullWidth
                  >
                    Download as JSON
                  </Button>
                </>
              )}
            </Box>
          )}

          {/* Records Tab */}
          {tabValue === 1 && (
            <Box sx={{ pt: 2 }}>
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress />
                </Box>
              )}

              {records && !loading && (
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Showing {records.records.length} of {records.total} records
                  </Typography>

                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                          <TableCell><strong>ID</strong></TableCell>
                          <TableCell><strong>Name</strong></TableCell>
                          <TableCell><strong>Tag</strong></TableCell>
                          <TableCell><strong>Created</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {records.records.map((record, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{record.id}</TableCell>
                            <TableCell>{record.name}</TableCell>
                            <TableCell>
                              {record.tag ? <Chip label={record.tag} size="small" /> : '—'}
                            </TableCell>
                            <TableCell>
                              {new Date(record.created_at).toLocaleDateString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
