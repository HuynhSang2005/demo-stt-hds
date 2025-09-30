/**
 * Vietnamese Language Utilities
 * Helper functions and constants for Vietnamese text processing and localization
 */

/**
 * Vietnamese language constants
 */
export const VIETNAMESE_LOCALE = 'vi-VN'

/**
 * Vietnamese text constants for UI
 */
export const VIETNAMESE_UI_TEXT = {
  // Audio recording
  recording: {
    start: 'Bắt đầu ghi âm',
    stop: 'Dừng ghi âm', 
    pause: 'Tạm dừng',
    resume: 'Tiếp tục',
    recording: 'Đang ghi âm...',
    paused: 'Tạm dừng',
    connecting: 'Đang kết nối...',
    connected: 'Đã kết nối',
    disconnected: 'Chưa kết nối',
    failed: 'Kết nối thất bại',
    permission: 'Cấp quyền microphone',
    noDevice: 'Không tìm thấy microphone',
    selectDevice: 'Chọn thiết bị ghi âm',
  },
  
  // Transcripts
  transcripts: {
    title: 'Bản ghi âm tiếng Việt',
    noResults: 'Chưa có bản ghi nào',
    searchPlaceholder: 'Tìm kiếm văn bản...',
    processing: 'Đang xử lý...',
    analyzing: 'Đang phân tích...',
    confidence: 'Độ tin cậy',
    timestamp: 'Thời gian',
    content: 'Nội dung',
    label: 'Nhãn cảm xúc',
    warning: 'Cảnh báo',
    selected: 'Đã chọn',
    clearSelection: 'Bỏ chọn',
  },
  
  // Warnings
  warnings: {
    title: 'Cảnh báo nội dung',
    toxic: 'Độc hại',
    negative: 'Tiêu cực', 
    positive: 'Tích cực',
    neutral: 'Trung tính',
    detected: 'Phát hiện nội dung',
    recentWarnings: 'Cảnh báo gần đây',
    totalWarnings: 'Tổng cộng',
    clearWarnings: 'Xóa cảnh báo',
    noWarnings: 'Chưa có cảnh báo nào',
    statistics: 'Thống kê cảnh báo',
    trend: 'Tăng hoạt động cảnh báo trong phút qua',
    lastWarning: 'Cảnh báo cuối',
    viewAll: 'Xem tất cả cảnh báo',
  },
  
  // Session management
  session: {
    title: 'Thống kê phiên',
    duration: 'Thời gian',
    transcripts: 'Bản ghi',
    warnings: 'Cảnh báo',
    status: 'Trạng thái',
    active: 'Đang hoạt động',
    paused: 'Tạm dừng',
    stopped: 'Đã dừng',
    completed: 'Hoàn thành',
  },
  
  // Export and actions
  actions: {
    export: 'Xuất file',
    exportJson: 'JSON (.json)',
    exportText: 'Text (.txt)',
    clear: 'Xóa tất cả',
    refresh: 'Làm mới',
    settings: 'Cài đặt',
    close: 'Đóng',
    save: 'Lưu',
    cancel: 'Hủy',
    confirm: 'Xác nhận',
    delete: 'Xóa',
  },
  
  // Messages
  messages: {
    noTranscripts: 'Không có bản ghi nào để xuất',
    confirmDelete: 'Bạn có chắc chắn muốn xóa tất cả bản ghi? Hành động này không thể hoàn tác.',
    exportSuccess: 'Xuất file thành công',
    exportError: 'Lỗi khi xuất file',
    connectionError: 'Lỗi kết nối WebSocket',
    recordingError: 'Lỗi khi ghi âm',
    permissionDenied: 'Quyền truy cập microphone bị từ chối',
    deviceNotFound: 'Không tìm thấy thiết bị microphone',
  },
  
  // Settings
  settings: {
    title: 'Cài đặt',
    connection: 'Kết nối',
    websocketUrl: 'WebSocket URL',
    status: 'Trạng thái',
    statistics: 'Thống kê',
    totalTranscripts: 'Tổng bản ghi',
    totalWarnings: 'Tổng cảnh báo',
    language: 'Ngôn ngữ',
    audio: 'Âm thanh',
    display: 'Hiển thị',
  }
} as const

/**
 * Vietnamese sentiment labels with descriptions
 */
export const VIETNAMESE_SENTIMENT_LABELS = {
  toxic: {
    label: 'Độc hại',
    description: 'Nội dung độc hại, xúc phạm',
    color: 'red',
    severity: 'critical'
  },
  negative: {
    label: 'Tiêu cực',
    description: 'Nội dung có tính tiêu cực',
    color: 'orange', 
    severity: 'high'
  },
  neutral: {
    label: 'Trung tính',
    description: 'Nội dung trung tính',
    color: 'gray',
    severity: 'low'
  },
  positive: {
    label: 'Tích cực',
    description: 'Nội dung tích cực, lạc quan',
    color: 'green',
    severity: 'low'
  }
} as const

/**
 * Vietnamese date/time formatting utilities
 */
export const formatVietnameseDateTime = {
  /**
   * Format timestamp for Vietnamese locale
   */
  time: (timestamp: number): string => {
    return new Intl.DateTimeFormat(VIETNAMESE_LOCALE, {
      hour: '2-digit',
      minute: '2-digit', 
      second: '2-digit',
      hour12: false,
    }).format(new Date(timestamp))
  },
  
  /**
   * Format date for Vietnamese locale
   */
  date: (timestamp: number): string => {
    return new Intl.DateTimeFormat(VIETNAMESE_LOCALE, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date(timestamp))
  },
  
  /**
   * Format full date and time for Vietnamese locale
   */
  datetime: (timestamp: number): string => {
    return new Intl.DateTimeFormat(VIETNAMESE_LOCALE, {
      year: 'numeric',
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(new Date(timestamp))
  },
  
  /**
   * Format relative time in Vietnamese
   */
  relative: (timestamp: number): string => {
    const rtf = new Intl.RelativeTimeFormat(VIETNAMESE_LOCALE, { numeric: 'auto' })
    const now = Date.now()
    const diff = timestamp - now
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    
    if (Math.abs(days) >= 1) return rtf.format(days, 'day')
    if (Math.abs(hours) >= 1) return rtf.format(hours, 'hour')
    if (Math.abs(minutes) >= 1) return rtf.format(minutes, 'minute')
    return rtf.format(seconds, 'second')
  }
}

/**
 * Vietnamese number formatting utilities
 */
export const formatVietnameseNumbers = {
  /**
   * Format percentage
   */
  percentage: (value: number): string => {
    return new Intl.NumberFormat(VIETNAMESE_LOCALE, {
      style: 'percent',
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(value)
  },
  
  /**
   * Format duration in Vietnamese
   */
  duration: (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours} giờ ${minutes % 60} phút ${seconds % 60} giây`
    }
    if (minutes > 0) {
      return `${minutes} phút ${seconds % 60} giây`
    }
    return `${seconds} giây`
  },
  
  /**
   * Format file size in Vietnamese
   */
  fileSize: (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }
}

/**
 * Vietnamese text processing utilities
 */
export const vietnameseTextUtils = {
  /**
   * Normalize Vietnamese text for search
   */
  normalizeForSearch: (text: string): string => {
    return text
      .toLowerCase()
      .normalize('NFD') // Decompose Vietnamese diacritics
      .replace(/[\u0300-\u036f]/g, '') // Remove diacritics
      .replace(/đ/g, 'd') // Replace đ with d
      .replace(/Đ/g, 'D') // Replace Đ with D
      .trim()
  },
  
  /**
   * Highlight Vietnamese search terms in text
   */
  highlightSearch: (text: string, searchTerm: string): string => {
    if (!searchTerm.trim()) return text
    
    const normalizedSearch = vietnameseTextUtils.normalizeForSearch(searchTerm)
    const regex = new RegExp(`(${normalizedSearch})`, 'gi')
    
    return text.replace(regex, '<mark class="vietnamese-search-highlight">$1</mark>')
  },
  
  /**
   * Truncate Vietnamese text properly (avoiding breaking words)
   */
  truncate: (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text
    
    const truncated = text.substring(0, maxLength)
    const lastSpace = truncated.lastIndexOf(' ')
    
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...'
    }
    
    return truncated + '...'
  },
  
  /**
   * Count Vietnamese words
   */
  wordCount: (text: string): number => {
    return text.trim().split(/\s+/).filter(word => word.length > 0).length
  },
  
  /**
   * Extract Vietnamese keywords from text
   */
  extractKeywords: (text: string, maxKeywords: number = 5): string[] => {
    // Simple keyword extraction - split by spaces and filter common Vietnamese words
    const commonWords = new Set([
      'và', 'của', 'có', 'là', 'được', 'trong', 'với', 'để', 'một', 'này',
      'đó', 'các', 'những', 'khi', 'không', 'đã', 'sẽ', 'cho', 'về', 'từ'
    ])
    
    return text
      .toLowerCase()
      .split(/\s+/)
      .filter(word => word.length > 3 && !commonWords.has(word))
      .slice(0, maxKeywords)
  }
}

/**
 * Vietnamese UI utility functions
 */
export const vietnameseUI = {
  /**
   * Get Vietnamese class names for text styling
   */
  getTextClasses: (variant: 'body' | 'heading' | 'transcript' | 'warning' | 'ui' = 'body') => {
    const base = 'vietnamese-text vietnamese-text-diacritics'
    
    switch (variant) {
      case 'heading':
        return `${base} vietnamese-heading`
      case 'transcript':
        return `${base} vietnamese-transcript`
      case 'warning':
        return `${base} vietnamese-warning`
      case 'ui':
        return `${base} vietnamese-ui`
      default:
        return `${base} vietnamese-body`
    }
  },
  
  /**
   * Get sentiment-based styling
   */
  getSentimentClasses: (sentiment: keyof typeof VIETNAMESE_SENTIMENT_LABELS) => {
    const config = VIETNAMESE_SENTIMENT_LABELS[sentiment]
    return {
      text: `text-${config.color}-700`,
      background: `bg-${config.color}-50`,
      border: `border-${config.color}-200`,
      ring: `ring-${config.color}-500`
    }
  },
  
  /**
   * Format warning message in Vietnamese
   */
  formatWarningMessage: (sentiment: keyof typeof VIETNAMESE_SENTIMENT_LABELS, count: number) => {
    const { label } = VIETNAMESE_SENTIMENT_LABELS[sentiment]
    
    if (count === 1) {
      return `Phát hiện nội dung ${label.toLowerCase()}`
    }
    
    return `${count} cảnh báo ${label.toLowerCase()}`
  }
}

export default {
  VIETNAMESE_LOCALE,
  VIETNAMESE_UI_TEXT,
  VIETNAMESE_SENTIMENT_LABELS,
  formatVietnameseDateTime,
  formatVietnameseNumbers,
  vietnameseTextUtils,
  vietnameseUI
}