import type { AuthResult, PaymentData } from '../types/pi-network';

class PiNetwork {

  static async authenticate(): Promise<AuthResult> {
    try {
      const scopes = ['payments', 'username'];
      const auth = await window.Pi.authenticate(scopes, () => {});
      return auth;
    } catch (error) {
      console.error('Pi Network authentication error:', error);
      throw error;
    }
  }

  static async createPayment(paymentData: PaymentData) {
    try {
      const payment = await window.Pi.createPayment({
        amount: paymentData.amount,
        memo: paymentData.memo,
        metadata: { orderType: 'prediction', ...paymentData.metadata }
      }, {
        onReadyForServerApproval: function(paymentId: string): void {
          console.log('Ready for server approval:', paymentId);
        },
        onReadyForServerCompletion: function(paymentId: string, txid: string): void {
          console.log('Ready for server completion:', paymentId, txid);
        },
        onCancel: function(paymentId: string): void {
          console.log('Payment cancelled:', paymentId);
        },
        onError: function(error: Error, payment?: unknown): void {
          console.error('Payment error:', error, payment);
        }
      });
      return payment;
    } catch (error) {
      console.error('Pi Network payment error:', error);
      throw error;
    }
  }
}

export default PiNetwork; 