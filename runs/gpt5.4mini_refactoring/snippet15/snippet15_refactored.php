public function getApplicable()
{
    try {
        $userId = $this->request->user['user_id'] ?? null;
        $userRole = $this->request->user['role'] ?? null;

        if (!$userId || !$userRole) {
            return $this->unauthorized('Authentication required');
        }

        $storeId = $this->request->getGet('store_id');
        $subtotal = (float) ($this->request->getGet('subtotal') ?? 0);
        $transactionId = $this->request->getGet('transaction_id');

        if (!$storeId) {
            return $this->error('store_id is required', null, 400);
        }

        $now = date('Y-m-d H:i:s');
        $allDiscounts = [];

        if ($transactionId) {
            $transactionData = $this->getTransactionDiscountContext($transactionId);
            $allDiscounts = array_merge(
                $allDiscounts,
                $this->getProductDiscounts($storeId, $transactionData['productIds'], $subtotal, $now),
                $this->getCategoryDiscounts($storeId, $transactionData['categoryIds'], $subtotal, $now)
            );
        }

        $allDiscounts = array_merge(
            $allDiscounts,
            $this->getStoreDiscounts($storeId, $subtotal, $now)
        );

        $uniqueDiscounts = $this->deduplicateAndSortDiscounts($allDiscounts);

        return $this->success($uniqueDiscounts, 'Applicable discounts retrieved successfully');
    } catch (\Exception $e) {
        log_message('error', '[DiscountController::getApplicable] Error: ' . $e->getMessage());
        return $this->error('An error occurred while retrieving applicable discounts: ' . $e->getMessage(), null, 500);
    }
}

private function getTransactionDiscountContext($transactionId): array
{
    $transactionModel = new \App\Models\TransactionModel();
    $transaction = $transactionModel->getTransactionWithRelations($transactionId);

    $productIds = [];
    $categoryIds = [];

    if ($transaction && isset($transaction['items'])) {
        $productModel = new \App\Models\ProductModel();

        foreach ($transaction['items'] as $item) {
            if (isset($item['product_id']) && $item['product_id']) {
                $productId = (int) $item['product_id'];
                $productIds[] = $productId;

                $product = $productModel->find($item['product_id']);
                if ($product && isset($product['category_id']) && $product['category_id']) {
                    $categoryIds[] = (int) $product['category_id'];
                }
            }
        }
    }

    return [
        'productIds' => array_unique($productIds),
        'categoryIds' => array_unique($categoryIds),
    ];
}

private function getProductDiscounts($storeId, array $productIds, float $subtotal, string $now): array
{
    if (empty($productIds)) {
        return [];
    }

    $db = \Config\Database::connect();
    $builder = $db->table('discounts');

    $builder->where('status', 'active')
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->where('category_id IS NULL', null, false);

    $this->applyDateFilters($builder, $now);
    $this->applyMinPurchaseFilter($builder, $subtotal);

    $builder->orderBy('value', 'DESC');

    log_message('error', '[DiscountController::getApplicable] Product IDs: ' . json_encode($productIds));
    log_message('error', '[DiscountController::getApplicable] Store ID: ' . $storeId);
    log_message('error', '[DiscountController::getApplicable] Subtotal: ' . $subtotal);
    log_message('error', '[DiscountController::getApplicable] Now: ' . $now);

    $discounts = $builder->get()->getResultArray();

    log_message('error', '[DiscountController::getApplicable] Product discounts found: ' . count($discounts));

    if (count($discounts) > 0) {
        log_message('error', '[DiscountController::getApplicable] Product discounts: ' . json_encode($discounts));
    } else {
        $this->logProductDiscountDiagnostics($db, $storeId, $productIds, $now);
    }

    return $discounts;
}

private function getCategoryDiscounts($storeId, array $categoryIds, float $subtotal, string $now): array
{
    if (empty($categoryIds)) {
        return [];
    }

    $db = \Config\Database::connect();
    $builder = $db->table('discounts');

    $builder->where('status', 'active')
        ->where('store_id', $storeId)
        ->where('category_id IS NOT NULL', null, false)
        ->whereIn('category_id', $categoryIds)
        ->where('product_id IS NULL', null, false);

    $this->applyDateFilters($builder, $now);
    $this->applyMinPurchaseFilter($builder, $subtotal);

    $discounts = $builder->orderBy('value', 'DESC')->get()->getResultArray();

    log_message('error', '[DiscountController::getApplicable] Category discounts found: ' . count($discounts));

    if (count($discounts) > 0) {
        log_message('error', '[DiscountController::getApplicable] Category discounts: ' . json_encode($discounts));
    } else {
        $this->logCategoryDiscountDiagnostics($db, $storeId, $categoryIds);
    }

    return $discounts;
}

private function getStoreDiscounts($storeId, float $subtotal, string $now): array
{
    $db = \Config\Database::connect();
    $builder = $db->table('discounts');

    $builder->where('status', 'active')
        ->where('store_id', $storeId)
        ->where('product_id IS NULL', null, false)
        ->where('category_id IS NULL', null, false);

    $this->applyDateFilters($builder, $now);
    $this->applyMinPurchaseFilter($builder, $subtotal);

    return $builder->orderBy('value', 'DESC')->get()->getResultArray();
}

private function applyDateFilters($builder, string $now): void
{
    $builder->groupStart()
        ->where('valid_from IS NULL', null, false)
        ->orWhere('valid_from <=', $now)
        ->groupEnd()
        ->groupStart()
        ->where('valid_to IS NULL', null, false)
        ->orWhere('valid_to >=', $now)
        ->groupEnd();
}

private function applyMinPurchaseFilter($builder, float $subtotal): void
{
    if ($subtotal > 0) {
        $builder->groupStart()
            ->where('min_purchase IS NULL', null, false)
            ->orWhere('min_purchase <=', $subtotal)
            ->groupEnd();
    }
}

private function deduplicateAndSortDiscounts(array $discounts): array
{
    $uniqueDiscounts = [];
    $seenIds = [];

    foreach ($discounts as $discount) {
        if (!in_array($discount['id'], $seenIds)) {
            $uniqueDiscounts[] = $discount;
            $seenIds[] = $discount['id'];
        }
    }

    usort($uniqueDiscounts, function ($a, $b) {
        $priorityA = !empty($a['product_id']) ? 1 : (!empty($a['category_id']) ? 2 : 3);
        $priorityB = !empty($b['product_id']) ? 1 : (!empty($b['category_id']) ? 2 : 3);

        if ($priorityA !== $priorityB) {
            return $priorityA - $priorityB;
        }

        return (float) $b['value'] <=> (float) $a['value'];
    });

    return $uniqueDiscounts;
}

private function logProductDiscountDiagnostics($db, $storeId, array $productIds, string $now): void
{
    $check1Builder = $db->table('discounts');
    $check1 = $check1Builder
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->get()->getResultArray();
    log_message('error', '[DiscountController::getApplicable] Check 1 - All product discounts (no filters): ' . count($check1));
    if (count($check1) > 0) {
        log_message('error', '[DiscountController::getApplicable] Check 1 discounts: ' . json_encode($check1));
    }

    $check2Builder = $db->table('discounts');
    $check2 = $check2Builder
        ->where('status', 'active')
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->get()->getResultArray();
    log_message('error', '[DiscountController::getApplicable] Check 2 - With status=active: ' . count($check2));
    if (count($check2) > 0) {
        log_message('error', '[DiscountController::getApplicable] Check 2 discounts: ' . json_encode($check2));
    }

    $check3Builder = $db->table('discounts');
    $check3 = $check3Builder
        ->where('status', 'active')
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->where('category_id IS NULL', null, false)
        ->get()->getResultArray();
    log_message('error', '[DiscountController::getApplicable] Check 3 - With category_id IS NULL: ' . count($check3));
    if (count($check3) > 0) {
        log_message('error', '[DiscountController::getApplicable] Check 3 discounts: ' . json_encode($check3));
    }

    $check4Builder = $db->table('discounts');
    $check4 = $check4Builder
        ->where('status', 'active')
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->where('category_id IS NULL', null, false)
        ->groupStart()
            ->where('valid_from IS NULL', null, false)
            ->orWhere('valid_from <=', $now)
        ->groupEnd()
        ->groupStart()
            ->where('valid_to IS NULL', null, false)
            ->orWhere('valid_to >=', $now)
        ->groupEnd()
        ->get()->getResultArray();
    log_message('error', '[DiscountController::getApplicable] Check 4 - With date filters: ' . count($check4));
    if (count($check4) > 0) {
        log_message('error', '[DiscountController::getApplicable] Check 4 discounts: ' . json_encode($check4));
    }
}

private function logCategoryDiscountDiagnostics($db, $storeId, array $categoryIds): void
{
    $catCheckBuilder = $db->table('discounts');
    $catCheck = $catCheckBuilder
        ->where('status', 'active')
        ->where('store_id', $storeId)
        ->where('category_id IS NOT NULL', null, false)
        ->whereIn('category_id', $categoryIds)
        ->where('product_id IS NULL', null, false)
        ->get()->getResultArray();

    log_message('error', '[DiscountController::getApplicable] Category check (no date filters): ' . count($catCheck));
    if (count($catCheck) > 0) {
        log_message('error', '[DiscountController::getApplicable] Category check discounts: ' . json_encode($catCheck));
    }
}