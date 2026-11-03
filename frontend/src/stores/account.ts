import { create } from 'zustand';
import { currentUser, type UserInfo } from '../services/api/auth.ts';
import { ApiError } from '../services/api/http.ts';

/**
 * Estado da conta: 'unknown' até a primeira consulta; 'unavailable' quando o servidor não tem
 * contas (sem banco → 503) ou está fora do ar. A identidade NUNCA é guardada no navegador.
 */
export type AccountStatus = 'unknown' | 'anonymous' | 'signed-in' | 'unavailable';

export interface AccountState {
  status: AccountStatus;
  user: UserInfo | null;
  set: (patch: Partial<Omit<AccountState, 'set'>>) => void;
}

export const useAccount = create<AccountState>()((set) => ({
  status: 'unknown',
  user: null,
  set: (patch) => set(patch),
}));

export async function refreshAccount(available: boolean): Promise<void> {
  if (!available) { useAccount.getState().set({ status: 'unavailable', user: null }); return; }
  try {
    const user = await currentUser();
    useAccount.getState().set({ status: user ? 'signed-in' : 'anonymous', user });
  } catch (err) {
    useAccount.getState().set({ status: err instanceof ApiError && err.status === 503 ? 'unavailable' : 'anonymous', user: null });
  }
}
