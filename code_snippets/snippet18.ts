const fetchInventoryItem = async (storeId: number, id: number) => {
    loading.value = true
    error.value = null
    try {
      const item = await inventoryService.getInventoryItem(storeId, id)
      // Update in inventory array if exists
      const index = inventory.value.findIndex(i => i.id === id)
      if (index !== -1) {
        inventory.value[index] = item
      } else {
        inventory.value.push(item)
      }
      return item
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch inventory item'
      throw err
    } finally {
      loading.value = false
    }
  }

  const createInventory = async (storeId: number, data: any) => {
    loading.value = true
    error.value = null
    try {
      const item = await inventoryService.createInventory(storeId, data)
      inventory.value.push(item)
      return item
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to create inventory item'
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateInventory = async (storeId: number, id: number, data: any) => {
    loading.value = true
    error.value = null
    try {
      const item = await inventoryService.updateInventory(storeId, id, data)
      const index = inventory.value.findIndex(i => i.id === id)
      if (index !== -1) {
        inventory.value[index] = item
      }
      if (currentInventory.value?.id === id) {
        currentInventory.value = item
      }
      return item
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to update inventory'
      throw err
    } finally {
      loading.value = false
    }
  }

  const adjustInventory = async (storeId: number, id: number, data: any) => {
    loading.value = true
    error.value = null
    try {
      const item = await inventoryService.adjustInventory(storeId, id, data)
      const index = inventory.value.findIndex(i => i.id === id)
      if (index !== -1) {
        inventory.value[index] = item
      }
      if (currentInventory.value?.id === id) {
        currentInventory.value = item
      }
      return item
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to adjust inventory'
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchLowStock = async (storeId: number) => {
    loading.value = true
    error.value = null
    try {
      lowStockItems.value = await inventoryService.getLowStock(storeId)
      return lowStockItems.value
    } catch (err: any) {
      error.value = err.response?.data?.message || 'Failed to fetch low stock items'
      throw err
    } finally {
      loading.value = false
    }
  }
