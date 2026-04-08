import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface Props {
  children: React.ReactNode;
  role?: 'owner' | 'mentee' | 'any';
}

export default function ProtectedRoute({ children, role = 'any' }: Props) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--bg)',
        color: 'var(--text-2)',
        fontFamily: 'var(--mono)',
        fontSize: '12px',
        letterSpacing: '1px',
      }}>
        LOADING...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (role === 'owner' && user.role !== 'owner') {
    return <Navigate to="/home" replace />;
  }

  if (role === 'mentee' && user.role !== 'mentee' && user.role !== 'trial') {
    return <Navigate to="/monitor" replace />;
  }

  return <>{children}</>;
}
