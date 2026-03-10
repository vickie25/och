# Modules Page - Edit Functionality & Video Upload Progress Bar

## Summary of Changes

Added edit functionality for modules and lessons, plus a progress bar for video uploads on the Director Modules page (`/dashboard/director/modules`).

## Features Added

### 1. Edit Module Functionality
- **Location**: Edit button added next to each module in the list view
- **What it does**: Opens a modal to edit module details including:
  - Track assignment
  - Level (Beginner, Intermediate, Advanced, Mastery)
  - Title and description
  - Order index
  - Estimated time
  - Core and Required flags
- **File**: `EditModuleForm` component added to `page.tsx`

### 2. Edit Lesson Functionality
- **Location**: Edit button added next to each lesson in the expanded module view
- **What it does**: Opens a modal to edit lesson details including:
  - Lesson type (Video, Guide, Quiz, Assessment, Lab, Reading)
  - Title
  - Content URL or file upload
  - Duration
  - Order index
- **File**: `EditLessonForm` component added to `page.tsx`

### 3. Video Upload Progress Bar
- **Location**: Appears when uploading a video file (both in Add Lesson and Edit Lesson forms)
- **What it does**: 
  - Shows real-time upload progress percentage
  - Displays a visual progress bar
  - Uses XMLHttpRequest for progress tracking
  - Disables form submission during upload
- **Visual**: Blue progress bar with percentage display

## Technical Implementation

### Progress Bar Implementation
```typescript
// Uses XMLHttpRequest for upload progress tracking
const xhr = new XMLHttpRequest()

xhr.upload.addEventListener('progress', (e) => {
  if (e.lengthComputable) {
    const percentComplete = Math.round((e.loaded / e.total) * 100)
    setUploadProgress(percentComplete)
  }
})
```

### State Management
Added new state variables:
- `editModule`: Tracks which module is being edited
- `editLesson`: Tracks which lesson is being edited
- `isUploading`: Indicates active upload
- `uploadProgress`: Stores upload percentage (0-100)

## User Interface

### Edit Module Button
- Located next to "+ Lesson" button on each module
- Blue/defender color scheme
- Opens modal with pre-filled form

### Edit Lesson Button
- Located next to "View" button on each lesson
- Blue/defender color scheme
- Opens modal with pre-filled form

### Progress Bar
- Appears below file input when uploading
- Shows "Uploading..." text with percentage
- Visual bar fills from left to right
- Mint green color for percentage text
- Defender blue color for progress bar

## File Modified

**File**: `c:\Users\AppleFi\och\frontend\nextjs_app\app\dashboard\director\modules\page.tsx`

### Changes Made:
1. Added `editModule` and `editLesson` state variables
2. Added "Edit" button to module actions
3. Added "Edit" button to lesson actions
4. Created `EditModuleForm` component
5. Created `EditLessonForm` component
6. Enhanced video upload with progress tracking using XMLHttpRequest
7. Added progress bar UI component
8. Added `isUploading` state to prevent form submission during upload

## How to Use

### Editing a Module:
1. Navigate to `/dashboard/director/modules`
2. Expand a track to see modules
3. Click the "Edit" button on any module
4. Update the fields in the modal
5. Click "Update Module"

### Editing a Lesson:
1. Navigate to `/dashboard/director/modules`
2. Expand a module to see lessons
3. Click the "Edit" button on any lesson
4. Update the fields in the modal
5. For video lessons, choose URL or file upload
6. If uploading a file, watch the progress bar
7. Click "Update Lesson"

### Video Upload Progress:
1. When adding or editing a video lesson
2. Select "Upload File" option
3. Choose a video file
4. Click "Add Lesson" or "Update Lesson"
5. Progress bar appears showing upload percentage
6. Form submits automatically after upload completes

## API Endpoints Used

- `PUT /api/v1/curriculum/modules/{id}/` - Update module
- `PUT /api/v1/curriculum/lessons/{id}/` - Update lesson
- `POST /api/v1/curriculum/lessons/upload-video/` - Upload video file

## Notes

- Progress bar only appears for video file uploads
- URL-based content doesn't show progress (instant)
- Upload can be cancelled by closing the modal
- Form is disabled during upload to prevent duplicate submissions
- Progress tracking requires XMLHttpRequest (not fetch API)
