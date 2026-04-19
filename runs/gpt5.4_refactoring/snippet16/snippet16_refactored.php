protected function authorizeDiscountAccess(string $action)
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

protected function getRequestValue(array $json, string $field)
{
    return $json[$field] ?? $this->request->getPost($field);
}

protected function normalizeNullableValue($value)
{
    return empty($value) ? null : $value;
}

protected function validateMutuallyExclusiveProductAndCategory($productId, $categoryId)
{
    if (!empty($productId) && !empty($categoryId)) {
        return $this->error('product_id and category_id cannot both be set. They are mutually exclusive.', null, 400);
    }

    return null;
}

protected function getCreateDiscountData()
{
    $json = $this->request->getJSON(true);

    $data = [
        'name' => $this->getRequestValue($json, 'name'),
        'type' => $this->getRequestValue($json, 'type'),
        'value' => $this->getRequestValue($json, 'value'),
        'product_id' => $this->getRequestValue($json, 'product_id'),
        'category_id' => $this->getRequestValue($json, 'category_id'),
        'store_id' => $this->getRequestValue($json, 'store_id'),
        'min_purchase' => $this->getRequestValue($json, 'min_purchase'),
        'valid_from' => $this->getRequestValue($json, 'valid_from'),
        'valid_to' => $this->getRequestValue($json, 'valid_to'),
        'status' => $this->getRequestValue($json, 'status') ?? 'active',
    ];

    $validationResponse = $this->validateMutuallyExclusiveProductAndCategory($data['product_id'], $data['category_id']);
    if ($validationResponse) {
        return $validationResponse;
    }

    foreach (['product_id', 'category_id', 'store_id', 'min_purchase', 'valid_from', 'valid_to'] as $field) {
        $data[$field] = $this->normalizeNullableValue($data[$field]);
    }

    return $data;
}

protected function getUpdateDiscountData(array $discount)
{
    $json = $this->request->getJSON(true);
    $data = [];

    $fields = ['name', 'type', 'value', 'status'];
    foreach ($fields as $field) {
        if (isset($json[$field]) || $this->request->getPost($field) !== null) {
            $data[$field] = $this->getRequestValue($json, $field);
        }
    }

    $nullableFields = ['product_id', 'category_id', 'store_id', 'min_purchase', 'valid_from', 'valid_to'];
    foreach ($nullableFields as $field) {
        if (isset($json[$field]) || $this->request->getPost($field) !== null) {
            $data[$field] = $this->normalizeNullableValue($this->getRequestValue($json, $field));
        }
    }

    $finalProductId = $data['product_id'] ?? $discount['product_id'];
    $finalCategoryId = $data['category_id'] ?? $discount['category_id'];

    $validationResponse = $this->validateMutuallyExclusiveProductAndCategory($finalProductId, $finalCategoryId);
    if ($validationResponse) {
        return $validationResponse;
    }

    return $data;
}

public function show($id = null)
{
    try {
        $authResponse = $this->authorizeDiscountAccess('view');
        if ($authResponse) {
            return $authResponse;
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
        $authResponse = $this->authorizeDiscountAccess('create');
        if ($authResponse) {
            return $authResponse;
        }

        $data = $this->getCreateDiscountData();
        if (!is_array($data)) {
            return $data;
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
        $authResponse = $this->authorizeDiscountAccess('update');
        if ($authResponse) {
            return $authResponse;
        }

        $discount = $this->discountModel->find($id);
        if (!$discount) {
            return $this->notFound('Discount not found');
        }

        $data = $this->getUpdateDiscountData($discount);
        if (!is_array($data)) {
            return $data;
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
        $authResponse = $this->authorizeDiscountAccess('delete');
        if ($authResponse) {
            return $authResponse;
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