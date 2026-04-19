<?php

private function authorizeDiscountAccess(string $action)
{
    $userId = $this->request->user['user_id'] ?? null;
    $userRole = $this->request->user['role'] ?? null;

    if (!$userId || !$userRole) {
        return $this->unauthorized('Authentication required');
    }

    if (!in_array($userRole, ['admin', 'manager'])) {
        return $this->forbidden("Only managers and admins can {$action} discounts");
    }

    return null;
}

public function show($id = null)
{
    try {
        if ($response = $this->authorizeDiscountAccess('view')) {
            return $response;
        }

        $discount = $this->discountModel->find($id);
        if (!$discount) {
            return $this->notFound('Discount not found');
        }

        return $this->success($discount, 'Discount retrieved successfully');

    } catch (\Exception $e) {
        log_message('error', '[DiscountController::show] Error: ' . $e->getMessage());
        return $this->error('An error occurred while retrieving discount: ' . $e->getMessage(), null, 500);
    }
}

/**
 * Create new discount
 * POST /api/discounts
 */
public function create()
{
    try {
        if ($response = $this->authorizeDiscountAccess('create')) {
            return $response;
        }

        $json = $this->request->getJSON(true);
        $data = [
            'name' => $json['name'] ?? $this->request->getPost('name'),
            'type' => $json['type'] ?? $this->request->getPost('type'),
            'value' => $json['value'] ?? $this->request->getPost('value'),
            'product_id' => $json['product_id'] ?? $this->request->getPost('product_id'),
            'category_id' => $json['category_id'] ?? $this->request->getPost('category_id'),
            'store_id' => $json['store_id'] ?? $this->request->getPost('store_id'),
            'min_purchase' => $json['min_purchase'] ?? $this->request->getPost('min_purchase'),
            'valid_from' => $json['valid_from'] ?? $this->request->getPost('valid_from'),
            'valid_to' => $json['valid_to'] ?? $this->request->getPost('valid_to'),
            'status' => $json['status'] ?? $this->request->getPost('status') ?? 'active',
        ];

        // Validate mutual exclusivity: product_id and category_id cannot both be set
        if (!empty($data['product_id']) && !empty($data['category_id'])) {
            return $this->error('product_id and category_id cannot both be set. They are mutually exclusive.', null, 400);
        }

        // Convert empty strings to null
        if (empty($data['product_id'])) {
            $data['product_id'] = null;
        }
        if (empty($data['category_id'])) {
            $data['category_id'] = null;
        }
        if (empty($data['store_id'])) {
            $data['store_id'] = null;
        }
        if (empty($data['min_purchase'])) {
            $data['min_purchase'] = null;
        }
        if (empty($data['valid_from'])) {
            $data['valid_from'] = null;
        }
        if (empty($data['valid_to'])) {
            $data['valid_to'] = null;
        }

        if (!$this->discountModel->insert($data)) {
            return $this->validationError($this->discountModel->errors(), 'Validation failed');
        }

        $discount = $this->discountModel->find($this->discountModel->getInsertID());
        return $this->success($discount, 'Discount created successfully', 201);

    } catch (\Exception $e) {
        log_message('error', '[DiscountController::create] Error: ' . $e->getMessage());
        return $this->error('An error occurred while creating discount: ' . $e->getMessage(), null, 500);
    }
}

/**
 * Update discount
 * PUT /api/discounts/:id
 */
public function update($id = null)
{
    try {
        if ($response = $this->authorizeDiscountAccess('update')) {
            return $response;
        }

        $discount = $this->discountModel->find($id);
        if (!$discount) {
            return $this->notFound('Discount not found');
        }

        $json = $this->request->getJSON(true);
        $data = [];

        if (isset($json['name']) || $this->request->getPost('name') !== null) {
            $data['name'] = $json['name'] ?? $this->request->getPost('name');
        }
        if (isset($json['type']) || $this->request->getPost('type') !== null) {
            $data['type'] = $json['type'] ?? $this->request->getPost('type');
        }
        if (isset($json['value']) || $this->request->getPost('value') !== null) {
            $data['value'] = $json['value'] ?? $this->request->getPost('value');
        }
        if (isset($json['product_id']) || $this->request->getPost('product_id') !== null) {
            $data['product_id'] = empty($json['product_id'] ?? $this->request->getPost('product_id')) ? null : ($json['product_id'] ?? $this->request->getPost('product_id'));
        }
        if (isset($json['category_id']) || $this->request->getPost('category_id') !== null) {
            $data['category_id'] = empty($json['category_id'] ?? $this->request->getPost('category_id')) ? null : ($json['category_id'] ?? $this->request->getPost('category_id'));
        }
        if (isset($json['store_id']) || $this->request->getPost('store_id') !== null) {
            $data['store_id'] = empty($json['store_id'] ?? $this->request->getPost('store_id')) ? null : ($json['store_id'] ?? $this->request->getPost('store_id'));
        }
        if (isset($json['min_purchase']) || $this->request->getPost('min_purchase') !== null) {
            $data['min_purchase'] = empty($json['min_purchase'] ?? $this->request->getPost('min_purchase')) ? null : ($json['min_purchase'] ?? $this->request->getPost('min_purchase'));
        }
        if (isset($json['valid_from']) || $this->request->getPost('valid_from') !== null) {
            $data['valid_from'] = empty($json['valid_from'] ?? $this->request->getPost('valid_from')) ? null : ($json['valid_from'] ?? $this->request->getPost('valid_from'));
        }
        if (isset($json['valid_to']) || $this->request->getPost('valid_to') !== null) {
            $data['valid_to'] = empty($json['valid_to'] ?? $this->request->getPost('valid_to')) ? null : ($json['valid_to'] ?? $this->request->getPost('valid_to'));
        }
        if (isset($json['status']) || $this->request->getPost('status') !== null) {
            $data['status'] = $json['status'] ?? $this->request->getPost('status');
        }

        // Validate mutual exclusivity
        $finalProductId = $data['product_id'] ?? $discount['product_id'];
        $finalCategoryId = $data['category_id'] ?? $discount['category_id'];
        if (!empty($finalProductId) && !empty($finalCategoryId)) {
            return $this->error('product_id and category_id cannot both be set. They are mutually exclusive.', null, 400);
        }

        if (empty($data)) {
            return $this->error('No data provided for update', null, 400);
        }

        if (!$this->discountModel->update($id, $data)) {
            return $this->validationError($this->discountModel->errors(), 'Validation failed');
        }

        $updatedDiscount = $this->discountModel->find($id);
        return $this->success($updatedDiscount, 'Discount updated successfully');

    } catch (\Exception $e) {
        log_message('error', '[DiscountController::update] Error: ' . $e->getMessage());
        return $this->error('An error occurred while updating discount: ' . $e->getMessage(), null, 500);
    }
}

/**
 * Delete discount
 * DELETE /api/discounts/:id
 */
public function delete($id = null)
{
    try {
        if ($response = $this->authorizeDiscountAccess('delete')) {
            return $response;
        }

        $discount = $this->discountModel->find($id);
        if (!$discount) {
            return $this->notFound('Discount not found');
        }

        if (!$this->discountModel->delete($id)) {
            return $this->error('Failed to delete discount', null, 500);
        }

        return $this->success(null, 'Discount deleted successfully');

    } catch (\Exception $e) {
        log_message('error', '[DiscountController::delete] Error: ' . $e->getMessage());
        return $this->error('An error occurred while deleting discount: ' . $e->getMessage(), null, 500);
    }
}