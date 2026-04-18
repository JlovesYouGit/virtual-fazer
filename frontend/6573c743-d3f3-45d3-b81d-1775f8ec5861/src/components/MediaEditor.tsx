import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  RotateCw, 
  Crop, 
  Palette, 
  Sun, 
  Contrast, 
  Sliders, 
  Download,
  Undo,
  Redo,
  Zap,
  Image as ImageIcon,
  Film,
  Check
} from 'lucide-react';

interface MediaEditorProps {
  file: File;
  preview: string;
  type: 'image' | 'video';
  onSave: (editedFile: File, metadata: any) => void;
  onCancel: () => void;
}

interface Filter {
  name: string;
  icon: React.ReactNode;
  apply: (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => void;
}

interface Adjustment {
  brightness: number;
  contrast: number;
  saturation: number;
  blur: number;
  sepia: number;
}

export function MediaEditor({ file, preview, type, onSave, onCancel }: MediaEditorProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string>('original');
  const [adjustments, setAdjustments] = useState<Adjustment>({
    brightness: 0,
    contrast: 0,
    saturation: 0,
    blur: 0,
    sepia: 0
  });
  const [rotation, setRotation] = useState(0);
  const [cropMode, setCropMode] = useState(false);
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Filters
  const filters: Filter[] = [
    {
      name: 'original',
      icon: <ImageIcon size={16} />,
      apply: (canvas, ctx) => {
        ctx.filter = 'none';
      }
    },
    {
      name: 'vintage',
      icon: <Sun size={16} />,
      apply: (canvas, ctx) => {
        ctx.filter = 'sepia(0.5) contrast(1.2) brightness(1.1)';
      }
    },
    {
      name: 'dramatic',
      icon: <Contrast size={16} />,
      apply: (canvas, ctx) => {
        ctx.filter = 'contrast(1.4) saturate(1.3) brightness(0.9)';
      }
    },
    {
      name: 'warm',
      icon: <Palette size={16} />,
      apply: (canvas, ctx) => {
        ctx.filter = 'sepia(0.2) saturate(1.2) brightness(1.05) hue-rotate(10deg)';
      }
    },
    {
      name: 'cool',
      icon: <Zap size={16} />,
      apply: (canvas, ctx) => {
        ctx.filter = 'hue-rotate(180deg) saturate(1.1) brightness(1.05)';
      }
    }
  ];

  // Apply adjustments to filter string
  const getFilterString = useCallback(() => {
    const filter = filters.find(f => f.name === selectedFilter);
    let filterString = filter ? 'none' : 'none';
    
    // Apply selected filter
    if (filter) {
      const tempCanvas = document.createElement('canvas');
      const tempCtx = tempCanvas.getContext('2d');
      if (tempCtx) {
        filter.apply(tempCanvas, tempCtx);
        filterString = tempCtx.filter;
      }
    }
    
    // Apply adjustments
    const adjustments_str = [
      adjustments.brightness !== 0 ? `brightness(${1 + adjustments.brightness})` : '',
      adjustments.contrast !== 0 ? `contrast(${1 + adjustments.contrast})` : '',
      adjustments.saturation !== 0 ? `saturate(${1 + adjustments.saturation})` : '',
      adjustments.blur !== 0 ? `blur(${adjustments.blur}px)` : '',
      adjustments.sepia !== 0 ? `sepia(${adjustments.sepia})` : ''
    ].filter(Boolean).join(' ');
    
    return adjustments_str || filterString;
  }, [selectedFilter, adjustments, filters]);

  // Load and display media
  const loadMedia = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    if (type === 'image') {
      const img = new Image();
      img.onload = () => {
        // Set canvas dimensions
        canvas.width = img.width;
        canvas.height = img.height;
        
        // Clear and draw
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.save();
        
        // Apply rotation
        if (rotation !== 0) {
          ctx.translate(canvas.width / 2, canvas.height / 2);
          ctx.rotate((rotation * Math.PI) / 180);
          ctx.translate(-canvas.width / 2, -canvas.height / 2);
        }
        
        // Apply filter
        ctx.filter = getFilterString();
        
        // Draw image
        ctx.drawImage(img, 0, 0);
        ctx.restore();
        
        // Save to history
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        setHistory(prev => [...prev.slice(0, historyIndex + 1), imageData]);
        setHistoryIndex(prev => prev + 1);
      };
      img.src = preview;
    } else {
      const video = videoRef.current;
      if (video) {
        video.onloadedmetadata = () => {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          
          const drawFrame = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.save();
            
            if (rotation !== 0) {
              ctx.translate(canvas.width / 2, canvas.height / 2);
              ctx.rotate((rotation * Math.PI) / 180);
              ctx.translate(-canvas.width / 2, -canvas.height / 2);
            }
            
            ctx.filter = getFilterString();
            ctx.drawImage(video, 0, 0);
            ctx.restore();
          };
          
          video.currentTime = 1; // Seek to 1 second for thumbnail
          video.onseeked = drawFrame;
        };
        video.src = preview;
      }
    }
  }, [preview, type, rotation, getFilterString, historyIndex]);

  useEffect(() => {
    loadMedia();
  }, [loadMedia]);

  // Undo/Redo functionality
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (canvas && ctx) {
        const previousState = history[historyIndex - 1];
        ctx.putImageData(previousState, 0, 0);
        setHistoryIndex(prev => prev - 1);
      }
    }
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (canvas && ctx) {
        const nextState = history[historyIndex + 1];
        ctx.putImageData(nextState, 0, 0);
        setHistoryIndex(prev => prev + 1);
      }
    }
  }, [history, historyIndex]);

  // Rotate image
  const rotate = useCallback((degrees: number) => {
    setRotation(prev => (prev + degrees) % 360);
  }, []);

  // Save edited media
  const save = useCallback(async () => {
    setIsProcessing(true);
    
    try {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      // Convert canvas to blob
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        
        // Create new file from blob
        const editedFile = new File([blob], file.name, {
          type: file.type,
          lastModified: Date.now()
        });
        
        // Extract metadata
        const metadata = {
          originalName: file.name,
          originalSize: file.size,
          editedSize: blob.size,
          dimensions: {
            width: canvas.width,
            height: canvas.height
          },
          rotation,
          filter: selectedFilter,
          adjustments,
          editedAt: new Date().toISOString()
        };
        
        onSave(editedFile, metadata);
        setIsProcessing(false);
      }, file.type, 0.9);
      
    } catch (error) {
      console.error('Error saving edited media:', error);
      setIsProcessing(false);
    }
  }, [file, canvas, rotation, selectedFilter, adjustments, onSave]);

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
      <div className="bg-dark-800 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            {type === 'video' ? <Film size={20} /> : <ImageIcon size={20} />}
            Edit {type === 'video' ? 'Video' : 'Photo'}
          </h2>
          
          <div className="flex items-center gap-2">
            {/* Undo/Redo */}
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Undo size={16} />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Redo size={16} />
            </button>
            
            {/* Actions */}
            <button
              onClick={onCancel}
              className="px-4 py-2 text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={save}
              disabled={isProcessing}
              className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Processing...
                </>
              ) : (
                <>
                  <Check size={16} />
                  Save
                </>
              )}
            </button>
          </div>
        </div>

        <div className="flex h-[calc(90vh-80px)]">
          {/* Canvas Area */}
          <div className="flex-1 flex items-center justify-center p-8 bg-dark-900">
            <div className="relative max-w-full max-h-full">
              <canvas
                ref={canvasRef}
                className="max-w-full max-h-full object-contain"
              />
              {type === 'video' && (
                <video
                  ref={videoRef}
                  className="hidden"
                  muted
                  playsInline
                />
              )}
              
              {/* Crop Mode Overlay */}
              {cropMode && (
                <div className="absolute inset-0 border-2 border-brand pointer-events-none">
                  <div className="absolute top-2 left-2 bg-brand text-white text-xs px-2 py-1 rounded">
                    Drag to crop
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Controls Sidebar */}
          <div className="w-80 bg-dark-800 border-l border-dark-700 overflow-y-auto">
            <div className="p-4 space-y-6">
              {/* Filters */}
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <Palette size={16} />
                  Filters
                </h3>
                <div className="grid grid-cols-3 gap-2">
                  {filters.map((filter) => (
                    <button
                      key={filter.name}
                      onClick={() => setSelectedFilter(filter.name)}
                      className={`p-3 rounded-lg border transition-all ${
                        selectedFilter === filter.name
                          ? 'border-brand bg-brand/20'
                          : 'border-dark-600 hover:border-gray-500'
                      }`}
                    >
                      <div className="flex flex-col items-center gap-1">
                        {filter.icon}
                        <span className="text-xs text-gray-300 capitalize">{filter.name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Adjustments */}
              <div>
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <Sliders size={16} />
                  Adjustments
                </h3>
                <div className="space-y-4">
                  {Object.entries(adjustments).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-300 capitalize">{key}</span>
                        <span className="text-brand">{Math.round(value * 100)}%</span>
                      </div>
                      <input
                        type="range"
                        min="-1"
                        max="1"
                        step="0.01"
                        value={value}
                        onChange={(e) => setAdjustments(prev => ({
                          ...prev,
                          [key]: parseFloat(e.target.value)
                        }))}
                        className="w-full"
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Tools */}
              <div>
                <h3 className="text-white font-medium mb-3">Tools</h3>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => rotate(90)}
                    className="p-3 bg-dark-700 text-white rounded-lg hover:bg-dark-600 flex items-center justify-center gap-2"
                  >
                    <RotateCw size={16} />
                    Rotate
                  </button>
                  <button
                    onClick={() => setCropMode(!cropMode)}
                    className={`p-3 rounded-lg flex items-center justify-center gap-2 ${
                      cropMode
                        ? 'bg-brand text-white'
                        : 'bg-dark-700 text-white hover:bg-dark-600'
                    }`}
                  >
                    <Crop size={16} />
                    Crop
                  </button>
                </div>
              </div>

              {/* Info */}
              <div className="bg-dark-700 rounded-lg p-3">
                <h4 className="text-white font-medium mb-2">File Info</h4>
                <div className="space-y-1 text-sm text-gray-400">
                  <div>Name: {file.name}</div>
                  <div>Size: {(file.size / 1024 / 1024).toFixed(2)} MB</div>
                  <div>Type: {file.type}</div>
                  {type === 'video' && (
                    <div>Duration: Loading...</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
