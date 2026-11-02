import { create } from 'zustand';
import { uid } from '../utils/id.ts';

export type ToastTone = 'info' | 'success' | 'warning' | 'error';
export interface Toast {
  id: string;
  tone: ToastTone;
  title: string;
  body?: string;
  action?: { label: string; run: () => void };
  /** ms; 0 = permanece até fechar. Erros não somem sozinhos. */
  timeout: number;
}

interface ToastState {
  toasts: Toast[];
  push: (t: Omit<Toast, 'id' | 'timeout'> & { timeout?: number }) => string;
  dismiss: (id: string) => void;
}

export const useToasts = create<ToastState>()((set, get) => ({
  toasts: [],
  push: (t) => {
    const id = uid('toast');
    const timeout = t.timeout ?? (t.tone === 'error' ? 0 : 6000);
    set({ toasts: [...get().toasts.slice(-4), { ...t, id, timeout }] });
    if (timeout > 0) setTimeout(() => get().dismiss(id), timeout);
    return id;
  },
  dismiss: (id) => set({ toasts: get().toasts.filter((x) => x.id !== id) }),
}));

export const toast = (t: Omit<Toast, 'id' | 'timeout'> & { timeout?: number }): string => useToasts.getState().push(t);
