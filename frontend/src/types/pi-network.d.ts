export interface AuthResult {
  accessToken: string;
  user: {
    uid: string;
    username: string;
  };
}

export interface PaymentData {
  amount: number;
  memo: string;
  metadata?: Record<string, unknown>;
}

export interface PaymentCallbacks {
  onReadyForServerApproval: (paymentId: string) => void;
  onReadyForServerCompletion: (paymentId: string, txid: string) => void;
  onCancel: (paymentId: string) => void;
  onError: (error: Error, payment?: unknown) => void;
}

export interface PiSDK {
  init: (config: { version: string; sandbox: boolean }) => void;
  authenticate: (
    scopes: string[],
    onIncompletePaymentFound: () => void
  ) => Promise<AuthResult>;
  createPayment: (
    payment: PaymentData,
    callbacks: PaymentCallbacks
  ) => Promise<unknown>;
}

// Extend the Window interface globally
declare global {
  interface Window {
    Pi: PiSDK;
  }
}

// This is needed to make this a module
export {}; 