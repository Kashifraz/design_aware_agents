const getErrorMessage = (err: any, fallback: string) =>
  err.response?.data?.message || fallback

const withInventoryRequest = async <T>(
  request: () => Promise<T>,
  fallbackErrorMessage: string
): Promise<T> => {
  loading.value = true
  error.value = null

  try {
    return await request()
  } catch (err: any) {
    error.value = getErrorMessage(err, fallbackErrorMessage)
    throw err
  } finally {
    loading.value = false
  }
}

const upsertInventoryItemById = (id: number, item: any) => {
  const index = inventory.value.findIndex(i => i.id === id)
  if (index !== -1) {
    inventory.value[index] = item
  } else {
    inventory.value.push(item)
  }
}

const syncCurrentInventoryById = (id: number, item: any) => {
  if (currentInventory.value?.id === id) {
    currentInventory.value = item
  }
}

const fetchInventoryItem = async (storeId: number, id: number) => {
  return withInventoryRequest(async () => {
    const item = await inventoryService.getInventoryItem(storeId, id)
    upsertInventoryItemById(id, item)
    return item
  }, 'Failed to fetch inventory item')
}

const createInventory = async (storeId: number, data: any) => {
  return withInventoryRequest(async () => {
    const item = await inventoryService.createInventory(storeId, data)
    inventory.value.push(item)
    return item
  }, 'Failed to create inventory item')
}

const updateInventory = async (storeId: number, id: number, data: any) => {
  return withInventoryRequest(async () => {
    const item = await inventoryService.updateInventory(storeId, id, data)
    upsertInventoryItemById(id, item)
    syncCurrentInventoryById(id, item)
    return item
  }, 'Failed to update inventory')
}

const adjustInventory = async (storeId: number, id: number, data: any) => {
  return withInventoryRequest(async () => {
    const item = await inventoryService.adjustInventory(storeId, id, data)
    upsertInventoryItemById(id, item)
    syncCurrentInventoryById(id, item)
    return item
  }, 'Failed to adjust inventory')
}

const fetchLowStock = async (storeId: number) => {
  return withInventoryRequest(async () => {
    lowStockItems.value = await inventoryService.getLowStock(storeId)
    return lowStockItems.value
  }, 'Failed to fetch low stock items')
}