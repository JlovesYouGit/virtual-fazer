-- Instagram-like Platform Database Initialization
-- This script sets up the database with initial data and configurations

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for performance optimization
-- These will be created after Django migrations

-- User-related indexes
CREATE INDEX IF NOT EXISTS idx_users_user_last_active ON users_user(last_active DESC);
CREATE INDEX IF NOT EXISTS idx_users_user_username_trgm ON users_user USING gin(username gin_trgm_ops);

-- Activity tracking indexes
CREATE INDEX IF NOT EXISTS idx_useractivity_user_timestamp ON users_useractivity(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_useractivity_type_timestamp ON users_useractivity(activity_type, timestamp DESC);

-- Neural interface indexes
CREATE INDEX IF NOT EXISTS idx_neural_profile_user ON neural_userneuralprofile(user_id);
CREATE INDEX IF NOT EXISTS idx_neural_interaction_user_timestamp ON neural_userinteraction(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_neural_prediction_user_type ON neural_userprediction(user_id, prediction_type);

-- Connection indexes
CREATE INDEX IF NOT EXISTS idx_connections_follower_status ON connections_connection(follower_id, status);
CREATE INDEX IF NOT EXISTS idx_connections_following_status ON connections_connection(following_id, status);
CREATE INDEX IF NOT EXISTS idx_suggestions_user_score ON connections_suggestedconnection(user_id, score DESC);

-- Chat indexes
CREATE INDEX IF NOT EXISTS idx_chat_room_last_message ON chat_chatroom(last_message_time DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_chat_message_room_timestamp ON chat_message(room_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_participant_user ON chat_chatparticipant(user_id, room_id);

-- Reels indexes
CREATE INDEX IF NOT EXISTS idx_reels_creator_created ON reels_reel(creator_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reels_view_count ON reels_reel(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_reels_like_count ON reels_reel(like_count DESC);
CREATE INDEX IF NOT EXISTS idx_reels_hashtags ON reels_reel USING gin(hashtags);
CREATE INDEX IF NOT EXISTS idx_reels_created_at ON reels_reel(created_at DESC);

-- Reel interaction indexes
CREATE INDEX IF NOT EXISTS idx_reel_interactions_reel_user ON reels_reelinteraction(reel_id, user_id);
CREATE INDEX IF NOT EXISTS idx_reel_interactions_type_timestamp ON reels_reelinteraction(interaction_type, timestamp DESC);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_reel_analytics_user_date ON reels_reelanalytics(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_chat_analytics_user_date ON chat_chatanalytics(user_id, date DESC);

-- Insert initial categories for user classification
INSERT INTO neural_categorypattern (name, description, keywords, behavior_weights, threshold_score, is_active, created_at) VALUES
('Technology', 'Users interested in tech content, programming, gadgets', '["tech", "programming", "coding", "software", "hardware", "gadgets", "ai", "ml", "data"]', '{"like_ratio": 0.3, "comment_ratio": 0.2, "view_duration_avg": 0.25, "content_preferences": 0.25}', 0.7, true, NOW()),
('Social', 'Highly social users who interact frequently', '["social", "friends", "community", "network", "connect", "chat", "message"]', '{"like_ratio": 0.4, "comment_ratio": 0.3, "follow_ratio": 0.3}', 0.8, true, NOW()),
('Creative', 'Users who create and engage with artistic content', '["art", "design", "creative", "photography", "video", "music", "drawing"]', '{"like_ratio": 0.35, "comment_ratio": 0.25, "share_ratio": 0.4}', 0.75, true, NOW()),
('Business', 'Users focused on business and professional content', '["business", "entrepreneur", "startup", "marketing", "sales", "professional"]', '{"like_ratio": 0.25, "comment_ratio": 0.35, "message_ratio": 0.4}', 0.7, true, NOW()),
('Entertainment', 'Users focused on entertainment and lifestyle content', '["entertainment", "movies", "music", "celebrity", "fun", "lifestyle"]', '{"like_ratio": 0.45, "comment_ratio": 0.3, "share_ratio": 0.25}', 0.8, true, NOW()),
('Sports', 'Sports enthusiasts and fitness focused users', '["sports", "fitness", "workout", "gym", "exercise", "health", "athlete"]', '{"like_ratio": 0.35, "comment_ratio": 0.25, "view_duration_avg": 0.4}', 0.75, true, NOW()),
('Travel', 'Users interested in travel and exploration', '["travel", "adventure", "explore", "vacation", "trip", "destination"]', '{"like_ratio": 0.4, "comment_ratio": 0.3, "share_ratio": 0.3}', 0.8, true, NOW()),
('Food', 'Food enthusiasts and cooking content lovers', '["food", "cooking", "recipe", "restaurant", "chef", "cuisine", "delicious"]', '{"like_ratio": 0.4, "comment_ratio": 0.35, "share_ratio": 0.25}', 0.75, true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Insert initial auto-follow rules
INSERT INTO connections_autofollowrule (name, description, category_match, behavior_threshold, min_followers, max_followers, follow_ratio_min, follow_ratio_max, activity_level, is_active, max_follows_per_day, created_at) VALUES
('Tech Enthusiasts', 'Auto-follow users with high tech engagement', '{"Technology": 0.8}', 0.85, 100, 10000, 0.1, 3.0, 'medium', true, 30, NOW()),
('Social Butterflies', 'Connect highly social users', '{"Social": 0.9}', 0.9, 50, 5000, 0.2, 5.0, 'high', true, 50, NOW()),
('Creative Minds', 'Connect creative content creators', '{"Creative": 0.8}', 0.8, 200, 50000, 0.15, 4.0, 'medium', true, 25, NOW()),
('Business Network', 'Connect business professionals', '{"Business": 0.7}', 0.75, 100, 10000, 0.1, 2.5, 'low', true, 20, NOW()),
('Entertainment Fans', 'Connect entertainment lovers', '{"Entertainment": 0.8}', 0.8, 50, 10000, 0.2, 6.0, 'high', true, 40, NOW())
ON CONFLICT (name) DO NOTHING;

-- Insert sample music tracks for reels
INSERT INTO reels_reelmusic (title, artist, duration, usage_count, is_trending, created_at) VALUES
('Summer Vibes', 'DJ Sunshine', 15.0, 0, false, NOW()),
('Upbeat Energy', 'The Beats', 30.0, 0, false, NOW()),
('Chill Moments', 'Relaxing Sounds', 20.0, 0, false, NOW()),
('Dance Floor', 'Party Mix', 25.0, 0, false, NOW()),
('Acoustic Dreams', 'Guitar Strings', 18.0, 0, false, NOW()),
('Electronic Pulse', 'Synth Wave', 22.0, 0, false, NOW()),
('Hip Hop Beat', 'Urban Rhythm', 28.0, 0, false, NOW()),
('Pop Sensation', 'Chart Topper', 24.0, 0, false, NOW())
ON CONFLICT (title, artist) DO NOTHING;

-- Create sample challenges
INSERT INTO reels_reelchallenge (name, description, hashtag, start_date, end_date, prize, rules, is_active, participant_count, created_at) VALUES
('Dance Challenge 2024', 'Show off your best dance moves', '#Dance2024', NOW(), NOW() + INTERVAL '30 days', 'Featured on homepage', 'Original dance choreography, 15-60 seconds', true, 0, NOW()),
('Comedy Challenge', 'Make us laugh with your best comedy', '#LaughOutLoud', NOW(), NOW() + INTERVAL '21 days', 'Verified badge', 'Original comedy content, family-friendly', true, 0, NOW()),
('Food Challenge', 'Share your amazing cooking skills', '#FoodMaster', NOW(), NOW() + INTERVAL '14 days', 'Kitchen appliance prize', 'Cooking tutorial or food creation', true, 0, NOW()),
('Tech Challenge', 'Show your latest tech projects', '#TechInnovation', NOW(), NOW() + INTERVAL '25 days', 'Tech gadget', 'Technology showcase or tutorial', true, 0, NOW())
ON CONFLICT (name) DO NOTHING;

-- Create database functions for analytics
CREATE OR REPLACE FUNCTION update_user_analytics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user's last activity timestamp
    UPDATE users_user SET last_active = NOW() WHERE id = NEW.user_id;
    
    -- Update profile counts based on activity type
    IF NEW.activity_type = 'follow' THEN
        UPDATE connections_usernetwork 
        SET following_count = following_count + 1 
        WHERE user_id = NEW.user_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic analytics updates
DROP TRIGGER IF EXISTS trigger_update_user_analytics ON users_useractivity;
CREATE TRIGGER trigger_update_user_analytics
    AFTER INSERT ON users_useractivity
    FOR EACH ROW
    EXECUTE FUNCTION update_user_analytics();

-- Create function for updating reel engagement metrics
CREATE OR REPLACE FUNCTION update_reel_engagement()
RETURNS TRIGGER AS $$
BEGIN
    -- Update reel engagement counts
    IF NEW.interaction_type = 'like' THEN
        UPDATE reels_reel SET like_count = like_count + 1 WHERE id = NEW.reel_id;
    ELSIF NEW.interaction_type = 'comment' THEN
        UPDATE reels_reel SET comment_count = comment_count + 1 WHERE id = NEW.reel_id;
    ELSIF NEW.interaction_type = 'share' THEN
        UPDATE reels_reel SET share_count = share_count + 1 WHERE id = NEW.reel_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for reel engagement updates
DROP TRIGGER IF EXISTS trigger_update_reel_engagement ON reels_reelinteraction;
CREATE TRIGGER trigger_update_reel_engagement
    AFTER INSERT ON reels_reelinteraction
    FOR EACH ROW
    EXECUTE FUNCTION update_reel_engagement();

-- Create view for user engagement summary
CREATE OR REPLACE VIEW user_engagement_summary AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT r.id) as total_reels,
    COALESCE(SUM(r.view_count), 0) as total_views,
    COALESCE(SUM(r.like_count), 0) as total_likes,
    COALESCE(SUM(r.comment_count), 0) as total_comments,
    COALESCE(SUM(r.share_count), 0) as total_shares,
    CASE 
        WHEN COALESCE(SUM(r.view_count), 0) > 0 
        THEN ROUND((COALESCE(SUM(r.like_count), 0) + COALESCE(SUM(r.comment_count), 0) + COALESCE(SUM(r.share_count), 0))::decimal / SUM(r.view_count) * 100, 2)
        ELSE 0 
    END as engagement_rate
FROM users_user u
LEFT JOIN reels_reel r ON u.id = r.creator_id
GROUP BY u.id, u.username;

-- Create view for trending content
CREATE OR REPLACE VIEW trending_content AS
SELECT 
    r.id,
    r.caption,
    r.creator_id,
    u.username as creator_username,
    r.view_count,
    r.like_count,
    r.comment_count,
    r.share_count,
    r.created_at,
    CASE 
        WHEN r.view_count > 0 
        THEN ROUND((r.like_count + r.comment_count + r.share_count)::decimal / r.view_count * 100, 2)
        ELSE 0 
    END as engagement_rate,
    -- Trending score based on recent engagement
    (r.like_count * 0.3 + r.comment_count * 0.4 + r.share_count * 0.3 + 
     EXTRACT(EPOCH FROM (NOW() - r.created_at)) / 3600 * -0.1) as trending_score
FROM reels_reel r
JOIN users_user u ON r.creator_id = u.id
WHERE r.is_private = false
AND r.created_at >= NOW() - INTERVAL '7 days'
ORDER BY trending_score DESC;

-- Create stored procedure for user recommendations
CREATE OR REPLACE FUNCTION get_user_recommendations(p_user_id UUID, p_limit INTEGER DEFAULT 20)
RETURNS TABLE(
    recommended_user_id UUID,
    username TEXT,
    match_score NUMERIC,
    match_reason TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH user_categories AS (
        SELECT category, confidence_score
        FROM neural_userbehaviorpattern
        WHERE user_id = p_user_id
        AND confidence_score > 0.5
    ),
    potential_matches AS (
        SELECT 
            u.id,
            u.username,
            SUM(CASE 
                WHEN ubp.category = uc.category 
                THEN (uc.confidence_score + ubp.confidence_score) / 2 
                ELSE 0 
            END) as similarity_score
        FROM users_user u
        JOIN neural_userbehaviorpattern ubp ON u.id = ubp.user_id
        CROSS JOIN user_categories uc
        WHERE u.id != p_user_id
        AND ubp.confidence_score > 0.5
        AND ubp.category = uc.category
        GROUP BY u.id, u.username
        HAVING SUM(CASE 
            WHEN ubp.category = uc.category 
            THEN (uc.confidence_score + ubp.confidence_score) / 2 
            ELSE 0 
        END) > 0.6
    )
    SELECT 
        pm.id,
        pm.username,
        pm.similarity_score,
        'Similar interests in ' || (
            SELECT category 
            FROM neural_userbehaviorpattern 
            WHERE user_id = p_user_id 
            AND confidence_score > 0.5 
            ORDER BY confidence_score DESC 
            LIMIT 1
        )
    FROM potential_matches pm
    WHERE NOT EXISTS (
        SELECT 1 FROM connections_connection 
        WHERE follower_id = p_user_id 
        AND following_id = pm.id
        AND status = 'following'
    )
    ORDER BY pm.similarity_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Create function for daily analytics aggregation
CREATE OR REPLACE FUNCTION aggregate_daily_analytics()
RETURNS VOID AS $$
BEGIN
    -- Aggregate user activity analytics
    INSERT INTO users_useractivity (user_id, activity_type, metadata, timestamp)
    SELECT 
        user_id,
        'daily_summary',
        json_build_object(
            'activities_count', COUNT(*),
            'likes_given', COUNT(*) FILTER (WHERE activity_type = 'like'),
            'comments_given', COUNT(*) FILTER (WHERE activity_type = 'comment'),
            'follows_given', COUNT(*) FILTER (WHERE activity_type = 'follow')
        ),
        NOW()
    FROM users_useractivity
    WHERE DATE(timestamp) = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY user_id
    ON CONFLICT DO NOTHING;
    
    -- Aggregate reel analytics
    INSERT INTO reels_reelanalytics (user_id, date, reels_created, total_views, total_likes, total_comments, total_shares, engagement_rate, reach, impressions)
    SELECT 
        creator_id,
        DATE(created_at),
        COUNT(*),
        SUM(view_count),
        SUM(like_count),
        SUM(comment_count),
        SUM(share_count),
        CASE 
            WHEN SUM(view_count) > 0 
            THEN ROUND((SUM(like_count) + SUM(comment_count) + SUM(share_count))::decimal / SUM(view_count) * 100, 2)
            ELSE 0 
        END,
        SUM(view_count),
        SUM(view_count) * 2
    FROM reels_reel
    WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
    GROUP BY creator_id, DATE(created_at)
    ON CONFLICT (user_id, date) DO UPDATE SET
        reels_created = EXCLUDED.reels_created,
        total_views = EXCLUDED.total_views,
        total_likes = EXCLUDED.total_likes,
        total_comments = EXCLUDED.total_comments,
        total_shares = EXCLUDED.total_shares,
        engagement_rate = EXCLUDED.engagement_rate,
        reach = EXCLUDED.reach,
        impressions = EXCLUDED.impressions;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for daily aggregation (requires pg_cron extension)
-- SELECT cron.schedule('daily-analytics', '0 2 * * *', 'SELECT aggregate_daily_analytics();');

-- Create indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_reels_caption_fts ON reels_reel USING gin(to_tsvector('english', caption));
CREATE INDEX IF NOT EXISTS idx_users_username_fts ON users_user USING gin(to_tsvector('english', username));

-- Create function for full-text search
CREATE OR REPLACE FUNCTION search_reels(p_query TEXT, p_limit INTEGER DEFAULT 50)
RETURNS TABLE(
    reel_id UUID,
    caption TEXT,
    creator_id UUID,
    creator_username TEXT,
    view_count BIGINT,
    like_count BIGINT,
    created_at TIMESTAMP,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id,
        r.caption,
        r.creator_id,
        u.username,
        r.view_count,
        r.like_count,
        r.created_at,
        ts_rank(to_tsvector('english', r.caption), plainto_tsquery('english', p_query)) as rank
    FROM reels_reel r
    JOIN users_user u ON r.creator_id = u.id
    WHERE r.is_private = false
    AND to_tsvector('english', r.caption) @@ plainto_tsquery('english', p_query)
    ORDER BY rank DESC, r.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMIT;
