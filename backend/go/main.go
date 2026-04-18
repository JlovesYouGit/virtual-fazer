package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"github.com/lib/pq"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type User struct {
	ID           string    `json:"id" gorm:"primaryKey"`
	Username     string    `json:"username" gorm:"unique"`
	Email        string    `json:"email" gorm:"unique"`
	ProfileImage string    `json:"profile_image"`
	IsVerified   bool      `json:"is_verified"`
	LastActive   time.Time `json:"last_active"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type UserCategory struct {
	ID          string    `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name" gorm:"unique"`
	Description string    `json:"description"`
	Color       string    `json:"color"`
	IsActive    bool      `json:"is_active"`
	CreatedAt   time.Time `json:"created_at"`
}

type UserBehavior struct {
	ID             string    `json:"id" gorm:"primaryKey"`
	UserID         string    `json:"user_id"`
	CategoryID     string    `json:"category_id"`
	ConfidenceScore float64  `json:"confidence_score"`
	BehaviorData   string    `json:"behavior_data"` // JSON string
	LastUpdated    time.Time `json:"last_updated"`
}

type UserInteraction struct {
	ID            string    `json:"id" gorm:"primaryKey"`
	UserID        string    `json:"user_id"`
	TargetUserID  *string   `json:"target_user_id"`
	ContentType   string    `json:"content_type"`
	ContentID     string    `json:"content_id"`
	Duration      *int      `json:"duration"`
	Timestamp     time.Time `json:"timestamp"`
	Metadata      string    `json:"metadata"` // JSON string
}

type HighPerformanceMetrics struct {
	TotalUsers       int64   `json:"total_users"`
	ActiveUsers      int64   `json:"active_users"`
	TotalInteractions int64  `json:"total_interactions"`
	AvgResponseTime  float64 `json:"avg_response_time"`
	MemoryUsage      int64   `json:"memory_usage"`
	CPUUsage         float64 `json:"cpu_usage"`
}

var (
	db    *gorm.DB
	redis *redis.Client
)

func main() {
	// Initialize database
	initDatabase()
	defer closeDatabase()

	// Initialize Redis
	initRedis()
	defer closeRedis()

	// Setup Gin router
	router := setupRouter()

	// Start server
	srv := &http.Server{
		Addr:    ":8080",
		Handler: router,
	}

	// Graceful shutdown
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	log.Println("Go microservice started on :8080")

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown:", err)
	}

	log.Println("Server exited")
}

func initDatabase() {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "host=localhost user=postgres dbname=instagran password=password port=5432 sslmode=disable"
	}

	var err error
	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// Auto migrate
	err = db.AutoMigrate(&User{}, &UserCategory{}, &UserBehavior{}, &UserInteraction{})
	if err != nil {
		log.Fatal("Failed to migrate database:", err)
	}

	log.Println("Database connected and migrated")
}

func initRedis() {
	redisAddr := os.Getenv("REDIS_URL")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}

	redis = redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "", // no password
		DB:       0,  // default DB
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := redis.Ping(ctx).Result()
	if err != nil {
		log.Fatal("Failed to connect to Redis:", err)
	}

	log.Println("Redis connected")
}

func closeDatabase() {
	sqlDB, err := db.DB()
	if err != nil {
		log.Println("Error getting database instance:", err)
		return
	}
	sqlDB.Close()
}

func closeRedis() {
	redis.Close()
}

func setupRouter() *gin.Engine {
	gin.SetMode(gin.ReleaseMode)
	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// CORS middleware
	router.Use(func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Routes
	api := router.Group("/api/v1")
	{
		// User management
		users := api.Group("/users")
		{
			users.GET("/", getUsers)
			users.GET("/:id", getUser)
			users.POST("/", createUser)
			users.PUT("/:id", updateUser)
			users.DELETE("/:id", deleteUser)
		}

		// Categories
		categories := api.Group("/categories")
		{
			categories.GET("/", getCategories)
			categories.POST("/", createCategory)
			categories.PUT("/:id", updateCategory)
		}

		// Behavior analysis
		behavior := api.Group("/behavior")
		{
			behavior.POST("/analyze", analyzeBehavior)
			behavior.GET("/:user_id", getUserBehavior)
			behavior.POST("/interaction", logInteraction)
		}

		// High performance metrics
		api.GET("/metrics", getMetrics)
		api.GET("/health", healthCheck)
	}

	return router
}

// User handlers
func getUsers(c *gin.Context) {
	var users []User
	result := db.Find(&users)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	// Cache in Redis
	ctx := context.Background()
	usersJSON, _ := json.Marshal(users)
	redis.Set(ctx, "users:list", usersJSON, 5*time.Minute)

	c.JSON(http.StatusOK, users)
}

func getUser(c *gin.Context) {
	id := c.Param("id")
	
	// Try cache first
	ctx := context.Background()
	cached, err := redis.Get(ctx, "user:"+id).Result()
	if err == nil {
		var user User
		json.Unmarshal([]byte(cached), &user)
		c.JSON(http.StatusOK, user)
		return
	}

	var user User
	result := db.First(&user, "id = ?", id)
	if result.Error != nil {
		if result.Error == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		}
		return
	}

	// Cache in Redis
	userJSON, _ := json.Marshal(user)
	redis.Set(ctx, "user:"+id, userJSON, 10*time.Minute)

	c.JSON(http.StatusOK, user)
}

func createUser(c *gin.Context) {
	var user User
	if err := c.ShouldBindJSON(&user); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user.ID = generateUUID()
	user.CreatedAt = time.Now()
	user.UpdatedAt = time.Now()

	result := db.Create(&user)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	// Invalidate cache
	ctx := context.Background()
	redis.Del(ctx, "users:list")

	c.JSON(http.StatusCreated, user)
}

func updateUser(c *gin.Context) {
	id := c.Param("id")
	var user User
	if err := db.First(&user, "id = ?", id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	if err := c.ShouldBindJSON(&user); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user.UpdatedAt = time.Now()
	db.Save(&user)

	// Update cache
	ctx := context.Background()
	userJSON, _ := json.Marshal(user)
	redis.Set(ctx, "user:"+id, userJSON, 10*time.Minute)

	c.JSON(http.StatusOK, user)
}

func deleteUser(c *gin.Context) {
	id := c.Param("id")
	
	result := db.Delete(&User{}, "id = ?", id)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	if result.RowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}

	// Remove from cache
	ctx := context.Background()
	redis.Del(ctx, "user:"+id, "users:list")

	c.JSON(http.StatusOK, gin.H{"message": "User deleted successfully"})
}

// Category handlers
func getCategories(c *gin.Context) {
	var categories []UserCategory
	result := db.Find(&categories)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	c.JSON(http.StatusOK, categories)
}

func createCategory(c *gin.Context) {
	var category UserCategory
	if err := c.ShouldBindJSON(&category); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	category.ID = generateUUID()
	category.CreatedAt = time.Now()

	result := db.Create(&category)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	c.JSON(http.StatusCreated, category)
}

func updateCategory(c *gin.Context) {
	id := c.Param("id")
	var category UserCategory
	if err := db.First(&category, "id = ?", id).Error; err != nil {
		if err == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "Category not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	if err := c.ShouldBindJSON(&category); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	db.Save(&category)
	c.JSON(http.StatusOK, category)
}

// Behavior analysis handlers
func analyzeBehavior(c *gin.Context) {
	var request struct {
		UserID string `json:"user_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&request); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get user interactions from last 30 days
	thirtyDaysAgo := time.Now().AddDate(0, 0, -30)
	var interactions []UserInteraction
	result := db.Where("user_id = ? AND timestamp >= ?", request.UserID, thirtyDaysAgo).Find(&interactions)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	// Analyze behavior patterns
	analysis := performBehaviorAnalysis(interactions)

	// Store or update user behavior
	var behavior UserBehavior
	err := db.Where("user_id = ?", request.UserID).First(&behavior).Error
	if err == gorm.ErrRecordNotFound {
		behavior = UserBehavior{
			ID:             generateUUID(),
			UserID:         request.UserID,
			ConfidenceScore: analysis.ConfidenceScore,
			BehaviorData:   analysis.BehaviorData,
			LastUpdated:    time.Now(),
		}
		db.Create(&behavior)
	} else {
		behavior.ConfidenceScore = analysis.ConfidenceScore
		behavior.BehaviorData = analysis.BehaviorData
		behavior.LastUpdated = time.Now()
		db.Save(&behavior)
	}

	c.JSON(http.StatusOK, analysis)
}

func getUserBehavior(c *gin.Context) {
	userID := c.Param("user_id")
	var behavior UserBehavior
	result := db.First(&behavior, "user_id = ?", userID)
	if result.Error != nil {
		if result.Error == gorm.ErrRecordNotFound {
			c.JSON(http.StatusNotFound, gin.H{"error": "User behavior not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		}
		return
	}

	c.JSON(http.StatusOK, behavior)
}

func logInteraction(c *gin.Context) {
	var interaction UserInteraction
	if err := c.ShouldBindJSON(&interaction); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	interaction.ID = generateUUID()
	interaction.Timestamp = time.Now()

	result := db.Create(&interaction)
	if result.Error != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": result.Error.Error()})
		return
	}

	// Update metrics in Redis
	ctx := context.Background()
	redis.Incr(ctx, "metrics:total_interactions")

	c.JSON(http.StatusCreated, interaction)
}

// Metrics and health
func getMetrics(c *gin.Context) {
	ctx := context.Background()
	
	// Get some metrics from Redis
	totalInteractions, _ := redis.Get(ctx, "metrics:total_interactions").Int64()
	
	// Get database metrics
	var totalUsers int64
	db.Model(&User{}).Count(&totalUsers)
	
	var activeUsers int64
	thirtyDaysAgo := time.Now().AddDate(0, 0, -30)
	db.Model(&User{}).Where("last_active >= ?", thirtyDaysAgo).Count(&activeUsers)

	metrics := HighPerformanceMetrics{
		TotalUsers:       totalUsers,
		ActiveUsers:      activeUsers,
		TotalInteractions: totalInteractions,
		AvgResponseTime:  0.0, // Would calculate from request logs
		MemoryUsage:      0,   // Would get from system
		CPUUsage:         0.0, // Would get from system
	}

	c.JSON(http.StatusOK, metrics)
}

func healthCheck(c *gin.Context) {
	// Check database
	sqlDB, err := db.DB()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "unhealthy", "database": "error"})
		return
	}

	err = sqlDB.Ping()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "unhealthy", "database": "down"})
		return
	}

	// Check Redis
	ctx := context.Background()
	_, err = redis.Ping(ctx).Result()
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"status": "unhealthy", "redis": "down"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"status": "healthy"})
}

// Helper functions
type BehaviorAnalysis struct {
	ConfidenceScore float64 `json:"confidence_score"`
	BehaviorData    string  `json:"behavior_data"`
	Categories      []string `json:"categories"`
}

func performBehaviorAnalysis(interactions []UserInteraction) BehaviorAnalysis {
	// This is a simplified analysis
	// In production, this would use machine learning models
	
	categoryCounts := make(map[string]int)
	totalDuration := 0
	
	for _, interaction := range interactions {
		categoryCounts[interaction.ContentType]++
		if interaction.Duration != nil {
			totalDuration += *interaction.Duration
		}
	}
	
	// Calculate confidence score based on interaction diversity
	confidenceScore := float64(len(categoryCounts)) / float64(len(interactions)+1)
	if confidenceScore > 1.0 {
		confidenceScore = 1.0
	}
	
	// Determine top categories
	categories := make([]string, 0, len(categoryCounts))
	for category := range categoryCounts {
		categories = append(categories, category)
	}
	
	behaviorDataJSON, _ := json.Marshal(map[string]interface{}{
		"category_counts": categoryCounts,
		"total_duration": totalDuration,
		"interaction_count": len(interactions),
	})
	
	return BehaviorAnalysis{
		ConfidenceScore: confidenceScore,
		BehaviorData:    string(behaviorDataJSON),
		Categories:      categories,
	}
}

func generateUUID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}
