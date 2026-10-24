import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getMe, signOut as apiSignOut, type User } from "./api";

export interface AuthValue {
  /** "loading" until we've asked the server who is signed in. */
  status: "loading" | "ready";
  user: User | null;
  /** False when the server has no GitHub app set up, so there is nothing to sign in to. */
  signInAvailable: boolean;
  /** False when the server has no Gemini key, so the chat panel isn't offered. */
  chatAvailable: boolean;
  /** Ask the server again, for example after it says the sign-in has ended. */
  refresh: () => Promise<void>;
  signOut: () => Promise<void>;
}

/** Without a provider (in tests, say) nobody is signed in and neither sign-in nor chat is offered. */
export const AuthContext = createContext<AuthValue>({
  status: "ready",
  user: null,
  signInAvailable: false,
  chatAvailable: false,
  refresh: async () => {},
  signOut: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ status: "loading" | "ready"; user: User | null; signInAvailable: boolean; chatAvailable: boolean }>({
    status: "loading",
    user: null,
    signInAvailable: false,
    chatAvailable: false,
  });

  const refresh = useCallback(async () => {
    try {
      const me = await getMe();
      setState({ status: "ready", user: me.user, signInAvailable: me.sign_in_available, chatAvailable: me.chat_available === true });
    } catch {
      // If we can't tell, behave as signed out. The pages explain when the server can't be reached.
      setState({ status: "ready", user: null, signInAvailable: false, chatAvailable: false });
    }
  }, []);

  const signOut = useCallback(async () => {
    await apiSignOut();
    await refresh();
  }, [refresh]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo(() => ({ ...state, refresh, signOut }), [state, refresh, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
