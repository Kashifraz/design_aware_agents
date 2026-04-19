const shouldSkipPaymentProcessing = () =>
  !canProcessPayment.value || hasPayment.value || paymentProcessed.value

const buildPaymentDataToSend = () => ({
  payment_method: paymentData.value.payment_method,
  amount: paymentData.value.amount, // Use the amount entered (includes change calculation)
  reference_number: paymentData.value.reference_number || undefined,
})

const markPaymentProcessed = () => {
  paymentProcessed.value = true
}

const handlePaymentProcessingError = (error) => {
  console.error('Payment processing error:', error)
  alert('Failed to process payment')
  paymentProcessed.value = false
}

const processPayment = async () => {
  if (shouldSkipPaymentProcessing()) {
    return
  }

  processing.value = true
  try {
    emit('paymentProcessed', buildPaymentDataToSend())
    markPaymentProcessed()
  } catch (error) {
    handlePaymentProcessingError(error)
  } finally {
    processing.value = false
  }
}