# Admin Users Page - Replace Alerts with Modals

## Changes Needed

Replace all `alert()` and `confirm()` calls with modal dialogs:

### 1. Create User Validation
- Replace alert for missing fields with error message in modal
- Replace alert for password validation with error message in modal  
- Replace success alert with toast notification

### 2. Bulk Actions Confirmations
- Replace confirm() for bulk assign role with confirmation modal
- Replace confirm() for bulk update status with confirmation modal
- Replace confirm() for bulk delete with confirmation modal (with text input)
- Replace confirm() for bulk activate with confirmation modal
- Replace confirm() for bulk deactivate with confirmation modal
- Replace confirm() for bulk erase with confirmation modal (with text input)

### 3. Error Messages
- Replace all error alerts with toast notifications or inline error messages

## Implementation

Add state for confirmation modals:
```typescript
const [confirmModal, setConfirmModal] = useState<{
  show: boolean
  title: string
  message: string
  confirmText: string
  onConfirm: () => void
  requiresInput?: boolean
  inputPlaceholder?: string
  expectedInput?: string
  variant?: 'danger' | 'warning' | 'info'
} | null>(null)

const [errorMessage, setErrorMessage] = useState<string | null>(null)
```

Create reusable ConfirmationModal component within the file.
