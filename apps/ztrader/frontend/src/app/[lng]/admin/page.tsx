"use client";

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { initI18n } from '../../i18n/client';
import { useTranslation } from 'react-i18next';
import { Toast } from '../../../components/Toast';

interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  role: string;
  created_at: string;
}

interface RentalContract {
  id: string;
  user_id: string;
  user_email: string | null;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

interface RiskConfig {
  kill_switch_active: boolean;
  max_order_notional: number;
  allowed_symbols: string[];
}

interface SystemHealth {
  status: string;
  db_connected: boolean;
  redis_connected: boolean;
  celery_queue_depth: number;
  broker_latency_ms: Record<string, number>;
}

type TabKey = 'overview' | 'users' | 'contracts' | 'risk';

function Shimmer({ w = '100%', h = '16px' }: { w?: string; h?: string }) {
  return <div className="shimmer" style={{ width: w, height: h }} />;
}

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={`status-dot ${ok ? 'status-dot-up' : 'status-dot-down'}`}
    />
  );
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, { cls: string }> = {
    admin: { cls: 'badge-secondary' },
    operator: { cls: 'badge-primary' },
    user: { cls: 'badge-info' },
  };
  const c = colors[role] ?? colors.user;
  return <span className={`badge ${c.cls}`}>{role}</span>;
}

export default function AdminPage() {
  const pathname = usePathname();
  const lng = pathname?.split('/')[1] || 'en';
  initI18n(lng);
  const { t } = useTranslation('translation');

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const getHeaders = useCallback(
    (extra: HeadersInit = {}) => {
      const token =
        typeof window !== 'undefined'
          ? window.localStorage.getItem('ztrader_admin_token')
          : null;
      return token
        ? { ...extra, Authorization: `Bearer ${token}` }
        : extra;
    },
    [],
  );

  const [tab, setTab] = useState<TabKey>('overview');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [contracts, setContracts] = useState<RentalContract[]>([]);
  const [riskConfig, setRiskConfig] = useState<RiskConfig | null>(null);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState({
    users: true,
    contracts: true,
    risk: true,
    health: true,
  });
  const [toast, setToast] = useState<{
    msg: string;
    type: 'success' | 'error';
  } | null>(null);

  const [editMaxNotional, setEditMaxNotional] = useState(100);
  const [editAllowedSymbols, setEditAllowedSymbols] = useState('');

  const [newUserId, setNewUserId] = useState('');
  const [newEndDate, setNewEndDate] = useState('');

  const headingRef = useRef<HTMLHeadingElement>(null);
  const tabListRef = useRef<HTMLDivElement>(null);
  const tabKeys: TabKey[] = React.useMemo(() => ['overview', 'users', 'contracts', 'risk'], []);

  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const idx = tabKeys.indexOf(tab);
      let next = idx;
      switch (e.key) {
        case 'ArrowRight': next = (idx + 1) % tabKeys.length; break;
        case 'ArrowLeft': next = (idx - 1 + tabKeys.length) % tabKeys.length; break;
        case 'Home': next = 0; break;
        case 'End': next = tabKeys.length - 1; break;
        default: return;
      }
      e.preventDefault();
      if (next !== idx) {
        setTab(tabKeys[next]);
        document.getElementById(`admin-tab-${tabKeys[next]}`)?.focus();
      }
    },
    [tab, tabKeys],
  );

  useEffect(() => {
    if (toast) {
      const el = document.querySelector('[role="alert"].animate-slide-up') as HTMLElement | null;
      el?.focus();
    }
  }, [toast]);

  const showToast = useCallback(
    (msg: string, type: 'success' | 'error') => {
      setToast({ msg, type });
      setTimeout(() => setToast(null), 4000);
    },
    [],
  );

  const fetchUsers = useCallback(async () => {
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/users`, {
        headers: getHeaders(),
      });
      if (r.ok) setUsers(await r.json());
    } catch {
      showToast('Failed to load users — check connection', 'error');
    } finally {
      setLoading((p) => ({ ...p, users: false }));
    }
  }, [backendUrl, getHeaders, showToast]);

  const fetchContracts = useCallback(async () => {
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/contracts`, {
        headers: getHeaders(),
      });
      if (r.ok) setContracts(await r.json());
    } catch {
      showToast('Failed to load contracts — check connection', 'error');
    } finally {
      setLoading((p) => ({ ...p, contracts: false }));
    }
  }, [backendUrl, getHeaders, showToast]);

  const fetchRisk = useCallback(async () => {
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/risk/config`, {
        headers: getHeaders(),
      });
      if (r.ok) {
        const d: RiskConfig = await r.json();
        setRiskConfig(d);
        setEditMaxNotional(d.max_order_notional);
        setEditAllowedSymbols(d.allowed_symbols.join(', '));
      }
    } catch {
      showToast('Failed to load risk config — check connection', 'error');
    } finally {
      setLoading((p) => ({ ...p, risk: false }));
    }
  }, [backendUrl, getHeaders, showToast]);

  const fetchHealth = useCallback(async () => {
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/system/health`, {
        headers: getHeaders(),
      });
      if (r.ok) setHealth(await r.json());
    } catch {
      showToast('Failed to load system health — check connection', 'error');
    } finally {
      setLoading((p) => ({ ...p, health: false }));
    }
  }, [backendUrl, getHeaders, showToast]);

  useEffect(() => {
    headingRef.current?.focus();
    fetchUsers();
    fetchContracts();
    fetchRisk();
    fetchHealth();
    const h = setInterval(fetchHealth, 15000);
    const d = setInterval(() => {
      fetchUsers();
      fetchContracts();
      fetchRisk();
    }, 30000);
    return () => {
      clearInterval(h);
      clearInterval(d);
    };
  }, [fetchUsers, fetchContracts, fetchRisk, fetchHealth]);

  const toggleKillSwitch = async () => {
    if (!riskConfig) return;
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/risk/config`, {
        method: 'PUT',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          ...riskConfig,
          kill_switch_active: !riskConfig.kill_switch_active,
        }),
      });
      if (r.ok) {
        const d = await r.json();
        setRiskConfig(d);
        showToast(
          d.kill_switch_active
            ? t('admin.toast_killswitch_active')
            : t('admin.toast_killswitch_inactive'),
          d.kill_switch_active ? 'error' : 'success',
        );
      } else {
        showToast(
          `Kill switch failed (${r.status})`,
          'error',
        );
      }
    } catch {
      showToast(t('admin.toast_killswitch_failed'), 'error');
    }
  };

  const updateUserRole = async (userId: string, role: string) => {
    try {
      const r = await fetch(
        `${backendUrl}/api/v1/admin/users/${userId}/role`,
        {
          method: 'PUT',
          headers: getHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({ role }),
        },
      );
      if (r.ok) {
        await fetchUsers();
        showToast(`${t('admin.toast_role_updated')} → ${role}`, 'success');
      } else {
        const e = await r.json().catch(() => ({}));
        showToast(e.detail || `Role update failed (${r.status})`, 'error');
      }
    } catch {
      showToast(t('admin.toast_role_failed'), 'error');
    }
  };

  const toggleContract = async (id: string) => {
    try {
      const r = await fetch(
        `${backendUrl}/api/v1/admin/contracts/${id}/toggle`,
        { method: 'PUT', headers: getHeaders() },
      );
      if (r.ok) {
        await fetchContracts();
        showToast(t('admin.toast_contract_toggled'), 'success');
      } else {
        const e = await r.json().catch(() => ({}));
        showToast(e.detail || `Toggle failed (${r.status})`, 'error');
      }
    } catch {
      showToast(t('admin.toast_contract_toggle_failed'), 'error');
    }
  };

  const createContract = async () => {
    if (!newUserId || !newEndDate) {
      showToast(t('admin.toast_fill_fields'), 'error');
      return;
    }
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/contracts`, {
        method: 'POST',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          user_id: newUserId,
          end_date: new Date(newEndDate).toISOString(),
          is_active: true,
        }),
      });
      if (r.ok) {
        await fetchContracts();
        setNewUserId('');
        setNewEndDate('');
        showToast(t('admin.toast_contract_created'), 'success');
      } else {
        const e = await r.json();
        showToast(
          e.detail || t('admin.toast_contract_create_failed'),
          'error',
        );
      }
    } catch {
      showToast(t('admin.toast_contract_create_failed'), 'error');
    }
  };

  const saveRisk = async () => {
    if (!riskConfig) return;
    try {
      const r = await fetch(`${backendUrl}/api/v1/admin/risk/config`, {
        method: 'PUT',
        headers: getHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          kill_switch_active: riskConfig.kill_switch_active,
          max_order_notional: editMaxNotional,
          allowed_symbols: editAllowedSymbols
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      });
      if (r.ok) {
        setRiskConfig(await r.json());
        showToast(t('admin.toast_risk_saved'), 'success');
      } else {
        const e = await r.json().catch(() => ({}));
        showToast(e.detail || `Risk save failed (${r.status})`, 'error');
      }
    } catch {
      showToast(t('admin.toast_risk_save_failed'), 'error');
    }
  };

  const latColor = (ms: number) =>
    ms < 50
      ? 'var(--color-accent)'
      : ms <= 100
        ? 'var(--color-warning)'
        : 'var(--color-danger)';

  const killActive = riskConfig?.kill_switch_active ?? false;

  const tabs: { key: TabKey; label: string; icon: React.ReactNode }[] = [
    {
      key: 'overview',
      label: t('admin.system_health'),
      icon: (
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      key: 'users',
      label: t('admin.users_title'),
      icon: (
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
    },
    {
      key: 'contracts',
      label: t('admin.contracts_title'),
      icon: (
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
      ),
    },
    {
      key: 'risk',
      label: t('risk.limits'),
      icon: (
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '28px 24px' }}>
      <style>{`
        @keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
        @keyframes killPulse { 0%,100%{box-shadow:0 0 24px rgba(239,68,68,0.35)} 50%{box-shadow:0 0 48px rgba(239,68,68,0.65)} }
        @keyframes safePulse { 0%,100%{box-shadow:0 0 16px rgba(16,185,129,0.15)} 50%{box-shadow:0 0 28px rgba(16,185,129,0.3)} }
        .admin-tab { display:flex;align-items:center;gap:7px;padding:9px 16px;border-radius:10px;font-size:14px;font-weight:500;color:var(--text-muted);background:transparent;border:1px solid transparent;cursor:pointer;transition:var(--transition-fast);white-space:nowrap; }
        .admin-tab:hover { color:var(--text-secondary);background:var(--bg-surface); }
        .admin-tab.active { color:var(--color-primary-light);background:var(--color-primary-bg);border-color:var(--color-primary-border);font-weight:600; }
        .admin-card { background:var(--bg-card);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid var(--border-card);border-radius:var(--radius-xl);padding:28px;box-shadow:var(--shadow-lg);transition:var(--transition-smooth); }
        .admin-input { width:100%;padding:10px 14px;background:var(--bg-surface);border:1px solid var(--border-input);border-radius:var(--radius-md);color:var(--text-primary);font-size:14px;outline:none;transition:var(--transition-smooth); }
        .admin-input:focus { border-color:var(--color-primary);box-shadow:0 0 0 3px var(--color-primary-glow-soft); }
        .admin-select { padding:6px 12px;background:var(--bg-surface);border:1px solid var(--border-input);border-radius:var(--radius-md);color:var(--text-primary);font-size:13px;outline:none;cursor:pointer;transition:var(--transition-fast); }
        .admin-select:focus { border-color:var(--color-primary); }
        .admin-th { padding:11px 16px;text-align:left;color:var(--text-muted);font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;border-bottom:1px solid var(--border-subtle); }
        .admin-td { padding:12px 16px;color:var(--text-primary);font-size:14px;border-bottom:1px solid rgba(255,255,255,0.025); }
        .admin-tr:hover td { background:rgba(255,255,255,0.015); }
        .stat-card { background:rgba(255,255,255,0.03);border:1px solid var(--border-subtle);border-radius:var(--radius-lg);padding:18px 20px;display:flex;flex-direction:column;gap:4px; }
        .latency-row { display:flex;align-items:center;justify-content:space-between;padding:9px 14px;border-radius:var(--radius-md);background:var(--bg-surface);border:1px solid var(--border-subtle);font-size:13px; }
        @media(max-width:768px){
          .admin-tabs-row { overflow-x:auto; }
          .admin-stats-row { grid-template-columns:1fr 1fr !important; }
          .admin-two-col { grid-template-columns:1fr !important; }
          .admin-three-col { grid-template-columns:1fr !important; }
        }
        @media(max-width:440px){
          .admin-stats-row { grid-template-columns:1fr 1fr !important; }
          .stat-card { padding:14px 12px; }
        }
        @media(max-width:360px){
          .admin-stats-row { grid-template-columns:1fr !important; }
        }
      `}</style>

      {/* ── Page Header ── */}
      <div
        style={{
          marginBottom: '28px',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div className="animate-fade-in">
          <h1
            ref={headingRef}
            tabIndex={-1}
            className="h1"
            style={{ display: 'flex', alignItems: 'center', gap: '10px' }}
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--color-primary)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            {t('admin.title')}
          </h1>
          <p
            className="text-muted"
            style={{ fontSize: '13px', marginTop: '4px' }}
          >
            {new Date().toLocaleString(lng)}
          </p>
        </div>

        <button
          onClick={toggleKillSwitch}
          className="animate-fade-in"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 20px',
            borderRadius: 'var(--radius-lg)',
            cursor: 'pointer',
            fontWeight: '700',
            fontSize: '13px',
            outline: 'none',
            letterSpacing: '0.04em',
            background: killActive
              ? 'rgba(239,68,68,0.15)'
              : 'rgba(16,185,129,0.1)',
            color: killActive ? 'var(--color-danger)' : 'var(--color-accent)',
            animation: killActive ? 'killPulse 2s infinite' : 'safePulse 3s infinite',
            border: `1px solid ${killActive ? 'rgba(239,68,68,0.35)' : 'rgba(16,185,129,0.25)'}`,
          }}
        >
          <StatusDot ok={!killActive} />
          {killActive ? t('admin.kill_active') : t('admin.kill_inactive')}
          <span
            style={{
              display: 'inline-flex',
              width: '40px',
              height: '22px',
              borderRadius: '11px',
              background: killActive
                ? 'var(--color-danger)'
                : 'var(--color-accent)',
              position: 'relative',
              flexShrink: 0,
              transition: 'background 0.3s',
            }}
          >
            <span
              style={{
                position: 'absolute',
                top: '3px',
                left: killActive ? '21px' : '3px',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: '#fff',
                transition: 'left 0.3s cubic-bezier(0.4,0,0.2,1)',
                boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
              }}
            />
          </span>
        </button>
      </div>

      <div
        className="admin-stats-row animate-fade-in"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '14px',
          marginBottom: '24px',
        }}
      >
        <div className="stat-card">
          <div
            style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
            }}
          >
            {t('admin.users_title')}
          </div>
          <div className="metric-value" style={{ fontSize: '28px' }}>
            {loading.users ? '–' : users.length}
          </div>
          <div className="text-muted" style={{ fontSize: '12px' }}>
            {users.filter((u) => u.role === 'admin').length} admin ·{' '}
            {users.filter((u) => u.role === 'operator').length} operator
          </div>
        </div>
        <div className="stat-card">
          <div
            style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
            }}
          >
            {t('admin.contracts_title')}
          </div>
          <div className="metric-value" style={{ fontSize: '28px' }}>
            {loading.contracts ? '–' : contracts.length}
          </div>
          <div className="text-muted" style={{ fontSize: '12px' }}>
            {contracts.filter((c) => c.is_active).length} active
          </div>
        </div>
        <div className="stat-card">
          <div
            style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
            }}
          >
            DB / Redis
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '4px',
            }}
          >
            <StatusDot ok={health?.db_connected ?? false} />
            <span
              style={{
                fontSize: '13px',
                color: health?.db_connected
                  ? 'var(--color-accent)'
                  : 'var(--color-danger)',
                fontWeight: '600',
              }}
            >
              DB
            </span>
            <StatusDot ok={health?.redis_connected ?? false} />
            <span
              style={{
                fontSize: '13px',
                color: health?.redis_connected
                  ? 'var(--color-accent)'
                  : 'var(--color-danger)',
                fontWeight: '600',
              }}
            >
              Redis
            </span>
          </div>
          <div className="text-muted" style={{ fontSize: '12px', marginTop: '4px' }}>
            Queue: {health?.celery_queue_depth ?? '–'} tasks
          </div>
        </div>
        <div
          className="stat-card"
          style={{
            borderColor: killActive
              ? 'rgba(239,68,68,0.3)'
              : 'rgba(16,185,129,0.2)',
            background: killActive
              ? 'rgba(239,68,68,0.06)'
              : 'rgba(16,185,129,0.05)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: '700',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.07em',
            }}
          >
            {t('risk.killswitch')}
          </div>
          <div
            style={{
              fontSize: '16px',
              fontWeight: '700',
              color: killActive
                ? 'var(--color-danger)'
                : 'var(--color-accent)',
              marginTop: '4px',
            }}
          >
            {killActive ? 'ACTIVE' : 'SAFE'}
          </div>
          <div className="text-muted" style={{ fontSize: '12px' }}>
            Max: ${riskConfig?.max_order_notional ?? '–'} USDT
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div
        className="admin-tabs-row"
        role="tablist"
        aria-orientation="horizontal"
        onKeyDown={handleTabKeyDown}
        ref={tabListRef}
        style={{ display: 'flex', gap: '4px', marginBottom: '20px' }}
      >
        {tabs.map((tb) => (
          <button
            key={tb.key}
            role="tab"
            id={`admin-tab-${tb.key}`}
            aria-selected={tab === tb.key}
            aria-controls={`admin-panel-${tb.key}`}
            tabIndex={tab === tb.key ? 0 : -1}
            className={`admin-tab${tab === tb.key ? ' active' : ''}`}
            onClick={() => setTab(tb.key)}
          >
            {tb.icon}
            {tb.label}
            {tb.key === 'users' && !loading.users && (
              <span
                style={{
                  marginLeft: '2px',
                  padding: '1px 7px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: '700',
                  background: 'rgba(255,255,255,0.07)',
                  color: 'var(--text-muted)',
                }}
              >
                {users.length}
              </span>
            )}
            {tb.key === 'contracts' && !loading.contracts && (
              <span
                style={{
                  marginLeft: '2px',
                  padding: '1px 7px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: '700',
                  background: 'rgba(255,255,255,0.07)',
                  color: 'var(--text-muted)',
                }}
              >
                {contracts.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {tab === 'overview' && (
        <div
          role="tabpanel"
          id="admin-panel-overview"
          aria-labelledby="admin-tab-overview"
          className="animate-fade-in"
        >
          {loading.health ? (
            <div
              className="admin-card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <Shimmer h="60px" /> <Shimmer h="60px" />{' '}
              <Shimmer h="60px" />
            </div>
          ) : health ? (
            <div
              className="layout-2col animate-fade-in"
              style={{ gap: '20px' }}
            >
              <div className="admin-card">
                <h3
                  className="h4"
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--color-primary)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                    <line x1="8" y1="21" x2="16" y2="21" />
                    <line x1="12" y1="17" x2="12" y2="21" />
                  </svg>
                  {t('admin.services')}
                </h3>
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                  }}
                >
                  <div
                    className="health-chip"
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      fontSize: '13px',
                      fontWeight: '500',
                      background: health.db_connected
                        ? 'rgba(16,185,129,0.08)'
                        : 'rgba(239,68,68,0.08)',
                      border: `1px solid ${health.db_connected ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                    }}
                  >
                    <StatusDot ok={health.db_connected} />
                    <span
                      style={{ color: 'var(--text-secondary)', flex: 1 }}
                    >
                      {t('admin.db_status')}
                    </span>
                    <span
                      style={{
                        color: health.db_connected
                          ? 'var(--color-accent)'
                          : 'var(--color-danger)',
                        fontWeight: '600',
                      }}
                    >
                      {health.db_connected
                        ? t('admin.connected')
                        : t('admin.disconnected')}
                    </span>
                  </div>
                  <div
                    className="health-chip"
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      fontSize: '13px',
                      fontWeight: '500',
                      background: health.redis_connected
                        ? 'rgba(16,185,129,0.08)'
                        : 'rgba(239,68,68,0.08)',
                      border: `1px solid ${health.redis_connected ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                    }}
                  >
                    <StatusDot ok={health.redis_connected} />
                    <span
                      style={{ color: 'var(--text-secondary)', flex: 1 }}
                    >
                      {t('admin.redis_status')}
                    </span>
                    <span
                      style={{
                        color: health.redis_connected
                          ? 'var(--color-accent)'
                          : 'var(--color-danger)',
                        fontWeight: '600',
                      }}
                    >
                      {health.redis_connected
                        ? t('admin.connected')
                        : t('admin.disconnected')}
                    </span>
                  </div>
                  <div
                    className="health-chip"
                    style={{
                      padding: '12px 16px',
                      borderRadius: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      fontSize: '13px',
                      fontWeight: '500',
                      background: 'var(--color-primary-bg)',
                      border: '1px solid var(--color-primary-border)',
                    }}
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="var(--color-primary-light)"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M3 12h18M3 6h18M3 18h18" />
                    </svg>
                    <span
                      style={{ color: 'var(--text-secondary)', flex: 1 }}
                    >
                      {t('admin.celery_queue')}
                    </span>
                    <span
                      style={{
                        color: 'var(--color-primary-light)',
                        fontWeight: '700',
                      }}
                    >
                      {health.celery_queue_depth}
                    </span>
                  </div>
                </div>
              </div>

              <div className="admin-card">
                <h3
                  className="h4"
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--color-secondary)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                  </svg>
                  {t('admin.broker_latency')}
                </h3>
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  {Object.entries(health.broker_latency_ms).map(
                    ([ex, ms]) => (
                      <div key={ex} className="latency-row">
                        <span
                          style={{
                            color: 'var(--text-secondary)',
                            fontWeight: '500',
                          }}
                        >
                          {ex}
                        </span>
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '10px',
                          }}
                        >
                          <div
                            style={{
                              width: '60px',
                              height: '4px',
                              borderRadius: '2px',
                              background: 'rgba(255,255,255,0.06)',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                height: '100%',
                                borderRadius: '2px',
                                width: `${Math.min(100, (ms / 200) * 100)}%`,
                                background: latColor(ms),
                                transition: 'width 0.5s',
                              }}
                            />
                          </div>
                          <span
                            style={{
                              color: latColor(ms),
                              fontWeight: '700',
                              fontVariantNumeric: 'tabular-nums',
                              minWidth: '48px',
                              textAlign: 'right',
                            }}
                          >
                            {ms}ms
                          </span>
                        </div>
                      </div>
                    ),
                  )}
                  {Object.keys(health.broker_latency_ms).length === 0 && (
                    <div
                      className="text-muted"
                      style={{ fontSize: '13px', padding: '12px 0' }}
                    >
                      {t('admin.no_broker_data')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div
              className="admin-card"
              style={{
                color: 'var(--text-muted)',
                textAlign: 'center',
                padding: '48px',
              }}
            >
              {t('admin.error')}
            </div>
          )}
        </div>
      )}

      {/* ── USERS ── */}
      {tab === 'users' && (
        <div
          role="tabpanel"
          id="admin-panel-users"
          aria-labelledby="admin-tab-users"
          className="admin-card animate-fade-in"
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '20px',
            }}
          >
            <h3
              className="h4"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-primary)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              {t('admin.users_title')}
            </h3>
            <button
              className="btn-base btn-ghost btn-sm"
              onClick={() => fetchUsers()}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              {t('admin.refresh')}
            </button>
          </div>

          {loading.users ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <Shimmer h="44px" />
              <Shimmer h="44px" />
              <Shimmer h="44px" />
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="table-base">
                <caption className="visually-hidden">{t('admin.users_title')}</caption>
                <thead>
                  <tr>
                    <th scope="col" className="admin-th">{t('admin.email')}</th>
                    <th scope="col" className="admin-th">{t('admin.name')}</th>
                    <th scope="col" className="admin-th">{t('admin.role')}</th>
                    <th scope="col" className="admin-th">{t('admin.created')}</th>
                    <th scope="col" className="admin-th">{t('admin.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                    {users.map((u) => (
                    <tr key={u.id} className="admin-tr">
                      <td className="admin-td" data-label={t('admin.email')}>
                        <span
                          style={{
                            color: 'var(--color-primary-light)',
                            fontWeight: '500',
                          }}
                        >
                          {u.email}
                        </span>
                      </td>
                      <td
                        className="admin-td"
                        style={{ color: 'var(--text-secondary)' }}
                        data-label={t('admin.name')}
                      >
                        {u.name || '—'}
                      </td>
                      <td className="admin-td" data-label={t('admin.role')}>
                        <RoleBadge role={u.role} />
                      </td>
                      <td
                        className="admin-td"
                        style={{ color: 'var(--text-muted)', fontSize: '13px' }}
                        data-label={t('admin.created')}
                      >
                        {new Date(u.created_at).toLocaleDateString(lng)}
                      </td>
                      <td className="admin-td" data-label={t('admin.actions')}>
                        <select
                          className="admin-select"
                          value={u.role}
                          onChange={(e) => updateUserRole(u.id, e.target.value)}
                        >
                          <option value="user">{t('admin.role_user')}</option>
                          <option value="operator">{t('admin.role_operator')}</option>
                          <option value="admin">{t('admin.role_admin')}</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="admin-td"
                        style={{
                          textAlign: 'center',
                          color: 'var(--text-muted)',
                          padding: '40px',
                        }}
                      >
                        {t('admin.no_users_found')}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── CONTRACTS ── */}
      {tab === 'contracts' && (
        <div
          role="tabpanel"
          id="admin-panel-contracts"
          aria-labelledby="admin-tab-contracts"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            animation: 'fadeIn 0.25s ease',
          }}
        >
          <div className="admin-card">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: '20px',
              }}
            >
              <h3
                className="h4"
                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="var(--color-primary)"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                {t('admin.contracts_title')}
              </h3>
              <button
                className="btn-base btn-ghost btn-sm"
                onClick={() => fetchContracts()}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
                {t('admin.refresh')}
              </button>
            </div>

            {loading.contracts ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <Shimmer h="44px" />
                <Shimmer h="44px" />
              </div>
            ) : (
              <div className="table-wrapper">
                <table className="table-base">
                  <caption className="visually-hidden">{t('admin.contracts_title')}</caption>
                  <thead>
                    <tr>
                      <th scope="col" className="admin-th">
                        {t('admin.contract_user')}
                      </th>
                      <th scope="col" className="admin-th">
                        {t('admin.contract_start')}
                      </th>
                      <th scope="col" className="admin-th">
                        {t('admin.contract_end')}
                      </th>
                      <th scope="col" className="admin-th">
                        {t('admin.contract_status')}
                      </th>
                      <th scope="col" className="admin-th">{t('admin.actions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contracts.map((c) => (
                      <tr key={c.id} className="admin-tr">
                        <td className="admin-td" data-label={t('admin.contract_user')}>
                          <span
                            style={{
                              color: 'var(--color-primary-light)',
                              fontWeight: '500',
                            }}
                          >
                            {c.user_email ||
                              c.user_id.slice(0, 8) + '...'}
                          </span>
                        </td>
                        <td
                          className="admin-td"
                          style={{
                            color: 'var(--text-secondary)',
                            fontSize: '13px',
                          }}
                          data-label={t('admin.contract_start')}
                        >
                          {new Date(c.start_date).toLocaleDateString(lng)}
                        </td>
                        <td
                          className="admin-td"
                          style={{
                            color: 'var(--text-secondary)',
                            fontSize: '13px',
                          }}
                          data-label={t('admin.contract_end')}
                        >
                          {new Date(c.end_date).toLocaleDateString(lng)}
                        </td>
                        <td className="admin-td" data-label={t('admin.contract_status')}>
                          <span
                            className={`badge ${c.is_active ? 'badge-accent' : 'badge-danger'}`}
                          >
                            {c.is_active
                              ? t('admin.contract_active')
                              : t('admin.contract_inactive')}
                          </span>
                        </td>
                        <td className="admin-td" data-label={t('admin.actions')}>
                          <button
                            className="btn-base btn-danger btn-sm"
                            onClick={() => toggleContract(c.id)}
                          >
                            {t('admin.contract_toggle')}
                          </button>
                        </td>
                      </tr>
                    ))}
                    {contracts.length === 0 && (
                      <tr>
                        <td
                          colSpan={5}
                          className="admin-td"
                          style={{
                            textAlign: 'center',
                            color: 'var(--text-muted)',
                            padding: '40px',
                          }}
                        >
                          {t('admin.no_contracts_found')}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div
            className="admin-card"
            style={{ borderColor: 'var(--color-primary-border)' }}
          >
            <h3
              className="h4"
              style={{
                color: 'var(--text-secondary)',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '7px',
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              {t('admin.contract_create')}
            </h3>
            <form
              onSubmit={(e) => { e.preventDefault(); createContract(); }}
              className="admin-three-col"
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr auto',
                gap: '12px',
                alignItems: 'end',
              }}
            >
              <div>
                <label
                  className="form-label"
                  style={{ fontSize: '12px', color: 'var(--text-muted)' }}
                >
                  {t('admin.user_id')}
                </label>
                <input
                  className="admin-input"
                  type="text"
                  value={newUserId}
                  onChange={(e) => setNewUserId(e.target.value)}
                  placeholder="UUID"
                />
              </div>
              <div>
                <label
                  className="form-label"
                  style={{ fontSize: '12px', color: 'var(--text-muted)' }}
                >
                  {t('admin.contract_end')}
                </label>
                <input
                  className="admin-input"
                  type="date"
                  value={newEndDate}
                  onChange={(e) => setNewEndDate(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="btn-base btn-primary"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                {t('admin.contract_create')}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ── RISK ── */}
      {tab === 'risk' && (
        <div
          role="tabpanel"
          id="admin-panel-risk"
          aria-labelledby="admin-tab-risk"
          className="layout-2col animate-fade-in"
          style={{ gap: '20px' }}
        >
          <div className="admin-card">
            <h3
              className="h4"
              style={{
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="var(--color-warning)"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
              {t('risk.limits')}
            </h3>

            {loading.risk ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                }}
              >
                <Shimmer h="44px" />
                <Shimmer h="44px" />
                <Shimmer w="140px" h="40px" />
              </div>
            ) : (
              <form onSubmit={(e) => { e.preventDefault(); saveRisk(); }}>
                <div className="form-group">
                  <label className="form-label">
                    {t('risk.max_notional')} (USDT)
                  </label>
                  <input
                    className="admin-input font-mono"
                    type="number"
                    value={editMaxNotional}
                    onChange={(e) =>
                      setEditMaxNotional(parseFloat(e.target.value) || 0)
                    }
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">
                    {t('risk.allowed_symbols')}
                  </label>
                  <input
                    className="admin-input"
                    type="text"
                    value={editAllowedSymbols}
                    onChange={(e) => setEditAllowedSymbols(e.target.value)}
                    placeholder="BTC/USDT, ETH/USDT"
                  />
                  <p
                    className="text-muted"
                    style={{ fontSize: '11px', marginTop: '6px' }}
                  >
                    {t('admin.comma_separated')}
                  </p>
                </div>
                <button
                  type="submit"
                  className="btn-base btn-primary"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  {t('admin.save_risk')}
                </button>
              </form>
            )}
          </div>

          <div
            className="admin-card"
            style={{
              borderColor: killActive
                ? 'rgba(239,68,68,0.25)'
                : 'rgba(16,185,129,0.15)',
            }}
          >
            <h3
              className="h4"
              style={{
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke={
                  killActive
                    ? 'var(--color-danger)'
                    : 'var(--color-accent)'
                }
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              {t('risk.killswitch')}
            </h3>

            {riskConfig ? (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '14px',
                }}
              >
                <div
                  style={{
                    padding: '20px',
                    borderRadius: 'var(--radius-lg)',
                    textAlign: 'center',
                    background: killActive
                      ? 'rgba(239,68,68,0.08)'
                      : 'rgba(16,185,129,0.06)',
                    border: `1px solid ${killActive ? 'rgba(239,68,68,0.25)' : 'rgba(16,185,129,0.2)'}`,
                  }}
                >
                  <span
                    className={`status-dot ${killActive ? 'status-dot-down' : 'status-dot-up'}`}
                    style={{
                      width: '32px',
                      height: '32px',
                      marginBottom: '8px',
                    }}
                  />
                  <div
                    style={{
                      fontSize: '16px',
                      fontWeight: '800',
                      color: killActive
                        ? 'var(--color-danger)'
                        : 'var(--color-accent)',
                      letterSpacing: '0.05em',
                    }}
                  >
                    {killActive
                      ? t('admin.kill_active')
                      : t('admin.kill_inactive')}
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                  }}
                >
                  <div className="latency-row">
                    <span
                      className="text-secondary"
                      style={{ fontSize: '13px' }}
                    >
                      {t('risk.max_notional')}
                    </span>
                    <span
                      className="font-mono"
                      style={{ fontWeight: '600', fontSize: '13px' }}
                    >
                      ${riskConfig.max_order_notional} USDT
                    </span>
                  </div>
                  <div
                    style={{
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: 'rgba(255,255,255,0.03)',
                    }}
                  >
                    <div
                      className="text-muted"
                      style={{ fontSize: '12px', marginBottom: '6px' }}
                    >
                      {t('risk.allowed_symbols')}
                    </div>
                    <div
                      style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '6px',
                      }}
                    >
                      {riskConfig.allowed_symbols.map((s) => (
                        <span key={s} className="badge badge-primary">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={toggleKillSwitch}
                  className={`btn-base ${killActive ? 'btn-accent' : 'btn-danger'} btn-full`}
                  style={{ justifyContent: 'center' }}
                >
                  {killActive
                    ? t('admin.deactivate_killswitch')
                    : t('admin.activate_killswitch')}
                </button>
              </div>
            ) : (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <Shimmer h="100px" />
                <Shimmer h="44px" />
              </div>
            )}
          </div>
        </div>
      )}

      {toast && <Toast msg={toast.msg} type={toast.type} />}
    </div>
  );
}
