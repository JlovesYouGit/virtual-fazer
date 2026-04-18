import React, { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Image as ImageIcon, 
  Film, 
  MapPin, 
  Users, 
  Send, 
  Loader2,
  ArrowLeft,
  Sparkles,
  Eye,
  Heart,
  MessageCircle,
  Share2
} from 'lucide-react';
import { MediaUploader } from './MediaUploader';
import { UploadApi, UploadResponse, UploadProgress } from '../services/uploadApi';
import { feedApi } from '../services/feedApi';
import { neuralApi } from '../services/neuralApi';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from './LoadingStates';

interface MediaFile {
  file: File;
  preview: string;
  type: 'image' | 'video';
  duration?: number;
  dimensions?: { width: number; height: number };
}

export function CreatePostPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [caption, setCaption] = useState('');
  const [location, setLocation] = useState('');
  const [taggedUsers, setTaggedUsers] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(true);
  const [allowComments, setAllowComments] = useState(true);
  const [currentStep, setCurrentStep] = useState<'upload' | 'edit' | 'details' | 'share'>('upload');
  const [selectedMediaIndex, setSelectedMediaIndex] = useState(0);
  const [uploadProgress, setUploadProgress] = useState<Record<number, UploadProgress>>({});
  
  // Get user's neural profile for optimization suggestions
  const { data: neuralProfile } = useQuery({
    queryKey: ['neuralProfile'],
    queryFn: neuralApi.getNeuralProfile,
    enabled: !!user,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      const results = await UploadApi.uploadMultipleFiles(
        files,
        (fileIndex, progress) => {
          setUploadProgress(prev => ({ ...prev, [fileIndex]: progress }));
        },
        (fileIndex, result) => {
          console.log(`File ${fileIndex} uploaded successfully:`, result);
        }
      );
      return results;
    },
    onSuccess: (uploadedFiles) => {
      console.log('All files uploaded:', uploadedFiles);
      setCurrentStep('edit');
    },
    onError: (error) => {
      console.error('Upload failed:', error);
    }
  });

  // Create post mutation
  const createPostMutation = useMutation({
    mutationFn: async (postData: {
      media_ids: string[];
      caption: string;
      location?: string;
      tagged_users?: string[];
      is_public: boolean;
      allow_comments: boolean;
    }) => {
      return feedApi.createReel(postData);
    },
    onSuccess: (newPost) => {
      console.log('Post created successfully:', newPost);
      setCurrentStep('share');
      
      // Track post creation for neural algorithm
      if (neuralProfile) {
        neuralApi.trackUserAction({
          action_type: 'create_post',
          target_type: 'post',
          target_id: newPost.id,
          metadata: {
            media_count: postData.media_ids.length,
            caption_length: postData.caption.length,
            has_location: !!postData.location,
            tagged_count: postData.tagged_users?.length || 0,
            neural_category: neuralProfile.category
          }
        });
      }
    },
    onError: (error) => {
      console.error('Post creation failed:', error);
    }
  });

  const handleMediaSelect = useCallback((files: MediaFile[]) => {
    setMediaFiles(files);
    if (files.length > 0) {
      setCurrentStep('edit');
    }
  }, []);

  const handleUpload = useCallback(async () => {
    if (mediaFiles.length === 0) return;
    
    const files = mediaFiles.map(m => m.file);
    uploadMutation.mutate(files);
  }, [mediaFiles, uploadMutation]);

  const handleCreatePost = useCallback(() => {
    if (mediaFiles.length === 0) return;
    
    const mediaIds = mediaFiles.map(m => m.file.name); // In real implementation, use uploaded file IDs
    
    createPostMutation.mutate({
      media_ids: mediaIds,
      caption,
      location: location || undefined,
      tagged_users: taggedUsers,
      is_public: isPublic,
      allow_comments: allowComments,
    });
  }, [mediaFiles, caption, location, taggedUsers, isPublic, allowComments, createPostMutation]);

  const getOptimizationSuggestions = useCallback(() => {
    if (!neuralProfile) return [];
    
    const suggestions = [];
    
    // Time-based suggestions
    const currentHour = new Date().getHours();
    if (currentHour >= 19 && currentHour <= 21) {
      suggestions.push('Peak engagement time (7-9 PM)');
    }
    
    // Content type suggestions
    if (neuralProfile.category === 'creator') {
      suggestions.push('Add hashtags to increase reach');
    }
    
    // Engagement suggestions
    if (neuralProfile.behavior_patterns.includes('high_engagement')) {
      suggestions.push('Ask a question to boost comments');
    }
    
    return suggestions;
  }, [neuralProfile]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner text="Please login to create posts" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-dark-900/95 backdrop-blur-lg border-b border-dark-700">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-dark-800 rounded-full transition-colors"
              >
                <ArrowLeft size={20} className="text-white" />
              </button>
              <h1 className="text-xl font-semibold text-white">Create Post</h1>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Progress indicator */}
              <div className="flex items-center gap-1">
                {['upload', 'edit', 'details', 'share'].map((step, index) => (
                  <div
                    key={step}
                    className={`w-2 h-2 rounded-full ${
                      index <= ['upload', 'edit', 'details', 'share'].indexOf(currentStep)
                        ? 'bg-brand'
                        : 'bg-gray-600'
                    }`}
                  />
                ))}
              </div>
              
              {currentStep === 'edit' && (
                <button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending || mediaFiles.length === 0}
                  className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Send size={16} />
                      Next
                    </>
                  )}
                </button>
              )}
              
              {currentStep === 'details' && (
                <button
                  onClick={handleCreatePost}
                  disabled={createPostMutation.isPending}
                  className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {createPostMutation.isPending ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Posting...
                    </>
                  ) : (
                    <>
                      <Send size={16} />
                      Share
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content Area */}
          <div className="lg:col-span-2">
            {currentStep === 'upload' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-dark-800 rounded-xl p-6"
              >
                <h2 className="text-lg font-semibold text-white mb-4">Select Media</h2>
                <MediaUploader
                  onMediaSelect={handleMediaSelect}
                  maxFiles={10}
                  accept={{ images: true, videos: true }}
                  maxSize={100}
                />
                
                {/* Upload Progress */}
                {Object.keys(uploadProgress).length > 0 && (
                  <div className="mt-6 space-y-3">
                    <h3 className="text-white font-medium">Upload Progress</h3>
                    {Object.entries(uploadProgress).map(([index, progress]) => (
                      <div key={index} className="space-y-2">
                        <div className="flex justify-between text-sm text-gray-400">
                          <span>File {parseInt(index) + 1}</span>
                          <span>{progress.percentage}%</span>
                        </div>
                        <div className="w-full bg-dark-700 rounded-full h-2">
                          <div
                            className="bg-brand h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {currentStep === 'edit' && mediaFiles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Media Preview */}
                <div className="bg-dark-800 rounded-xl overflow-hidden">
                  <div className="aspect-square relative">
                    {mediaFiles[selectedMediaIndex].type === 'video' ? (
                      <video
                        src={mediaFiles[selectedMediaIndex].preview}
                        className="w-full h-full object-cover"
                        controls
                        muted
                        loop
                        playsInline
                      />
                    ) : (
                      <img
                        src={mediaFiles[selectedMediaIndex].preview}
                        alt="Preview"
                        className="w-full h-full object-cover"
                      />
                    )}
                    
                    {/* Media Type Badge */}
                    <div className="absolute top-4 left-4">
                      <div className="p-2 bg-black/50 rounded-full">
                        {mediaFiles[selectedMediaIndex].type === 'video' ? (
                          <Film size={16} className="text-white" />
                        ) : (
                          <ImageIcon size={16} className="text-white" />
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Multiple Files Navigation */}
                  {mediaFiles.length > 1 && (
                    <div className="p-4 flex gap-2 overflow-x-auto">
                      {mediaFiles.map((file, index) => (
                        <button
                          key={index}
                          onClick={() => setSelectedMediaIndex(index)}
                          className={`flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 ${
                            index === selectedMediaIndex ? 'border-brand' : 'border-transparent'
                          }`}
                        >
                          {file.type === 'video' ? (
                            <video
                              src={file.preview}
                              className="w-full h-full object-cover"
                              muted
                            />
                          ) : (
                            <img
                              src={file.preview}
                              alt={`Thumbnail ${index + 1}`}
                              className="w-full h-full object-cover"
                            />
                          )}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Caption Input */}
                <div className="bg-dark-800 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Caption</h3>
                  <textarea
                    value={caption}
                    onChange={(e) => setCaption(e.target.value)}
                    placeholder="Write a caption..."
                    className="w-full min-h-[120px] bg-dark-700 border border-dark-600 rounded-lg p-4 text-white placeholder-gray-400 resize-none focus:outline-none focus:border-brand"
                    maxLength={2200}
                  />
                  <div className="flex justify-between mt-2 text-sm text-gray-400">
                    <span>Add hashtags to increase visibility</span>
                    <span>{caption.length}/2200</span>
                  </div>
                </div>
              </motion.div>
            )}

            {currentStep === 'details' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Location */}
                <div className="bg-dark-800 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <MapPin size={20} />
                    Location
                  </h3>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="Add location"
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg p-3 text-white placeholder-gray-400 focus:outline-none focus:border-brand"
                  />
                </div>

                {/* Tag Users */}
                <div className="bg-dark-800 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Users size={20} />
                    Tag Users
                  </h3>
                  <input
                    type="text"
                    placeholder="Tag users (e.g., @username)"
                    className="w-full bg-dark-700 border border-dark-600 rounded-lg p-3 text-white placeholder-gray-400 focus:outline-none focus:border-brand"
                  />
                </div>

                {/* Privacy Settings */}
                <div className="bg-dark-800 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Privacy Settings</h3>
                  <div className="space-y-4">
                    <label className="flex items-center justify-between">
                      <span className="text-white">Public post</span>
                      <input
                        type="checkbox"
                        checked={isPublic}
                        onChange={(e) => setIsPublic(e.target.checked)}
                        className="w-5 h-5 text-brand bg-dark-700 border-dark-600 rounded focus:ring-brand"
                      />
                    </label>
                    <label className="flex items-center justify-between">
                      <span className="text-white">Allow comments</span>
                      <input
                        type="checkbox"
                        checked={allowComments}
                        onChange={(e) => setAllowComments(e.target.checked)}
                        className="w-5 h-5 text-brand bg-dark-700 border-dark-600 rounded focus:ring-brand"
                      />
                    </label>
                  </div>
                </div>
              </motion.div>
            )}

            {currentStep === 'share' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-dark-800 rounded-xl p-8 text-center"
              >
                <div className="w-16 h-16 bg-green-500/20 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <Send size={32} className="text-green-500" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Post Shared!</h2>
                <p className="text-gray-400 mb-6">Your content is now visible to other users</p>
                
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="text-center">
                    <Eye className="w-6 h-6 text-brand mx-auto mb-1" />
                    <div className="text-white font-semibold">0</div>
                    <div className="text-gray-400 text-sm">Views</div>
                  </div>
                  <div className="text-center">
                    <Heart className="w-6 h-6 text-brand mx-auto mb-1" />
                    <div className="text-white font-semibold">0</div>
                    <div className="text-gray-400 text-sm">Likes</div>
                  </div>
                  <div className="text-center">
                    <MessageCircle className="w-6 h-6 text-brand mx-auto mb-1" />
                    <div className="text-white font-semibold">0</div>
                    <div className="text-gray-400 text-sm">Comments</div>
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <button
                    onClick={() => navigate('/feed')}
                    className="flex-1 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover transition-colors"
                  >
                    View Feed
                  </button>
                  <button
                    onClick={() => {
                      // Reset form for new post
                      setMediaFiles([]);
                      setCaption('');
                      setLocation('');
                      setTaggedUsers([]);
                      setCurrentStep('upload');
                    }}
                    className="flex-1 py-2 bg-dark-700 text-white rounded-lg hover:bg-dark-600 transition-colors"
                  >
                    Create Another
                  </button>
                </div>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Neural Optimization Suggestions */}
            {neuralProfile && currentStep === 'details' && (
              <div className="bg-dark-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Sparkles size={20} className="text-brand" />
                  AI Optimization
                </h3>
                <div className="space-y-3">
                  {getOptimizationSuggestions().map((suggestion, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <div className="w-2 h-2 bg-brand rounded-full mt-2 flex-shrink-0" />
                      <p className="text-sm text-gray-300">{suggestion}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Post Preview */}
            {mediaFiles.length > 0 && currentStep !== 'share' && (
              <div className="bg-dark-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Preview</h3>
                <div className="space-y-4">
                  {/* Media Preview */}
                  <div className="aspect-square rounded-lg overflow-hidden bg-dark-700">
                    {mediaFiles[0].type === 'video' ? (
                      <video
                        src={mediaFiles[0].preview}
                        className="w-full h-full object-cover"
                        muted
                      />
                    ) : (
                      <img
                        src={mediaFiles[0].preview}
                        alt="Preview"
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                  
                  {/* Caption Preview */}
                  {caption && (
                    <div className="text-sm text-gray-300">
                      <span className="font-medium text-white">{user.username}</span> {caption}
                    </div>
                  )}
                  
                  {/* Engagement Preview */}
                  <div className="flex items-center gap-4 text-gray-400">
                    <Heart size={16} />
                    <span>Predicted: High engagement</span>
                  </div>
                </div>
              </div>
            )}

            {/* Algorithm Impact */}
            {neuralProfile && currentStep === 'details' && (
              <div className="bg-dark-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Algorithm Impact</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Reach Score</span>
                    <span className="text-brand font-semibold">85%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Engagement Rate</span>
                    <span className="text-brand font-semibold">12%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Category Match</span>
                    <span className="text-brand font-semibold">{neuralProfile.category}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Best Time to Post</span>
                    <span className="text-brand font-semibold">7-9 PM</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
