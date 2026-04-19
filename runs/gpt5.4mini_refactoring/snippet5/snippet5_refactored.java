public String exportOrdersToCSV(String status, String paymentStatus, String startDate, String endDate) {
    StringBuilder csv = new StringBuilder();
    csv.append("Order Number,Status,Payment Status,Customer Email,Total Amount,Subtotal,Tax,Shipping,Created At\n");

    Order.OrderStatus orderStatus = parseOrderStatus(status);
    Order.PaymentStatus orderPaymentStatus = parsePaymentStatus(paymentStatus);
    LocalDateTime startDateTime = parseStartDate(startDate);
    LocalDateTime endDateTime = parseEndDate(endDate);

    List<Order> orders = orderRepository.findForExport(orderStatus, orderPaymentStatus, startDateTime, endDateTime);

    for (Order order : orders) {
        appendOrderAsCsv(csv, order);
    }

    return csv.toString();
}

private Order.OrderStatus parseOrderStatus(String status) {
    if (status != null && !status.isEmpty()) {
        try {
            return Order.OrderStatus.valueOf(status);
        } catch (IllegalArgumentException e) {
            // Invalid status, will be ignored
        }
    }
    return null;
}

private Order.PaymentStatus parsePaymentStatus(String paymentStatus) {
    if (paymentStatus != null && !paymentStatus.isEmpty()) {
        try {
            return Order.PaymentStatus.valueOf(paymentStatus);
        } catch (IllegalArgumentException e) {
            // Invalid payment status, will be ignored
        }
    }
    return null;
}

private LocalDateTime parseStartDate(String startDate) {
    if (startDate != null && !startDate.isEmpty()) {
        try {
            return LocalDateTime.parse(startDate + "T00:00:00");
        } catch (Exception e) {
            // Invalid date format, will be ignored
        }
    }
    return null;
}

private LocalDateTime parseEndDate(String endDate) {
    if (endDate != null && !endDate.isEmpty()) {
        try {
            return LocalDateTime.parse(endDate + "T23:59:59");
        } catch (Exception e) {
            // Invalid date format, will be ignored
        }
    }
    return null;
}

private void appendOrderAsCsv(StringBuilder csv, Order order) {
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