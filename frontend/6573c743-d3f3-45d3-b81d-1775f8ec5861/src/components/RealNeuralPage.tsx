import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { neuralApi, NeuralCategory, UserMatch, AutoFollowSettings } from '../services/neuralApi';
import { useAuth } from '../context/AuthContext';
import { 
  Brain, 
  Users, 
  TrendingUp, 
  Settings, 
  Zap, 
  Target, 
  Star,
  ChevronRight,
  RefreshCw,
  Check,
  X
} from 'lucide-react';
import { motion } from 'framer-motion';

export function RealNeuralPage() {
  const { user } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [autoFollowSettings, setAutoFollowSettings] = useState<AutoFollowSettings>({
    enabled: false,
    confidence_threshold: 0.8,
    max_follows_per_day: 10,
    categories: []
  });

  // Get user's neural profile from backend
  const { data: neuralProfile, isLoading: profileLoading } = useQuery({
    queryKey: ['neuralProfile'],
    queryFn: neuralApi.getNeuralProfile,
    enabled: !!user,
  });

  // Get neural categories from backend
  const { data: categories = [], isLoading: categoriesLoading } = useQuery({
    queryKey: ['neuralCategories'],
    queryFn: neuralApi.getCategories,
  });

  // Get user recommendations from backend
  const { data: recommendations = [], isLoading: recommendationsLoading, refetch: refetchRecommendations } = useQuery({
    queryKey: ['neuralRecommendations', selectedCategory],
    queryFn: () => neuralApi.getRecommendations(20),
    enabled: !!user,
  });

  // Get auto-follow settings from backend
  const { data: currentSettings, isLoading: settingsLoading } = useQuery({
    queryKey: ['autoFollowSettings'],
    queryFn: neuralApi.getAutoFollowSettings,
    enabled: !!user,
  });

  // Get behavioral insights from backend
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['behavioralInsights'],
    queryFn: neuralApi.getBehavioralInsights,
    enabled: !!user,
  });

  // Auto-follow mutation to backend
  const autoFollowMutation = useMutation({
    mutationFn: neuralApi.autoFollow,
    onSuccess: (data) => {
      console.log(`Auto-follow completed: ${data.followed_users} users followed, ${data.skipped_users} skipped`);
      refetchRecommendations();
    },
  });

  // Update auto-follow settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: neuralApi.updateAutoFollowSettings,
    onSuccess: (newSettings) => {
      setAutoFollowSettings(newSettings);
    },
  });

  // Follow user mutation
  const followUserMutation = useMutation({
    mutationFn: (userId: string) => neuralApi.trackUserAction({
      action_type: 'follow',
      target_type: 'user',
      target_id: userId,
      metadata: { source: 'neural_recommendations' }
    }),
  });

  // Initialize settings when loaded from backend
  React.useEffect(() => {
    if (currentSettings && !settingsLoading) {
      setAutoFollowSettings(currentSettings);
    }
  }, [currentSettings, settingsLoading]);

  if (profileLoading || categoriesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Brain className="text-brand" size={32} />
          Neural Interface
        </h1>
        <p className="text-gray-400">
          AI-powered user categorization and intelligent recommendations
        </p>
      </div>

      {/* Neural Profile Overview */}
      {neuralProfile && (
        <div className="bg-dark-800 border border-dark-600 rounded-xl p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">Your Neural Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto mb-3 flex items-center justify-center">
                <Brain size={32} className="text-white" />
              </div>
              <h3 className="font-semibold text-white">{neuralProfile.category}</h3>
              <p className="text-sm text-gray-400">Primary Category</p>
              <div className="mt-2">
                <div className="text-2xl font-bold text-brand">
                  {Math.round(neuralProfile.confidence_score * 100)}%
                </div>
                <p className="text-xs text-gray-500">Confidence</p>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-2">Behavior Patterns</h4>
              <div className="flex flex-wrap gap-2">
                {neuralProfile.behavior_patterns.map((pattern, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-dark-700 text-gray-300 rounded-full text-sm"
                  >
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-2">Interests</h4>
              <div className="flex flex-wrap gap-2">
                {neuralProfile.interests.slice(0, 5).map((interest, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-brand/20 text-brand rounded-full text-sm"
                  >
                    {interest}
                  </span>
                ))}
                {neuralProfile.interests.length > 5 && (
                  <span className="px-3 py-1 bg-gray-700 text-gray-400 rounded-full text-sm">
                    +{neuralProfile.interests.length - 5} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Category Filter */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-white mb-4">Explore by Category</h2>
        <div className="flex gap-3 overflow-x-auto pb-2">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
              !selectedCategory
                ? 'bg-brand text-white'
                : 'bg-dark-800 text-gray-300 hover:bg-dark-700'
            }`}
          >
            All Categories
          </button>
          {categories.map((category: NeuralCategory) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.name)}
              className={`px-4 py-2 rounded-full whitespace-nowrap transition-colors flex items-center gap-2 ${
                selectedCategory === category.name
                  ? 'bg-brand text-white'
                  : 'bg-dark-800 text-gray-300 hover:bg-dark-700'
              }`}
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: category.color }}
              />
              {category.name}
              <span className="text-xs opacity-75">({category.user_count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Recommendations */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Users size={24} />
              Neural Recommendations
            </h2>
            <button
              onClick={() => refetchRecommendations()}
              className="p-2 text-gray-400 hover:text-white"
              disabled={recommendationsLoading}
            >
              <RefreshCw size={20} className={recommendationsLoading ? 'animate-spin' : ''} />
            </button>
          </div>

          {recommendationsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand"></div>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Users size={48} className="mx-auto mb-4 opacity-50" />
              <p>No recommendations available</p>
              <p className="text-sm mt-2">Try adjusting your neural profile settings</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recommendations.map((match: UserMatch) => (
                <RecommendationCard
                  key={match.user.id}
                  match={match}
                  onFollow={() => followUserMutation.mutate(match.user.id)}
                  isFollowing={followUserMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Auto-Follow Settings */}
          <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Zap size={20} />
              Auto-Follow Settings
            </h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Enable Auto-Follow</span>
                <button
                  onClick={() => {
                    const newSettings = { ...autoFollowSettings, enabled: !autoFollowSettings.enabled };
                    setAutoFollowSettings(newSettings);
                    updateSettingsMutation.mutate(newSettings);
                  }}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    autoFollowSettings.enabled ? 'bg-brand' : 'bg-gray-600'
                  }`}
                >
                  <div
                    className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      autoFollowSettings.enabled ? 'translate-x-6' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="text-gray-300 text-sm">Confidence Threshold</label>
                <input
                  type="range"
                  min="0.5"
                  max="1.0"
                  step="0.1"
                  value={autoFollowSettings.confidence_threshold}
                  onChange={(e) => {
                    const newSettings = { ...autoFollowSettings, confidence_threshold: parseFloat(e.target.value) };
                    setAutoFollowSettings(newSettings);
                    updateSettingsMutation.mutate(newSettings);
                  }}
                  className="w-full mt-1"
                />
                <div className="text-xs text-gray-500 mt-1">
                  {Math.round(autoFollowSettings.confidence_threshold * 100)}%
                </div>
              </div>

              <div>
                <label className="text-gray-300 text-sm">Max Follows per Day</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={autoFollowSettings.max_follows_per_day}
                  onChange={(e) => {
                    const newSettings = { ...autoFollowSettings, max_follows_per_day: parseInt(e.target.value) };
                    setAutoFollowSettings(newSettings);
                    updateSettingsMutation.mutate(newSettings);
                  }}
                  className="w-full mt-1 px-3 py-2 bg-dark-700 border border-dark-600 rounded text-white"
                />
              </div>

              <button
                onClick={() => autoFollowMutation.mutate(autoFollowSettings)}
                disabled={autoFollowMutation.isPending || !autoFollowSettings.enabled}
                className="w-full py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {autoFollowMutation.isPending ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  <Target size={16} />
                )}
                Run Auto-Follow
              </button>

              {autoFollowMutation.data && (
                <div className="text-sm text-green-400">
                  <Check size={16} className="inline mr-1" />
                  {autoFollowMutation.data.followed_users} users followed
                </div>
              )}
            </div>
          </div>

          {/* Behavioral Insights */}
          {insights && (
            <div className="bg-dark-800 border border-dark-600 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp size={20} />
                Behavioral Insights
              </h3>
              
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Top Interests</h4>
                  <div className="flex flex-wrap gap-2">
                    {insights.top_interests.slice(0, 3).map((interest, index) => (
                      <span key={index} className="px-2 py-1 bg-brand/20 text-brand rounded text-xs">
                        {interest}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Engagement Patterns</h4>
                  <div className="text-xs text-gray-400">
                    {insights.engagement_patterns.slice(0, 2).map((pattern, index) => (
                      <div key={index} className="mb-1">- {pattern}</div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-300 mb-2">Best Times to Post</h4>
                  <div className="text-xs text-gray-400">
                    {insights.best_posting_times.slice(0, 2).map((time, index) => (
                      <div key={index} className="mb-1">- {time}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Recommendation Card Component
function RecommendationCard({ 
  match, 
  onFollow, 
  isFollowing 
}: { 
  match: UserMatch; 
  onFollow: () => void; 
  isFollowing: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-dark-800 border border-dark-600 rounded-xl p-6"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <img
            src={match.user.avatar_url}
            alt={match.user.username}
            className="w-16 h-16 rounded-full object-cover"
          />
          <div>
            <h3 className="font-semibold text-white">{match.user.username}</h3>
            <p className="text-sm text-gray-400">
              {match.user.first_name} {match.user.last_name}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex items-center gap-1">
                <Star size={14} className="text-yellow-500" />
                <span className="text-sm text-gray-300">
                  {Math.round(match.similarity_score * 100)}% match
                </span>
              </div>
            </div>
          </div>
        </div>
        
        <button
          onClick={onFollow}
          disabled={isFollowing}
          className="px-4 py-2 bg-brand text-white rounded-lg hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isFollowing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Following...
            </>
          ) : (
            <>
              <Users size={16} />
              Follow
            </>
          )}
        </button>
      </div>
      
      <div className="mt-4 space-y-2">
        <div>
          <h4 className="text-sm font-medium text-gray-300 mb-1">Why we recommend:</h4>
          <p className="text-sm text-gray-400">{match.match_reason}</p>
        </div>
        
        {match.common_interests.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-300 mb-1">Common interests:</h4>
            <div className="flex flex-wrap gap-1">
              {match.common_interests.slice(0, 3).map((interest, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-dark-700 text-gray-300 rounded text-xs"
                >
                  {interest}
                </span>
              ))}
              {match.common_interests.length > 3 && (
                <span className="px-2 py-1 bg-dark-700 text-gray-500 rounded text-xs">
                  +{match.common_interests.length - 3}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
