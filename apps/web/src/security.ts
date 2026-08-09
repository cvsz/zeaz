const SAFE_IMAGE_PREVIEW_TYPES = new Set([
  'image/gif',
  'image/jpeg',
  'image/png',
  'image/webp',
])

export function isSafeImagePreviewType(mimeType: string): boolean {
  return SAFE_IMAGE_PREVIEW_TYPES.has(mimeType.trim().toLowerCase())
}
