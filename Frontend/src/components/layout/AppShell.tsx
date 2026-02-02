import { Box, Toolbar } from '@mui/material';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Header />
      <Sidebar />
      <Box component="main" sx={{ flex: 1, overflow: 'auto', width: '100%' }}>
        <Toolbar />
        <Box sx={{ width: '100%', p: 2 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};
