# Instagran - Instagram-like Neural Social Platform

A comprehensive social media platform with intelligent user categorization and auto-following capabilities using a neural interface backend.

## Architecture Overview

This project implements a multi-language microservices architecture inspired by Instagram's backend evolution:

### Core Services

1. **Python Django** - Main application logic, authentication, and core APIs
2. **Go** - High-performance data processing and caching
3. **Ruby** - Background job processing and analytics
4. **Node.js** - Real-time WebSocket communications
5. **Cobol** - Fast memory parsing for database operations

### Key Features

- **Neural Interface**: AI-powered user categorization based on behavior patterns
- **Auto-follow System**: Intelligent user matching and automatic following
- **Real-time Chat**: WebSocket-based messaging with typing indicators
- **User Analytics**: Comprehensive behavior tracking and insights
- **Multi-service Communication**: Cross-service API integration
- **Scalable Architecture**: Docker containerization with load balancing

## Project Structure

```
instagran/
|-- backend/
|   |-- python/          # Django main service
|   |-- go/              # High-performance service
|   |-- ruby/            # Background jobs & analytics
|   |-- nodejs/          # WebSocket service
|   |-- cobol/           # Fast memory parsing
|-- frontend/           # React frontend (to be implemented)
|-- database/           # Database schemas and migrations
|-- config/             # Configuration files
|-- docs/               # Documentation
|-- scripts/            # Utility scripts
|-- docker-compose.yml  # Container orchestration
|-- rule.md            # Project rules and goals
```

## Technology Stack

### Backend Services

- **Python/Django 4.2**: Core framework with REST API
- **Go 1.21**: High-performance microservices
- **Ruby/Sinatra**: Background job processing
- **Node.js/Express**: Real-time WebSocket server
- **Cobol/GnuCOBOL**: Database memory optimization

### Database & Cache

- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **Cassandra**: Time-series data (planned)

### Infrastructure

- **Docker**: Containerization
- **Nginx**: Load balancing
- **Celery**: Python task queue
- **Sidekiq**: Ruby job processing

## Installation & Setup

### Prerequisites

- Docker & Docker Compose
- GnuCOBOL (for Cobol compilation)
- Node.js 16+
- Python 3.9+
- Go 1.21+
- Ruby 3.0+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd instagran
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec python_backend python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec python_backend python manage.py createsuperuser
   ```

### Individual Service Setup

#### Python Django Service
```bash
cd backend/python
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Go Service
```bash
cd backend/go
go mod download
go build -o main main.go
./main
```

#### Ruby Service
```bash
cd backend/ruby
bundle install
bundle exec ruby app.rb
```

#### Node.js Service
```bash
cd backend/nodejs
npm install
npm start
```

#### Cobol Integration
```bash
cd backend/cobol
chmod +x compile_and_run.sh
./compile_and_run.sh
```

## API Documentation

### Python Django API (Port 8000)

#### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

#### Neural Interface
- `POST /api/neural/analyze/` - Analyze user behavior
- `POST /api/neural/match/` - Find matching users
- `POST /api/neural/auto-follow/` - Auto-follow users

#### Connections
- `POST /api/connections/follow/` - Follow user
- `POST /api/connections/unfollow/` - Unfollow user
- `GET /api/connections/suggestions/` - Get suggestions

#### Chat
- `GET /api/chat/rooms/` - Get chat rooms
- `POST /api/chat/send-message/` - Send message

### Go API (Port 8080)

#### User Management
- `GET /api/v1/users/` - List users
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/:id` - Get user

#### Behavior Analysis
- `POST /api/v1/behavior/analyze` - Analyze behavior
- `GET /api/v1/behavior/:user_id` - Get user behavior

#### Metrics
- `GET /api/v1/metrics` - System metrics
- `GET /api/v1/health` - Health check

### Ruby API (Port 4567)

#### Analytics
- `GET /api/v1/analytics/users/:user_id` - User analytics
- `GET /api/v1/metrics/system` - System metrics

#### Background Jobs
- `POST /api/v1/jobs/enqueue` - Queue job
- `GET /api/v1/jobs/:job_id` - Job status

### Node.js WebSocket (Port 3000)

#### Real-time Communication
- WebSocket connection: `ws://localhost:3000`
- Events: `chat_message`, `typing_start`, `typing_stop`, `new_notification`

## Neural Interface Features

### User Categorization

The neural interface automatically categorizes users based on:

- **Behavior Patterns**: Like/comment ratios, content preferences
- **Activity Timing**: Peak usage hours, frequency
- **Social Interactions**: Following patterns, engagement levels
- **Content Consumption**: View duration, interaction types

### Auto-Follow Algorithm

The system automatically follows users based on:

- **Category Matching**: Similar behavioral categories
- **Confidence Scores**: Minimum similarity thresholds
- **Activity Levels**: User engagement patterns
- **Network Analysis**: Mutual connections and influence

## Development Guidelines

### Code Standards

- Follow language-specific best practices
- Implement comprehensive error handling
- Use consistent API design patterns
- Maintain detailed documentation
- Implement proper logging and monitoring

### Testing

- Unit tests for all services
- Integration tests for API endpoints
- Load testing for performance validation
- Security testing for vulnerability assessment

### Deployment

- Use Docker containers for all services
- Implement CI/CD pipelines
- Monitor performance and errors
- Regular security audits

## Project Goals & Timeline

### Phase 1: Foundation (Week 1-2) - COMPLETED
- [x] Project structure setup
- [x] Database schema design
- [x] Basic authentication system
- [x] Core API endpoints

### Phase 2: Neural Interface (Week 3-4) - COMPLETED
- [x] Behavior tracking implementation
- [x] Category algorithm development
- [x] Pattern recognition system
- [x] Machine learning model integration

### Phase 3: Connection System (Week 5-6) - COMPLETED
- [x] User matching algorithms
- [x] Auto-follow functionality
- [x] Network analysis tools
- [x] Recommendation engine

### Phase 4: Integration (Week 7-8) - COMPLETED
- [x] Cross-service communication
- [x] Performance optimization
- [x] Caching implementation
- [x] Testing and debugging

### Phase 5: Deployment (Week 9-10)
- [ ] Production setup
- [ ] Monitoring and logging
- [ ] Security hardening
- [ ] Documentation completion

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support, please refer to the project documentation or create an issue in the repository.

---

**Note**: This is a demonstration project showcasing multi-language microservices architecture with neural interface capabilities. Some features may require additional configuration or development for production use.
