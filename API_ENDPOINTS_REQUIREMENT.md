# CRM SaaS Platform - API Endpoints Requirement Document

This document lists all API endpoints required for the CRM SaaS platform frontend integration.

**Base URL**: `/v1` (or as per backend convention)

**Authentication**: All endpoints (except auth endpoints) require Bearer token in Authorization header:
```
Authorization: Bearer <access_token>
```

**Response Format**: All endpoints should return data in a consistent format:
```json
{
  "data": { ... },
  "message": "Success message" // optional
}
```

For paginated responses:
```json
{
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

---

## 1. AUTHENTICATION ENDPOINTS

### 1.1 Login
- **Method**: `POST`
- **Endpoint**: `/v1/auth/login/`
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
- **Response**: `AuthResponse`
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 1.2 Register
- **Method**: `POST`
- **Endpoint**: `/v1/auth/register/`
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "John",
  "last_name": "Doe"
}
```
- **Response**: `AuthResponse` (same as login)

### 1.3 Logout
- **Method**: `POST`
- **Endpoint**: `/v1/auth/logout/`
- **Request Body**: None
- **Response**: `{ "message": "Logged out successfully" }`

### 1.4 Refresh Token
- **Method**: `POST`
- **Endpoint**: `/v1/auth/refresh/`
- **Request Body**:
```json
{
  "refresh": "jwt_refresh_token"
}
```
- **Response**:
```json
{
  "access": "new_jwt_access_token"
}
```

### 1.5 Get User Profile
- **Method**: `GET`
- **Endpoint**: `/v1/auth/users/me/`
- **Request Body**: None
- **Response**: `User` object

---

## 2. ORGANIZATION ENDPOINTS

### 2.1 List Organizations (for user)
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/`
- **Query Params**: None
- **Response**: Array of `Organization`
```json
[
  {
    "id": "org_123",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "logo_url": "https://...",
    "industry": "technology",
    "size": "11-50",
    "website": "https://acme.com",
    "description": "Description",
    "owner_id": "user_1",
    "settings": {
      "default_role_id": "role_123",
      "allow_member_invites": true,
      "require_two_factor": false,
      "timezone": "UTC",
      "date_format": "MM/DD/YYYY",
      "currency": "USD"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 2.2 Get Organization Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/`
- **Response**: Single `Organization` object

### 2.3 Create Organization
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/`
- **Request Body**:
```json
{
  "name": "Acme Corp",
  "industry": "technology",
  "size": "11-50",
  "website": "https://acme.com"
}
```
- **Response**: `Organization` object
- **Note**: Should automatically create default roles and assign creator as Owner

### 2.4 Update Organization
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/`
- **Request Body**:
```json
{
  "name": "Updated Name",
  "logo_url": "https://...",
  "industry": "healthcare",
  "size": "51-200",
  "website": "https://newwebsite.com",
  "description": "New description",
  "settings": {
    "timezone": "America/New_York",
    "currency": "EUR",
    "date_format": "DD/MM/YYYY"
  }
}
```
- **Response**: Updated `Organization` object

### 2.5 Delete Organization
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/`
- **Response**: `{ "message": "Organization deleted" }`
- **Note**: Only owner can delete

---

## 3. TEAM ENDPOINTS

### 3.1 List Teams (for organization)
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/teams/`
- **Response**: Array of `Team`
```json
[
  {
    "id": "team_123",
    "organization_id": "org_123",
    "name": "Sales Team",
    "description": "Sales department",
    "color": "#1677ff",
    "leader_id": "member_123",
    "member_count": 5,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 3.2 Get Team Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/teams/{team_id}/`
- **Response**: Single `Team` object

### 3.3 Create Team
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/teams/`
- **Request Body**:
```json
{
  "name": "Sales Team",
  "description": "Sales department",
  "color": "#1677ff",
  "leader_id": "member_123",
  "member_ids": ["member_1", "member_2"]
}
```
- **Response**: `Team` object

### 3.4 Update Team
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/teams/{team_id}/`
- **Request Body**:
```json
{
  "name": "Updated Team Name",
  "description": "Updated description",
  "color": "#52c41a",
  "leader_id": "member_456"
}
```
- **Response**: Updated `Team` object

### 3.5 Delete Team
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/teams/{team_id}/`
- **Response**: `{ "message": "Team deleted" }`

### 3.6 Add Members to Team
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/teams/{team_id}/members/`
- **Request Body**:
```json
{
  "member_ids": ["member_1", "member_2"]
}
```
- **Response**: `{ "message": "Members added" }`

### 3.7 Remove Member from Team
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/teams/{team_id}/members/{member_id}/`
- **Response**: `{ "message": "Member removed" }`

---

## 4. MEMBER ENDPOINTS

### 4.1 List Organization Members
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/members/`
- **Query Params**: 
  - `status` (optional): Filter by status (active, inactive, pending, suspended)
  - `team_id` (optional): Filter by team
  - `role_id` (optional): Filter by role
- **Response**: Array of `OrganizationMember`
```json
[
  {
    "id": "member_123",
    "user_id": "user_123",
    "organization_id": "org_123",
    "email": "member@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "avatar_url": "https://...",
    "job_title": "Sales Manager",
    "phone": "+1234567890",
    "status": "active",
    "role": {
      "id": "role_123",
      "name": "Manager",
      "description": "...",
      "permissions": { ... }
    },
    "teams": [
      {
        "id": "team_123",
        "name": "Sales Team"
      }
    ],
    "joined_at": "2024-01-01T00:00:00Z",
    "last_active_at": "2024-01-15T10:30:00Z"
  }
]
```

### 4.2 Get Member Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/members/{member_id}/`
- **Response**: Single `OrganizationMember` object

### 4.3 Get Current User's Member Profile
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/members/me/`
- **Response**: Single `OrganizationMember` object for current user

### 4.4 Update Member
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/members/{member_id}/`
- **Request Body**:
```json
{
  "role_id": "role_456",
  "status": "active",
  "job_title": "Senior Manager",
  "team_ids": ["team_1", "team_2"]
}
```
- **Response**: Updated `OrganizationMember` object
- **Note**: Only admins/owners can change role_id and status

### 4.5 Remove Member from Organization
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/members/{member_id}/`
- **Response**: `{ "message": "Member removed" }`
- **Note**: Cannot remove owner

---

## 5. ROLE ENDPOINTS

### 5.1 List Roles (for organization)
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/roles/`
- **Response**: Array of `Role`
```json
[
  {
    "id": "role_123",
    "name": "Manager",
    "description": "Can manage team data",
    "permissions": {
      "contacts": ["view", "create", "edit", "export"],
      "leads": ["view", "create", "edit", "export"],
      "deals": ["view", "create", "edit"],
      "tasks": ["view", "create", "edit", "delete"],
      "reports": ["view", "create", "export"],
      "settings": ["view"],
      "team": ["view", "edit"],
      "organization": ["view"]
    },
    "is_default": false,
    "is_system": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### 5.2 Get Role Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/roles/{role_id}/`
- **Response**: Single `Role` object

### 5.3 Create Custom Role
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/roles/`
- **Request Body**:
```json
{
  "name": "Custom Role",
  "description": "Custom role description",
  "permissions": {
    "contacts": ["view", "create"],
    "leads": ["view"],
    "deals": [],
    "tasks": ["view"],
    "reports": ["view"],
    "settings": [],
    "team": [],
    "organization": []
  },
  "is_default": false
}
```
- **Response**: `Role` object
- **Note**: Cannot create system roles

### 5.4 Update Role
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/roles/{role_id}/`
- **Request Body**: Same as create (partial updates allowed)
- **Response**: Updated `Role` object
- **Note**: Cannot update system roles

### 5.5 Delete Role
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/roles/{role_id}/`
- **Response**: `{ "message": "Role deleted" }`
- **Note**: Cannot delete system roles or roles in use

---

## 6. INVITATION ENDPOINTS

### 6.1 List Invitations (for organization)
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/invitations/`
- **Query Params**:
  - `status` (optional): Filter by status (pending, accepted, expired, cancelled)
- **Response**: Array of `Invitation`
```json
[
  {
    "id": "inv_123",
    "organization_id": "org_123",
    "email": "newuser@example.com",
    "role_id": "role_123",
    "team_ids": ["team_1"],
    "status": "pending",
    "invited_by": "user_123",
    "invited_at": "2024-01-01T00:00:00Z",
    "expires_at": "2024-01-08T00:00:00Z",
    "accepted_at": null,
    "token": "invitation_token_123"
  }
]
```

### 6.2 Get Invitation Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/invitations/{invitation_id}/`
- **Response**: Single `Invitation` object

### 6.3 Send Invitation
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/invitations/`
- **Request Body**:
```json
{
  "email": "newuser@example.com",
  "role_id": "role_123",
  "team_ids": ["team_1", "team_2"],
  "message": "Optional invitation message"
}
```
- **Response**: `Invitation` object
- **Note**: Should send email with invitation link

### 6.4 Cancel Invitation
- **Method**: `POST` or `PATCH`
- **Endpoint**: `/v1/organizations/{org_id}/invitations/{invitation_id}/cancel/`
- **Request Body**: None
- **Response**: `{ "message": "Invitation cancelled" }`

### 6.5 Accept Invitation (Public endpoint)
- **Method**: `POST`
- **Endpoint**: `/v1/invitations/{token}/accept/`
- **Request Body**:
```json
{
  "user_id": "user_123" // if user already exists
  // OR create new user
  "first_name": "John",
  "last_name": "Doe",
  "password": "password123"
}
```
- **Response**: `AuthResponse` (same as login)

### 6.6 Resend Invitation
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/invitations/{invitation_id}/resend/`
- **Request Body**: None
- **Response**: `{ "message": "Invitation resent" }`

---

## 7. CONTACT ENDPOINTS

### 7.1 List Contacts
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/`
- **Query Params**:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 10)
  - `search` (optional): Search in name, email, company
  - `status` (optional): Filter by status (active, inactive) - can be array
  - `tags` (optional): Filter by tags - array of tag names
  - `assigned_to` (optional): Filter by assigned member - array of member IDs
  - `source` (optional): Filter by source - array
  - `created_from` (optional): Filter by created date from (ISO date)
  - `created_to` (optional): Filter by created date to (ISO date)
  - `sort_by` (optional): Field to sort by (e.g., "created_at", "first_name")
  - `sort_order` (optional): "asc" or "desc" (default: "desc")
- **Response**: Paginated `Contact` array
```json
{
  "data": [
    {
      "id": "contact_123",
      "organization_id": "org_123",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "mobile": "+1234567891",
      "company": "Acme Corp",
      "job_title": "CEO",
      "department": "Executive",
      "website": "https://acme.com",
      "address": {
        "street": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA"
      },
      "status": "active",
      "tags": ["VIP", "Enterprise"],
      "assigned_to": "member_123",
      "assigned_to_name": "Jane Smith",
      "source": "website",
      "notes": "Important client",
      "avatar_url": "https://...",
      "social_profiles": {
        "linkedin": "https://linkedin.com/in/johndoe",
        "twitter": "@johndoe"
      },
      "custom_fields": {},
      "created_by": "user_123",
      "created_by_name": "Current User",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z",
      "last_contacted_at": "2024-01-10T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10
}
```

### 7.2 Get Contact Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/{contact_id}/`
- **Response**: Single `Contact` object

### 7.3 Create Contact
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/`
- **Request Body**:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "mobile": "+1234567891",
  "company": "Acme Corp",
  "job_title": "CEO",
  "department": "Executive",
  "website": "https://acme.com",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  },
  "status": "active",
  "tags": ["VIP", "Enterprise"],
  "assigned_to": "member_123",
  "source": "website",
  "notes": "Important client",
  "social_profiles": {
    "linkedin": "https://linkedin.com/in/johndoe"
  },
  "custom_fields": {}
}
```
- **Response**: Created `Contact` object

### 7.4 Update Contact
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/{contact_id}/`
- **Request Body**: Same as create (all fields optional)
- **Response**: Updated `Contact` object

### 7.5 Delete Contact
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/{contact_id}/`
- **Response**: `{ "message": "Contact deleted" }`

### 7.6 Bulk Delete Contacts
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/bulk-delete/`
- **Request Body**:
```json
{
  "contact_ids": ["contact_1", "contact_2", "contact_3"]
}
```
- **Response**: `{ "message": "3 contacts deleted", "deleted_count": 3 }`

### 7.7 Bulk Update Contacts
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/bulk-update/`
- **Request Body**:
```json
{
  "contact_ids": ["contact_1", "contact_2"],
  "updates": {
    "assigned_to": "member_123",
    "tags": ["New Tag"]
  }
}
```
- **Response**: `{ "message": "2 contacts updated", "updated_count": 2 }`

### 7.8 Import Contacts (CSV)
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/import/`
- **Content-Type**: `multipart/form-data`
- **Request Body**: Form data with `file` field (CSV file)
- **Response**:
```json
{
  "total": 100,
  "successful": 95,
  "failed": 5,
  "errors": [
    {
      "row": 3,
      "field": "email",
      "message": "Invalid email format",
      "data": { "first_name": "John", "email": "invalid" }
    }
  ]
}
```

### 7.9 Export Contacts
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/export/`
- **Query Params**: Same filters as list endpoint
- **Response**: CSV file download
- **Content-Type**: `text/csv`

### 7.10 Get Contact Statistics
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/stats/`
- **Response**: `ContactStats`
```json
{
  "total": 150,
  "active": 120,
  "inactive": 30,
  "by_source": {
    "website": 50,
    "referral": 30,
    "social": 20,
    "campaign": 30,
    "other": 20
  },
  "by_tag": {
    "VIP": 10,
    "Enterprise": 25,
    "SMB": 50
  },
  "recent_count": 15
}
```

### 7.11 Get Contact Tags
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/tags/`
- **Response**: Array of `Tag`
```json
[
  {
    "id": "tag_123",
    "organization_id": "org_123",
    "name": "VIP",
    "color": "#1677ff",
    "usage_count": 10,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### 7.12 Create Contact Tag
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/tags/`
- **Request Body**:
```json
{
  "name": "New Tag",
  "color": "#52c41a"
}
```
- **Response**: `Tag` object

---

## 8. LEAD ENDPOINTS

### 8.1 List Leads
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/leads/`
- **Query Params**:
  - `page` (optional): Page number (default: 1)
  - `page_size` (optional): Items per page (default: 10)
  - `search` (optional): Search in name, email, company
  - `status` (optional): Filter by status - array (new, contacted, qualified, unqualified, converted)
  - `source` (optional): Filter by source - array
  - `priority` (optional): Filter by priority - array (low, medium, high, urgent)
  - `tags` (optional): Filter by tags - array
  - `assigned_to` (optional): Filter by assigned member - array
  - `score_min` (optional): Minimum lead score (0-100)
  - `score_max` (optional): Maximum lead score (0-100)
  - `created_from` (optional): Filter by created date from (ISO date)
  - `created_to` (optional): Filter by created date to (ISO date)
  - `sort_by` (optional): Field to sort by
  - `sort_order` (optional): "asc" or "desc"
- **Response**: Paginated `Lead` array
```json
{
  "data": [
    {
      "id": "lead_123",
      "organization_id": "org_123",
      "contact_id": "contact_123",
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "+1234567890",
      "company": "Tech Corp",
      "job_title": "CTO",
      "website": "https://techcorp.com",
      "source": "website",
      "status": "qualified",
      "score": 75,
      "priority": "high",
      "estimated_value": 50000,
      "currency": "USD",
      "assigned_to": "member_123",
      "assigned_to_name": "John Doe",
      "notes": "Interested in enterprise plan",
      "tags": ["Enterprise", "Hot Lead"],
      "custom_fields": {},
      "created_by": "user_123",
      "created_by_name": "Current User",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T00:00:00Z",
      "converted_at": null,
      "converted_to_contact_id": null,
      "last_activity_at": "2024-01-14T00:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

### 8.2 Get Leads by Status (for Kanban)
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/leads/by-status/`
- **Query Params**: Optional filters (same as list)
- **Response**: Object grouped by status
```json
{
  "new": [...],
  "contacted": [...],
  "qualified": [...],
  "unqualified": [...],
  "converted": [...]
}
```

### 8.3 Get Lead Details
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/`
- **Response**: Single `Lead` object

### 8.4 Create Lead
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/leads/`
- **Request Body**:
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "company": "Tech Corp",
  "job_title": "CTO",
  "website": "https://techcorp.com",
  "source": "website",
  "status": "new",
  "priority": "medium",
  "estimated_value": 50000,
  "currency": "USD",
  "assigned_to": "member_123",
  "notes": "Interested in enterprise plan",
  "tags": ["Enterprise"],
  "custom_fields": {}
}
```
- **Response**: Created `Lead` object
- **Note**: `score` should be auto-calculated or default to a value

### 8.5 Update Lead
- **Method**: `PATCH` or `PUT`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/`
- **Request Body**: Same as create (all fields optional)
- **Response**: Updated `Lead` object

### 8.6 Update Lead Status
- **Method**: `PATCH`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/status/`
- **Request Body**:
```json
{
  "status": "qualified"
}
```
- **Response**: Updated `Lead` object
- **Note**: If status is "converted", should set `converted_at` timestamp

### 8.7 Delete Lead
- **Method**: `DELETE`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/`
- **Response**: `{ "message": "Lead deleted" }`

### 8.8 Convert Lead to Contact
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/convert/`
- **Request Body**:
```json
{
  "create_contact": true,
  "contact_data": {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com"
  }
}
```
- **Response**:
```json
{
  "lead": { ... },
  "contact": { ... },
  "message": "Lead converted to contact"
}
```

### 8.9 Get Lead Statistics
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/leads/stats/`
- **Response**: `LeadStats`
```json
{
  "total": 100,
  "by_status": {
    "new": 20,
    "contacted": 30,
    "qualified": 25,
    "unqualified": 15,
    "converted": 10
  },
  "by_source": {
    "website": 40,
    "referral": 20,
    "social": 15,
    "campaign": 15,
    "other": 10
  },
  "by_priority": {
    "low": 20,
    "medium": 40,
    "high": 30,
    "urgent": 10
  },
  "conversion_rate": 10.0,
  "average_score": 65.5,
  "total_estimated_value": 2500000,
  "recent_count": 15
}
```

### 8.10 Update Lead Score
- **Method**: `PATCH`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/score/`
- **Request Body**:
```json
{
  "score": 80
}
```
- **Response**: Updated `Lead` object
- **Note**: Score should be 0-100

---

## 9. ACTIVITY/TIMELINE ENDPOINTS

### 9.1 Get Contact Activities
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/{contact_id}/activities/`
- **Query Params**:
  - `page` (optional)
  - `page_size` (optional)
- **Response**: Paginated `Activity` array
```json
{
  "data": [
    {
      "id": "activity_123",
      "entity_type": "contact",
      "entity_id": "contact_123",
      "type": "note",
      "title": "Follow-up call",
      "description": "Discussed pricing options",
      "metadata": {},
      "created_by": "user_123",
      "created_by_name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

### 9.2 Get Lead Activities
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/leads/{lead_id}/activities/`
- **Query Params**: Same as contact activities
- **Response**: Paginated `Activity` array

### 9.3 Create Activity
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/activities/`
- **Request Body**:
```json
{
  "entity_type": "contact",
  "entity_id": "contact_123",
  "type": "note",
  "title": "Follow-up call",
  "description": "Discussed pricing options",
  "metadata": {}
}
```
- **Response**: Created `Activity` object

---

## 10. DASHBOARD/AGGREGATION ENDPOINTS

### 10.1 Get Dashboard Statistics
- **Method**: `GET`
- **Endpoint**: `/v1/organizations/{org_id}/dashboard/stats/`
- **Response**:
```json
{
  "contacts": {
    "total": 150,
    "active": 120,
    "inactive": 30,
    "recent_count": 15
  },
  "leads": {
    "total": 100,
    "qualified": 25,
    "conversion_rate": 10.0,
    "total_estimated_value": 2500000
  },
  "recent_contacts": [...], // Last 5 contacts
  "recent_leads": [...] // Last 5 leads
}
```

---

## 11. FILE UPLOAD ENDPOINTS

### 11.1 Upload Organization Logo
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/logo/`
- **Content-Type**: `multipart/form-data`
- **Request Body**: Form data with `file` field
- **Response**:
```json
{
  "logo_url": "https://cdn.example.com/logos/org_123.png"
}
```

### 11.2 Upload Contact Avatar
- **Method**: `POST`
- **Endpoint**: `/v1/organizations/{org_id}/contacts/{contact_id}/avatar/`
- **Content-Type**: `multipart/form-data`
- **Request Body**: Form data with `file` field
- **Response**:
```json
{
  "avatar_url": "https://cdn.example.com/avatars/contact_123.png"
}
```

---

## ERROR RESPONSES

All endpoints should return consistent error responses:

### 400 Bad Request
```json
{
  "error": "Validation Error",
  "message": "Invalid input data",
  "details": {
    "email": ["This field is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Authentication credentials were not provided"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "You do not have permission to perform this action"
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## NOTES FOR BACKEND TEAM

1. **Organization Context**: Most endpoints require `org_id` in the path. The frontend will determine the current organization from the user's context.

2. **Pagination**: All list endpoints should support pagination with `page` and `page_size` query parameters.

3. **Filtering**: List endpoints should support multiple filter options via query parameters. Arrays can be passed as comma-separated values or multiple query params.

4. **Sorting**: List endpoints should support `sort_by` and `sort_order` query parameters.

5. **Permissions**: The backend should enforce role-based permissions. The frontend will check permissions but backend must validate.

6. **Multi-tenancy**: All data must be scoped to the organization. Users should only access data from organizations they belong to.

7. **Default Roles**: When an organization is created, default roles (Owner, Admin, Manager, Member, Viewer) should be automatically created.

8. **Invitations**: Invitation tokens should expire after 7 days. Email notifications should be sent when invitations are created.

9. **Lead Scoring**: Lead scores should be calculated based on various factors (engagement, company size, etc.) or can be manually updated.

10. **Activity Tracking**: Activities should be automatically created for status changes, assignments, and other important events.

11. **File Uploads**: Logo and avatar uploads should return CDN URLs or storage URLs.

12. **Search**: Search functionality should search across multiple fields (name, email, company, etc.).

13. **Bulk Operations**: Bulk delete and update operations should be transactional and return detailed results.

14. **Export**: CSV export should include all filtered results, not just current page.

15. **Statistics**: Stats endpoints should be optimized for performance, possibly using cached data or materialized views.

---

## ENDPOINT SUMMARY COUNT

- **Authentication**: 5 endpoints
- **Organization**: 5 endpoints
- **Teams**: 7 endpoints
- **Members**: 5 endpoints
- **Roles**: 5 endpoints
- **Invitations**: 6 endpoints
- **Contacts**: 12 endpoints
- **Leads**: 10 endpoints
- **Activities**: 3 endpoints
- **Dashboard**: 1 endpoint
- **File Uploads**: 2 endpoints

**Total: 61 API endpoints**

---

This document should be used as a reference for backend implementation. All endpoints should follow RESTful conventions and return consistent response formats.

