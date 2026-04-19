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
            $transactionData = $this->extractTransactionProductAndCategoryIds($transactionId);

            if (!empty($transactionData['productIds'])) {
                $productDiscounts = $this->getProductDiscounts(
                    $storeId,
                    $transactionData['productIds'],
                    $subtotal,
                    $now,
                    $transactionData['categoryIds']
                );
                $allDiscounts = array_merge($allDiscounts, $productDiscounts);
            }

            if (!empty($transactionData['categoryIds'])) {
                $categoryDiscounts = $this->getCategoryDiscounts(
                    $storeId,
                    $transactionData['categoryIds'],
                    $subtotal,
                    $now
                );
                $allDiscounts = array_merge($allDiscounts, $categoryDiscounts);
            }
        }

        $storeDiscounts = $this->getStoreWideDiscounts($storeId, $subtotal, $now);
        $allDiscounts = array_merge($allDiscounts, $storeDiscounts);

        $uniqueDiscounts = $this->removeDuplicateDiscounts($allDiscounts);
        $this->sortDiscountsByPriority($uniqueDiscounts);

        return $this->success($uniqueDiscounts, 'Applicable discounts retrieved successfully');
    } catch (\Exception $e) {
        log_message('error', '[DiscountController::getApplicable] Error: ' . $e->getMessage());
        return $this->error('An error occurred while retrieving applicable discounts: ' . $e->getMessage(), null, 500);
    }
}

private function extractTransactionProductAndCategoryIds($transactionId)
{
    $transactionModel = new \App\Models\TransactionModel();
    $transaction = $transactionModel->getTransactionWithRelations($transactionId);

    $productIds = [];
    $categoryIds = [];

    if ($transaction && isset($transaction['items'])) {
        $productModel = new \App\Models\ProductModel();

        foreach ($transaction['items'] as $item) {
            if (isset($item['product_id']) && $item['product_id']) {
                $productIds[] = (int) $item['product_id'];
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

private function getProductDiscounts($storeId, array $productIds, $subtotal, $now, array $categoryIds = [])
{
    $db = \Config\Database::connect();
    $productDiscountsQuery = $db->table('discounts');

    $productDiscountsQuery->where('status', 'active')
        ->where('store_id', $storeId)
        ->whereIn('product_id', $productIds)
        ->where('category_id IS NULL', null, false);

    $this->applyValidityFilters($productDiscountsQuery, $now);
    $this->applyMinPurchaseFilter($productDiscountsQuery, $subtotal);

    $productDiscountsQuery->orderBy('value', 'DESC');

    log_message('error', '[DiscountController::getApplicable] Product IDs: ' . json_encode($productIds));
    log_message('error', '[DiscountController::getApplicable] Store ID: ' . $storeId);
    log_message('error', '[DiscountController::getApplicable] Subtotal: ' . $subtotal);
    log_message('error', '[DiscountController::getApplicable] Now: ' . $now);
    log_message('error', '[DiscountController::getApplicable] Category IDs: ' . json_encode($categoryIds));

    $productDiscounts = $productDiscountsQuery->get()->getResultArray();

    log_message('error', '[DiscountController::getApplicable] Product discounts found: ' . count($productDiscounts));
    if (count($productDiscounts) > 0) {
        log_message('error', '[DiscountController::getApplicable] Product discounts: ' . json_encode($productDiscounts));
    } else {
        $this->logProductDiscountDiagnostics($db, $storeId, $productIds, $now);
    }

    return $productDiscounts;
}

private function getCategoryDiscounts($storeId, array $categoryIds, $subtotal, $now)
{
    $db = \Config\Database::connect();
    $categoryDiscountsBuilder = $db->table('discounts');

    $categoryDiscountsBuilder->where('status', 'active')
        ->where('store_id', $storeId)
        ->where('category_id IS NOT NULL', null, false)
        ->whereIn('category_id', $categoryIds)
        ->where('product_id IS NULL', null, false);

    $this->applyValidityFilters($categoryDiscountsBuilder, $now);
    $this->applyMinPurchaseFilter($categoryDiscountsBuilder, $subtotal);

    $categoryDiscounts = $categoryDiscountsBuilder->orderBy('value', 'DESC')->get()->getResultArray();

    log_message('error', '[DiscountController::getApplicable] Category discounts found: ' . count($categoryDiscounts));
    if (count($categoryDiscounts) > 0) {
        log_message('error', '[DiscountController::getApplicable] Category discounts: ' . json_encode($categoryDiscounts));
    } else {
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

    return $categoryDiscounts;
}

private function getStoreWideDiscounts($storeId, $subtotal, $now)
{
    $db = \Config\Database::connect();
    $storeDiscountsBuilder = $db->table('discounts');

    $storeDiscountsBuilder->where('status', 'active')
        ->where('store_id', $storeId)
        ->where('product_id IS NULL', null, false)
        ->where('category_id IS NULL', null, false);

    $this->applyValidityFilters($storeDiscountsBuilder, $now);
    $this->applyMinPurchaseFilter($storeDiscountsBuilder, $subtotal);

    return $storeDiscountsBuilder->orderBy('value', 'DESC')->get()->getResultArray();
}

private function applyValidityFilters($builder, $now)
{
    $builder->groupStart()
        ->where('valid_from IS NULL', null, false)
        ->orWhere('valid_from <=', $now)
        ->groupEnd();

    $builder->groupStart()
        ->where('valid_to IS NULL', null, false)
        ->orWhere('valid_to >=', $now)
        ->groupEnd();
}

private function applyMinPurchaseFilter($builder, $subtotal)
{
    if ($subtotal > 0) {
        $builder->groupStart()
            ->where('min_purchase IS NULL', null, false)
            ->orWhere('min_purchase <=', $subtotal)
            ->groupEnd();
    }
}

private function removeDuplicateDiscounts(array $discounts)
{
    $uniqueDiscounts = [];
    $seenIds = [];

    foreach ($discounts as $discount) {
        if (!in_array($discount['id'], $seenIds)) {
            $uniqueDiscounts[] = $discount;
            $seenIds[] = $discount['id'];
        }
    }

    return $uniqueDiscounts;
}

private function sortDiscountsByPriority(array &$discounts)
{
    usort($discounts, function ($a, $b) {
        $priorityA = !empty($a['product_id']) ? 1 : (!empty($a['category_id']) ? 2 : 3);
        $priorityB = !empty($b['product_id']) ? 1 : (!empty($b['category_id']) ? 2 : 3);

        if ($priorityA !== $priorityB) {
            return $priorityA - $priorityB;
        }

        return (float) $b['value'] <=> (float) $a['value'];
    });
}

private function logProductDiscountDiagnostics($db, $storeId, array $productIds, $now)
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