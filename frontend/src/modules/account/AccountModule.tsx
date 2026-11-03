/**
 * Conta (#/conta): entrar, criar conta, sair (desta sessão ou de todas) e histórico pessoal de
 * cálculos. Toda regra (senha, bloqueio, expiração) é do servidor; aqui só se exibe a resposta.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { useI18n } from '../../i18n/index.ts';
import { useAccount } from '../../stores/account.ts';
import { history, login, logout, register, type HistoryPage } from '../../services/api/auth.ts';
import { ApiError } from '../../services/api/http.ts';
import { Button } from '../../design-system/primitives/Button.tsx';
import { TextInput, Segmented } from '../../design-system/primitives/Field.tsx';
import { Badge, Spinner } from '../../design-system/primitives/misc.tsx';
import { Panel } from '../../design-system/layout/Panel.tsx';
import { Workbench } from '../../design-system/layout/AppShell.tsx';
import { toast } from '../../stores/toast.ts';

const message = (err: unknown): string => (err instanceof Error ? err.message : String(err));

function SignIn() {
  const { t } = useI18n();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === 'register') await register(nome, email, senha);
      const user = await login(email, senha);
      setSenha('');
      useAccount.getState().set({ status: 'signed-in', user });
      toast({ tone: 'success', title: t('account.welcome', { name: user.nome }) });
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel title={mode === 'login' ? t('account.signIn') : t('account.createAccount')} headingLevel={2} testId="account-form">
      <Segmented name="account-mode" label={t('account.mode')} hideLabel value={mode} onChange={(v) => { setMode(v); setError(null); }}
        options={[{ value: 'login', label: t('account.signIn') }, { value: 'register', label: t('account.createAccount') }]} />
      <form className="ds-stack" onSubmit={(e) => void submit(e)} noValidate={false}>
        {mode === 'register' ? <TextInput label={t('account.name')} value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name" required minLength={2} maxLength={120} /> : null}
        <TextInput label={t('account.email')} type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required maxLength={254} />
        <TextInput label={t('account.password')} type="password" value={senha} onChange={(e) => setSenha(e.target.value)}
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required maxLength={256}
          hint={mode === 'register' ? t('account.passwordHint') : undefined} error={error ?? undefined} />
        <Button type="submit" variant="primary" disabled={busy} data-testid="account-submit">{busy ? <Spinner size={14} /> : null}{mode === 'login' ? t('account.signIn') : t('account.createAccount')}</Button>
      </form>
      <p className="ds-field__hint">{t('account.privacy')}</p>
    </Panel>
  );
}

function History() {
  const { t } = useI18n();
  const [page, setPage] = useState<HistoryPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const ctrl = new AbortController();
    history(1, ctrl.signal).then(setPage).catch((err: unknown) => { if (!(err instanceof ApiError && err.kind === 'aborted')) setError(message(err)); });
    return () => ctrl.abort();
  }, []);
  return (
    <Panel title={t('account.history')} aside={page ? t('account.historyTotal', { n: page.total }) : undefined} headingLevel={2} testId="account-history">
      {error ? <p role="alert">{error}</p> : !page ? <Spinner size={18} label={t('common.loading')} /> : page.itens.length === 0 ? <p className="empty-state">{t('account.historyEmpty')}</p> : (
        <div className="ds-table-wrap"><table className="ds-table">
          <thead><tr><th scope="col">{t('account.when')}</th><th scope="col">{t('account.operation')}</th><th scope="col">{t('account.parameters')}</th><th scope="col">{t('account.provenance')}</th></tr></thead>
          <tbody>{page.itens.map((i) => (
            <tr key={i.id}><td>{new Date(i.criado_em).toLocaleString()}</td><th scope="row">{i.operacao}</th><td><code>{JSON.stringify(i.parametros)}</code></td><td><Badge tone={i.classe === 'analitico' ? 'success' : 'info'}>{i.classe}</Badge> {i.motor} {i.versao_motor}</td></tr>
          ))}</tbody>
        </table></div>
      )}
    </Panel>
  );
}

export default function AccountModule() {
  const { t } = useI18n();
  const status = useAccount((s) => s.status);
  const user = useAccount((s) => s.user);

  async function signOut(all: boolean) {
    try {
      const n = await logout(all);
      useAccount.getState().set({ status: 'anonymous', user: null });
      toast({ tone: 'info', title: all ? t('account.signedOutAll', { n }) : t('account.signedOut') });
    } catch (err) {
      toast({ tone: 'error', title: message(err) });
    }
  }

  return (
    <Workbench center={
      <main id="main-content" tabIndex={-1} className="module-main" data-testid="account">
        <header className="module-head"><h1>{t('nav.account')}</h1><p className="module-head__lead">{t('account.lead')}</p></header>
        {status === 'unknown' ? <Spinner size={20} label={t('common.loading')} /> : null}
        {status === 'unavailable' ? <p className="empty-state" data-testid="account-unavailable">{t('account.unavailable')}</p> : null}
        {status === 'anonymous' ? <SignIn /> : null}
        {status === 'signed-in' && user ? (
          <>
            <Panel title={user.nome} aside={user.email} headingLevel={2} testId="account-user">
              <div className="ds-row">
                <Button onClick={() => void signOut(false)} data-testid="account-logout">{t('account.signOut')}</Button>
                <Button variant="ghost" onClick={() => void signOut(true)}>{t('account.signOutAll')}</Button>
              </div>
            </Panel>
            <History />
          </>
        ) : null}
      </main>
    } />
  );
}
