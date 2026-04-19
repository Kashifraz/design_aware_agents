const canActuallyProcessPayment = () => {
  return canProcessPayment.value && !hasPayment.value && !paymentProcessed.value
}

const processPayment = async () => {
  if (!canActuallyProcessPayment()) {
    return
  }

  processing.value = true
  try {
    const paymentDataToSend = {
      payment_method: paymentData.value.payment_method,
      amount: paymentData.value.amount, // Use the amount entered (includes change calculation)
      reference_number: paymentData.value.reference_number || undefined,
    }
    emit('paymentProcessed', paymentDataToSend)
    paymentProcessed.value = true
  } catch (error) {
    console.error('Payment processing error:', error)
    alert('Failed to process payment')
    paymentProcessed.value = false
  } finally {
    processing.value = false
  }
}