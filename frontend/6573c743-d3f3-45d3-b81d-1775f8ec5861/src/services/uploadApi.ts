import { apiClient } from '../lib/apiClient';

export interface UploadResponse {
  id: string;
  url: string;
  thumbnail_url?: string;
  file_type: 'image' | 'video';
  file_size: number;
  dimensions?: {
    width: number;
    height: number;
  };
  duration?: number;
  upload_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export class UploadApi {
  // Get upload URL and credentials from backend
  static async getUploadUrl(fileType: 'image' | 'video', fileName: string, fileSize: number) {
    return apiClient.post<{
      upload_url: string;
      file_id: string;
      headers: Record<string, string>;
      max_size: number;
    }>('/upload/init/', {
      file_type: fileType,
      file_name: fileName,
      file_size: fileSize,
    });
  }

  // Upload file directly to storage (S3, CloudFront, etc.)
  static async uploadFile(
    uploadUrl: string,
    file: File,
    headers: Record<string, string>,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress: UploadProgress = {
              loaded: event.loaded,
              total: event.total,
              percentage: Math.round((event.loaded / event.total) * 100),
            };
            onProgress(progress);
          }
        });
      }
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });
      
      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed due to network error'));
      });
      
      xhr.open('PUT', uploadUrl);
      
      // Set required headers
      Object.entries(headers).forEach(([key, value]) => {
        xhr.setRequestHeader(key, value);
      });
      
      xhr.send(file);
    });
  }

  // Confirm upload completion and trigger backend processing
  static async confirmUpload(fileId: string, metadata: {
    original_name: string;
    mime_type: string;
    dimensions?: { width: number; height: number };
    duration?: number;
  }) {
    return apiClient.post<UploadResponse>(`/upload/confirm/${fileId}/`, metadata);
  }

  // Get upload status
  static async getUploadStatus(fileId: string) {
    return apiClient.get<UploadResponse>(`/upload/status/${fileId}/`);
  }

  // Delete uploaded file
  static async deleteFile(fileId: string) {
    return apiClient.delete(`/upload/file/${fileId}/`);
  }

  // Get file info
  static async getFileInfo(fileId: string) {
    return apiClient.get<UploadResponse>(`/upload/file/${fileId}/`);
  }

  // Batch upload multiple files
  static async uploadMultipleFiles(
    files: File[],
    onProgress?: (fileIndex: number, progress: UploadProgress) => void,
    onFileComplete?: (fileIndex: number, result: UploadResponse) => void
  ): Promise<UploadResponse[]> {
    const results: UploadResponse[] = [];
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const fileType = file.type.startsWith('video/') ? 'video' : 'image';
      
      try {
        // Get upload URL
        const { data: uploadData } = await this.getUploadUrl(fileType, file.name, file.size);
        
        // Upload file
        await this.uploadFile(
          uploadData.upload_url,
          file,
          uploadData.headers,
          (progress) => onProgress?.(i, progress)
        );
        
        // Extract metadata
        const metadata = await this.extractFileMetadata(file);
        
        // Confirm upload
        const { data: uploadResult } = await this.confirmUpload(uploadData.file_id, {
          original_name: file.name,
          mime_type: file.type,
          ...metadata,
        });
        
        results.push(uploadResult);
        onFileComplete?.(i, uploadResult);
        
      } catch (error) {
        console.error(`Failed to upload file ${file.name}:`, error);
        throw error;
      }
    }
    
    return results;
  }

  // Extract metadata from file (dimensions, duration, etc.)
  private static async extractFileMetadata(file: File): Promise<{
    dimensions?: { width: number; height: number };
    duration?: number;
  }> {
    return new Promise((resolve) => {
      const metadata: {
        dimensions?: { width: number; height: number };
        duration?: number;
      } = {};
      
      if (file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.preload = 'metadata';
        
        video.onloadedmetadata = () => {
          metadata.dimensions = { width: video.videoWidth, height: video.videoHeight };
          metadata.duration = video.duration;
          resolve(metadata);
        };
        
        video.onerror = () => resolve(metadata);
        video.src = URL.createObjectURL(file);
      } else if (file.type.startsWith('image/')) {
        const img = new Image();
        
        img.onload = () => {
          metadata.dimensions = { width: img.width, height: img.height };
          resolve(metadata);
        };
        
        img.onerror = () => resolve(metadata);
        img.src = URL.createObjectURL(file);
      } else {
        resolve(metadata);
      }
    });
  }

  // Generate thumbnail for video
  static async generateVideoThumbnail(file: File, time: number = 1): Promise<string> {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        reject(new Error('Failed to get canvas context'));
        return;
      }
      
      video.onloadedmetadata = () => {
        video.currentTime = time;
      };
      
      video.onseeked = () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        const thumbnail = canvas.toDataURL('image/jpeg', 0.8);
        URL.revokeObjectURL(video.src);
        resolve(thumbnail);
      };
      
      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        reject(new Error('Failed to load video for thumbnail generation'));
      };
      
      video.src = URL.createObjectURL(file);
    });
  }

  // Process uploaded file (apply filters, compress, etc.)
  static async processFile(fileId: string, options: {
    compress?: boolean;
    quality?: number;
    filters?: string[];
    format?: string;
  }) {
    return apiClient.post<UploadResponse>(`/upload/process/${fileId}/`, options);
  }

  // Get user's uploaded files
  static async getUserUploads(params: {
    page?: number;
    limit?: number;
    file_type?: 'image' | 'video';
    upload_status?: string;
  } = {}) {
    return apiClient.get<{
      results: UploadResponse[];
      count: number;
      next: string | null;
      previous: string | null;
    }>('/upload/user-files/', { params });
  }

  // Get upload analytics
  static async getUploadAnalytics() {
    return apiClient.get<{
      total_uploads: number;
      total_size: number;
      file_type_breakdown: {
        images: number;
        videos: number;
      };
      upload_trends: {
        date: string;
        count: number;
      }[];
    }>('/upload/analytics/');
  }
}
