require 'sinatra'
require 'sinatra/json'
require 'json'
require 'pg'
require 'redis'
require 'sidekiq'
require 'sidekiq/api'
require 'dotenv/load'

# Sinatra application for background job processing and analytics
class InstagranRubyService < Sinatra::Base
  set :bind, '0.0.0.0'
  set :port, 4567
  set :json_encoder, :to_json

  # Database connection
  def db
    @db ||= PG.connect(
      host: ENV['DB_HOST'] || 'localhost',
      port: ENV['DB_PORT'] || 5432,
      dbname: ENV['DB_NAME'] || 'instagran',
      user: ENV['DB_USER'] || 'postgres',
      password: ENV['DB_PASSWORD'] || 'password'
    )
  end

  # Redis connection
  def redis
    @redis ||= Redis.new(
      host: ENV['REDIS_HOST'] || 'localhost',
      port: ENV['REDIS_PORT'] || 6379,
      db: 0
    )
  end

  # Middleware
  before do
    content_type :json
    
    # CORS headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Handle preflight requests
    request.request_method == 'OPTIONS' && halt(204)
  end

  # Error handling
  error do
    error = env['sinatra.error']
    status 500
    json error: error.message
  end

  # Health check
  get '/health' do
    begin
      db.ping
      redis.ping
      json status: 'healthy', services: { database: 'up', redis: 'up', sidekiq: Sidekiq::ProcessSet.new.size }
    rescue => e
      status 503
      json status: 'unhealthy', error: e.message
    end
  end

  # User analytics
  get '/api/v1/analytics/users/:user_id' do
    user_id = params[:user_id]
    
    begin
      # Get user activity from last 30 days
      query = <<-SQL
        SELECT 
          COUNT(*) as total_activities,
          COUNT(CASE WHEN activity_type = 'like' THEN 1 END) as likes,
          COUNT(CASE WHEN activity_type = 'comment' THEN 1 END) as comments,
          COUNT(CASE WHEN activity_type = 'follow' THEN 1 END) as follows,
          COUNT(CASE WHEN activity_type = 'post' THEN 1 END) as posts,
          COUNT(CASE WHEN activity_type = 'message' THEN 1 END) as messages,
          DATE_TRUNC('day', timestamp) as activity_date
        FROM users_useractivity 
        WHERE user_id = $1 
        AND timestamp >= NOW() - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', timestamp)
        ORDER BY activity_date DESC
      SQL
      
      results = db.exec_params(query, [user_id])
      
      analytics = results.map do |row|
        {
          date: row['activity_date'],
          total_activities: row['total_activities'].to_i,
          likes: row['likes'].to_i,
          comments: row['comments'].to_i,
          follows: row['follows'].to_i,
          posts: row['posts'].to_i,
          messages: row['messages'].to_i
        }
      end
      
      json analytics: analytics
    rescue => e
      status 500
      json error: e.message
    end
  end

  # System metrics
  get '/api/v1/metrics/system' do
    begin
      # Get Sidekiq stats
      stats = Sidekiq::Stats.new
      workers = Sidekiq::Workers.new
      queues = Sidekiq::Queue.all
      
      # Get database stats
      db_stats = db.exec_params('SELECT 
        COUNT(*) as total_users,
        COUNT(CASE WHEN last_active >= NOW() - INTERVAL \'24 hours\' THEN 1 END) as active_users,
        COUNT(*) as total_activities
        FROM users_user', []).first
      
      # Get Redis stats
      redis_info = redis.info
      
      metrics = {
        sidekiq: {
          processed: stats.processed,
          failed: stats.failed,
          busy: workers.size,
          enqueued: stats.enqueued,
          queues: queues.map { |q| { name: q.name, size: q.size } }
        },
        database: {
          total_users: db_stats['total_users'].to_i,
          active_users: db_stats['active_users'].to_i,
          total_activities: db_stats['total_activities'].to_i
        },
        redis: {
          used_memory: redis_info['used_memory_human'],
          connected_clients: redis_info['connected_clients'],
          total_commands_processed: redis_info['total_commands_processed']
        }
      }
      
      json metrics: metrics
    rescue => e
      status 500
      json error: e.message
    end
  end

  # Background job management
  post '/api/v1/jobs/enqueue' do
    job_data = JSON.parse(request.body.read)
    
    begin
      case job_data['type']
      when 'user_analysis'
        UserAnalysisWorker.perform_async(job_data['user_id'])
      when 'category_update'
        CategoryUpdateWorker.perform_async(job_data['user_id'], job_data['categories'])
      when 'notification_batch'
        NotificationBatchWorker.perform_async(job_data['user_ids'], job_data['message'])
      when 'data_cleanup'
        DataCleanupWorker.perform_async(job_data['days_old'])
      else
        status 400
        json error: 'Unknown job type'
      end
      
      json status: 'queued', job_type: job_data['type']
    rescue => e
      status 500
      json error: e.message
    end
  end

  # Get job status
  get '/api/v1/jobs/:job_id' do
    job_id = params[:job_id]
    
    begin
      job = Sidekiq::Status::get_all(job_id)
      if job.empty?
        status 404
        json error: 'Job not found'
      else
        json job: job
      end
    rescue => e
      status 500
      json error: e.message
    end
  end

  # User recommendations
  get '/api/v1/recommendations/:user_id' do
    user_id = params[:user_id]
    
    begin
      # Get user's current categories
      categories_query = <<-SQL
        SELECT category, confidence_score 
        FROM neural_userbehaviorpattern 
        WHERE user_id = $1 
        ORDER BY confidence_score DESC 
        LIMIT 5
      SQL
      
      categories = db.exec_params(categories_query, [user_id])
      
      # Find similar users
      similar_users_query = <<-SQL
        SELECT DISTINCT u.id, u.username, u.profile_image,
          COUNT(*) as common_categories,
          AVG(bp.confidence_score) as avg_confidence
        FROM users_user u
        JOIN neural_userbehaviorpattern bp ON u.id = bp.user_id
        WHERE bp.category IN (SELECT category FROM neural_userbehaviorpattern WHERE user_id = $1)
        AND u.id != $1
        AND bp.confidence_score > 0.7
        GROUP BY u.id, u.username, u.profile_image
        ORDER BY common_categories DESC, avg_confidence DESC
        LIMIT 20
      SQL
      
      similar_users = db.exec_params(similar_users_query, [user_id])
      
      recommendations = similar_users.map do |user|
        {
          user_id: user['id'],
          username: user['username'],
          profile_image: user['profile_image'],
          match_score: (user['common_categories'].to_i * user['avg_confidence'].to_f).round(2),
          reason: "Similar interests in #{categories.first&.[]('category')}"
        }
      end
      
      json recommendations: recommendations
    rescue => e
      status 500
      json error: e.message
    end
  end

  # Content analytics
  get '/api/v1/analytics/content' do
    days = params[:days]&.to_i || 30
    
    begin
      query = <<-SQL
        SELECT 
          DATE_TRUNC('day', created_at) as date,
          COUNT(*) as total_posts,
          COUNT(CASE WHEN content_type = 'reel' THEN 1 END) as reels,
          COUNT(CASE WHEN content_type = 'post' THEN 1 END) as posts,
          AVG(view_count) as avg_views,
          AVG(like_count) as avg_likes
        FROM reels_reel
        WHERE created_at >= NOW() - INTERVAL '#{days} days'
        GROUP BY DATE_TRUNC('day', created_at)
        ORDER BY date DESC
      SQL
      
      results = db.exec_params(query, [])
      
      analytics = results.map do |row|
        {
          date: row['date'],
          total_posts: row['total_posts'].to_i,
          reels: row['reels'].to_i,
          posts: row['posts'].to_i,
          avg_views: row['avg_views']&.to_f || 0,
          avg_likes: row['avg_likes']&.to_f || 0
        }
      end
      
      json analytics: analytics
    rescue => e
      status 500
      json error: e.message
    end
  end

  # Trending hashtags
  get '/api/v1/trends/hashtags' do
    hours = params[:hours]&.to_i || 24
    
    begin
      query = <<-SQL
        SELECT 
          unnest(hashtags) as hashtag,
          COUNT(*) as usage_count,
          COUNT(DISTINCT creator_id) as unique_users
        FROM reels_reel
        WHERE created_at >= NOW() - INTERVAL '#{hours} hours'
        AND hashtags != '{}'
        GROUP BY hashtag
        ORDER BY usage_count DESC, unique_users DESC
        LIMIT 50
      SQL
      
      results = db.exec_params(query, [])
      
      trends = results.map do |row|
        {
          hashtag: row['hashtag'],
          usage_count: row['usage_count'].to_i,
          unique_users: row['unique_users'].to_i
        }
      end
      
      json trends: trends
    rescue => e
      status 500
      json error: e.message
    end
  end

  # User engagement metrics
  get '/api/v1/analytics/engagement/:user_id' do
    user_id = params[:user_id]
    days = params[:days]&.to_i || 30
    
    begin
      query = <<-SQL
        WITH user_posts AS (
          SELECT id, view_count, like_count, comment_count, share_count
          FROM reels_reel
          WHERE creator_id = $1
          AND created_at >= NOW() - INTERVAL '#{days} days'
        ),
        user_interactions AS (
          SELECT 
            COUNT(*) as total_interactions,
            COUNT(CASE WHEN interaction_type = 'like' THEN 1 END) as likes_given,
            COUNT(CASE WHEN interaction_type = 'comment' THEN 1 END) as comments_given,
            COUNT(CASE WHEN interaction_type = 'share' THEN 1 END) as shares_given
          FROM neural_userinteraction
          WHERE user_id = $1
          AND timestamp >= NOW() - INTERVAL '#{days} days'
        )
        SELECT 
          COUNT(*) as posts_created,
          COALESCE(SUM(view_count), 0) as total_views,
          COALESCE(SUM(like_count), 0) as total_likes_received,
          COALESCE(SUM(comment_count), 0) as total_comments_received,
          COALESCE(SUM(share_count), 0) as total_shares_received,
          (SELECT total_interactions FROM user_interactions) as total_interactions,
          (SELECT likes_given FROM user_interactions) as likes_given,
          (SELECT comments_given FROM user_interactions) as comments_given,
          (SELECT shares_given FROM user_interactions) as shares_given
        FROM user_posts
      SQL
      
      result = db.exec_params(query, [user_id]).first
      
      if result
        engagement = {
          posts_created: result['posts_created'].to_i,
          total_views: result['total_views'].to_i,
          total_likes_received: result['total_likes_received'].to_i,
          total_comments_received: result['total_comments_received'].to_i,
          total_shares_received: result['total_shares_received'].to_i,
          total_interactions: result['total_interactions'].to_i,
          likes_given: result['likes_given'].to_i,
          comments_given: result['comments_given'].to_i,
          shares_given: result['shares_given'].to_i,
          engagement_rate: calculate_engagement_rate(result)
        }
        
        json engagement: engagement
      else
        json engagement: {}
      end
    rescue => e
      status 500
      json error: e.message
    end
  end

  private

  def calculate_engagement_rate(data)
    views = data['total_views'].to_i
    interactions = data['total_likes_received'].to_i + 
                   data['total_comments_received'].to_i + 
                   data['total_shares_received'].to_i
    
    return 0.0 if views == 0
    ((interactions.to_f / views) * 100).round(2)
  end
end

# Sidekiq Workers
class UserAnalysisWorker
  include Sidekiq::Worker
  
  def perform(user_id)
    # Perform user behavior analysis
    puts "Analyzing user: #{user_id}"
    
    # This would integrate with the neural interface
    # For now, just simulate processing
    sleep(2)
    
    # Store results in Redis
    redis = Redis.new
    redis.setex("user_analysis:#{user_id}", 3600, { 
      analyzed_at: Time.now,
      status: 'completed'
    }.to_json)
  end
end

class CategoryUpdateWorker
  include Sidekiq::Worker
  
  def perform(user_id, categories)
    # Update user categories
    puts "Updating categories for user: #{user_id}"
    puts "Categories: #{categories.inspect}"
    
    # Process and update categories
    sleep(1)
  end
end

class NotificationBatchWorker
  include Sidekiq::Worker
  
  def perform(user_ids, message)
    # Send batch notifications
    puts "Sending notification to #{user_ids.length} users"
    puts "Message: #{message}"
    
    # Process notifications
    sleep(0.5)
  end
end

class DataCleanupWorker
  include Sidekiq::Worker
  
  def perform(days_old)
    # Clean up old data
    puts "Cleaning up data older than #{days_old} days"
    
    # Perform cleanup operations
    sleep(3)
  end
end

# Run the application
if __FILE__ == $0
  InstagranRubyService.run!
end
