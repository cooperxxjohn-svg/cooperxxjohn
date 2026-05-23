# Day 4 Plan: Authentication & User Management

**Date**: May 23, 2026  
**Goal**: Implement JWT authentication and secure user management  
**Hours**: 10 (10 hrs/day target)  

---

## 🎯 Day 4 Objectives

### Primary Goals
1. Implement JWT authentication
2. User registration and login endpoints
3. Password hashing with bcrypt
4. Protected API routes
5. Session management
6. User profile management
7. Email validation
8. Error handling for auth flows

### Success Criteria
- ✅ User can register with email/password
- ✅ User can login and receive JWT token
- ✅ Protected routes require valid token
- ✅ Tokens expire and refresh properly
- ✅ Passwords are securely hashed
- ✅ All auth tests passing

---

## 📋 Hour-by-Hour Plan

### Hours 1-2: JWT Authentication Setup (2 hrs)

**Hour 1: Dependencies & Configuration**
- [ ] Install PyJWT, passlib, python-jose
- [ ] Create auth configuration (SECRET_KEY, algorithm)
- [ ] Create auth utilities module
- [ ] JWT token generation function
- [ ] JWT token verification function

**Hour 2: Password Hashing & Validation**
- [ ] Install bcrypt
- [ ] Password hashing functions
- [ ] Password verification
- [ ] Email validation
- [ ] Strong password requirements
- [ ] Helper functions

**Deliverables**:
- backend/auth.py with auth utilities
- backend/config.py with auth settings
- JWT functions working

---

### Hours 3-4: Registration & Login Endpoints (2 hrs)

**Hour 3: User Registration**
- [ ] POST /api/auth/register endpoint
- [ ] Email uniqueness validation
- [ ] Password strength validation
- [ ] Create user with hashed password
- [ ] Return JWT token on registration
- [ ] Error handling (duplicate email, weak password)

**Hour 4: User Login**
- [ ] POST /api/auth/login endpoint
- [ ] Verify email and password
- [ ] Return JWT token on success
- [ ] Return user info (without password)
- [ ] Error handling (wrong credentials, user not found)
- [ ] Rate limiting considerations

**Deliverables**:
- Registration endpoint working
- Login endpoint working
- JWT tokens generated

---

### Hours 5-6: Protected Routes & Middleware (2 hrs)

**Hour 5: Auth Middleware**
- [ ] Create @require_auth decorator
- [ ] Extract token from Authorization header
- [ ] Verify token and extract user_id
- [ ] Attach user to request context
- [ ] Handle expired tokens
- [ ] Handle invalid tokens

**Hour 6: Protect Existing Routes**
- [ ] Update GET /api/projects (user's projects only)
- [ ] Update POST /api/estimate/* (require auth)
- [ ] Update POST /api/boq/* (require auth)
- [ ] Update DELETE /api/projects/:id (owner only)
- [ ] Add GET /api/users/me (current user)
- [ ] Test all protected routes

**Deliverables**:
- Auth middleware working
- All routes protected
- User context in requests

---

### Hours 7-8: Token Refresh & Profile Management (2 hrs)

**Hour 7: Token Refresh**
- [ ] POST /api/auth/refresh endpoint
- [ ] Refresh token generation
- [ ] Refresh token validation
- [ ] Short-lived access tokens (15 min)
- [ ] Long-lived refresh tokens (7 days)
- [ ] Token blacklist (logout)

**Hour 8: User Profile**
- [ ] GET /api/users/me endpoint
- [ ] PUT /api/users/me (update profile)
- [ ] PUT /api/users/me/password (change password)
- [ ] Email change with verification (future)
- [ ] Profile validation

**Deliverables**:
- Token refresh working
- Profile management complete

---

### Hours 9-10: Testing & Documentation (2 hrs)

**Hour 9: Authentication Tests**
- [ ] Test registration (success, duplicate, weak password)
- [ ] Test login (success, wrong password, user not found)
- [ ] Test protected routes (with/without token)
- [ ] Test token expiration
- [ ] Test token refresh
- [ ] Test password change
- [ ] All tests passing

**Hour 10: Documentation & Polish**
- [ ] Create AUTH.md documentation
- [ ] Update API documentation
- [ ] Update frontend for authentication
- [ ] Create auth flow diagrams
- [ ] Day 4 completion summary

**Deliverables**:
- Comprehensive auth tests
- Complete documentation
- Day 4 summary

---

## 🔐 Authentication Flow

### Registration Flow
```
1. POST /api/auth/register
   {
     "email": "user@example.com",
     "password": "SecurePass123!",
     "name": "John Doe"
   }

2. Validate email (format, uniqueness)
3. Validate password (strength)
4. Hash password with bcrypt
5. Create user in database
6. Generate JWT access token (15min)
7. Generate JWT refresh token (7 days)
8. Return tokens + user info

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Login Flow
```
1. POST /api/auth/login
   {
     "email": "user@example.com",
     "password": "SecurePass123!"
   }

2. Find user by email
3. Verify password hash
4. Generate new JWT tokens
5. Return tokens + user info

Response: Same as registration
```

### Protected Route Flow
```
1. GET /api/projects
   Headers: {
     "Authorization": "Bearer eyJ..."
   }

2. Extract token from header
3. Verify token signature
4. Check token expiration
5. Extract user_id from token
6. Load user from database
7. Attach user to request
8. Execute endpoint logic
9. Return user's projects only

Response:
{
  "projects": [...],
  "total": 5
}
```

### Token Refresh Flow
```
1. POST /api/auth/refresh
   {
     "refresh_token": "eyJ..."
   }

2. Verify refresh token
3. Extract user_id
4. Generate new access token
5. Optionally generate new refresh token
6. Return new tokens

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 900
}
```

---

## 📦 Dependencies to Add

```txt
# Authentication
PyJWT==2.8.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Email validation
email-validator==2.1.0
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Requirements
MIN_PASSWORD_LENGTH=8
REQUIRE_PASSWORD_UPPERCASE=true
REQUIRE_PASSWORD_LOWERCASE=true
REQUIRE_PASSWORD_DIGIT=true
REQUIRE_PASSWORD_SPECIAL=false
```

---

## 🧪 Testing Strategy

### Unit Tests
1. Password hashing/verification
2. JWT token generation/verification
3. Email validation
4. Password strength validation

### Integration Tests
1. Register new user
2. Login with correct credentials
3. Login with wrong credentials
4. Access protected route without token
5. Access protected route with valid token
6. Access protected route with expired token
7. Refresh access token
8. Update user profile
9. Change password

### Security Tests
1. SQL injection attempts
2. XSS in user inputs
3. Brute force login attempts
4. Token tampering
5. Expired token usage

---

## 🔒 Security Best Practices

### Password Security
- ✅ Bcrypt with salt rounds (12+)
- ✅ Minimum length (8 characters)
- ✅ Complexity requirements
- ✅ No password in responses
- ✅ Secure password reset (future)

### Token Security
- ✅ Short-lived access tokens (15 min)
- ✅ Secure secret key (environment variable)
- ✅ HTTPS only in production
- ✅ HttpOnly cookies (optional)
- ✅ Token blacklist for logout

### API Security
- ✅ Rate limiting (future)
- ✅ Input validation
- ✅ SQL injection prevention (ORM)
- ✅ XSS prevention
- ✅ CORS configuration

---

## 📊 Success Metrics

### Functional
- [ ] Users can register
- [ ] Users can login
- [ ] Tokens work for authentication
- [ ] Protected routes enforce auth
- [ ] Token refresh works
- [ ] Profile management works

### Security
- [ ] Passwords securely hashed
- [ ] Tokens properly signed
- [ ] Tokens expire correctly
- [ ] No sensitive data in responses
- [ ] Input validation working

### Quality
- [ ] All tests passing (20+ tests)
- [ ] Error messages helpful
- [ ] Code documented
- [ ] API consistent

---

## 🚨 Potential Challenges

### Challenge 1: Secret Key Management
**Risk**: Hardcoded secrets in code
**Mitigation**: Environment variables, never commit

### Challenge 2: Token Expiration
**Risk**: Users logged out unexpectedly
**Mitigation**: Refresh tokens, clear expiration times

### Challenge 3: Password Requirements
**Risk**: Too strict = frustrated users, too loose = insecure
**Mitigation**: Reasonable defaults, configurable

### Challenge 4: Existing Demo User
**Risk**: Breaking existing functionality
**Mitigation**: Keep demo user for testing, add real auth alongside

---

## 🔄 Migration Strategy

### Backward Compatibility
1. Keep demo user authentication working
2. Add auth as optional (for now)
3. Gradually move to required auth
4. Update frontend to handle tokens

### Database Migration
```bash
# Already have password_hash column in users table
# Just need to add JWT secret to env
# No migration needed!
```

---

## 📝 Documentation Deliverables

### AUTH.md
- Authentication overview
- API endpoint documentation
- Code examples (curl, JavaScript)
- Error codes and messages
- Security best practices
- Troubleshooting guide

### Updated README.md
- Authentication section
- Environment variables
- Setup instructions

---

## 🎯 End of Day 4 Target

### What Should Work
1. ✅ Register new user → Returns JWT token
2. ✅ Login with email/password → Returns JWT token
3. ✅ Access protected route with token → Returns user's data
4. ✅ Access protected route without token → 401 Unauthorized
5. ✅ Refresh token → Returns new access token
6. ✅ Update profile → Updates user info
7. ✅ Change password → Updates password hash
8. ✅ All tests passing

### What's Ready for Day 5
- Complete authentication system
- User management working
- Ready for Stripe integration
- Ready for API key generation
- Ready for frontend integration

---

**Day 4 Start Time**: Now  
**Expected Completion**: 10 hours  
**Difficulty**: Medium (JWT + security considerations)  
**Priority**: HIGH (Required for production)

Let's build! 🔐
