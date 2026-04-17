public String exportOrdersToCSV(String status, String paymentStatus, String startDate, String endDate) {
        StringBuilder csv = new StringBuilder();
        csv.append("Order Number,Status,Payment Status,Customer Email,Total Amount,Subtotal,Tax,Shipping,Created At\n");
        
        // Convert String parameters to appropriate types
        Order.OrderStatus orderStatus = null;
        if (status != null && !status.isEmpty()) {
            try {
                orderStatus = Order.OrderStatus.valueOf(status);
            } catch (IllegalArgumentException e) {
                // Invalid status, will be ignored
            }
        }
        
        Order.PaymentStatus orderPaymentStatus = null;
        if (paymentStatus != null && !paymentStatus.isEmpty()) {
            try {
                orderPaymentStatus = Order.PaymentStatus.valueOf(paymentStatus);
            } catch (IllegalArgumentException e) {
                // Invalid payment status, will be ignored
            }
        }
        
        LocalDateTime startDateTime = null;
        if (startDate != null && !startDate.isEmpty()) {
            try {
                startDateTime = LocalDateTime.parse(startDate + "T00:00:00");
            } catch (Exception e) {
                // Invalid date format, will be ignored
            }
        }
        
        LocalDateTime endDateTime = null;
        if (endDate != null && !endDate.isEmpty()) {
            try {
                endDateTime = LocalDateTime.parse(endDate + "T23:59:59");
            } catch (Exception e) {
                // Invalid date format, will be ignored
            }
        }
        
        List<Order> orders = orderRepository.findForExport(orderStatus, orderPaymentStatus, startDateTime, endDateTime);
        
        for (Order order : orders) {
            csv.append(order.getOrderNumber()).append(",");
            csv.append(order.getStatus()).append(",");
            csv.append(order.getPaymentStatus()).append(",");
            csv.append(order.getUser().getEmail()).append(",");
            csv.append(order.getTotalAmount()).append(",");
            csv.append(order.getSubtotal()).append(",");
            csv.append(order.getTaxAmount()).append(",");
            csv.append(order.getShippingAmount()).append(",");
            csv.append(order.getCreatedAt()).append("\n");
        }
        
        return csv.toString();
    }