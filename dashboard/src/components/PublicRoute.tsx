import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface Props {
  children: React.ReactNode;
}

export default function PublicRoute({ children }: Props) {
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

  if (user) {
    if (user.role === 'owner') return <Navigate to="/monitor" replace />;
    return <Navigate to="/home" replace />;
  }

  return <>{children}</>;
}
