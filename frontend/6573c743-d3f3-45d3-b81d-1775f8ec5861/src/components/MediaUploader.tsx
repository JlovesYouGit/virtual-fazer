import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, Film, Image as ImageIcon, Loader2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';

interface MediaFile {
  file: File;
  preview: string;
  type: 'image' | 'video';
  duration?: number;
  dimensions?: { width: number; height: number };
}

interface MediaUploaderProps {
  onMediaSelect: (media: MediaFile[]) => void;
  maxFiles?: number;
  accept?: {
    images?: boolean;
    videos?: boolean;
  };
  maxSize?: number; // in MB
  className?: string;
}

export function MediaUploader({ 
  onMediaSelect, 
  maxFiles = 10,
  accept = { images: true, videos: true },
  maxSize = 100,
  className = ''
}: MediaUploaderProps) {
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const createMediaPreview = useCallback(async (file: File): Promise<MediaFile> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = async (e) => {
        const preview = e.target?.result as string;
        const type = file.type.startsWith('video/') ? 'video' : 'image';
        
        let dimensions: { width: number; height: number } | undefined;
        let duration: number | undefined;
        
        if (type === 'video') {
          // Get video dimensions and duration
          const video = document.createElement('video');
          video.preload = 'metadata';
          
          video.onloadedmetadata = () => {
            dimensions = { width: video.videoWidth, height: video.videoHeight };
            duration = video.duration;
            resolve({ file, preview, type, dimensions, duration });
          };
          
          video.onerror = () => reject(new Error('Failed to load video metadata'));
          video.src = preview;
        } else {
          // Get image dimensions
          const img = new Image();
          img.onload = () => {
            dimensions = { width: img.width, height: img.height };
            resolve({ file, preview, type, dimensions });
          };
          img.onerror = () => reject(new Error('Failed to load image'));
          img.src = preview;
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsDataURL(file);
    });
  }, []);

  const processFiles = useCallback(async (files: File[]) => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const processedFiles: MediaFile[] = [];
      
      for (const file of files) {
        // Validate file size
        if (file.size > maxSize * 1024 * 1024) {
          setError(`File ${file.name} exceeds ${maxSize}MB limit`);
          continue;
        }
        
        // Validate file type
        const isImage = file.type.startsWith('image/');
        const isVideo = file.type.startsWith('video/');
        
        if ((accept.images && isImage) || (accept.videos && isVideo)) {
          try {
            const mediaFile = await createMediaPreview(file);
            processedFiles.push(mediaFile);
          } catch (err) {
            console.error(`Failed to process ${file.name}:`, err);
            setError(`Failed to process ${file.name}`);
          }
        } else {
          setError(`Unsupported file type: ${file.type}`);
        }
      }
      
      setMediaFiles(prev => [...prev, ...processedFiles].slice(0, maxFiles));
      onMediaSelect([...mediaFiles, ...processedFiles].slice(0, maxFiles));
    } catch (err) {
      setError('Failed to process files');
      console.error(err);
    } finally {
      setIsProcessing(false);
    }
  }, [maxFiles, maxSize, accept, createMediaPreview, onMediaSelect]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    processFiles(acceptedFiles);
  }, [processFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': accept.images ? ['.jpg', '.jpeg', '.png', '.gif', '.webp'] : undefined,
      'video/*': accept.videos ? ['.mp4', '.mov', '.avi', '.webm'] : undefined,
    },
    maxFiles,
    multiple: true,
    disabled: isProcessing
  });

  const removeFile = useCallback((index: number) => {
    const newFiles = mediaFiles.filter((_, i) => i !== index);
    setMediaFiles(newFiles);
    onMediaSelect(newFiles);
  }, [mediaFiles, onMediaSelect]);

  const openFileDialog = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${isDragActive 
            ? 'border-brand bg-brand/10' 
            : 'border-dark-600 hover:border-gray-500 hover:bg-dark-800/50'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} ref={fileInputRef} />
        
        <div className="flex flex-col items-center space-y-4">
          {isProcessing ? (
            <>
              <Loader2 className="w-12 h-12 text-brand animate-spin" />
              <p className="text-gray-400">Processing media...</p>
            </>
          ) : (
            <>
              <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center">
                <Upload className="w-8 h-8 text-gray-400" />
              </div>
              <div>
                <p className="text-white font-medium">
                  {isDragActive ? 'Drop your media here' : 'Upload media'}
                </p>
                <p className="text-gray-400 text-sm mt-1">
                  Drag and drop or click to browse
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 text-xs text-gray-500">
                {accept.images && <span className="px-2 py-1 bg-dark-700 rounded">Photos</span>}
                {accept.videos && <span className="px-2 py-1 bg-dark-700 rounded">Videos</span>}
                <span className="px-2 py-1 bg-dark-700 rounded">Max {maxSize}MB</span>
                <span className="px-2 py-1 bg-dark-700 rounded">Max {maxFiles} files</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400 text-sm"
          >
            <AlertCircle size={16} />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              <X size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Media Preview Grid */}
      {mediaFiles.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-medium">Selected Media ({mediaFiles.length})</h3>
            <button
              onClick={() => {
                setMediaFiles([]);
                onMediaSelect([]);
              }}
              className="text-gray-400 hover:text-white text-sm"
            >
              Clear all
            </button>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {mediaFiles.map((media, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="relative group aspect-square rounded-lg overflow-hidden bg-dark-800"
              >
                {media.type === 'video' ? (
                  <video
                    src={media.preview}
                    className="w-full h-full object-cover"
                    muted
                    loop
                    playsInline
                  />
                ) : (
                  <img
                    src={media.preview}
                    alt="Upload preview"
                    className="w-full h-full object-cover"
                  />
                )}
                
                {/* Media Type Badge */}
                <div className="absolute top-2 left-2">
                  <div className="p-1.5 bg-black/50 rounded-full">
                    {media.type === 'video' ? (
                      <Film size={12} className="text-white" />
                    ) : (
                      <ImageIcon size={12} className="text-white" />
                    )}
                  </div>
                </div>
                
                {/* Remove Button */}
                <button
                  onClick={() => removeFile(index)}
                  className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X size={12} className="text-white" />
                </button>
                
                {/* Media Info Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="text-xs text-white">
                    {media.type === 'video' && media.duration && (
                      <div>Duration: {Math.round(media.duration)}s</div>
                    )}
                    {media.dimensions && (
                      <div>{media.dimensions.width} × {media.dimensions.height}</div>
                    )}
                    <div>{(media.file.size / 1024 / 1024).toFixed(1)} MB</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Action Button */}
      {mediaFiles.length > 0 && (
        <button
          onClick={openFileDialog}
          className="w-full py-3 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors flex items-center justify-center gap-2"
        >
          <Upload size={20} />
          Add More Media
        </button>
      )}
    </div>
  );
}
