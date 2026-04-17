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

            // If transaction_id is provided, get product-specific and category discounts
            if ($transactionId) {
                $transactionModel = new \App\Models\TransactionModel();
                $transaction = $transactionModel->getTransactionWithRelations($transactionId);
                
                if ($transaction && isset($transaction['items'])) {
                    $productIds = [];
                    $categoryIds = [];
                    $productModel = new \App\Models\ProductModel();
                    
                    // Collect product IDs and category IDs from transaction items
                    foreach ($transaction['items'] as $item) {
                        if (isset($item['product_id']) && $item['product_id']) {
                            $productIds[] = (int)$item['product_id'];
                            $product = $productModel->find($item['product_id']);
                            if ($product && isset($product['category_id']) && $product['category_id']) {
                                $categoryIds[] = (int)$product['category_id'];
                            }
                        }
                    }
                    
                    $productIds = array_unique($productIds);
                    $categoryIds = array_unique($categoryIds);
                    
                    // Get product-specific discounts (product_id must NOT be NULL)
                    if (!empty($productIds)) {
                        // Build the query step by step
                        // For product discounts: product_id must be set, category_id must be NULL
                        // Create a completely fresh builder instance
                        $db = \Config\Database::connect();
                        $productDiscountsQuery = $db->table('discounts');
                        
                        $productDiscountsQuery->where('status', 'active')
                            ->where('store_id', $storeId)
                            ->whereIn('product_id', $productIds)
                            ->where('category_id IS NULL', null, false); // Use raw SQL for IS NULL check
                        
                        // Date validation: discount must be currently valid
                        // valid_from must be NULL or <= now (discount has started)
                        // valid_to must be NULL or >= now (discount hasn't expired)
                        $productDiscountsQuery->groupStart()
                            ->where('valid_from IS NULL', null, false)
                            ->orWhere('valid_from <=', $now)
                            ->groupEnd();
                        $productDiscountsQuery->groupStart()
                            ->where('valid_to IS NULL', null, false)
                            ->orWhere('valid_to >=', $now)
                            ->groupEnd();
                        
                        // Min purchase validation
                        if ($subtotal > 0) {
                            $productDiscountsQuery->groupStart()
                                ->where('min_purchase IS NULL', null, false)
                                ->orWhere('min_purchase <=', $subtotal)
                                ->groupEnd();
                        }
                        
                        // Order and execute
                        $productDiscountsQuery->orderBy('value', 'DESC');
                        
                        // Debug: Log the query and parameters
                        log_message('error', '[DiscountController::getApplicable] Product IDs: ' . json_encode($productIds));
                        log_message('error', '[DiscountController::getApplicable] Store ID: ' . $storeId);
                        log_message('error', '[DiscountController::getApplicable] Subtotal: ' . $subtotal);
                        log_message('error', '[DiscountController::getApplicable] Now: ' . $now);
                        log_message('error', '[DiscountController::getApplicable] Category IDs: ' . json_encode($categoryIds));
                        
                        $productDiscounts = $productDiscountsQuery->get()->getResultArray();
                        
                        // Debug logging
                        log_message('error', '[DiscountController::getApplicable] Product discounts found: ' . count($productDiscounts));
                        if (count($productDiscounts) > 0) {
                            log_message('error', '[DiscountController::getApplicable] Product discounts: ' . json_encode($productDiscounts));
                        } else {
                            // Diagnostic queries to find what's filtering out the discounts
                            // Check 1: All product discounts for these products (no filters)
                            $check1Builder = $db->table('discounts');
                            $check1 = $check1Builder
                                ->where('store_id', $storeId)
                                ->whereIn('product_id', $productIds)
                                ->get()->getResultArray();
                            log_message('error', '[DiscountController::getApplicable] Check 1 - All product discounts (no filters): ' . count($check1));
                            if (count($check1) > 0) {
                                log_message('error', '[DiscountController::getApplicable] Check 1 discounts: ' . json_encode($check1));
                            }
                            
                            // Check 2: With status filter
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
                            
                            // Check 3: With category_id IS NULL
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
                            
                            // Check 4: With date filters
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
                        
                        $allDiscounts = array_merge($allDiscounts, $productDiscounts);
                    }
                    
                    // Get category discounts (category_id must NOT be NULL, product_id must be NULL)
                    if (!empty($categoryIds)) {
                        // Create a completely fresh builder instance
                        $db = \Config\Database::connect();
                        $categoryDiscountsBuilder = $db->table('discounts');
                        
                        $categoryDiscountsBuilder->where('status', 'active')
                            ->where('store_id', $storeId)
                            ->where('category_id IS NOT NULL', null, false)
                            ->whereIn('category_id', $categoryIds)
                            ->where('product_id IS NULL', null, false) // Ensure it's category-level, not product-specific
                            ->groupStart()
                                ->where('valid_from IS NULL', null, false)
                                ->orWhere('valid_from <=', $now)
                            ->groupEnd()
                            ->groupStart()
                                ->where('valid_to IS NULL', null, false)
                                ->orWhere('valid_to >=', $now)
                            ->groupEnd();
                        
                        if ($subtotal > 0) {
                            $categoryDiscountsBuilder->groupStart()
                                ->where('min_purchase IS NULL', null, false)
                                ->orWhere('min_purchase <=', $subtotal)
                                ->groupEnd();
                        }
                        
                        $categoryDiscounts = $categoryDiscountsBuilder->orderBy('value', 'DESC')->get()->getResultArray();
                        
                        // Debug logging for category discounts
                        log_message('error', '[DiscountController::getApplicable] Category discounts found: ' . count($categoryDiscounts));
                        if (count($categoryDiscounts) > 0) {
                            log_message('error', '[DiscountController::getApplicable] Category discounts: ' . json_encode($categoryDiscounts));
                        } else {
                            // Diagnostic query for category discounts
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
                        
                        $allDiscounts = array_merge($allDiscounts, $categoryDiscounts);
                    }
                }
            }
            
            // Get store-wide discounts (always include these)
            $db = \Config\Database::connect();
            $storeDiscountsBuilder = $db->table('discounts');
            
            $storeDiscountsBuilder->where('status', 'active')
                ->where('store_id', $storeId)
                ->where('product_id IS NULL', null, false)
                ->where('category_id IS NULL', null, false)
                ->groupStart()
                    ->where('valid_from IS NULL', null, false)
                    ->orWhere('valid_from <=', $now)
                ->groupEnd()
                ->groupStart()
                    ->where('valid_to IS NULL', null, false)
                    ->orWhere('valid_to >=', $now)
                ->groupEnd();
            
            if ($subtotal > 0) {
                $storeDiscountsBuilder->groupStart()
                    ->where('min_purchase IS NULL', null, false)
                    ->orWhere('min_purchase <=', $subtotal)
                    ->groupEnd();
            }
            
            $storeDiscounts = $storeDiscountsBuilder->orderBy('value', 'DESC')->get()->getResultArray();
            $allDiscounts = array_merge($allDiscounts, $storeDiscounts);
            
            // Remove duplicates and sort by priority: product > category > store-wide
            $uniqueDiscounts = [];
            $seenIds = [];
            foreach ($allDiscounts as $discount) {
                if (!in_array($discount['id'], $seenIds)) {
                    $uniqueDiscounts[] = $discount;
                    $seenIds[] = $discount['id'];
                }
            }
            
            // Sort by priority: product discounts first, then category, then store-wide
            usort($uniqueDiscounts, function($a, $b) {
                $priorityA = !empty($a['product_id']) ? 1 : (!empty($a['category_id']) ? 2 : 3);
                $priorityB = !empty($b['product_id']) ? 1 : (!empty($b['category_id']) ? 2 : 3);
                
                if ($priorityA !== $priorityB) {
                    return $priorityA - $priorityB;
                }
                
                // If same priority, sort by value descending
                return (float)$b['value'] <=> (float)$a['value'];
            });
            
            return $this->success($uniqueDiscounts, 'Applicable discounts retrieved successfully');

        } catch (\Exception $e) {
            log_message('error', '[DiscountController::getApplicable] Error: ' . $e->getMessage());
            return $this->error('An error occurred while retrieving applicable discounts: ' . $e->getMessage(), null, 500);
        }
    }