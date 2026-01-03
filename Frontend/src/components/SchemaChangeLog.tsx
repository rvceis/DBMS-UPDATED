import { useEffect, useState } from 'react';
import { Card, CardContent, Typography, Stack, Chip, Divider } from '@mui/material';

export function SchemaChangeLog({ schemaId }: { schemaId: number }) {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!schemaId) return;
    setLoading(true);
    fetch(`/api/schemas/${schemaId}/changelog`)
      .then((res) => res.json())
      .then((data) => setLogs(data))
      .finally(() => setLoading(false));
  }, [schemaId]);

  if (!schemaId) return null;

  return (
    <Card sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          Schema Change Log
        </Typography>
        {loading ? (
          <Typography>Loading...</Typography>
        ) : logs.length === 0 ? (
          <Typography color="textSecondary">No change log entries.</Typography>
        ) : (
          <Stack spacing={2} divider={<Divider flexItem />}>
            {logs.map((log) => (
              <Stack key={log.id} spacing={0.5}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label={log.change_type} size="small" color="primary" />
                  <Typography variant="body2" color="textSecondary">
                    {log.timestamp?.replace('T', ' ').slice(0, 19)}
                  </Typography>
                  {log.changed_by_name && (
                    <Typography variant="body2" color="textSecondary">
                      by {log.changed_by_name}
                    </Typography>
                  )}
                </Stack>
                <Typography variant="body2">{log.description}</Typography>
                {log.change_details && log.change_details.changes && log.change_details.changes.length > 0 && (
                  <Stack spacing={0.5} sx={{ mt: 1, pl: 2 }}>
                    {log.change_details.changes.map((change: string, idx: number) => (
                      <Typography 
                        key={idx} 
                        variant="body2" 
                        sx={{ 
                          fontFamily: 'monospace', 
                          fontSize: 12,
                          color: 'text.secondary'
                        }}
                      >
                        → {change}
                      </Typography>
                    ))}
                  </Stack>
                )}
              </Stack>
            ))}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
