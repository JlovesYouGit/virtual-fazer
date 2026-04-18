FROM ruby:3.2-slim

# Set environment variables
ENV RAILS_ENV=production
ENV RACK_ENV=production
ENV BUNDLE_DEPLOYMENT=true
ENV BUNDLE_PATH=/usr/local/bundle
ENV BUNDLE_WITHOUT=development:test

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        nodejs \
        npm \
        && rm -rf /var/lib/apt/lists/*

# Install bundler
RUN gem install bundler

# Copy Gemfile
COPY Gemfile Gemfile.lock ./

# Install Ruby dependencies
RUN bundle config set --local without 'development test' \
    && bundle install --jobs 4 --retry 3

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 4567

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:4567/health || exit 1

# Start the application
CMD ["bundle", "exec", "ruby", "app.rb"]
