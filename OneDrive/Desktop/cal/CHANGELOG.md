# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-10-31

### Added
#### Daily Studio Module - Complete AI-Powered Daily Briefing System

**Phase 1: Core Infrastructure**
- **Data Models**: Added `DailyMedia`, `BriefInput`, `BriefOutput`, and `BriefCache` models
- **Database Schema**: Extended `Settings` model with Daily Studio configuration options
- **Service Interfaces**: Created `IDailyStudioService`, `IGeminiService`, `IGoogleApiService`, and `ICalendarProvider`
- **Dependency Injection**: Registered all services in DI container with proper HttpClient configuration
- **Database Migrations**: Added EF Core migrations for new tables and schema changes

**Phase 2: Enhanced Data Collection & Brief Generation**
- **Calendar Integration**: Implemented `IcsCalendarProvider` for ICS file-based calendar reading
- **Gemini API Integration**: Full REST API client with schema-first JSON prompts (temperature 0.2)
- **Intelligent Caching**: SHA256 hash-based brief caching to avoid redundant API calls
- **Privacy Controls**: Configurable redaction of private information (locations, notes)
- **Offline Fallback**: Deterministic local brief generation when APIs are unavailable
- **Brief Cache Table**: Database table for storing generated briefs with access statistics

**Phase 3: Audio/Video Generation Pipeline**
- **Google OAuth**: Service account authentication with JWT token generation
- **NotebookLM API**: Integration with `POST /v1alpha/projects/{project}/locations/{location}/notebooks/{notebookId}/audioOverviews`
- **Multi-Tier Audio Generation**:
  - Primary: NotebookLM API for contextual AI audio
  - Fallback: Gemini TTS for high-quality speech synthesis
  - Offline: Placeholder audio generation for guaranteed output
- **Video Pipeline**: Foundation for FFmpeg/Veo integration (60-90s overview videos)
- **Quota Handling**: Automatic fallback when API limits are exceeded
- **Error Recovery**: Circuit breaker patterns and comprehensive logging

**Phase 4: WinUI3 Media Player & UI**
- **Daily Studio Page**: Modern WinUI3 interface with acrylic design language
- **Media Library**: Browse and select from 30 days of generated daily briefs
- **Media Player Controls**:
  - Play/Pause/Stop transport controls
  - ±30 second seek buttons
  - 0.5x to 2.0x playback speed control
  - Volume slider with tooltip
  - Seekable progress bar with time display
- **Brief Generation UI**: One-click generation with loading states and auto-refresh
- **Settings Integration**: UI hooks for configuration management
- **Responsive Design**: Clean, modern interface with proper spacing and typography

### Technical Enhancements
- **NuGet Packages**: Added JWT tokens, IdentityModel, and HttpClient extensions
- **Service Architecture**: Clean separation of concerns with interface-based design
- **Error Handling**: Comprehensive exception handling with graceful degradation
- **Logging**: Structured logging throughout all services and operations
- **Async Patterns**: Proper async/await implementation for UI responsiveness
- **Data Validation**: Input sanitization and validation throughout the pipeline

### Database Changes
- **New Tables**:
  - `DailyMedia`: Stores generated audio/video files with metadata
  - `BriefCache`: Caches generated briefs with hash-based lookup
- **Schema Extensions**:
  - `Settings`: Added 10+ Daily Studio configuration properties
- **Migrations**: Proper EF Core migrations with data seeding

### API Integrations
- **Google Gemini API**: `v1beta/models/gemini-1.5-pro:generateContent` with structured prompts
- **Google NotebookLM API**: Audio overview generation with episode focus
- **OAuth 2.0**: Service account authentication with JWT bearer tokens
- **Calendar Support**: ICS file parsing with Ical.Net library

### UI/UX Improvements
- **Modern Design**: WinUI3 with acrylic backgrounds and system theme integration
- **Accessibility**: Proper contrast ratios and keyboard navigation
- **Performance**: Efficient data loading and UI updates
- **User Feedback**: Loading states, error messages, and progress indicators

### Configuration Options
- **Daily Studio Settings**:
  - Enable/disable module
  - Schedule time (default 07:30 MDT)
  - Time zone configuration
  - Data source toggles (calendar, tasks, habits)
  - Privacy settings (redact private info)
  - Preferred generation method (notebooklm/gemini/offline)
  - Video generation toggle
  - Retention period (default 30 days)
  - API key configuration for Google/Gemini services

### Known Limitations
- Windows App SDK AppNotification (toast) integration not yet wired to NotificationService
- Background scheduling (automatic run at configured time) not yet implemented
- Live calendar sync beyond ICS provider (e.g., Google Calendar) not yet implemented
- Video generation: FFmpeg/Veo pipeline is foundational only; final rendering not shipped

### Future Roadmap
- **Phase 5**: Background scheduling, advanced settings, performance optimizations
- **Phase 6**: Additional calendar providers, voice capture, focus modes
- **Phase 7**: Advanced analytics, habit insights, productivity metrics

---

## [1.0.0] - 2025-10-31

### Added
- Initial project structure with WinUI3, .NET 9, and Entity Framework
- Basic task, calendar, and habit management system
- SQLite database with migrations
- Dependency injection setup
- Basic UI with MainPage

### Technical Foundation
- **Architecture**: Clean Architecture with Core/Data/App layers
- **Database**: EF Core with SQLite
- **UI Framework**: WinUI3 with modern Windows design
- **DI Container**: Microsoft.Extensions.DependencyInjection
- **Build System**: .NET 9 SDK with WinUI workload
