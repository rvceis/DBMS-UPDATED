import { useEffect, useMemo, useState } from 'react';
import { useTheme } from '@mui/material/styles';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Stack,
  Typography,
  Divider,
  Button,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';
import { useAuthStore } from '@/stores/authStore';
import { useSchemaStore } from '@/stores/schemaStore';
import { useDataStore } from '@/stores/dataStore';

type DashboardStats = {
  total_data_records: number;
  total_schemas: number;
  total_users: number;
  total_asset_types: number;
  recent_records_7days: number;
};

type ActivityItem = {
  id: number;
  schema_id: number | null;
  schema_version: number | null;
  change_type: string;
  description: string | null;
  changed_by: number | null;
  changed_by_name: string | null;
  timestamp: string | null;
};

const COLORS = ['#6366F1', '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6'];

export const Analytics = () => {
  const theme = useTheme();
  const { token, user } = useAuthStore();
  const { schemas, fetchSchemas } = useSchemaStore();
  const { records, fetchRecords } = useDataStore();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [byAssetType, setByAssetType] = useState<{ name: string; value: number }[]>([]);
  const [timeline, setTimeline] = useState<{ date: string; records: number }[]>([]);
  const [topTypes, setTopTypes] = useState<{ name: string; count: number }[]>([]);
  const [recent, setRecent] = useState<ActivityItem[]>([]);
  const [userActivity, setUserActivity] = useState<{ username: string; count: number }[]>([]);
  const [expandedAssets, setExpandedAssets] = useState<string[]>([]);
  const [expandedSchemas, setExpandedSchemas] = useState<string[]>([]);
  const [assetTypeNames, setAssetTypeNames] = useState<Record<number, string>>({});
  const [nodePositions, setNodePositions] = useState<Record<string, { x: number; y: number }>>({});
  const [draggingNode, setDraggingNode] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [flowMode, setFlowMode] = useState<'assign' | 'auto'>('assign');

  useEffect(() => {
    fetchSchemas();
    fetchRecords({ limit: 50 });
  }, []);

  useEffect(() => {
    const fetchAnalytics = async () => {
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
      const safeJson = async (res: Response) => {
        if (!res.ok) throw new Error((await res.text()) || 'Request failed');
        return res.json();
      };
      try {
        const [s, bat, tl, ta, ra] = await Promise.all([
          fetch('/api/analytics/dashboard', { headers }).then(safeJson),
          fetch('/api/analytics/data-by-asset-type', { headers }).then(safeJson),
          fetch('/api/analytics/data-timeline', { headers }).then(safeJson),
          fetch('/api/analytics/top-asset-types', { headers }).then(safeJson),
          fetch('/api/analytics/recent-activity', { headers }).then(safeJson),
        ]);
        setStats(s);
        console.log('📊 Analytics data:', { bat, tl, ta, ra });
        setByAssetType(bat || []);
        setTimeline(tl || []);
        setTopTypes(ta || []);
        setRecent(ra || []);
        // Admin-only aggregated user activity
        try {
          if (user?.role === 'admin') {
            const ua = await fetch('/api/analytics/user-activity', { headers }).then(safeJson);
            setUserActivity(ua || []);
          } else {
            setUserActivity([]);
          }
        } catch (e) {
          console.warn('user-activity fetch failed', e);
          setUserActivity([]);
        }
      } catch (e) {
        console.error('Analytics fetch error:', e);
      }
    };
    if (token) {
      fetchAnalytics();
    }
  }, [token, user?.role]);

  // Relationship graph layout: hierarchical tree with parent-child relationships
  const relationGraph = useMemo(() => {
    // Build unique asset type nodes from schemas and records
    const assetTypes = new Map<number | 'none', { id: string; label: string; col: number }>();
    const schemaNodes = new Map<number, { id: string; label: string; col: number; asset_type_id?: number; parent?: string }>();
    const recordNodes = new Map<number, { id: string; label: string; col: number; schema_id?: number; parent?: string }>();

    schemas.forEach((s) => {
      schemaNodes.set(s.id, { id: `S${s.id}`, label: `${s.name} v${s.version}`, col: 1, asset_type_id: s.asset_type_id, parent: `A${s.asset_type_id ?? -1}` });
      const k = (s.asset_type_id ?? -1) as number | 'none';
      if (!assetTypes.has(k)) {
        const assetTypeId = s.asset_type_id || -1;
        const assetTypeName = assetTypeNames[assetTypeId] || (s.asset_type_id ? `AssetType #${s.asset_type_id}` : 'Unassigned');
        assetTypes.set(k, { id: `A${k}`, label: assetTypeName, col: 0 });
      }
    });
    records.slice(0, 30).forEach((r) => {
      recordNodes.set(r.id, { id: `M${r.id}`, label: r.name || `Record #${r.id}`, col: 2, schema_id: r.schema_id, parent: `S${r.schema_id}` });
    });

    // Build hierarchical structure
    const assetTypesArray = Array.from(assetTypes.values());
    const schemaArray = Array.from(schemaNodes.values());
    const recordArray = Array.from(recordNodes.values());
    
    const nodes: Array<any> = [];
    const links: { from: string; to: string; color: string }[] = [];
    
    let currentX = 100;
    const verticalSpacing = 70;
    
    // Position asset types with their children hierarchically
    assetTypesArray.forEach((at) => {
      const childSchemas = schemaArray.filter(s => (s.asset_type_id ?? -1) === parseInt(at.id.substring(1)));
      
      if (childSchemas.length === 0) {
        // No children, just position the asset type
        nodes.push({ ...at, x: currentX, y: 100, children: [] });
        currentX += 250;
        return;
      }

      // Calculate total height needed for this subtree
      let subtreeHeight = 0;
      const childHeights: number[] = [];
      
      childSchemas.forEach((schema) => {
        const schemaRecords = recordArray.filter(r => r.schema_id === schema.id && expandedAssets.includes(schema.id));
        const height = (schemaRecords.length + 1) * verticalSpacing;
        childHeights.push(height);
        subtreeHeight += height;
      });
      
      // Position asset type at top
      const assetTypeY = 50 + subtreeHeight / 2 - 35;
      nodes.push({ ...at, x: currentX, y: assetTypeY, children: childSchemas.map(s => s.id) });
      
      // Position child schemas vertically below asset type
      let currentY = 100;
      childSchemas.forEach((s, idx) => {
        const schemaRecords = recordArray.filter(r => r.schema_id === s.id);
        nodes.push({ ...s, x: currentX + 200, y: currentY, children: schemaRecords.map(r => r.id) });
        links.push({ from: at.id, to: s.id, color: '#94A3B8' });
        
        // Add a single records node instead of individual records
        if (schemaRecords.length > 0) {
          const recordsNodeId = `RECS${s.id}`;
          const recordLabel = expandedSchemas.includes(s.id) 
            ? `${schemaRecords.length} Records`
            : `+${schemaRecords.length}`;
          
          nodes.push({
            id: recordsNodeId,
            label: recordLabel,
            col: 2,
            x: currentX + 400,
            y: currentY,
            children: expandedSchemas.includes(s.id) ? schemaRecords.map(r => r.id) : [],
            isRecordsNode: true,
            schemaId: s.id
          });
          links.push({ from: s.id, to: recordsNodeId, color: '#6366F1' });
          
          // Only show individual records if expanded
          if (expandedSchemas.includes(s.id)) {
            schemaRecords.forEach((r, rIdx) => {
              nodes.push({ ...r, x: currentX + 600, y: currentY + rIdx * verticalSpacing, children: [] });
              links.push({ from: recordsNodeId, to: r.id, color: '#34D399' });
            });
          }
        }
        
        currentY += childHeights[idx];
      });
      
      currentX += 600;
    });

    const maxX = currentX + 200;
    const maxY = Math.max(...nodes.map(n => n.y + 40), 800);
    return { nodes, links, width: Math.max(maxX, 1200), height: Math.max(maxY, 800) };
  }, [schemas, records, assetTypeNames, expandedAssets, expandedSchemas]);

  const toggleAssetExpand = (id: string) => {
    setExpandedAssets((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  // Fetch asset type names
  useEffect(() => {
    const fetchAssetTypes = async () => {
      try {
        const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};
        const response = await fetch('/api/asset-types', { headers });
        if (response.ok) {
          const data = await response.json();
          const names: Record<number, string> = {};
          if (Array.isArray(data)) {
            data.forEach((at: any) => {
              names[at.id] = at.name || `Asset Type ${at.id}`;
            });
          }
          setAssetTypeNames(names);
        }
      } catch (e) {
        console.warn('Failed to fetch asset types:', e);
      }
    };
    if (token) {
      fetchAssetTypes();
    }
  }, [token]);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 3 }}>Analytics</Typography>

      <Grid container spacing={3}>
        {/* Stat cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">Total Records</Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_data_records ?? 0}</Typography>
              <Typography variant="body2" color="text.secondary">Last 7d: {stats?.recent_records_7days ?? 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Schemas</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_schemas ?? 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Asset Types</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_asset_types ?? 0}</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">Users</Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>{stats?.total_users ?? (user ? 1 : 0)}</Typography>
          </CardContent></Card>
        </Grid>

        {/* Timeline */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Data Records Created (Last 30 days)" />
            <CardContent sx={{ height: 300 }}>
              {timeline.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timeline} margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip formatter={(value) => `${value} records`} />
                    <Line type="monotone" dataKey="records" stroke="#6366F1" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* By asset type */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="By Asset Type" />
            <CardContent sx={{ height: 300 }}>
              {byAssetType.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={byAssetType} dataKey="value" nameKey="name" outerRadius={90}>
                      {byAssetType.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value} records`} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Top asset types */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Top Asset Types" />
            <CardContent sx={{ height: 280 }}>
              {topTypes.length === 0 ? (
                <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                  No data yet
                </Box>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topTypes}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip formatter={(value) => `${value} records`} />
                    <Bar dataKey="count" fill="#10B981" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Recent Activity" />
            <CardContent sx={{ maxHeight: 280, overflow: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Change</TableCell>
                    <TableCell>Schema</TableCell>
                    <TableCell>By</TableCell>
                    <TableCell align="right">When</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recent.map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>{r.change_type}</TableCell>
                      <TableCell>{r.schema_id ? `#${r.schema_id} v${r.schema_version ?? ''}` : '-'}</TableCell>
                      <TableCell>{r.changed_by_name ?? r.changed_by ?? '-'}</TableCell>
                      <TableCell align="right">{r.timestamp?.replace('T', ' ').slice(0, 19) ?? '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        {/* Relationship hierarchy - Draggable Tree Diagram */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Relationships: Asset Types → Schemas → Data Records (Drag to Move)" />
            <CardContent sx={{ p: 2, overflowX: 'auto', overflowY: 'auto' }}>
              <Box sx={{ minHeight: 750, position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'flex-start' }}>
                <svg 
                  width={relationGraph.width} 
                  height={relationGraph.height} 
                  style={{ background: theme.palette.mode === 'dark' ? '#0F172A' : '#FFFFFF', cursor: draggingNode ? 'grabbing' : 'grab' }}
                  onMouseMove={(e) => {
                    if (!draggingNode) return;
                    const svg = e.currentTarget;
                    const rect = svg.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    const deltaX = (x - dragOffset.x) - (nodePositions[draggingNode]?.x || 0);
                    const deltaY = (y - dragOffset.y) - (nodePositions[draggingNode]?.y || 0);
                    
                    // Find all children and move them together
                    const draggedNode = relationGraph.nodes.find(n => n.id === draggingNode);
                    const movedNodes: Record<string, { x: number; y: number }> = {};
                    
                    const moveNodeAndChildren = (nodeId: string, dx: number, dy: number) => {
                      const currentPos = nodePositions[nodeId] || relationGraph.nodes.find(n => n.id === nodeId);
                      if (!currentPos) return;
                      
                      movedNodes[nodeId] = {
                        x: (currentPos.x || 0) + dx,
                        y: (currentPos.y || 0) + dy
                      };
                      
                      const node = relationGraph.nodes.find(n => n.id === nodeId);
                      if (node?.children) {
                        node.children.forEach(childId => moveNodeAndChildren(childId, dx, dy));
                      }
                    };
                    
                    moveNodeAndChildren(draggingNode, deltaX, deltaY);
                    setNodePositions(prev => ({ ...prev, ...movedNodes }));
                  }}
                  onMouseUp={() => setDraggingNode(null)}
                  onMouseLeave={() => setDraggingNode(null)}
                >
                  {/* Draw vertical connections */}
                  {relationGraph.links.map((link, idx) => {
                    const fromNode = relationGraph.nodes.find((n) => n.id === link.from);
                    const toNode = relationGraph.nodes.find((n) => n.id === link.to);
                    if (!fromNode || !toNode) return null;

                    const fromPos = nodePositions[fromNode.id] || { x: fromNode.x, y: fromNode.y };
                    const toPos = nodePositions[toNode.id] || { x: toNode.x, y: toNode.y };

                    const fromCenterX = fromPos.x + 90;
                    const fromCenterY = fromPos.y + 20;
                    const toCenterX = toPos.x + 90;
                    const toCenterY = toPos.y;

                    return (
                      <g key={`link-${idx}`} pointerEvents="none">
                        {/* Vertical line down */}
                        <line
                          x1={fromCenterX}
                          y1={fromCenterY}
                          x2={fromCenterX}
                          y2={fromCenterY + 80}
                          stroke={link.color}
                          strokeWidth="1.5"
                          opacity="0.5"
                        />
                        {/* Horizontal line */}
                        <line
                          x1={fromCenterX}
                          y1={fromCenterY + 80}
                          x2={toCenterX}
                          y2={fromCenterY + 80}
                          stroke={link.color}
                          strokeWidth="1.5"
                          opacity="0.5"
                        />
                        {/* Vertical line up to target */}
                        <line
                          x1={toCenterX}
                          y1={fromCenterY + 80}
                          x2={toCenterX}
                          y2={toCenterY}
                          stroke={link.color}
                          strokeWidth="1.5"
                          opacity="0.5"
                        />
                      </g>
                    );
                  })}

                  {/* Draw nodes */}
                  {relationGraph.nodes.map((node) => {
                    const pos = nodePositions[node.id] || { x: node.x, y: node.y };
                    
                    let bgColor = theme.palette.mode === 'dark' ? '#1E293B' : '#F1F5F9';
                    let borderColor = '#6366F1';
                    let textColor = theme.palette.mode === 'dark' ? '#E0E7FF' : '#1E293B';
                    let isClickable = false;

                    if (node.col === 1) {
                      bgColor = theme.palette.mode === 'dark' ? '#1A365D' : '#DBEAFE';
                      borderColor = '#0EA5E9';
                      textColor = theme.palette.mode === 'dark' ? '#E0F2FE' : '#0C4A6E';
                    } else if (node.col === 2) {
                      bgColor = theme.palette.mode === 'dark' ? '#0D3B2C' : '#DCFCE7';
                      borderColor = '#34D399';
                      textColor = theme.palette.mode === 'dark' ? '#D1FAE5' : '#15803D';
                    }
                    
                    // Special styling for records node
                    if (node.isRecordsNode) {
                      bgColor = theme.palette.mode === 'dark' ? '#2D4A2B' : '#E0F2E9';
                      borderColor = '#10B981';
                      textColor = theme.palette.mode === 'dark' ? '#A7E8C9' : '#0B6E4F';
                      isClickable = true;
                    }

                    return (
                      <g 
                        key={node.id}
                        onClick={() => {
                          if (node.isRecordsNode) {
                            setExpandedSchemas((prev) =>
                              prev.includes(node.schemaId)
                                ? prev.filter((x) => x !== node.schemaId)
                                : [...prev, node.schemaId]
                            );
                          }
                        }}
                        onMouseDown={(e) => {
                          if (node.isRecordsNode) {
                            e.stopPropagation();
                            return;
                          }
                          const svg = (e.target as SVGElement).closest('svg');
                          if (!svg) return;
                          const rect = svg.getBoundingClientRect();
                          setDraggingNode(node.id);
                          setDragOffset({
                            x: e.clientX - rect.left - pos.x,
                            y: e.clientY - rect.top - pos.y
                          });
                        }}
                        style={{ cursor: isClickable ? 'pointer' : 'grab' }}
                      >
                        {/* Node box */}
                        <rect
                          x={pos.x}
                          y={pos.y}
                          width="180"
                          height="40"
                          rx="6"
                          fill={bgColor}
                          stroke={borderColor}
                          strokeWidth={draggingNode === node.id ? '3' : isClickable && expandedSchemas.includes(node.schemaId) ? '2.5' : '2'}
                          opacity="0.95"
                          style={{ transition: 'stroke-width 0.1s' }}
                        />
                        {/* Node label */}
                        <text
                          x={pos.x + 10}
                          y={pos.y + 26}
                          fontSize="11"
                          fontWeight="600"
                          fill={textColor}
                          fontFamily="Courier New, monospace"
                          pointerEvents="none"
                        >
                          {node.label.substring(0, 20)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Admin: user activity */}
        {user?.role === 'admin' && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="User Activity (admin)" />
              <CardContent sx={{ height: 280 }}>
                {userActivity.length === 0 ? (
                  <Box sx={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'text.secondary' }}>
                    No data yet
                  </Box>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={userActivity}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="username" />
                      <YAxis allowDecimals={false} />
                      <Tooltip formatter={(value) => `${value} records`} />
                      <Bar dataKey="count" fill="#6366F1" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Dynamic assignment/auto-create explainer */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="How new data records assign/create schemas"
              action={
                <Stack direction="row" spacing={1}>
                  <Button size="small" variant={flowMode === 'assign' ? 'contained' : 'outlined'} onClick={() => setFlowMode('assign')}>Assign Existing</Button>
                  <Button size="small" variant={flowMode === 'auto' ? 'contained' : 'outlined'} onClick={() => setFlowMode('auto')}>Auto-Create</Button>
                </Stack>
              }
            />
            <CardContent>
              {flowMode === 'assign' ? (
                <Stack spacing={1}>
                  <Typography variant="body2">1. User submits data with values (e.g., title, width, height)</Typography>
                  <Typography variant="body2">2. Backend compares incoming keys to existing schemas (overlap score)</Typography>
                  <Typography variant="body2">3. If a best match exists, the record is linked to that schema</Typography>
                  <Typography variant="body2">4. Values are validated and stored against defined fields</Typography>
                </Stack>
              ) : (
                <Stack spacing={1}>
                  <Typography variant="body2">1. No existing schema sufficiently matches the incoming values</Typography>
                  <Typography variant="body2">2. If allowed and asset type is provided, a new schema is created from the values</Typography>
                  <Typography variant="body2">3. The record links to this new schema; fields can be refined later</Typography>
                  <Typography variant="body2">4. This mirrors your current auto-create behavior when submitting data</Typography>
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
