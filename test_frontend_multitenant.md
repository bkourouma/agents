# Frontend Multi-Tenant Testing Guide

## 🎯 Overview

This document provides a comprehensive testing guide for the frontend multi-tenant implementation. Since frontend testing requires manual interaction with the UI, this guide provides step-by-step instructions for validating tenant isolation and functionality.

## ✅ Test Scenarios

### 1. **Authentication & Tenant Context**

#### Test 1.1: User Login with Tenant Information
**Steps:**
1. Navigate to `/login`
2. Login with valid credentials
3. Verify that user information includes `tenant_id`
4. Check that tenant information is loaded and displayed

**Expected Results:**
- ✅ User object contains `tenant_id` field
- ✅ Tenant information is fetched and stored in context
- ✅ TenantHeader displays tenant name, plan, and status
- ✅ Dashboard shows tenant-specific information

#### Test 1.2: Tenant Header Display
**Steps:**
1. Login and navigate to any page
2. Verify TenantHeader is displayed at the top
3. Check tenant information display
4. Verify admin controls (if user is tenant admin)

**Expected Results:**
- ✅ Tenant name and slug are displayed
- ✅ Plan badge shows correct plan (Free, Starter, Professional, Enterprise)
- ✅ Status badge shows correct status (Active, Trial, Suspended)
- ✅ Usage statistics are displayed (users, agents, storage)
- ✅ Admin controls visible only for tenant admins

### 2. **Tenant Dashboard Functionality**

#### Test 2.1: Dashboard Overview
**Steps:**
1. Navigate to `/dashboard` (or `/`)
2. Verify tenant dashboard components load
3. Check usage statistics and warnings
4. Test quick action buttons

**Expected Results:**
- ✅ Tenant overview section displays correct information
- ✅ Usage statistics show current vs. limits
- ✅ Progress bars reflect actual usage percentages
- ✅ Warning messages appear when approaching limits
- ✅ Quick action buttons navigate to correct pages

#### Test 2.2: Usage Warnings
**Steps:**
1. Simulate high usage scenarios (if possible)
2. Check for warning messages when usage > 80%
3. Verify error styling when usage > 95%

**Expected Results:**
- ✅ Yellow warnings appear at 80% usage
- ✅ Red errors appear at 95% usage
- ✅ Storage warnings show in toast notifications
- ✅ Warnings are dismissible and informative

### 3. **Tenant Context Propagation**

#### Test 3.1: Context Availability
**Steps:**
1. Navigate to different pages while logged in
2. Open browser developer tools
3. Check React DevTools for context values
4. Verify tenant context is available throughout app

**Expected Results:**
- ✅ AuthContext contains user and tenant objects
- ✅ TenantContext provides stats and usage data
- ✅ Context values persist across page navigation
- ✅ Context refreshes when tenant data changes

#### Test 3.2: API Calls with Tenant Context
**Steps:**
1. Monitor network requests in browser DevTools
2. Navigate to pages that make API calls (agents, chat, etc.)
3. Verify API calls include proper authentication
4. Check that responses are tenant-scoped

**Expected Results:**
- ✅ All API calls include Authorization header
- ✅ Responses contain only tenant-scoped data
- ✅ No cross-tenant data leakage in responses
- ✅ Error handling for tenant-related failures

### 4. **Multi-Tenant UI Components**

#### Test 4.1: Agent Management
**Steps:**
1. Navigate to `/agents`
2. Verify only tenant's agents are displayed
3. Test agent creation (if within limits)
4. Check agent permissions and access

**Expected Results:**
- ✅ Agent list shows only tenant's agents
- ✅ Agent creation respects tenant limits
- ✅ Agent details show tenant context
- ✅ No access to other tenants' agents

#### Test 4.2: Chat Interface
**Steps:**
1. Navigate to `/chat`
2. Start a conversation
3. Verify conversation is tenant-scoped
4. Check message history isolation

**Expected Results:**
- ✅ Chat interface loads with tenant context
- ✅ Conversations are isolated to tenant
- ✅ Message history is tenant-specific
- ✅ Agent routing respects tenant boundaries

#### Test 4.3: Knowledge Base
**Steps:**
1. Navigate to `/file-upload`
2. Upload documents
3. Verify documents are tenant-scoped
4. Test document search and retrieval

**Expected Results:**
- ✅ File uploads are tenant-isolated
- ✅ Document list shows only tenant's files
- ✅ Search results are tenant-scoped
- ✅ No access to other tenants' documents

### 5. **Tenant Administration (Admin Users Only)**

#### Test 5.1: Tenant Settings Access
**Steps:**
1. Login as tenant admin
2. Verify admin controls in TenantHeader
3. Test navigation to tenant management pages
4. Check permission restrictions for non-admin users

**Expected Results:**
- ✅ Admin badge displayed for tenant admins
- ✅ Tenant management dropdown available
- ✅ Admin-only pages accessible
- ✅ Non-admin users cannot access admin features

#### Test 5.2: Usage Monitoring
**Steps:**
1. As tenant admin, check usage statistics
2. Verify real-time usage updates
3. Test usage limit warnings
4. Check historical usage data (if available)

**Expected Results:**
- ✅ Accurate usage statistics displayed
- ✅ Real-time updates when usage changes
- ✅ Proactive warnings before limits reached
- ✅ Historical data shows usage trends

### 6. **Error Handling & Edge Cases**

#### Test 6.1: Network Failures
**Steps:**
1. Simulate network disconnection
2. Test API failure scenarios
3. Verify error messages and recovery
4. Check offline behavior

**Expected Results:**
- ✅ Graceful handling of network failures
- ✅ Informative error messages in French
- ✅ Automatic retry mechanisms where appropriate
- ✅ Cached data used when available

#### Test 6.2: Invalid Tenant Data
**Steps:**
1. Simulate invalid tenant responses
2. Test with missing tenant information
3. Verify fallback behavior
4. Check error boundaries

**Expected Results:**
- ✅ Graceful degradation with invalid data
- ✅ Fallback UI when tenant data unavailable
- ✅ Error boundaries prevent app crashes
- ✅ Clear error messages for users

### 7. **Performance & User Experience**

#### Test 7.1: Loading Performance
**Steps:**
1. Measure page load times
2. Check for loading indicators
3. Test with slow network conditions
4. Verify smooth transitions

**Expected Results:**
- ✅ Fast initial page loads
- ✅ Loading indicators during data fetching
- ✅ Smooth transitions between pages
- ✅ Responsive UI during loading states

#### Test 7.2: Mobile Responsiveness
**Steps:**
1. Test on mobile devices or browser dev tools
2. Verify tenant header responsiveness
3. Check dashboard layout on small screens
4. Test touch interactions

**Expected Results:**
- ✅ Responsive design works on all screen sizes
- ✅ Tenant header adapts to mobile layout
- ✅ Dashboard components stack properly
- ✅ Touch interactions work correctly

## 🔧 Testing Tools & Setup

### Browser Developer Tools
1. **Network Tab**: Monitor API calls and responses
2. **Console**: Check for JavaScript errors
3. **Application Tab**: Verify localStorage data
4. **React DevTools**: Inspect component state and context

### Test Data Setup
1. Create multiple test tenants with different plans
2. Set up users with different roles (admin/non-admin)
3. Create test data at different usage levels
4. Prepare scenarios for limit testing

### Manual Testing Checklist

#### Pre-Testing Setup
- [ ] Clear browser cache and localStorage
- [ ] Ensure test tenants exist in database
- [ ] Verify API endpoints are accessible
- [ ] Check that frontend is running on correct port

#### Authentication Flow
- [ ] Login with tenant admin user
- [ ] Login with regular tenant user
- [ ] Verify logout clears tenant context
- [ ] Test token refresh scenarios

#### Tenant Context
- [ ] Verify tenant information loads correctly
- [ ] Check context propagation across pages
- [ ] Test context refresh functionality
- [ ] Validate error handling for missing tenant

#### UI Components
- [ ] TenantHeader displays correctly
- [ ] TenantDashboard shows accurate data
- [ ] Usage warnings appear appropriately
- [ ] Admin controls work for authorized users

#### Data Isolation
- [ ] Agents list shows only tenant's agents
- [ ] Conversations are tenant-scoped
- [ ] Documents are isolated by tenant
- [ ] No cross-tenant data visible

#### Performance
- [ ] Pages load within acceptable time
- [ ] No memory leaks in long sessions
- [ ] Smooth navigation between pages
- [ ] Responsive design works correctly

## 🚨 Common Issues & Troubleshooting

### Issue 1: Tenant Context Not Loading
**Symptoms:** TenantHeader not displaying, missing tenant data
**Solutions:**
- Check API endpoint for tenant data
- Verify user has valid tenant_id
- Check network requests for errors
- Clear localStorage and re-login

### Issue 2: Cross-Tenant Data Visible
**Symptoms:** Seeing data from other tenants
**Solutions:**
- Check API responses for proper filtering
- Verify authentication headers
- Check database queries include tenant_id
- Review API endpoint implementations

### Issue 3: Usage Statistics Incorrect
**Symptoms:** Wrong usage percentages or limits
**Solutions:**
- Verify tenant limits in database
- Check usage calculation logic
- Refresh tenant data manually
- Check for caching issues

### Issue 4: Admin Controls Not Visible
**Symptoms:** Tenant admin cannot see management options
**Solutions:**
- Verify user has is_tenant_admin flag
- Check role-based rendering logic
- Refresh user context
- Check authentication state

## 📊 Success Criteria

The frontend multi-tenant implementation is successful when:

1. **Complete Tenant Isolation**: Users can only see and interact with their tenant's data
2. **Accurate Context Propagation**: Tenant context is available throughout the application
3. **Proper Permission Handling**: Admin features are only available to authorized users
4. **Responsive UI**: Interface adapts to different screen sizes and usage scenarios
5. **Error Resilience**: Graceful handling of network failures and invalid data
6. **Performance**: Fast loading times and smooth user interactions
7. **Accessibility**: Interface is usable by all users regardless of abilities

## 🎉 Completion Verification

To verify the frontend multi-tenant implementation is complete:

1. ✅ All test scenarios pass
2. ✅ No cross-tenant data leakage observed
3. ✅ Tenant context works across all pages
4. ✅ Admin features properly restricted
5. ✅ Usage monitoring accurate and responsive
6. ✅ Error handling robust and user-friendly
7. ✅ Performance meets requirements
8. ✅ Mobile responsiveness verified
