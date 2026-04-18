import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Camera, Image, Type, Send, Plus, Palette, 
  Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight
} from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { storiesApi, CreateStoryData } from '../services/storiesApi';

interface StoryCreatorProps {
  onClose: () => void;
  onSuccess?: () => void;
  initialType?: 'image' | 'video' | 'text';
}

export function StoryCreator({ 
  onClose, 
  onSuccess, 
  initialType = 'image' 
}: StoryCreatorProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [contentType, setContentType] = useState<'image' | 'video' | 'text'>(initialType);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [mediaPreview, setMediaPreview] = useState<string>('');
  const [textContent, setTextContent] = useState('');
  const [caption, setCaption] = useState('');
  const [backgroundColor, setBackgroundColor] = useState('#000000');
  const [textColor, setTextColor] = useState('#FFFFFF');
  const [hashtags, setHashtags] = useState('');
  const [mentions, setMentions] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Create story mutation
  const createStoryMutation = useMutation({
    mutationFn: (data: CreateStoryData) => storiesApi.createStory(data),
    onSuccess: (response) => {
      setIsCreating(false);
      queryClient.invalidateQueries({ queryKey: ['stories'] });
      onSuccess?.();
      onClose();
    },
    onError: () => {
      setIsCreating(false);
    }
  });

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setMediaFile(file);
      const preview = URL.createObjectURL(file);
      setMediaPreview(preview);
    }
  }, []);

  const handleRemoveMedia = useCallback(() => {
    setMediaFile(null);
    setMediaPreview('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const handleCreateStory = useCallback(() => {
    if (!user) return;

    // Validation
    if (contentType === 'text' && !textContent.trim()) {
      alert('Please enter text content');
      return;
    }

    if ((contentType === 'image' || contentType === 'video') && !mediaFile) {
      alert('Please select a media file');
      return;
    }

    setIsCreating(true);

    const data: CreateStoryData = {
      content_type: contentType,
      caption: caption.trim(),
      hashtags: hashtags.trim(),
      mentions: mentions.trim(),
      background_color: backgroundColor,
      text_color: textColor
    };

    if (contentType === 'text') {
      data.text_content = textContent.trim();
    } else if (mediaFile) {
      data.media_file = mediaFile;
    }

    createStoryMutation.mutate(data);
  }, [contentType, textContent, mediaFile, caption, hashtags, mentions, backgroundColor, textColor, user, createStoryMutation]);

  const renderContentCreator = () => {
    switch (contentType) {
      case 'image':
      case 'video':
        return (
          <div className="space-y-4">
            {/* Media upload area */}
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
              {mediaPreview ? (
                <div className="relative">
                  {contentType === 'image' ? (
                    <img 
                      src={mediaPreview} 
                      alt="Preview" 
                      className="w-full h-64 object-contain rounded-lg"
                    />
                  ) : (
                    <video 
                      src={mediaPreview} 
                      className="w-full h-64 object-contain rounded-lg"
                      controls
                    />
                  )}
                  <button
                    onClick={handleRemoveMedia}
                    className="absolute top-2 right-2 p-2 bg-red-500 text-white rounded-full hover:bg-red-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto">
                    <Camera size={32} className="text-gray-400" />
                  </div>
                  <div>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      Upload {contentType === 'image' ? 'Image' : 'Video'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {contentType === 'image' ? 'JPG, PNG, GIF up to 10MB' : 'MP4, MOV, WebM up to 100MB'}
                    </p>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={contentType === 'image' ? 'image/*' : 'video/*'}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover"
                  >
                    Choose File
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      
      case 'text':
        return (
          <div className="space-y-4">
            {/* Text content */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Text Content
              </label>
              <textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Write your story text..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                rows={4}
                maxLength={2000}
              />
              <div className="text-xs text-gray-500 dark:text-gray-400 text-right">
                {textContent.length}/2000
              </div>
            </div>

            {/* Text formatting options */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Text Style
              </label>
              <div className="flex gap-2">
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <Bold size={16} />
                </button>
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <Italic size={16} />
                </button>
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <Underline size={16} />
                </button>
                <div className="w-px bg-gray-300 dark:border-gray-600 mx-2" />
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <AlignLeft size={16} />
                </button>
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <AlignCenter size={16} />
                </button>
                <button className="p-2 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                  <AlignRight size={16} />
                </button>
              </div>
            </div>

            {/* Color options */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Background Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={backgroundColor}
                    onChange={(e) => setBackgroundColor(e.target.value)}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={backgroundColor}
                    onChange={(e) => setBackgroundColor(e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm"
                    placeholder="#000000"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Text Color
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={textColor}
                    onChange={(e) => setTextColor(e.target.value)}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={textColor}
                    onChange={(e) => setTextColor(e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-sm"
                    placeholder="#FFFFFF"
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Preview
              </label>
              <div 
                className="w-full h-32 rounded-lg flex items-center justify-center p-4"
                style={{ backgroundColor, color: textColor }}
              >
                <p className="text-lg font-medium text-center">
                  {textContent || 'Your text will appear here...'}
                </p>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-gray-900 rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Create Story
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content type selector */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex gap-2">
            <button
              onClick={() => setContentType('image')}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                contentType === 'image'
                  ? 'bg-brand text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <Image size={16} className="inline mr-2" />
              Image
            </button>
            <button
              onClick={() => setContentType('video')}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                contentType === 'video'
                  ? 'bg-brand text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <Camera size={16} className="inline mr-2" />
              Video
            </button>
            <button
              onClick={() => setContentType('text')}
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                contentType === 'text'
                  ? 'bg-brand text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              <Type size={16} className="inline mr-2" />
              Text
            </button>
          </div>
        </div>

        {/* Content creator */}
        <div className="p-4">
          {renderContentCreator()}
        </div>

        {/* Additional options */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-4">
          {/* Caption */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Caption (optional)
            </label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder="Add a caption to your story..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
              rows={2}
              maxLength={2000}
            />
            <div className="text-xs text-gray-500 dark:text-gray-400 text-right">
              {caption.length}/2000
            </div>
          </div>

          {/* Hashtags and mentions */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Hashtags
              </label>
              <input
                type="text"
                value={hashtags}
                onChange={(e) => setHashtags(e.target.value)}
                placeholder="tag1, tag2, tag3"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Mentions
              </label>
              <input
                type="text"
                value={mentions}
                onChange={(e) => setMentions(e.target.value)}
                placeholder="user1, user2, user3"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreateStory}
            disabled={isCreating || createStoryMutation.isPending}
            className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isCreating || createStoryMutation.isPending ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send size={16} />
            )}
            Create Story
          </button>
        </div>
      </motion.div>
    </div>
  );
}
