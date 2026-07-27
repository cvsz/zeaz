export interface MenuItem { id: string; name: string; description?: string; price: number; available: boolean; imageUrl?: string; category?: string; }
export interface Menu { id: string; restaurantId: string; items: MenuItem[]; updatedAt: string; }
