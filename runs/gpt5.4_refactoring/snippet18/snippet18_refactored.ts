const withLoadingAndError = async <T>(
  action: () => Promise<T>,
  defaultMessage: string
): Promise<T> => {
  loading.value = true
  error.value = null
  try {
    return await action()
  } catch (err: any) {
    error.value = err.response?.data?.message || defaultMessage
    throw err
  } finally {
    loading.value = false
  }
}

const replaceInventoryItemIfExists = (id: number, item: any) => {
  const index = inventory.value.findIndex(i => i.id === id)
  if (index !== -1) {
    inventory.value[index] = item
  }
}

const upsertInventoryItemByItemId = (item: any) => {
  const index = inventory.value.findIndex(i => i.id === item.id)
  if (index !== -1) {
    inventory.value[index] = item
  } else {
    inventory.value.push(item)
  }
}

const syncCurrentInventoryIfMatching = (id: number, item: any) => {
  if (currentInventory.value?.id === id) {
    currentInventory.value = item
  }
}

const fetchInventoryItem = async (storeId: number, id: number) => {
  return withLoadingAndError(async () => {
    const item = await inventoryService.getInventoryItem(storeId, id)
    // Update in inventory array if exists
    upsertInventoryItemByItemId(item)
    return item
  }, 'Failed to fetch inventory item')
}

const createInventory = async (storeId: number, data: any) => {
  return withLoadingAndError(async () => {
    const item = await inventoryService.createInventory(storeId, data)
    inventory.value.push(item)
    return item
  }, 'Failed to create inventory item')
}

const updateInventory = async (storeId: number, id: number, data: any) => {
  return withLoadingAndError(async () => {
    const item = await inventoryService.updateInventory(storeId, id, data)
    replaceInventoryItemIfExists(id, item)
    syncCurrentInventoryIfMatching(id, item)
    return item
  }, 'Failed to update inventory')
}

const adjustInventory = async (storeId: number, id: number, data: any) => {
  return withLoadingAndError(async () => {
    const item = await inventoryService.adjustInventory(storeId, id, data)
    replaceInventoryItemIfExists(id, item)
    syncCurrentInventoryIfMatching(id, item)
    return item
  }, 'Failed to adjust inventory')
}

const fetchLowStock = async (storeId: number) => {
  return withLoadingAndError(async () => {
    lowStockItems.value = await inventoryService.getLowStock(storeId)
    return lowStockItems.value
  }, 'Failed to fetch low stock items')
}